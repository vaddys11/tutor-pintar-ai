"""
curriculum.py — Pipeline RAG buat fitur "Kelola Modul Kurikulum":
ekstraksi teks (PDF/TXT/MD) -> chunking -> embedding (lokal, gratis) -> simpan
ke Supabase (pgvector) -> similarity search saat chat (cuma modul status aktif).

Embedding pakai sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 —
jalan LOKAL di server (bukan panggil API luar), lisensi Apache-2.0, 100% gratis,
dukung resmi 50+ bahasa termasuk Indonesia. 384 dimensi (beda dari model OpenAI
yang 1536 — jangan dicampur, lihat migrations/003 kalau upgrade dari versi lama).

Trade-off yang perlu disadari:
- Model ini punya max_seq_length 128 token (~90-100 kata Indonesia). Chunk 600
  karakter kita kadang sedikit lebih panjang dari itu — bagian ekor chunk yang
  kepotong pas dibikin vector (teks aslinya tetap tersimpan utuh di DB, cuma
  representasi embedding-nya yang gak "melihat" ekor chunk kalau kepanjangan).
  Bukan bug, cuma karakteristik model kecil/cepat ini.
- Model (~470MB) di-download sekali dari HuggingFace pas pertama kali dipanggil,
  lalu di-cache di memory proses. Request pertama setelah server nyala/deploy
  ulang bakal terasa lebih lambat (nunggu download+load model).
- Nambah dependency berat (torch + transformers) ke requirements.txt — install
  & build time di Railway jadi lebih lama, image lebih besar. Ini trade-off
  wajar buat dapetin embedding gratis tanpa API luar.
"""
import io
import os
import re
import requests
from typing import Optional

import pypdf
from supabase import Client

HF_TOKEN = os.getenv("HF_TOKEN")
# Menggunakan Serverless API resmi dari Hugging Face untuk model MiniLM-L6-v2
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_DIMENSIONS = 384
CHUNK_SIZE = 600
CHUNK_OVERLAP = 60
EMBEDDING_BATCH_SIZE = 50

def get_embeddings_batch(texts: list[str]) -> Optional[list[list[float]]]:
    """
    Generate embedding via Hugging Face Serverless API (Ringan, tanpa RAM server/PyTorch).
    Return None kalau gagal — caller (process_and_store_document & search) tetep aman handle graceful.
    """
    if not texts:
        return None
        
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": texts,
        "options": {"wait_for_model": True}
    }
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            embeddings = response.json()
            # Memastikan format balikan adalah list of vectors
            if isinstance(embeddings, list):
                return embeddings
            return None
        else:
            print(f"[curriculum] HF API Error status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"[curriculum] Gagal panggil HF API: {e}")
        return None


def process_and_store_document(supabase: Client, doc_id: str, raw_text: str) -> None:
    """
    Background task (dipanggil lewat FastAPI BackgroundTasks): chunking -> embedding
    -> simpan ke curriculum_chunks -> update status doc jadi 'ready'/'failed'.
    Request upload/text gak nunggu proses ini kelar (langsung return duluan).
    """
    try:
        chunks = chunk_text(raw_text)
        if not chunks:
            supabase.table("curriculum_docs").update(
                {"processing_status": "failed", "chunk_count": 0}
            ).eq("id", doc_id).execute()
            return

        all_rows = []
        for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
            batch = chunks[i : i + EMBEDDING_BATCH_SIZE]
            embeddings = get_embeddings_batch(batch)
            if embeddings is None:
                raise RuntimeError("Embedding lokal gagal di-generate")
            for j, (chunk, emb) in enumerate(zip(batch, embeddings)):
                all_rows.append(
                    {"doc_id": doc_id, "chunk_index": i + j, "content": chunk, "embedding": emb}
                )

        # Insert per-batch juga, biar gak kena limit payload di sisi Supabase/PostgREST
        for i in range(0, len(all_rows), EMBEDDING_BATCH_SIZE):
            supabase.table("curriculum_chunks").insert(all_rows[i : i + EMBEDDING_BATCH_SIZE]).execute()

        supabase.table("curriculum_docs").update(
            {"processing_status": "ready", "chunk_count": len(all_rows)}
        ).eq("id", doc_id).execute()

    except Exception as e:
        print(f"[curriculum] Gagal proses dokumen {doc_id}: {e}")
        try:
            supabase.table("curriculum_docs").update({"processing_status": "failed"}).eq("id", doc_id).execute()
        except Exception:
            pass


def search_relevant_chunks(
    supabase: Optional[Client], query: str, jenjang: str, top_k: int = 4
) -> list[dict]:
    """
    Cari chunk kurikulum paling relevan buat query, HANYA dari modul berstatus 'aktif'
    dan sesuai jenjang (difilter di RPC Postgres `match_curriculum_chunks`).

    Selalu return [] kalau gagal apapun sebabnya — RAG ini enhancement, bukan hal
    yang boleh bikin fitur chat utama down kalau error (model gagal load, RPC belum
    ada, dsb). Chat tetap jalan normal tanpa konteks kurikulum kalau ini gagal.
    """
    if supabase is None or not query.strip():
        return []
    try:
        embeddings = get_embeddings_batch([query])
        if not embeddings:
            return []
        result = supabase.rpc(
            "match_curriculum_chunks",
            {"query_embedding": embeddings[0], "match_jenjang": jenjang, "match_count": top_k},
        ).execute()
        return result.data or []
    except Exception as e:
        print(f"[curriculum] Gagal similarity search: {e}")
        return []

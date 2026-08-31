"""
main.py — Backend FastAPI Tutor Pintar AI.
Migrasi dari app.py (Streamlit) — logika bisnis (llm.py, db.py, guardrail.py,
export.py) dipakai apa adanya, cuma lapisan presentasinya yang ganti dari
Streamlit widget jadi endpoint REST buat dikonsumsi frontend Next.js.
"""
import os
import re
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from llm import get_openrouter_client, generate_response_with_fallback, fetch_free_models
from db import (
    get_supabase_client,
    new_session_id,
    save_message,
    load_history,
    get_all_sessions,
    update_session_title,
    delete_session,
    session_exists,
)
from guardrail import detect_jailbreak_attempt, log_attempt, guardrail_refusal_message, check_output_too_direct
from export import generate_pdf
from prompts import build_system_instruction, VALID_JENJANG, QUIZ_TRIGGER_MESSAGE
from curriculum import search_relevant_chunks
from modules import router as modules_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Backend Tutor Pintar AI siap! (Embedding via HF API)")
    yield

app = FastAPI(title="Tutor Pintar AI — Backend", lifespan=lifespan)

# --- Pasang Middleware CORS Manual (Menjamin Header Terkirim 100%) ---
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    # Langsung tangani preflight OPTIONS dari browser
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Hapus / Komentari CORSMiddleware bawaan sebelumnya, lalu lanjutkan router:
app.include_router(modules_router)

# --- Client & resource level-module (mirip @st.cache_resource di versi Streamlit) ---
openrouter_client = get_openrouter_client()
supabase = get_supabase_client()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


# -----------------------------------------------------------------------------
# Skema request/response
# -----------------------------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: str
    jenjang: str
    message: str = Field(..., min_length=1, max_length=4000)
    mode: Literal["chat", "quiz"] = "chat"


class ChatResponse(BaseModel):
    reply: str
    model: Optional[str] = None
    blocked: bool = False


class SessionCreateRequest(BaseModel):
    jenjang: str = "SD (Sekolah Dasar)"


class SessionCreateResponse(BaseModel):
    session_id: str


class SessionItem(BaseModel):
    session_id: str
    title: str
    jenjang: str
    updated_at: str


class SessionMessage(BaseModel):
    role: str
    content: str


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


class GuardrailStatus(BaseModel):
    blocked_count: int


class ExportRequest(BaseModel):
    session_id: str


def _validate_jenjang(jenjang: str) -> str:
    if jenjang not in VALID_JENJANG:
        raise HTTPException(status_code=400, detail=f"jenjang harus salah satu dari: {VALID_JENJANG}")
    return jenjang


# -----------------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "openrouter_connected": openrouter_client is not None,
        "supabase_connected": supabase is not None,
    }


# -----------------------------------------------------------------------------
# POST /api/sessions — bikin sesi baru
# -----------------------------------------------------------------------------
@app.post("/api/sessions", response_model=SessionCreateResponse)
def create_session(payload: SessionCreateRequest):
    _validate_jenjang(payload.jenjang)
    sid = new_session_id()
    # Baris di tabel `sessions` baru dibuat pas pesan user pertama masuk
    # (lihat db._touch_session), jadi di sini cuma generate ID-nya.
    return SessionCreateResponse(session_id=sid)


# -----------------------------------------------------------------------------
# GET /api/sessions — daftar semua sesi (buat sidebar)
# -----------------------------------------------------------------------------
@app.get("/api/sessions", response_model=list[SessionItem])
def list_sessions():
    if supabase is None:
        return []
    sessions = get_all_sessions(supabase)
    return [SessionItem(**s) for s in sessions]


# -----------------------------------------------------------------------------
# GET /api/sessions/{session_id}/messages — riwayat chat 1 sesi
# -----------------------------------------------------------------------------
@app.get("/api/sessions/{session_id}/messages", response_model=list[SessionMessage])
def get_session_messages(session_id: str):
    if supabase is None:
        return []
    return [SessionMessage(**m) for m in load_history(supabase, session_id)]


# -----------------------------------------------------------------------------
# PATCH /api/sessions/{session_id} — rename judul sesi
# -----------------------------------------------------------------------------
@app.patch("/api/sessions/{session_id}")
def rename_session(session_id: str, payload: RenameRequest):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase belum terhubung")
    ok = update_session_title(supabase, session_id, payload.title)
    if not ok:
        raise HTTPException(status_code=400, detail="Gagal rename sesi")
    return {"success": True}


# -----------------------------------------------------------------------------
# DELETE /api/sessions/{session_id} — hapus sesi total (chat_history + sessions)
# -----------------------------------------------------------------------------
@app.delete("/api/sessions/{session_id}")
def remove_session(session_id: str):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase belum terhubung")
    ok = delete_session(supabase, session_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Gagal hapus sesi")
    return {"success": True}


# -----------------------------------------------------------------------------
# GET /api/sessions/{session_id}/guardrail — jumlah percobaan diblokir
# (dihitung dari guardrail.log, biar gak perlu tabel DB baru)
# -----------------------------------------------------------------------------
@app.get("/api/sessions/{session_id}/guardrail", response_model=GuardrailStatus)
def get_guardrail_status(session_id: str):
    count = 0
    try:
        with open("guardrail.log", "r") as f:
            for line in f:
                if f"session={session_id} " in line:
                    count += 1
    except FileNotFoundError:
        pass
    return GuardrailStatus(blocked_count=count)


# -----------------------------------------------------------------------------
# POST /api/chat — endpoint utama: kirim pesan, terima balasan tutor
# -----------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    jenjang = _validate_jenjang(payload.jenjang)
    session_id = payload.session_id
    user_message = payload.message.strip()
    is_quiz = payload.mode == "quiz"

    if not user_message:
        raise HTTPException(status_code=400, detail="Pesan gak boleh kosong")

    # --- Guardrail: filter input sebelum diproses ---
    matched_pattern = detect_jailbreak_attempt(user_message)

    save_message(supabase, session_id, jenjang, "user", user_message)

    if matched_pattern:
        log_attempt(session_id, user_message, matched_pattern)
        refusal = guardrail_refusal_message(jenjang)
        save_message(supabase, session_id, jenjang, "assistant", refusal)
        return ChatResponse(reply=refusal, model=None, blocked=True)

    # --- Susun messages format OpenAI dari riwayat tersimpan ---
    history = load_history(supabase, session_id)  # sudah termasuk pesan user barusan
    system_instruction = build_system_instruction(jenjang, is_quiz=is_quiz)

    # --- RAG: selipkan materi kurikulum relevan (cuma dari modul status 'aktif') ---
    relevant_chunks = search_relevant_chunks(supabase, user_message, jenjang, top_k=4)
    if relevant_chunks:
        context_block = "\n\n".join(f"- {c['content']}" for c in relevant_chunks)
        system_instruction += (
            "\n\n[MATERI KURIKULUM RELEVAN — gunakan sebagai referensi utama kalau cocok "
            f"dengan pertanyaan siswa]:\n{context_block}"
        )

    messages = [{"role": "system", "content": system_instruction}]
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})

    free_models = fetch_free_models(OPENROUTER_API_KEY)
    reply, model_label = generate_response_with_fallback(
        openrouter_client, messages, temperature=0.7 if is_quiz else 0.6, free_models=free_models
    )

    if reply is None:
        raise HTTPException(status_code=503, detail="Semua model AI gratis sedang penuh/gagal. Coba lagi sesaat lagi.")

    if check_output_too_direct(reply):
        reply += "\n\n⚠️ *Tutor mendeteksi jawaban ini terlalu langsung — coba tetap pikirkan ulang prosesnya ya!*"

    save_message(supabase, session_id, jenjang, "assistant", reply)

    return ChatResponse(reply=reply, model=model_label, blocked=False)


# -----------------------------------------------------------------------------
# POST /api/export-pdf — ekspor catatan belajar
# -----------------------------------------------------------------------------
@app.post("/api/export-pdf")
def export_pdf(payload: ExportRequest):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase belum terhubung, gak ada riwayat buat diekspor")
    if not session_exists(supabase, payload.session_id):
        raise HTTPException(status_code=404, detail="Sesi gak ditemukan")

    history = load_history(supabase, payload.session_id)
    if not history:
        raise HTTPException(status_code=400, detail="Sesi ini belum ada riwayat chat")

    sessions = get_all_sessions(supabase)
    jenjang = next((s["jenjang"] for s in sessions if s["session_id"] == payload.session_id), "SD (Sekolah Dasar)")

    pdf_bytes = generate_pdf(history, jenjang, payload.session_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=catatan-belajar-{payload.session_id}.pdf"},
    )

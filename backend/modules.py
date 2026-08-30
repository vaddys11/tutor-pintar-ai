"""
modules.py — Endpoint admin buat "Kelola Modul Kurikulum/Skills": upload file
atau input teks langsung, jadi basis pengetahuan RAG buat Tutor Pintar AI.
"""
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from db import get_supabase_client
from curriculum import extract_text_from_file, process_and_store_document
from prompts import VALID_JENJANG

router = APIRouter(prefix="/api/modules", tags=["modules"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = (".pdf", ".txt", ".md")


# Helper untuk mengambil client Supabase secara real-time
def get_db():
    client = get_supabase_client()
    if client is None:
        raise HTTPException(
            status_code=503, 
            detail="Supabase belum terhubung. Pastikan SUPABASE_URL dan SUPABASE_KEY terisi di backend/.env"
        )
    return client


# -----------------------------------------------------------------------------
# Skema
# -----------------------------------------------------------------------------
class ModuleResponse(BaseModel):
    id: str
    title: str
    jenjang: str
    mata_pelajaran: str
    source_type: str
    original_filename: Optional[str] = None
    status: str
    processing_status: str
    chunk_count: int
    created_at: str


class ModuleTextRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    jenjang: str
    mata_pelajaran: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=200_000)


class ModuleStatusUpdate(BaseModel):
    status: Literal["aktif", "nonaktif"]


def _validate_jenjang(jenjang: str) -> str:
    if jenjang not in VALID_JENJANG:
        raise HTTPException(status_code=400, detail=f"jenjang harus salah satu dari: {VALID_JENJANG}")
    return jenjang


# -----------------------------------------------------------------------------
# POST /api/modules/upload — upload file (.pdf/.txt/.md)
# -----------------------------------------------------------------------------
@router.post("/upload", response_model=ModuleResponse)
async def upload_module(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=150),
    jenjang: str = Form(...),
    mata_pelajaran: str = Form(..., min_length=1, max_length=100),
):
    _validate_jenjang(jenjang)

    if not file.filename or not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Format file harus .pdf, .txt, atau .md")

    db = get_db()

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 5MB")

    try:
        raw_text = extract_text_from_file(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Gak ada teks yang bisa diekstrak dari file ini")

    row = {
        "title": title,
        "jenjang": jenjang,
        "mata_pelajaran": mata_pelajaran,
        "source_type": "upload",
        "original_filename": file.filename,
        "status": "aktif",
        "processing_status": "processing",
        "chunk_count": 0,
    }
    res = db.table("curriculum_docs").insert(row).execute()
    doc = res.data[0]

    background_tasks.add_task(process_and_store_document, db, doc["id"], raw_text)

    return ModuleResponse(**doc)


# -----------------------------------------------------------------------------
# POST /api/modules/text — input teks/rangkuman langsung (tanpa file)
# -----------------------------------------------------------------------------
@router.post("/text", response_model=ModuleResponse)
async def add_module_text(background_tasks: BackgroundTasks, payload: ModuleTextRequest):
    _validate_jenjang(payload.jenjang)
    db = get_db()

    row = {
        "title": payload.title,
        "jenjang": payload.jenjang,
        "mata_pelajaran": payload.mata_pelajaran,
        "source_type": "text",
        "original_filename": None,
        "status": "aktif",
        "processing_status": "processing",
        "chunk_count": 0,
    }
    res = db.table("curriculum_docs").insert(row).execute()
    doc = res.data[0]

    background_tasks.add_task(process_and_store_document, db, doc["id"], payload.content)

    return ModuleResponse(**doc)


# -----------------------------------------------------------------------------
# GET /api/modules — daftar semua modul (buat tabel admin)
# -----------------------------------------------------------------------------
@router.get("", response_model=list[ModuleResponse])
def list_modules():
    try:
        db = get_db()
        res = db.table("curriculum_docs").select("*").order("created_at", desc=True).execute()
        return [ModuleResponse(**d) for d in res.data]
    except HTTPException:
        return []


# -----------------------------------------------------------------------------
# PATCH /api/modules/{id} — toggle status aktif/nonaktif
# -----------------------------------------------------------------------------
@router.patch("/{module_id}")
def update_module_status(module_id: str, payload: ModuleStatusUpdate):
    db = get_db()
    res = db.table("curriculum_docs").update({"status": payload.status}).eq("id", module_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Modul gak ditemukan")
    return {"success": True}


# -----------------------------------------------------------------------------
# DELETE /api/modules/{id} — hapus modul + semua chunk-nya
# -----------------------------------------------------------------------------
@router.delete("/{module_id}")
def delete_module(module_id: str):
    db = get_db()
    res = db.table("curriculum_docs").delete().eq("id", module_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Modul gak ditemukan")
    return {"success": True}
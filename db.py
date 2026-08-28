"""
db.py — Layer database Supabase buat riwayat chat Tutor Pintar AI.
"""
import os
import uuid
from datetime import datetime, timezone
from supabase import create_client, Client


def get_supabase_client() -> Client | None:
    """Init client Supabase. Return None kalau env var gak lengkap."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def new_session_id() -> str:
    """Generate session id baru, pendek biar gampang diketik ulang user."""
    return uuid.uuid4().hex[:8]


def save_message(client: Client, session_id: str, jenjang: str, role: str, content: str) -> None:
    """Simpan satu pesan ke tabel chat_history. Gagal diam-diam (log ke console), gak ganggu chat flow."""
    if client is None:
        return
    try:
        client.table("chat_history").insert({
            "session_id": session_id,
            "jenjang": jenjang,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        print(f"[db] Gagal simpan pesan: {e}")


def load_history(client: Client, session_id: str) -> list[dict]:
    """Ambil riwayat chat berdasar session_id, urut waktu."""
    if client is None:
        return []
    try:
        res = (
            client.table("chat_history")
            .select("role, content, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return [{"role": r["role"], "content": r["content"]} for r in res.data]
    except Exception as e:
        print(f"[db] Gagal ambil riwayat: {e}")
        return []


def session_exists(client: Client, session_id: str) -> bool:
    """Cek apakah session_id ada di database."""
    if client is None or not session_id:
        return False
    try:
        res = (
            client.table("chat_history")
            .select("id")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        return len(res.data) > 0
    except Exception:
        return False

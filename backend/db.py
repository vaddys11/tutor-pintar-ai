"""
db.py — Layer database Supabase buat riwayat chat & manajemen sesi Tutor Pintar AI.

Tabel dipakai:
- chat_history: log tiap pesan (role, content, session_id)
- sessions: satu baris per sesi (title, jenjang, updated_at) buat list sidebar
"""
import os
import uuid
from datetime import datetime, timezone
from supabase import create_client, Client

MAX_TITLE_LEN = 30


def get_supabase_client() -> Client | None:
    """Init client Supabase. Return None kalau env var gak lengkap."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def new_session_id() -> str:
    """Generate session id baru (internal, gak perlu diketik user lagi)."""
    return uuid.uuid4().hex[:8]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _auto_title(text: str) -> str:
    """Bikin judul otomatis dari pesan pertama: 30 karakter pertama + '...' kalau dipotong."""
    clean = " ".join(text.split())
    if not clean:
        return "Percakapan Baru"
    return clean[:MAX_TITLE_LEN] + "..." if len(clean) > MAX_TITLE_LEN else clean


def _touch_session(client: Client, session_id: str, jenjang: str, first_message: str) -> None:
    """Bikin baris sessions kalau belum ada (dengan auto-title), atau update updated_at kalau sudah ada."""
    try:
        existing = (
            client.table("sessions")
            .select("session_id")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            client.table("sessions").update({"updated_at": _now_iso()}).eq("session_id", session_id).execute()
        else:
            client.table("sessions").insert({
                "session_id": session_id,
                "jenjang": jenjang,
                "title": _auto_title(first_message),
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }).execute()
    except Exception as e:
        print(f"[db] Gagal update sessions: {e}")


def save_message(client: Client, session_id: str, jenjang: str, role: str, content: str) -> None:
    """Simpan satu pesan ke chat_history + jaga baris sessions (title & updated_at). Gagal diam-diam."""
    if client is None:
        return
    try:
        client.table("chat_history").insert({
            "session_id": session_id,
            "jenjang": jenjang,
            "role": role,
            "content": content,
            "created_at": _now_iso(),
        }).execute()
    except Exception as e:
        print(f"[db] Gagal simpan pesan: {e}")
        return

    if role == "user":
        _touch_session(client, session_id, jenjang, content)


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


def get_all_sessions(client: Client) -> list[dict]:
    """Ambil daftar semua sesi (session_id, title, jenjang, updated_at), urut terbaru dulu."""
    if client is None:
        return []
    try:
        res = (
            client.table("sessions")
            .select("session_id, title, jenjang, updated_at")
            .order("updated_at", desc=True)
            .execute()
        )
        return res.data
    except Exception as e:
        print(f"[db] Gagal ambil daftar sesi: {e}")
        return []


def update_session_title(client: Client, session_id: str, new_title: str) -> bool:
    """Rename judul sesi. Return True kalau sukses."""
    if client is None:
        return False
    clean_title = new_title.strip()
    if not clean_title:
        return False
    try:
        client.table("sessions").update({"title": clean_title[:MAX_TITLE_LEN]}).eq("session_id", session_id).execute()
        return True
    except Exception as e:
        print(f"[db] Gagal rename sesi: {e}")
        return False


def session_exists(client: Client, session_id: str) -> bool:
    """Cek apakah session_id ada di tabel sessions."""
    if client is None or not session_id:
        return False
    try:
        res = (
            client.table("sessions")
            .select("session_id")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        return len(res.data) > 0
    except Exception:
        return False

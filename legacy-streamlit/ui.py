"""
ui.py — Styling modern (Tailwind-style) + Lucide icons + avatar kustom buat Tutor Pintar AI.
Streamlit gak support Tailwind compiler asli, jadi ini custom CSS yang niru
utility classes Tailwind (warna, spacing, radius, shadow) + Lucide via CDN.
"""
import base64

LUCIDE_SCRIPT = """
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    if (window.lucide) lucide.createIcons();
  });
  // Streamlit rerender pake DOM baru, jadi re-init tiap saat script ini muncul lagi
  if (window.lucide) { setTimeout(() => lucide.createIcons(), 100); }
</script>
"""


def lucide_icon(name: str, size: int = 18, color: str = "currentColor") -> str:
    """Return tag <i> Lucide, dipanggil inline dalam HTML markdown."""
    return f'<i data-lucide="{name}" style="width:{size}px;height:{size}px;color:{color};vertical-align:middle;"></i>'


# -----------------------------------------------------------------------------
# Avatar kustom (SVG inline -> data URI) — dipakai di st.chat_message(avatar=...)
# -----------------------------------------------------------------------------
def _svg_to_data_uri(svg: str) -> str:
    b64 = base64.b64encode(svg.strip().encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


_BOT_AVATAR_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="botGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#818cf8"/>
      <stop offset="1" stop-color="#4338ca"/>
    </linearGradient>
  </defs>
  <circle cx="50" cy="50" r="50" fill="url(#botGrad)"/>
  <line x1="50" y1="30" x2="50" y2="22" stroke="white" stroke-width="3" stroke-linecap="round"/>
  <circle cx="50" cy="18" r="4" fill="white"/>
  <rect x="27" y="30" width="46" height="38" rx="13" fill="white"/>
  <circle cx="40" cy="49" r="5.5" fill="#4338ca"/>
  <circle cx="60" cy="49" r="5.5" fill="#4338ca"/>
  <rect x="43" y="59" width="14" height="4" rx="2" fill="#4338ca"/>
  <rect x="16" y="44" width="7" height="14" rx="3.5" fill="#a5b4fc"/>
  <rect x="77" y="44" width="7" height="14" rx="3.5" fill="#a5b4fc"/>
</svg>
"""

_USER_AVATAR_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="userGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#fbbf24"/>
      <stop offset="1" stop-color="#d97706"/>
    </linearGradient>
  </defs>
  <circle cx="50" cy="50" r="50" fill="url(#userGrad)"/>
  <circle cx="50" cy="40" r="17" fill="white"/>
  <path d="M18 92c1-20 14-34 32-34s31 14 32 34" fill="white"/>
</svg>
"""

BOT_AVATAR = _svg_to_data_uri(_BOT_AVATAR_SVG)
USER_AVATAR = _svg_to_data_uri(_USER_AVATAR_SVG)


CUSTOM_CSS = """
<style>
:root {
    --tp-indigo-50: #eef2ff;
    --tp-indigo-100: #e0e7ff;
    --tp-indigo-400: #818cf8;
    --tp-indigo-500: #6366f1;
    --tp-indigo-600: #4f46e5;
    --tp-indigo-700: #4338ca;
    --tp-purple-500: #8b5cf6;
    --tp-amber-500: #f59e0b;
    --tp-emerald-500: #10b981;
    --tp-emerald-50: #ecfdf5;
    --tp-slate-50: #f8fafc;
    --tp-slate-100: #f1f5f9;
    --tp-slate-200: #e2e8f0;
    --tp-slate-600: #475569;
    --tp-slate-800: #1e293b;
    --tp-red-50: #fef2f2;
    --tp-red-600: #dc2626;

    /* Palet sidebar dark/modern */
    --tp-side-bg-1: #1e1b3a;
    --tp-side-bg-2: #15122b;
    --tp-side-card: rgba(255,255,255,0.05);
    --tp-side-border: rgba(255,255,255,0.10);
    --tp-side-text: #e2e8f0;
    --tp-side-text-dim: #94a3b8;
    --tp-side-input-bg: #2a2657;

    --tp-radius-2xl: 20px;
    --tp-radius-lg: 16px;
    --tp-radius-md: 12px;
    --tp-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
    --tp-shadow-soft: 0 4px 16px rgba(30, 27, 75, 0.06);
}

/* Base app background — clean & ramah anak, gak berasa default Streamlit */
.main {
    background: radial-gradient(circle at top left, #f5f3ff 0%, #f8fafc 45%, #ffffff 100%);
}
[data-testid="stAppViewContainer"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

/* ===================== HERO HEADER ===================== */
.tp-hero {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 22px 26px;
    background: linear-gradient(135deg, var(--tp-indigo-600), var(--tp-purple-500));
    border-radius: var(--tp-radius-2xl);
    box-shadow: var(--tp-shadow-soft);
    margin-bottom: 22px;
    color: white;
}
.tp-hero h1 {
    font-size: 1.55rem;
    font-weight: 800;
    margin: 0;
    color: white;
    letter-spacing: -0.01em;
}
.tp-hero p {
    margin: 2px 0 0 0;
    font-size: 0.85rem;
    opacity: 0.92;
}
.tp-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    background: rgba(255,255,255,0.22);
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: white;
    backdrop-filter: blur(4px);
}

/* ===================== CHAT BUBBLES ===================== */
/* User: ungu/indigo lembut, rounded-2xl, teks putih jernih */
.tp-bubble-user {
    background: linear-gradient(135deg, var(--tp-indigo-500), var(--tp-purple-500));
    color: #ffffff;
    padding: 13px 18px;
    border-radius: var(--tp-radius-2xl) var(--tp-radius-2xl) 6px var(--tp-radius-2xl);
    margin: 4px 0 4px auto;
    max-width: 78%;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25);
    line-height: 1.55;
}
/* AI Tutor: card putih netral, border tipis, shadow halus */
.tp-bubble-assistant {
    background: #ffffff;
    border: 1px solid var(--tp-slate-200);
    color: var(--tp-slate-800);
    padding: 13px 18px;
    border-radius: var(--tp-radius-2xl) var(--tp-radius-2xl) var(--tp-radius-2xl) 6px;
    margin: 4px auto 4px 0;
    max-width: 78%;
    box-shadow: var(--tp-shadow-soft);
    line-height: 1.55;
}

/* Rapikan avatar bulat default Streamlit biar konsisten sama bubble custom */
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"],
[data-testid="chatAvatarIcon-user"], [data-testid="chatAvatarIcon-assistant"] {
    box-shadow: 0 2px 6px rgba(0,0,0,0.12);
}

/* ===================== SIDEBAR — kontras dark/modern ===================== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--tp-side-bg-1) 0%, var(--tp-side-bg-2) 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not(.tp-badge span) {
    color: var(--tp-side-text) !important;
}
[data-testid="stSidebar"] .tp-section-title {
    color: #f8fafc !important;
}
[data-testid="stSidebar"] hr { border-color: var(--tp-side-border) !important; }

/* Input & select di sidebar: bg gelap konsisten, teks terang, border jelas */
[data-testid="stSidebar"] .stTextInput>div>div>input,
[data-testid="stSidebar"] .stTextInput>div>div>textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: var(--tp-side-input-bg) !important;
    color: #f1f5f9 !important;
    border: 1px solid var(--tp-side-border) !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span {
    color: var(--tp-side-text-dim) !important;
}

/* Card section di sidebar (dark card, border tipis, kontras jelas) */
[data-testid="stSidebar"] .tp-section {
    background: var(--tp-side-card);
    border: 1px solid var(--tp-side-border);
    border-radius: var(--tp-radius-md);
    padding: 14px;
    margin-bottom: 14px;
}
.tp-section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: 0.82rem;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* ===================== TOMBOL ===================== */
.stButton>button {
    width: 100%;
    border-radius: 10px;
    font-weight: 600;
    border: 1px solid transparent;
    background: var(--tp-indigo-500);
    color: #ffffff;
    transition: all 0.15s ease;
}
.stButton>button:hover {
    background: var(--tp-indigo-700);
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
    transform: translateY(-1px);
}
.stButton>button:active { transform: translateY(0); }

/* Tombol ✏️ / ikon kecil di kolom sempit (col_edit) — pill netral, kontras tetap terjaga */
[data-testid="stSidebar"] [data-testid="column"]:has(button[kind]) button {
    min-height: 38px;
}
[data-testid="stSidebar"] .stButton>button:disabled {
    background: #3f3a72 !important;
    color: var(--tp-side-text-dim) !important;
}

/* Tombol "+ Sesi Baru" — hijau emerald, beda dari tombol biasa */
.tp-newsession-btn button {
    background: var(--tp-emerald-500) !important;
    font-weight: 700 !important;
}
.tp-newsession-btn button:hover {
    background: #059669 !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

/* Tombol mic 🎙️ — CATATAN: streamlit-mic-recorder render di custom
   component (iframe tersandbox), jadi CSS halaman TIDAK BISA nembus ke
   tombolnya. Satu-satunya jalur kustomisasi resmi buat komponen ini adalah
   lewat tema Streamlit (.streamlit/config.toml) — komponen otomatis
   ngikutin primaryColor dkk dari situ. Lihat file .streamlit/config.toml.
   Baris di bawah cuma styling wrapper kolom di sekitarnya, bukan tombolnya. */
.tp-mic-wrap {
    display: flex;
    align-items: center;
}

/* ===================== GUARDRAIL STATUS ===================== */
.tp-guard-active {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.15);
    color: #6ee7b7;
    padding: 9px 12px;
    border-radius: var(--tp-radius-md);
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid rgba(16, 185, 129, 0.25);
}
.tp-guard-alert {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(220, 38, 38, 0.15);
    color: #fca5a5;
    padding: 9px 12px;
    border-radius: var(--tp-radius-md);
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid rgba(220, 38, 38, 0.25);
}

/* ===================== DAFTAR SESI ===================== */
.tp-session-list-item {
    font-size: 0.78rem;
    color: var(--tp-side-text-dim);
    padding: 0 4px 6px 4px;
}
.tp-session-empty {
    font-size: 0.8rem;
    color: var(--tp-side-text-dim);
    font-style: italic;
    padding: 6px 2px;
}

/* File uploader & inputs area utama (non-sidebar) tetap rounded rapi */
.stSelectbox>div>div {
    border-radius: 10px !important;
}
</style>
"""


def render_hero(jenjang: str) -> str:
    return f"""
    <div class="tp-hero">
        {lucide_icon('graduation-cap', 32, 'white')}
        <div>
            <h1>Tutor Pintar AI</h1>
            <p>Pendamping belajar interaktif dengan metode Socratic</p>
        </div>
        <div style="margin-left:auto;">
            <span class="tp-badge">{lucide_icon('layers', 14, 'white')} {jenjang}</span>
        </div>
    </div>
    """


def render_section_title(icon: str, title: str) -> str:
    return f'<div class="tp-section-title">{lucide_icon(icon, 16)} {title}</div>'


def render_chat_bubble(role: str, content_html: str) -> str:
    css_class = "tp-bubble-user" if role == "user" else "tp-bubble-assistant"
    return f'<div class="{css_class}">{content_html}</div>'


def format_session_time(updated_at: str) -> str:
    """Format timestamp ISO Supabase jadi label pendek 'dd Mon, HH:MM'."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        return dt.strftime("%d %b, %H:%M")
    except Exception:
        return ""


def render_guardrail_status(blocked_count: int) -> str:
    if blocked_count == 0:
        return f'<div class="tp-guard-active">{lucide_icon("shield-check", 16)} Guardrail aktif — belum ada percobaan mencurigakan</div>'
    return f'<div class="tp-guard-alert">{lucide_icon("shield-alert", 16)} {blocked_count} percobaan diblokir sesi ini</div>'

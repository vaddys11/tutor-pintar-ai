"""
ui.py — Styling modern (Tailwind-style) + Lucide icons buat Tutor Pintar AI.
Streamlit gak support Tailwind compiler asli, jadi ini custom CSS yang niru
utility classes Tailwind (warna, spacing, radius, shadow) + Lucide via CDN.
"""

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


CUSTOM_CSS = """
<style>
:root {
    --tp-indigo-50: #eef2ff;
    --tp-indigo-100: #e0e7ff;
    --tp-indigo-600: #4f46e5;
    --tp-indigo-700: #4338ca;
    --tp-emerald-500: #10b981;
    --tp-emerald-50: #ecfdf5;
    --tp-slate-50: #f8fafc;
    --tp-slate-100: #f1f5f9;
    --tp-slate-200: #e2e8f0;
    --tp-slate-600: #475569;
    --tp-slate-800: #1e293b;
    --tp-red-50: #fef2f2;
    --tp-red-600: #dc2626;
    --tp-radius-lg: 16px;
    --tp-radius-md: 12px;
    --tp-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
}

/* Base app background */
.main {
    background: linear-gradient(180deg, var(--tp-slate-50) 0%, #ffffff 100%);
}

/* Header hero */
.tp-hero {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 24px;
    background: linear-gradient(135deg, var(--tp-indigo-600), #6366f1);
    border-radius: var(--tp-radius-lg);
    box-shadow: var(--tp-shadow);
    margin-bottom: 20px;
    color: white;
}
.tp-hero h1 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: white;
}
.tp-hero p {
    margin: 2px 0 0 0;
    font-size: 0.85rem;
    opacity: 0.9;
}

/* Badge jenjang */
.tp-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    background: rgba(255,255,255,0.2);
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: white;
}

/* Sidebar section card */
.tp-section {
    background: white;
    border: 1px solid var(--tp-slate-200);
    border-radius: var(--tp-radius-md);
    padding: 14px;
    margin-bottom: 14px;
    box-shadow: var(--tp-shadow);
}
.tp-section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--tp-slate-800);
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

/* Chat bubbles custom */
.tp-bubble-user {
    background: var(--tp-indigo-600);
    color: white;
    padding: 12px 16px;
    border-radius: var(--tp-radius-md) var(--tp-radius-md) 4px var(--tp-radius-md);
    margin: 6px 0 6px auto;
    max-width: 80%;
    box-shadow: var(--tp-shadow);
}
.tp-bubble-assistant {
    background: white;
    border: 1px solid var(--tp-slate-200);
    color: var(--tp-slate-800);
    padding: 12px 16px;
    border-radius: var(--tp-radius-md) var(--tp-radius-md) var(--tp-radius-md) 4px;
    margin: 6px auto 6px 0;
    max-width: 80%;
    box-shadow: var(--tp-shadow);
}

/* Buttons */
.stButton>button {
    width: 100%;
    border-radius: 10px;
    font-weight: 600;
    border: none;
    background: var(--tp-indigo-600);
    color: white;
    transition: all 0.15s ease;
}
.stButton>button:hover {
    background: var(--tp-indigo-700);
    box-shadow: var(--tp-shadow);
    transform: translateY(-1px);
}

/* Guardrail status pill */
.tp-guard-active {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--tp-emerald-50);
    color: #047857;
    padding: 8px 12px;
    border-radius: var(--tp-radius-md);
    font-size: 0.8rem;
    font-weight: 600;
}
.tp-guard-alert {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--tp-red-50);
    color: var(--tp-red-600);
    padding: 8px 12px;
    border-radius: var(--tp-radius-md);
    font-size: 0.8rem;
    font-weight: 600;
}

/* File uploader & inputs rounded */
[data-testid="stFileUploader"], .stTextInput>div>div>input, .stSelectbox>div>div {
    border-radius: 10px !important;
}

/* Daftar sesi chat */
.tp-session-list-item {
    font-size: 0.82rem;
    color: var(--tp-slate-600);
    padding: 2px 4px;
}
.tp-session-active-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--tp-indigo-700);
    padding: 4px 8px;
    background: var(--tp-indigo-50);
    border-radius: 8px;
    margin-bottom: 4px;
}
.tp-session-empty {
    font-size: 0.78rem;
    color: var(--tp-slate-600);
    font-style: italic;
    padding: 4px 0;
}

/* Tombol "+ Sesi Baru" beda warna dari tombol biasa */
.tp-newsession-btn button {
    background: var(--tp-emerald-500) !important;
}
.tp-newsession-btn button:hover {
    background: #059669 !important;
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

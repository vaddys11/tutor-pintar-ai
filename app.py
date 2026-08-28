import os
import base64
import io
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import pypdf

from llm import get_openrouter_client, generate_response_with_fallback, fetch_free_models

from db import (
    get_supabase_client,
    new_session_id,
    save_message,
    load_history,
    get_all_sessions,
    update_session_title,
)
from export import generate_pdf
from guardrail import (
    detect_jailbreak_attempt,
    log_attempt,
    guardrail_refusal_message,
    harden_system_instruction,
    check_output_too_direct,
)
from ui import (
    CUSTOM_CSS,
    LUCIDE_SCRIPT,
    lucide_icon,
    render_hero,
    render_section_title,
    render_chat_bubble,
    render_guardrail_status,
    format_session_time,
)

# -----------------------------------------------------------------------------
# 1. Konfigurasi Halaman & Styling UI
# -----------------------------------------------------------------------------
load_dotenv()

st.set_page_config(
    page_title="Tutor Pintar AI - Multi Jenjang",
    page_icon="🎓",
    layout="wide"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(LUCIDE_SCRIPT, unsafe_allow_html=True)

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("🔑 Masukkan OpenRouter API Key:", type="password")
    if api_key:
        os.environ["OPENROUTER_API_KEY"] = api_key

if not api_key:
    st.info("👋 Masukkan OpenRouter API Key di sidebar atau file .env untuk mulai.")
    st.stop()

client = get_openrouter_client()
supabase = get_supabase_client()
free_models = fetch_free_models(api_key)

# -----------------------------------------------------------------------------
# 2. State Awal
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = new_session_id()
if "blocked_count" not in st.session_state:
    st.session_state.blocked_count = 0
if "last_model" not in st.session_state:
    st.session_state.last_model = None

# -----------------------------------------------------------------------------
# 3. Sidebar: Pengaturan, Sesi, Upload, Ekspor, Guardrail
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(render_section_title("settings", "Pengaturan Tutor"), unsafe_allow_html=True)
    jenjang = st.selectbox(
        "Tingkat Pendidikan",
        ["SD (Sekolah Dasar)", "SMP (Sekolah Menengah Pertama)", "SMA (Sekolah Menengah Atas)", "S1 (Mahasiswa)"],
        label_visibility="collapsed",
    )
    enable_tts = st.toggle("🔊 Aktifkan Suara Tutor (TTS)", value=True)

    st.markdown("---")

    # --- Sesi Belajar (Supabase) ---
    st.markdown(render_section_title("database", "Sesi Belajar"), unsafe_allow_html=True)
    if supabase is None:
        st.warning("Supabase belum terhubung. Set SUPABASE_URL & SUPABASE_KEY di .env untuk simpan riwayat.")
    else:
        # Tombol "+ Sesi Baru" paling atas
        st.markdown('<div class="tp-newsession-btn">', unsafe_allow_html=True)
        if st.button("＋ Sesi Baru", key="btn_new_session", use_container_width=True):
            st.session_state.session_id = new_session_id()
            st.session_state.messages = []
            st.session_state.renaming_id = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if "renaming_id" not in st.session_state:
            st.session_state.renaming_id = None

        sessions = get_all_sessions(supabase)

        if not sessions:
            st.markdown('<div class="tp-session-empty">Belum ada sesi tersimpan — mulai ngobrol dulu!</div>',
                        unsafe_allow_html=True)
        else:
            for sess in sessions:
                sid = sess["session_id"]
                title = sess.get("title") or "Percakapan Baru"
                time_label = format_session_time(sess.get("updated_at", ""))
                is_active = sid == st.session_state.session_id

                if st.session_state.renaming_id == sid:
                    # --- Mode edit judul ---
                    new_title = st.text_input(
                        "Judul baru", value=title, key=f"rename_input_{sid}", label_visibility="collapsed"
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Simpan", key=f"save_rename_{sid}", use_container_width=True):
                            update_session_title(supabase, sid, new_title)
                            st.session_state.renaming_id = None
                            st.rerun()
                    with c2:
                        if st.button("Batal", key=f"cancel_rename_{sid}", use_container_width=True):
                            st.session_state.renaming_id = None
                            st.rerun()
                else:
                    row_label = title if is_active else title
                    col_main, col_edit = st.columns([5, 1])
                    with col_main:
                        prefix = "🟢 " if is_active else ""
                        if st.button(f"{prefix}{row_label}", key=f"open_session_{sid}", use_container_width=True):
                            if not is_active:
                                st.session_state.session_id = sid
                                st.session_state.messages = load_history(supabase, sid)
                                st.session_state.renaming_id = None
                                st.rerun()
                    with col_edit:
                        if st.button("✏️", key=f"edit_btn_{sid}"):
                            st.session_state.renaming_id = sid
                            st.rerun()
                    if time_label:
                        st.markdown(f'<div class="tp-session-list-item">{time_label}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(render_section_title("image", "Upload Foto Soal"), unsafe_allow_html=True)
    uploaded_image = st.file_uploader("Upload gambar/foto PR", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(render_section_title("file-text", "Upload Dokumen (PDF)"), unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("Upload buku paket / jurnal acuan", type=["pdf"], label_visibility="collapsed")

    pdf_context = ""
    if uploaded_pdf:
        try:
            pdf_reader = pypdf.PdfReader(uploaded_pdf)
            for page in pdf_reader.pages:
                pdf_context += page.extract_text() or ""
            st.success("✅ PDF Berhasil Dibaca!")
        except Exception as e:
            st.error(f"Gagal membaca PDF: {e}")

    st.markdown("---")
    st.markdown(render_section_title("brain-circuit", "Evaluasi Belajar"), unsafe_allow_html=True)
    btn_quiz = st.button("📝 Uji Pemahamanku")

    st.markdown("---")
    st.markdown(render_section_title("download", "Ekspor Catatan Belajar"), unsafe_allow_html=True)
    if st.session_state.messages:
        pdf_bytes = generate_pdf(st.session_state.messages, jenjang, st.session_state.session_id)
        st.download_button(
            "⬇️ Unduh sebagai PDF",
            data=pdf_bytes,
            file_name=f"catatan-belajar-{st.session_state.session_id}.pdf",
            mime="application/pdf",
        )
    else:
        st.caption("Belum ada riwayat buat diekspor.")

    st.markdown("---")
    st.markdown(render_section_title("shield", "Status Guardrail"), unsafe_allow_html=True)
    st.markdown(render_guardrail_status(st.session_state.blocked_count), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(render_section_title("cpu", "Status Model AI"), unsafe_allow_html=True)
    st.caption(f"📡 {len(free_models)} model gratis terdeteksi live dari OpenRouter")
    if st.session_state.get("last_model"):
        st.caption(f"🤖 Terakhir merespons: **{st.session_state.last_model}**")
    else:
        st.caption("Belum ada respons dari AI di sesi ini.")

# -----------------------------------------------------------------------------
# 4. Dynamic System Instruction Sesuai Jenjang
# -----------------------------------------------------------------------------
PROMPT_PER_JENJANG = {
    "SD (Sekolah Dasar)": """
    Kamu adalah "Tutor Pintar" untuk anak Sekolah Dasar (SD).
    Aturan:
    1. DILARANG KERAS memberikan jawaban langsung untuk soal hitungan, bacaan, atau PR.
    2. Gunakan gaya bahasa yang sangat ceria, penuh semangat, ramah, dan sederhana. Banyak gunakan pemisalan atau cerita sehari-hari.
    3. Puji setiap kali anak bertanya atau menjawab.
    4. Berikan 1 petunjuk kecil dan ajukan 1 pertanyaan pembimbing yang sangat mudah dijawab anak SD.
    """,

    "SMP (Sekolah Menengah Pertama)": """
    Kamu adalah "Tutor Pintar" untuk siswa SMP.
    Aturan:
    1. DILARANG KERAS memberikan jawaban akhir atau kunci jawaban langsung untuk tugas sekolah.
    2. Terapkan metode Socrates: Berikan petunjuk konsep dasar dan akhiri dengan 1 pertanyaan pembimbing.
    3. Gunakan gaya bahasa santai, bersahabat, dan mendukung khas anak remaja SMP.
    4. Bantu mereka menghubungkan konsep pelajaran dengan pemahaman logika sederhana.
    """,

    "SMA (Sekolah Menengah Atas)": """
    Kamu adalah "Tutor Pintar" untuk siswa SMA.
    Aturan:
    1. DILARANG KERAS memberikan penyelesaian final atau solusinya secara instan.
    2. Fokus pada penguatan logika dasar, rumus penentu, dan analisis sebab-akibat.
    3. Berikan hint terstruktur dan minta siswa menentukan langkah berikutnya sendiri.
    4. Gunakan gaya bahasa komunikatif, komunikatif-edukatif, khas remaja SMA yang bersiap ke perguruan tinggi.
    """,

    "S1 (Mahasiswa)": """
    Kamu adalah "Academic Mentor" untuk Mahasiswa Sarjana (S1).
    Aturan:
    1. DILARANG KERAS menuliskan draf skripsi, kodingan penuh, atau jawaban analisis tugas secara utuh.
    2. Bertindaklah sebagai mitra kritis (sparring partner berpikir): Uji asumsi, metodologi, atau logika argumen mahasiswa.
    3. Berikan referensi konsep akademis, struktur kerangka berpikir, atau pertanyakan validitas sampel/data mereka.
    4. Gunakan bahasa akademis yang profesional, lugas, namun tetap suportif.
    """
}

BASE_SYSTEM_INSTRUCTION = PROMPT_PER_JENJANG[jenjang] + """
Aturan Umum:
- Jika pengguna meminta/memaksa jawaban langsung, tolak dengan ramah dan jelaskan pentingnya proses berpikir mandiri sesuai tingkat pendidikan mereka.
- Selalu batasi respons agar tidak menjadi 'penjawab instan'.
"""

# Guardrail: bungkus system instruction dengan lapisan anti-override
SYSTEM_INSTRUCTION = harden_system_instruction(BASE_SYSTEM_INSTRUCTION)

# -----------------------------------------------------------------------------
# 5. Header & Riwayat Chat
# -----------------------------------------------------------------------------
st.markdown(render_hero(jenjang), unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(render_chat_bubble(message["role"], message["content"]), unsafe_allow_html=True)
        if message["role"] == "assistant" and message.get("model"):
            st.caption(f"🤖 {message['model']}")


def speak_text(text):
    clean_text = text.replace("*", "").replace("\n", " ").replace('"', "'")
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = 'id-ID';
        window.speechSynthesis.speak(msg);
        </script>
    """
    st.components.v1.html(js_code, height=0)


def _image_to_data_url(uploaded_file) -> str:
    """Convert file upload gambar jadi data URL base64, format yang diterima OpenRouter vision."""
    img = Image.open(uploaded_file).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def build_messages(history: list[dict], pdf_ctx: str, image=None) -> list:
    """Susun messages format OpenAI (role/content) dari riwayat chat + konteks PDF + gambar."""
    messages = []
    if pdf_ctx:
        messages.append({"role": "system", "content": f"[DOKUMEN ACUAN/BUKU]:\n{pdf_ctx[:4000]}"})

    last_user_index = max((i for i, m in enumerate(history) if m["role"] == "user"), default=-1)

    for i, msg in enumerate(history):
        role = "user" if msg["role"] == "user" else "assistant"
        # Gambar cuma dilampirkan ke pesan user terakhir, biar gak dobel tiap giliran
        if image is not None and i == last_user_index:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": msg["content"]},
                    {"type": "image_url", "image_url": {"url": _image_to_data_url(image)}},
                ],
            })
        else:
            messages.append({"role": role, "content": msg["content"]})
    return messages


def handle_model_call(instruction: str, temperature: float, spinner_text: str) -> tuple[str | None, str | None]:
    """Panggil AI via OpenRouter dengan fallback multi-model. Return (teks_respons, label_model) atau (None, None)."""
    with st.spinner(spinner_text):
        history_messages = build_messages(st.session_state.messages, pdf_context, uploaded_image)
        messages = [{"role": "system", "content": instruction}] + history_messages

        bot_reply, model_label = generate_response_with_fallback(
            client, messages, temperature=temperature, free_models=free_models
        )

        if bot_reply is None:
            st.error("Semua model AI gratis sedang penuh atau gagal merespons. Coba lagi sesaat lagi.")
            return None, None

        # Guardrail: cek ringan kalau respons kelewat instan
        if check_output_too_direct(bot_reply):
            bot_reply += "\n\n⚠️ *Tutor mendeteksi jawaban ini terlalu langsung — coba tetap pikirkan ulang prosesnya ya!*"

        return bot_reply, model_label

# -----------------------------------------------------------------------------
# 6. Tombol Kuis Adaptif
# -----------------------------------------------------------------------------
if btn_quiz:
    if not st.session_state.messages:
        st.sidebar.warning("⚠️ Belum ada riwayat percakapan. Mulai obrolan terlebih dahulu!")
    else:
        quiz_user_msg = "📝 Tolong buatkan 2 soal latihan adaptif berdasarkan materi yang telah kita bahas untuk menguji pemahamanku."
        st.session_state.messages.append({"role": "user", "content": quiz_user_msg})
        save_message(supabase, st.session_state.session_id, jenjang, "user", quiz_user_msg)

        with st.chat_message("assistant"):
            quiz_instruction = SYSTEM_INSTRUCTION + """
            TUGAS KHUSUS UJI PEMAHAMAN:
            1. Analisis seluruh riwayat percakapan sebelumnya.
            2. Buatkan tepat 2 soal latihan adaptif yang relevan dengan topik yang dipelajari dan tingkat pendidikan pengguna.
            3. DILARANG KERAS memberikan kunci jawaban, pembahasannya, atau solusinya terlebih dahulu.
            4. Berikan dorongan agar pengguna mencoba menjawabnya sendiri.
            """
            bot_reply, model_label = handle_model_call(
                quiz_instruction, 0.7,
                f"Menyiapkan 2 soal latihan adaptif untuk tingkat {jenjang.split()[0]}..."
            )
            if bot_reply:
                st.markdown(render_chat_bubble("assistant", bot_reply), unsafe_allow_html=True)
                st.caption(f"🤖 {model_label}")
                if enable_tts:
                    speak_text(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply, "model": model_label})
                st.session_state.last_model = model_label
                save_message(supabase, st.session_state.session_id, jenjang, "assistant", bot_reply)
                st.rerun()

# -----------------------------------------------------------------------------
# 7. Input Chat Utama (dengan Guardrail)
# -----------------------------------------------------------------------------
if prompt := st.chat_input("Tanyakan materi atau konsep pelajaran di sini..."):

    # --- Guardrail: filter input sebelum diproses ---
    matched_pattern = detect_jailbreak_attempt(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(supabase, st.session_state.session_id, jenjang, "user", prompt)
    with st.chat_message("user"):
        st.markdown(render_chat_bubble("user", prompt), unsafe_allow_html=True)

    if matched_pattern:
        st.session_state.blocked_count += 1
        log_attempt(st.session_state.session_id, prompt, matched_pattern)
        bot_reply = guardrail_refusal_message(jenjang)
        with st.chat_message("assistant"):
            st.markdown(render_chat_bubble("assistant", bot_reply), unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        save_message(supabase, st.session_state.session_id, jenjang, "assistant", bot_reply)
        st.rerun()
    else:
        with st.chat_message("assistant"):
            bot_reply, model_label = handle_model_call(
                SYSTEM_INSTRUCTION, 0.6,
                f"Tutor sedang menyiapkan petunjuk untuk tingkat {jenjang.split()[0]}..."
            )
            if bot_reply:
                st.markdown(render_chat_bubble("assistant", bot_reply), unsafe_allow_html=True)
                st.caption(f"🤖 {model_label}")
                if enable_tts:
                    speak_text(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply, "model": model_label})
                st.session_state.last_model = model_label
                save_message(supabase, st.session_state.session_id, jenjang, "assistant", bot_reply)
                st.rerun()

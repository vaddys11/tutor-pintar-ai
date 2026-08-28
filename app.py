import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import pypdf

from db import get_supabase_client, new_session_id, save_message, load_history, session_exists
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

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("🔑 Masukkan Gemini API Key:", type="password")

if not api_key:
    st.info("👋 Masukkan Gemini API Key di sidebar atau file .env untuk mulai.")
    st.stop()


@st.cache_resource
def get_client(key: str):
    return genai.Client(api_key=key)


client = get_client(api_key)
supabase = get_supabase_client()

# -----------------------------------------------------------------------------
# 2. State Awal
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = new_session_id()
if "blocked_count" not in st.session_state:
    st.session_state.blocked_count = 0

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
        st.text_input("Kode Sesi Kamu", value=st.session_state.session_id, disabled=True,
                       help="Catat kode ini buat lanjut belajar nanti.")
        load_code = st.text_input("Lanjut sesi lama? Masukkan kode:", key="load_code_input")
        if st.button("📂 Muat Sesi"):
            if load_code and session_exists(supabase, load_code):
                st.session_state.session_id = load_code
                st.session_state.messages = load_history(supabase, load_code)
                st.success("Riwayat berhasil dimuat!")
                st.rerun()
            else:
                st.error("Kode sesi gak ditemukan.")

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


def build_contents(history: list[dict], pdf_ctx: str, image=None) -> list:
    """Susun contents buat dikirim ke Gemini dari riwayat chat + konteks PDF + gambar."""
    contents = []
    if pdf_ctx:
        contents.append(types.Part.from_text(text=f"[DOKUMEN ACUAN/BUKU]:\n{pdf_ctx[:4000]}"))
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    if image is not None:
        contents.append(Image.open(image))
    return contents


def handle_model_call(instruction: str, temperature: float, spinner_text: str) -> str | None:
    """Panggil Gemini, return teks respons atau None kalau error (sudah ditampilkan)."""
    with st.spinner(spinner_text):
        try:
            contents = build_contents(st.session_state.messages, pdf_context, uploaded_image)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=instruction,
                    temperature=temperature,
                )
            )
            bot_reply = response.text

            # Guardrail: cek ringan kalau respons kelewat instan
            if check_output_too_direct(bot_reply):
                bot_reply += "\n\n⚠️ *Tutor mendeteksi jawaban ini terlalu langsung — coba tetap pikirkan ulang prosesnya ya!*"

            return bot_reply
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {str(e)}")
            return None

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
            bot_reply = handle_model_call(
                quiz_instruction, 0.7,
                f"Menyiapkan 2 soal latihan adaptif untuk tingkat {jenjang.split()[0]}..."
            )
            if bot_reply:
                st.markdown(render_chat_bubble("assistant", bot_reply), unsafe_allow_html=True)
                if enable_tts:
                    speak_text(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
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
            bot_reply = handle_model_call(
                SYSTEM_INSTRUCTION, 0.6,
                f"Tutor sedang menyiapkan petunjuk untuk tingkat {jenjang.split()[0]}..."
            )
            if bot_reply:
                st.markdown(render_chat_bubble("assistant", bot_reply), unsafe_allow_html=True)
                if enable_tts:
                    speak_text(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                save_message(supabase, st.session_state.session_id, jenjang, "assistant", bot_reply)

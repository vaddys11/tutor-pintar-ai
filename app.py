import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import pypdf

# -----------------------------------------------------------------------------
# 1. Konfigurasi Halaman & Styling UI
# -----------------------------------------------------------------------------
load_dotenv()

st.set_page_config(
    page_title="Tutor Pintar AI - Multi Jenjang",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS UI
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 12px; padding: 10px; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

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

# -----------------------------------------------------------------------------
# 2. Sidebar: Tingkat Pendidikan & Media Upload
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ Pengaturan Tutor")

# Fitur Pilihan Jenjang Pendidikan
jenjang = st.sidebar.selectbox(
    "🎓 Pilih Tingkat Pendidikan:",
    ["SD (Sekolah Dasar)", "SMP (Sekolah Menengah Pertama)", "SMA (Sekolah Menengah Atas)", "S1 (Mahasiswa)"]
)

enable_tts = st.sidebar.toggle("🔊 Aktifkan Suara Tutor (TTS)", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📸 Upload Foto Soal")
uploaded_image = st.sidebar.file_uploader("Upload gambar/foto PR", type=["jpg", "jpeg", "png"])

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Upload Dokumen (PDF)")
uploaded_pdf = st.sidebar.file_uploader("Upload buku paket / jurnal acuan", type=["pdf"])

pdf_context = ""
if uploaded_pdf:
    try:
        pdf_reader = pypdf.PdfReader(uploaded_pdf)
        for page in pdf_reader.pages:
            pdf_context += page.extract_text() or ""
        st.sidebar.success("✅ PDF Berhasil Dibaca!")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca PDF: {e}")

# -----------------------------------------------------------------------------
# 3. Dynamic System Instruction Sesuai Jenjang
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

# Ambil prompt sesuai yang dipilih di UI
SYSTEM_INSTRUCTION = PROMPT_PER_JENJANG[jenjang] + """
Aturan Umum:
- Jika pengguna meminta/memaksa jawaban langsung, tolak dengan ramah dan jelaskan pentingnya proses berpikir mandiri sesuai tingkat pendidikan mereka.
- Selalu batasi respons agar tidak menjadi 'penjawab instan'.
"""

# -----------------------------------------------------------------------------
# 4. State & Interface Utama
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🎓 Tutor Pintar AI")
st.caption(f"🚀 Pendamping Belajar Mode: **{jenjang}**")

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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------------------------------------------------------
# 5. Input & Respon Agen
# -----------------------------------------------------------------------------
if prompt := st.chat_input("Tanyakan materi atau konsep pelajaran di sini..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    contents = []
    
    if pdf_context:
        contents.append(types.Part.from_text(text=f"[DOKUMEN ACUAN/BUKU]:\n{pdf_context[:4000]}"))

    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

    if uploaded_image:
        img = Image.open(uploaded_image)
        contents.append(img)

    with st.chat_message("assistant"):
        with st.spinner(f"Tutor sedang menyiapkan petunjuk untuk tingkat {jenjang.split()[0]}..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.6,
                    )
                )
                
                bot_reply = response.text
                st.markdown(bot_reply)
                
                if enable_tts:
                    speak_text(bot_reply)

                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
            except Exception as e:
                st.error(f"Terjadi kesalahan teknis: {str(e)}")
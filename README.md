# 🎓 Tutor Pintar AI

Asisten Belajar Interaktif untuk siswa SMP/SMA menggunakan **Google Gemini 2.5 Flash**, **Streamlit**, dan **Metode Socratic**.

## 🚀 Cara Menjalankan Proyek

1. **Clone/Buka Folder Proyek** di VS Code.
2. **Buat Virtual Environment (opsional tapi disarankan):**
   ```bash
   python -m venv venv
   # Aktifkan di Windows:
   venv\Scripts\activate
   # Atau di Mac/Linux:
   source venv/bin/activate
   ```
3. **Install Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Konfigurasi API Key:**
   - Salin file `.env.example` menjadi `.env`:
     ```bash
     cp .env.example .env
     ```
   - Masukkan `GEMINI_API_KEY` kamu di dalam file `.env`. (Atau bisa dimasukkan langsung via sidebar UI Streamlit nanti).
5. **Jalankan Aplikasi:**
   ```bash
   streamlit run app.py
   ```

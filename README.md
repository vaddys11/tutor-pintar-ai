# 🎓 Tutor Pintar AI

Aplikasi bimbingan belajar interaktif berbasis **Streamlit** dan **AI** yang menerapkan metode pembelajaran **Socratic** (membimbing siswa menemukan jawaban sendiri melalui pertanyaan pemantik) serta dilengkapi dengan fitur **Kuis Adaptif**, **Riwayat Chat Tersimpan**, **Ekspor Catatan Belajar**, dan **Guardrail Anti-Jailbreak**.

---

## 🚀 Fitur Utama

- 💡 **Metode Pembelajaran Socratic**: AI bertindak sebagai tutor bijak yang membimbing siswa memahami konsep dasar, bukan sekadar memberikan jawaban langsung.
- 📝 **Kuis Adaptif & Evaluasi Pemahaman**: Generasi soal kuis otomatis di akhir sesi belajar berdasarkan riwayat percakapan.
- 💾 **Riwayat Chat Tersimpan (Supabase)**: Setiap pesan otomatis tersimpan ke database. Siswa bisa lanjut belajar kapan saja pakai kode sesi.
- 📄 **Ekspor Catatan Belajar (PDF)**: Unduh seluruh riwayat percakapan jadi PDF rapi, siap dicetak atau dibaca ulang.
- 🛡️ **Guardrail & Anti-Jailbreak**: Filter input mendeteksi percobaan manipulasi prompt (jailbreak), system instruction dikunci lapis tambahan, dan status keamanan tampil real-time di sidebar.
- 🎨 **UI/UX Modern**: Styling ala Tailwind CSS (custom, karena Streamlit tidak mendukung Tailwind compiler native) + ikon Lucide, bubble chat kustom, sidebar terstruktur per section.
- ⚡ **Multi-Model AI Fallback (Gratis)**: Terhubung lewat OpenRouter — kalau satu model gratis kena limit, otomatis pindah ke model gratis berikutnya tanpa gangguan.

---

## 🛠️ Teknologi yang Digunakan

- **Bahasa Pemrograman**: Python 3.10+
- **Framework UI**: [Streamlit](https://streamlit.io/) + custom CSS (Tailwind-style) + [Lucide Icons](https://lucide.dev/)
- **Model AI**: OpenRouter (OpenAI-compatible) — multi-model gratis dengan fallback otomatis (Gemini 2.0 Flash Lite, DeepSeek R1, Llama 3.3 70B, Qwen 2.5 72B)
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **Ekspor PDF**: fpdf2
- **Versi Kontrol**: Git & GitHub

---

## 📂 Struktur Proyek

```text
tutor-pintar-ai/
├── app.py              # Logika utama aplikasi Streamlit & alur chat
├── db.py                # Layer koneksi & query Supabase (riwayat chat)
├── export.py             # Generator PDF catatan belajar
├── guardrail.py           # Filter jailbreak & hardening system prompt
├── ui.py                  # Styling Tailwind-style + helper Lucide icon
├── requirements.txt      # Daftar dependensi & modul Python
└── README.md              # Dokumentasi resmi proyek
```

---

## ⚙️ Cara Menjalankan Proyek di Lokal

### 1. Prasyarat
Pastikan kamu sudah menginstal **Python 3.10** atau versi yang lebih baru di komputermu.

### 2. Clone Repositori
```bash
git clone https://github.com/vaddys11/tutor-pintar-ai.git
cd tutor-pintar-ai
```

### 3. Buat & Aktifkan Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate
  ```
- **Linux / macOS**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 4. Instal Dependensi
```bash
pip install -r requirements.txt
```

### 5. Setup Database Supabase
1. Buat project baru di [supabase.com](https://supabase.com/).
2. Buka **SQL Editor**, jalankan query berikut untuk buat tabel riwayat chat & daftar sesi:
   ```sql
   create table chat_history (
       id uuid primary key default gen_random_uuid(),
       session_id text not null,
       jenjang text not null,
       role text not null,
       content text not null,
       created_at timestamptz default now()
   );

   create index idx_session on chat_history(session_id);

   create table sessions (
       session_id text primary key,
       jenjang text not null,
       title text not null default 'Percakapan Baru',
       created_at timestamptz default now(),
       updated_at timestamptz default now()
   );

   create index idx_sessions_updated on sessions(updated_at desc);
   ```
   > Tabel `sessions` dipakai buat daftar sesi di sidebar (judul otomatis + rename). Judul dibuat otomatis dari pesan pertama tiap sesi, dan bisa diganti manual lewat ikon ✏️.
3. Ambil `Project URL` dan `anon public key` dari **Project Settings > API**.

> Kalau Supabase tidak dikonfigurasi, aplikasi tetap bisa dijalankan — hanya fitur simpan/lanjut riwayat chat yang nonaktif.

### 6. Konfigurasi API Key
Buat file `.env` di root folder proyek (atau set via Streamlit secrets):
```env
OPENROUTER_API_KEY=sk-or-v1-API_KEY_OPENROUTER_KAMU_DI_SINI
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=SUPABASE_ANON_KEY_KAMU_DI_SINI
```

### 7. Jalankan Aplikasi Streamlit
```bash
streamlit run app.py
```
Aplikasi akan otomatis terbuka di browser kamu pada alamat `http://localhost:8501`.

---

## 🛡️ Catatan Guardrail

Sistem anti-jailbreak bekerja di tiga lapis:
1. **Filter input** — mencocokkan pesan pengguna dengan pola percobaan manipulasi yang dikenal (contoh: perintah "abaikan instruksi sebelumnya", "aktifkan mode tanpa batasan", dsb).
2. **System instruction hardening** — instruksi inti dibungkus aturan non-negotiable yang melarang override peran atau kebocoran system prompt.
3. **Pengecekan output ringan** — mendeteksi kalau respons AI terlanjur memberi jawaban instan, lalu menambahkan pengingat.

Percobaan yang terdeteksi dicatat ke `guardrail.log` (lokal) dan ditampilkan sebagai penghitung di sidebar. Sistem ini adalah lapis pertahanan standar — bukan jaminan 100%, tetap disarankan pengawasan pengajar untuk penggunaan di lingkungan sekolah.

---

## 📝 Catatan Pengembangan & Keamanan

- **File `.env` & Konfigurasi Lokal**: Jangan pernah men-commit API Key atau kunci autentikasi ke repositori publik. Pastikan folder `.continue/` dan file `.env` sudah terdaftar di `.gitignore`.
- **Supabase Key**: Gunakan `anon public key` untuk aplikasi client-side seperti ini, bukan `service_role key`.

---

## 📄 Lisensi

Proyek ini dikembangkan untuk tujuan edukasi dan pembelajaran terbuka.

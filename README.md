# 🎓 Tutor Pintar AI

Aplikasi bimbingan belajar interaktif berbasis AI yang menerapkan metode
pembelajaran **Socratic** (membimbing siswa menemukan jawaban sendiri lewat
pertanyaan pemantik), dilengkapi **Kuis Adaptif**, **Riwayat Chat Tersimpan**,
**Ekspor Catatan Belajar (PDF)**, **Guardrail Anti-Jailbreak**, dan
**Speech-to-Text**.

> **Migrasi arsitektur:** Project ini awalnya Streamlit monolitik, sekarang
> full-stack **FastAPI (backend) + Next.js (frontend)**. Versi Streamlit lama
> masih disimpan di `legacy-streamlit/` sebagai referensi/cadangan — gak lagi
> dikembangkan.

---

## 🏗️ Arsitektur

```text
tutor-pintar-ai/
├── backend/               # FastAPI — logika AI, guardrail, database, PDF
│   ├── main.py             # Endpoint REST
│   ├── prompts.py           # System prompt per jenjang pendidikan
│   ├── llm.py                 # OpenRouter + multi-model fallback gratis
│   ├── db.py                   # Supabase (riwayat chat & sesi)
│   ├── guardrail.py              # Filter anti-jailbreak
│   ├── export.py                  # Generator PDF catatan belajar
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/               # Next.js (App Router) + Tailwind CSS
│   ├── app/                  # Layout & halaman utama
│   ├── components/            # Sidebar, ChatWindow, ChatInput, MicButton, dst
│   ├── context/ChatContext.tsx  # State management (React Context)
│   ├── hooks/useSpeechRecognition.ts  # Web Speech API (STT)
│   ├── lib/                     # Connector API + tipe data
│   └── .env.local.example
│
└── legacy-streamlit/        # Versi lama (Streamlit), disimpan sebagai arsip
```

**Alur data:** Frontend (Next.js, `localhost:3000`) → REST API (FastAPI,
`localhost:8000`) → OpenRouter (multi-model AI gratis) + Supabase (riwayat
chat & sesi).

---

## 🚀 Fitur

- 💡 **Metode Socratic** — AI membimbing lewat pertanyaan, bukan kasih jawaban instan
- 📝 **Kuis Adaptif** — soal latihan otomatis dari riwayat percakapan
- 💾 **Riwayat Chat Tersimpan** — Supabase, sidebar bisa buka/rename sesi kapan saja
- 📄 **Ekspor PDF** — catatan belajar diunduh langsung dari chat
- 🛡️ **Guardrail Anti-Jailbreak** — filter pola manipulasi prompt + status real-time
- 🎙️ **Speech-to-Text** — native Web Speech API browser, gratis tanpa API key tambahan
- ⚡ **Multi-Model AI Fallback** — OpenRouter, otomatis pindah model gratis kalau satu kena limit
- 🎨 **UI Modern** — Tailwind CSS, rounded-2xl, avatar kustom, tema ramah anak

---

## ⚙️ Cara Menjalankan (Lokal)

Butuh **2 terminal terpisah** — backend dan frontend jalan sebagai proses independen.

### 1. Setup Database Supabase

Buka [supabase.com](https://supabase.com/) → bikin project baru → **SQL Editor**, jalankan:

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

Ambil `Project URL` dan `anon public key` dari **Project Settings > API**.

### 2. Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\Activate
pip install -r requirements.txt

cp .env.example .env
# isi OPENROUTER_API_KEY, SUPABASE_URL, SUPABASE_KEY di .env

uvicorn main:app --reload --port 8000
```

Cek jalan: buka `http://localhost:8000/docs` (Swagger UI otomatis dari FastAPI).

**OpenRouter API key** — daftar gratis di [openrouter.ai/keys](https://openrouter.ai/keys).
Model gratis yang dipakai **diambil live** dari katalog OpenRouter (bukan
hardcode), karena katalog gratisnya sering rotasi.

### 3. Frontend (Next.js)

Di terminal terpisah:

```bash
cd frontend
npm install

cp .env.local.example .env.local
# defaultnya udah nunjuk ke http://localhost:8000, biasanya gak perlu diubah

npm run dev
```

Buka `http://localhost:3000`.

---

## 🎙️ Catatan Speech-to-Text

Fitur mic pakai **Web Speech API** bawaan browser (`webkitSpeechRecognition`),
bukan library/model eksternal — jadi gratis dan gak nambah beban ke backend.

**Keterbatasan:** cuma jalan optimal di **Chrome/Edge** (Chromium). Firefox &
Safari dukungannya terbatas/gak ada — tombol mic otomatis hilang kalau browser
gak dukung, chat tetap bisa dipakai lewat teks seperti biasa.

---

## 🛡️ Catatan Guardrail

Filter anti-jailbreak jalan di backend (`guardrail.py`), tiga lapis:
1. **Filter input** — deteksi pola manipulasi prompt umum (ID + EN)
2. **System instruction hardening** — instruksi inti dibungkus aturan anti-override
3. **Pengecekan output ringan** — deteksi kalau AI kebetulan kasih jawaban terlalu instan

Percobaan yang diblokir dicatat ke `backend/guardrail.log`, dihitung ulang
lewat endpoint `GET /api/sessions/{id}/guardrail` — gak perlu tabel DB terpisah.

Ini lapis pertahanan standar, bukan jaminan 100% — tetap disarankan pengawasan
pengajar buat penggunaan di lingkungan sekolah.

---

## 🌐 Deploy

- **Backend**: platform apapun yang jalanin ASGI (Railway, Render, Fly.io, VPS + `uvicorn`/`gunicorn`). Set `FRONTEND_ORIGINS` di env ke domain frontend production.
- **Frontend**: Vercel paling gampang buat Next.js. Set `NEXT_PUBLIC_API_URL` ke URL backend production.
- Pastikan `SUPABASE_URL`, `SUPABASE_KEY`, `OPENROUTER_API_KEY` di-set sebagai env var di platform deploy backend — jangan pernah commit `.env` ke repo publik.

---

## 📌 Catatan Scope

Fitur upload gambar/PDF referensi (ada di versi Streamlit lama) **belum
dipindah** ke versi FastAPI + Next.js ini — di luar scope migrasi yang
diminta. Kalau dibutuhkan, perlu endpoint upload terpisah di backend + UI
upload di frontend.

---

## 📄 Lisensi

Proyek ini dikembangkan untuk tujuan edukasi dan pembelajaran terbuka.

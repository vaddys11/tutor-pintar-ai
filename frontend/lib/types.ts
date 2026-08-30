export const JENJANG_OPTIONS = [
  "SD (Sekolah Dasar)",
  "SMP (Sekolah Menengah Pertama)",
  "SMA (Sekolah Menengah Atas)",
  "S1 (Mahasiswa)",
] as const;

export type Jenjang = (typeof JENJANG_OPTIONS)[number];

export interface Message {
  role: "user" | "assistant";
  content: string;
  model?: string | null;
}

export interface SessionItem {
  session_id: string;
  title: string;
  jenjang: string;
  updated_at: string;
}

export const QUIZ_TRIGGER_MESSAGE =
  "📝 Tolong buatkan 2 soal latihan adaptif berdasarkan materi yang telah kita bahas untuk menguji pemahamanku.";

export interface CurriculumModule {
  id: string;
  title: string;
  jenjang: string;
  mata_pelajaran: string;
  source_type: "upload" | "text";
  original_filename?: string | null;
  status: "aktif" | "nonaktif";
  processing_status: "processing" | "ready" | "failed";
  chunk_count: number;
  created_at: string;
}

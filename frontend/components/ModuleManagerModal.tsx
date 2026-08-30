"use client";

import { useCallback, useEffect, useState } from "react";
import { FileText, Loader2, Trash2, Upload, X } from "lucide-react";
import {
  apiAddModuleText,
  apiDeleteModule,
  apiListModules,
  apiUpdateModuleStatus,
  apiUploadModule,
} from "@/lib/api";
import { JENJANG_OPTIONS, type CurriculumModule } from "@/lib/types";

interface ModuleManagerModalProps {
  open: boolean;
  onClose: () => void;
}

const ALLOWED_EXT = ".pdf,.txt,.md";
const POLL_INTERVAL_MS = 4000;

export function ModuleManagerModal({ open, onClose }: ModuleManagerModalProps) {
  const [tab, setTab] = useState<"upload" | "text">("upload");
  const [title, setTitle] = useState("");
  const [jenjang, setJenjang] = useState<string>(JENJANG_OPTIONS[0]);
  const [mataPelajaran, setMataPelajaran] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [textContent, setTextContent] = useState("");

  const [modules, setModules] = useState<CurriculumModule[]>([]);
  const [modulesLoading, setModulesLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const refreshModules = useCallback(async () => {
    try {
      const data = await apiListModules();
      setModules(data);
    } catch {
      setModules([]);
    } finally {
      setModulesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch daftar modul begitu modal dibuka, pola standar
    setModulesLoading(true);
    refreshModules();
  }, [open, refreshModules]);

  // Poll ringan tiap beberapa detik SELAMA masih ada modul "processing", biar status
  // "Memproses..." otomatis update jadi "Siap" tanpa user harus tutup-buka modal lagi.
  useEffect(() => {
    if (!open) return;
    const hasProcessing = modules.some((m) => m.processing_status === "processing");
    if (!hasProcessing) return;
    const interval = setInterval(refreshModules, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [open, modules, refreshModules]);

  const resetForm = () => {
    setTitle("");
    setMataPelajaran("");
    setFile(null);
    setTextContent("");
    setFormError(null);
  };

  const handleSubmit = async () => {
    setFormError(null);
    if (!title.trim() || !mataPelajaran.trim()) {
      setFormError("Judul modul & mata pelajaran wajib diisi.");
      return;
    }
    if (tab === "upload" && !file) {
      setFormError("Pilih file dulu (.pdf, .txt, atau .md).");
      return;
    }
    if (tab === "text" && !textContent.trim()) {
      setFormError("Isi teks/rangkumannya dulu.");
      return;
    }

    setSubmitting(true);
    try {
      if (tab === "upload" && file) {
        await apiUploadModule(file, title.trim(), jenjang, mataPelajaran.trim());
      } else {
        await apiAddModuleText(title.trim(), jenjang, mataPelajaran.trim(), textContent.trim());
      }
      resetForm();
      await refreshModules();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Gagal simpan modul");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (m: CurriculumModule) => {
    const next: "aktif" | "nonaktif" = m.status === "aktif" ? "nonaktif" : "aktif";
    setModules((prev) => prev.map((x) => (x.id === m.id ? { ...x, status: next } : x))); // optimistic
    try {
      await apiUpdateModuleStatus(m.id, next);
    } catch {
      await refreshModules(); // rollback dari server kalau request gagal
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiDeleteModule(id);
      await refreshModules();
    } finally {
      setDeletingId(null);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-3 sm:p-4">
      <div className="flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 sm:px-6">
          <div className="min-w-0">
            <h2 className="truncate text-base font-bold text-slate-800 sm:text-lg">
              Kelola Modul Kurikulum
            </h2>
            <p className="hidden text-xs text-slate-500 sm:block">
              Tambah materi referensi buat dijadiin acuan jawaban Tutor Pintar
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Tutup"
            className="shrink-0 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 sm:px-6">
          {/* Form tambah modul */}
          <div className="mb-6 rounded-xl border border-slate-200 p-3 sm:p-4">
            {/* Tabs */}
            <div className="mb-4 flex gap-1.5 rounded-lg bg-slate-100 p-1">
              <button
                onClick={() => setTab("upload")}
                className={`flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 text-xs font-semibold transition-colors sm:text-sm ${
                  tab === "upload" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500 hover:text-slate-700"
                }`}
              >
                <Upload size={15} /> Upload File
              </button>
              <button
                onClick={() => setTab("text")}
                className={`flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 text-xs font-semibold transition-colors sm:text-sm ${
                  tab === "text" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500 hover:text-slate-700"
                }`}
              >
                <FileText size={15} /> Input Teks
              </button>
            </div>

            {/* Metadata (dipakai kedua tab) */}
            <div className="mb-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-600">Judul Modul</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Contoh: Fotosintesis Bab 3"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-indigo-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-600">Jenjang</label>
                <select
                  value={jenjang}
                  onChange={(e) => setJenjang(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-indigo-400"
                >
                  {JENJANG_OPTIONS.map((j) => (
                    <option key={j} value={j}>
                      {j}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-600">Mata Pelajaran</label>
                <input
                  value={mataPelajaran}
                  onChange={(e) => setMataPelajaran(e.target.value)}
                  placeholder="Contoh: IPA"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-indigo-400"
                />
              </div>
            </div>

            {/* Konten sesuai tab aktif */}
            {tab === "upload" ? (
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-600">
                  File (.pdf, .txt, .md — maks 5MB)
                </label>
                <input
                  type="file"
                  accept={ALLOWED_EXT}
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full rounded-lg border border-dashed border-slate-300 px-3 py-2 text-xs text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-50 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-indigo-600 sm:text-sm"
                />
              </div>
            ) : (
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-600">Isi Rangkuman/Materi</label>
                <textarea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  rows={6}
                  placeholder="Paste atau ketik rangkuman materi di sini..."
                  className="w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-indigo-400"
                />
              </div>
            )}

            {formError && <p className="mt-2 text-xs font-medium text-red-600">{formError}</p>}

            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting && <Loader2 size={16} className="animate-spin" />}
              {submitting ? "Memproses..." : "Simpan Modul"}
            </button>
          </div>

          {/* Tabel daftar modul */}
          <div>
            <h3 className="mb-2 text-sm font-bold text-slate-700">Daftar Modul ({modules.length})</h3>
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full min-w-[560px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-3 py-2">Judul</th>
                    <th className="px-3 py-2">Jenjang</th>
                    <th className="px-3 py-2">Mapel</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-center">Aktif</th>
                    <th className="px-3 py-2 text-center">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {modulesLoading && (
                    <tr>
                      <td colSpan={6} className="px-3 py-6 text-center text-slate-400">
                        <Loader2 size={18} className="mx-auto animate-spin" />
                      </td>
                    </tr>
                  )}
                  {!modulesLoading && modules.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-3 py-6 text-center text-xs italic text-slate-400">
                        Belum ada modul kurikulum ditambahkan.
                      </td>
                    </tr>
                  )}
                  {modules.map((m) => (
                    <tr key={m.id}>
                      <td className="max-w-[160px] truncate px-3 py-2.5 font-medium text-slate-800">
                        {m.title}
                      </td>
                      <td className="px-3 py-2.5 text-xs text-slate-500">{m.jenjang.split(" ")[0]}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-500">{m.mata_pelajaran}</td>
                      <td className="px-3 py-2.5">
                        {m.processing_status === "processing" && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-600">
                            <Loader2 size={10} className="animate-spin" /> Memproses
                          </span>
                        )}
                        {m.processing_status === "ready" && (
                          <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-600">
                            Siap ({m.chunk_count} chunk)
                          </span>
                        )}
                        {m.processing_status === "failed" && (
                          <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-semibold text-red-600">
                            Gagal
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <button
                          onClick={() => handleToggleStatus(m)}
                          aria-label={m.status === "aktif" ? "Nonaktifkan modul" : "Aktifkan modul"}
                          className={`relative h-5 w-9 rounded-full transition-colors ${
                            m.status === "aktif" ? "bg-emerald-500" : "bg-slate-300"
                          }`}
                        >
                          <span
                            className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
                              m.status === "aktif" ? "translate-x-[18px]" : "translate-x-0.5"
                            }`}
                          />
                        </button>
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        {deletingId === m.id ? (
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => handleDelete(m.id)}
                              className="text-[11px] font-semibold text-red-600 hover:underline"
                            >
                              Ya
                            </button>
                            <button
                              onClick={() => setDeletingId(null)}
                              className="text-[11px] text-slate-400 hover:underline"
                            >
                              Batal
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeletingId(m.id)}
                            aria-label="Hapus modul"
                            className="text-slate-400 hover:text-red-500"
                          >
                            <Trash2 size={15} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

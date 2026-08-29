"use client";

import { useState } from "react";
import { Check, GraduationCap, Loader2, Pencil, Plus, Trash2, X } from "lucide-react";
import { useChat } from "@/context/ChatContext";
import { JENJANG_OPTIONS } from "@/lib/types";

function formatSessionTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString("id-ID", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function Sidebar() {
  const {
    sessions,
    sessionsLoading,
    activeSessionId,
    jenjang,
    setJenjang,
    createNewSession,
    selectSession,
    renameSession,
    deleteSession,
    blockedCount,
    sidebarOpen,
    closeSidebar,
  } = useChat();

  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const startRename = (id: string, currentTitle: string) => {
    setDeletingId(null);
    setRenamingId(id);
    setRenameValue(currentTitle);
  };

  const confirmRename = async (id: string) => {
    if (renameValue.trim()) {
      await renameSession(id, renameValue.trim());
    }
    setRenamingId(null);
  };

  const confirmDelete = async (id: string) => {
    await deleteSession(id);
    setDeletingId(null);
  };

  return (
    <>
      {/* Backdrop — cuma muncul pas sidebar dibuka di layar kecil */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex h-screen w-72 max-w-[85vw] shrink-0 transform flex-col border-r border-white/10 bg-gradient-to-b from-[#1e1b3a] to-[#15122b] text-slate-200 transition-transform duration-200 ease-out md:static md:z-auto md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500">
            <GraduationCap size={20} className="text-white" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-bold leading-none text-white">Tutor Pintar AI</h1>
            <p className="mt-0.5 truncate text-[11px] text-slate-400">Belajar seru, tanpa jawaban instan</p>
          </div>
          <button
            onClick={closeSidebar}
            aria-label="Tutup menu"
            className="shrink-0 rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white md:hidden"
          >
            <X size={18} />
          </button>
        </div>

        {/* Jenjang */}
        <div className="mb-3 px-4">
          <label className="px-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Tingkat Pendidikan
          </label>
          <select
            value={jenjang}
            onChange={(e) => setJenjang(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-white/10 bg-[#2a2657] px-3 py-2.5 text-sm text-slate-100 outline-none transition-colors focus:border-indigo-400"
          >
            {JENJANG_OPTIONS.map((j) => (
              <option key={j} value={j}>
                {j}
              </option>
            ))}
          </select>
        </div>

        {/* Sesi baru */}
        <div className="mb-3 px-4">
          <button
            onClick={createNewSession}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-600 hover:shadow-emerald-500/30"
          >
            <Plus size={16} /> Sesi Baru
          </button>
        </div>

        {/* Daftar sesi */}
        <div className="flex-1 space-y-1 overflow-y-auto px-3 pb-3">
          <div className="px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Riwayat Belajar
          </div>

          {sessionsLoading && (
            <div className="flex items-center justify-center py-6 text-slate-500">
              <Loader2 size={18} className="animate-spin" />
            </div>
          )}

          {!sessionsLoading && sessions.length === 0 && (
            <p className="px-2 py-2 text-xs italic text-slate-500">
              Belum ada sesi tersimpan — mulai ngobrol dulu!
            </p>
          )}

          {sessions.map((s) => {
            const isActive = s.session_id === activeSessionId;
            const isRenaming = renamingId === s.session_id;
            const isDeleting = deletingId === s.session_id;

            return (
              <div
                key={s.session_id}
                className={`group rounded-xl border px-2.5 py-2 transition-colors ${
                  isActive
                    ? "border-indigo-400/40 bg-indigo-500/20"
                    : "border-transparent hover:bg-white/5"
                }`}
              >
                {isRenaming ? (
                  <div className="flex items-center gap-1.5">
                    <input
                      autoFocus
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && confirmRename(s.session_id)}
                      className="flex-1 rounded-lg border border-indigo-400/50 bg-[#2a2657] px-2 py-1 text-xs text-white outline-none"
                    />
                    <button
                      onClick={() => confirmRename(s.session_id)}
                      className="shrink-0 text-emerald-400 hover:text-emerald-300"
                      aria-label="Simpan judul"
                    >
                      <Check size={14} />
                    </button>
                    <button
                      onClick={() => setRenamingId(null)}
                      className="shrink-0 text-slate-400 hover:text-slate-300"
                      aria-label="Batal"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ) : isDeleting ? (
                  <div className="flex items-center gap-1.5">
                    <span className="flex-1 truncate text-xs text-red-300">Hapus sesi ini?</span>
                    <button
                      onClick={() => confirmDelete(s.session_id)}
                      className="shrink-0 text-red-400 hover:text-red-300"
                      aria-label="Ya, hapus"
                    >
                      <Check size={14} />
                    </button>
                    <button
                      onClick={() => setDeletingId(null)}
                      className="shrink-0 text-slate-400 hover:text-slate-300"
                      aria-label="Batal"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => !isActive && selectSession(s.session_id)}
                      className={`min-w-0 flex-1 truncate text-left text-sm ${
                        isActive ? "font-semibold text-white" : "text-slate-300"
                      }`}
                    >
                      {isActive && (
                        <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 align-middle" />
                      )}
                      {s.title}
                    </button>
                    <button
                      onClick={() => startRename(s.session_id, s.title)}
                      className="shrink-0 rounded p-1 text-slate-400 opacity-0 transition-opacity hover:text-indigo-300 group-hover:opacity-100 group-focus-within:opacity-100"
                      aria-label="Ganti judul"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      onClick={() => setDeletingId(s.session_id)}
                      className="shrink-0 rounded p-1 text-slate-400 opacity-0 transition-opacity hover:text-red-400 group-hover:opacity-100 group-focus-within:opacity-100"
                      aria-label="Hapus sesi"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                )}
                {s.updated_at && !isDeleting && (
                  <p className="mt-0.5 pl-0.5 text-[10px] text-slate-500">
                    {formatSessionTime(s.updated_at)}
                  </p>
                )}
              </div>
            );
          })}
        </div>

        {/* Guardrail status */}
        <div className="border-t border-white/10 px-4 py-3">
          <div
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold ${
              blockedCount === 0
                ? "border-emerald-400/20 bg-emerald-500/15 text-emerald-300"
                : "border-red-400/20 bg-red-500/15 text-red-300"
            }`}
          >
            {blockedCount === 0 ? "🛡️ Guardrail aktif" : `⚠️ ${blockedCount} percobaan diblokir`}
          </div>
        </div>
      </aside>
    </>
  );
}

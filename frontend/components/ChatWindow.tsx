"use client";

import { useEffect, useRef } from "react";
import { AlertCircle, FileDown, Loader2, Menu, Sparkles, Volume2, VolumeX, X } from "lucide-react";
import { useChat } from "@/context/ChatContext";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

export function ChatWindow() {
  const {
    messages,
    jenjang,
    activeSessionId,
    sendMessage,
    sendQuizRequest,
    exportPdf,
    isSending,
    error,
    clearError,
    toggleSidebar,
    autoSpeak,
    toggleAutoSpeak,
    isSpeaking,
    ttsSupported,
  } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  return (
    <div className="flex h-screen min-w-0 flex-1 flex-col bg-gradient-to-br from-violet-50 via-slate-50 to-white">
      {/* Hero header */}
      <div className="m-3 mb-2 flex items-center gap-2.5 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-500 px-4 py-4 text-white shadow-lg shadow-indigo-500/20 sm:m-5 sm:mb-3 sm:gap-3 sm:px-6 sm:py-5">
        {/* Hamburger — cuma muncul di layar kecil */}
        <button
          onClick={toggleSidebar}
          aria-label="Buka menu sesi"
          className="shrink-0 rounded-lg p-1.5 transition-colors hover:bg-white/15 md:hidden"
        >
          <Menu size={22} />
        </button>

        <div className="min-w-0">
          <h2 className="truncate text-base font-extrabold leading-tight sm:text-lg">Tutor Pintar AI</h2>
          <p className="hidden text-xs text-white/85 sm:block">
            Pendamping belajar interaktif dengan metode Socratic
          </p>
        </div>

        <div className="ml-auto flex shrink-0 items-center gap-2">
          {/* Toggle baca otomatis (TTS) — sembunyi kalau browser gak dukung */}
          {ttsSupported && (
            <button
              onClick={toggleAutoSpeak}
              aria-label={autoSpeak ? "Matikan baca otomatis" : "Aktifkan baca otomatis"}
              title={autoSpeak ? "Baca otomatis aktif — klik buat matikan" : "Klik buat aktifkan baca otomatis"}
              className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors ${
                autoSpeak ? "bg-white/25 text-white" : "bg-white/10 text-white/70 hover:bg-white/20"
              } ${isSpeaking ? "animate-pulse" : ""}`}
            >
              {autoSpeak ? <Volume2 size={16} /> : <VolumeX size={16} />}
            </button>
          )}
          <span className="rounded-full bg-white/20 px-2.5 py-1.5 text-[11px] font-semibold backdrop-blur-sm sm:px-3 sm:text-xs">
            {jenjang.split(" ")[0]}
          </span>
        </div>
      </div>

      {/* Aksi */}
      <div className="mb-2 flex flex-wrap items-center gap-2 px-3 sm:px-5">
        <button
          onClick={sendQuizRequest}
          disabled={messages.length === 0 || isSending}
          className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-indigo-600 shadow-sm transition-colors hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-40 sm:px-3.5"
        >
          <Sparkles size={14} /> <span className="hidden sm:inline">Uji Pemahamanku</span>
          <span className="sm:hidden">Kuis</span>
        </button>
        <button
          onClick={exportPdf}
          disabled={messages.length === 0 || !activeSessionId}
          className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 shadow-sm transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 sm:px-3.5"
        >
          <FileDown size={14} /> <span className="hidden sm:inline">Ekspor PDF</span>
          <span className="sm:hidden">PDF</span>
        </button>
      </div>

      {/* Banner error */}
      {error && (
        <div className="mx-3 mb-2 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700 sm:mx-5 sm:px-4">
          <AlertCircle size={16} className="shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={clearError} aria-label="Tutup notifikasi" className="shrink-0 text-red-400 hover:text-red-600">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Pesan */}
      <div className="flex-1 space-y-4 overflow-y-auto px-3 py-3 sm:px-5">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-slate-400">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100 text-3xl">
              👋
            </div>
            <p className="max-w-xs text-sm">
              Halo! Aku Tutor Pintar. Tanyakan materi pelajaran apa aja, aku bakal bantu kamu mikir,
              bukan cuma kasih jawaban 😊
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} model={m.model} />
        ))}

        {isSending && (
          <div className="flex items-center gap-2 pl-11 text-sm text-slate-400">
            <Loader2 size={14} className="animate-spin" /> Tutor lagi mikir...
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-3 pb-3 pt-2 sm:px-5 sm:pb-5">
        <ChatInput onSend={sendMessage} disabled={isSending} />
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef } from "react";
import { AlertCircle, FileDown, Loader2, Sparkles, X } from "lucide-react";
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
  } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  return (
    <div className="flex h-screen flex-1 flex-col bg-gradient-to-br from-violet-50 via-slate-50 to-white">
      {/* Hero header */}
      <div className="m-5 mb-3 flex items-center gap-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-500 px-6 py-5 text-white shadow-lg shadow-indigo-500/20">
        <div>
          <h2 className="text-lg font-extrabold leading-tight">Tutor Pintar AI</h2>
          <p className="text-xs text-white/85">Pendamping belajar interaktif dengan metode Socratic</p>
        </div>
        <span className="ml-auto shrink-0 rounded-full bg-white/20 px-3 py-1.5 text-xs font-semibold backdrop-blur-sm">
          {jenjang}
        </span>
      </div>

      {/* Aksi */}
      <div className="mb-2 flex items-center gap-2 px-5">
        <button
          onClick={sendQuizRequest}
          disabled={messages.length === 0 || isSending}
          className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-indigo-600 shadow-sm transition-colors hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Sparkles size={14} /> Uji Pemahamanku
        </button>
        <button
          onClick={exportPdf}
          disabled={messages.length === 0 || !activeSessionId}
          className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-600 shadow-sm transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <FileDown size={14} /> Ekspor PDF
        </button>
      </div>

      {/* Banner error */}
      {error && (
        <div className="mx-5 mb-2 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700">
          <AlertCircle size={16} className="shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={clearError} aria-label="Tutup notifikasi" className="shrink-0 text-red-400 hover:text-red-600">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Pesan */}
      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-3">
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
      <div className="px-5 pb-5 pt-2">
        <ChatInput onSend={sendMessage} disabled={isSending} />
      </div>
    </div>
  );
}

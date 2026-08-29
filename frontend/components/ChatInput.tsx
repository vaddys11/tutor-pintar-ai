"use client";

import { useState, type KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { MicButton } from "./MicButton";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTranscript = (text: string) => {
    setValue((prev) => (prev ? `${prev} ${text}` : text));
  };

  return (
    <div className="flex items-end gap-1.5 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm focus-within:border-indigo-300 focus-within:ring-2 focus-within:ring-indigo-100 sm:gap-2 sm:p-3">
      <MicButton onTranscript={handleTranscript} disabled={disabled} />
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Tanyakan materi atau konsep pelajaran di sini..."
        rows={1}
        disabled={disabled}
        className="max-h-32 min-w-0 flex-1 resize-none bg-transparent py-2.5 text-base text-slate-800 outline-none placeholder:text-slate-400 disabled:opacity-60"
      />
      <button
        type="button"
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        aria-label="Kirim pesan"
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Send size={18} />
      </button>
    </div>
  );
}

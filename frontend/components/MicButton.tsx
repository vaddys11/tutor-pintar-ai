"use client";

import { useCallback, useState } from "react";
import { Mic, Square } from "lucide-react";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";

interface MicButtonProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export function MicButton({ onTranscript, disabled }: MicButtonProps) {
  const [notice, setNotice] = useState<string | null>(null);

  const handleResult = useCallback(
    (text: string) => {
      onTranscript(text);
    },
    [onTranscript]
  );

  const handleError = useCallback((message: string) => {
    setNotice(message);
    setTimeout(() => setNotice(null), 3500);
  }, []);

  const { isListening, isSupported, start, stop } = useSpeechRecognition({
    lang: "id-ID",
    onResult: handleResult,
    onError: handleError,
  });

  // Belum sempat dicek di client (SSR) -> render placeholder biar gak ada layout shift
  if (isSupported === null) {
    return <div className="h-11 w-11 shrink-0" />;
  }

  // Browser gak dukung Web Speech API (Firefox/Safari umumnya) -> sembunyikan tombol
  if (isSupported === false) {
    return null;
  }

  return (
    <div className="relative shrink-0">
      <button
        type="button"
        onClick={isListening ? stop : start}
        disabled={disabled}
        aria-label={isListening ? "Berhenti merekam" : "Mulai bicara"}
        title={isListening ? "Berhenti merekam" : "Tekan buat ngomong"}
        className={`flex h-11 w-11 items-center justify-center rounded-full transition-all disabled:cursor-not-allowed disabled:opacity-40 ${
          isListening
            ? "animate-pulse bg-red-500 text-white shadow-lg shadow-red-500/30"
            : "bg-gradient-to-br from-indigo-500 to-purple-500 text-white hover:shadow-lg hover:shadow-indigo-500/30"
        }`}
      >
        {isListening ? <Square size={18} /> : <Mic size={20} />}
      </button>
      {notice && (
        <div className="absolute bottom-full right-0 mb-2 w-52 rounded-xl bg-slate-800 px-3 py-2 text-xs text-white shadow-lg">
          {notice}
        </div>
      )}
    </div>
  );
}

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Bersihin teks dari markup markdown & simbol yang bikin TTS ngeja aneh
 * (misal "**penting**" jangan dibaca "bintang bintang penting bintang bintang").
 */
export function cleanTextForSpeech(raw: string): string {
  let text = raw;

  // Blok kode ```...``` dibuang total (gak ada gunanya dibacain)
  text = text.replace(/```[\s\S]*?```/g, " ");
  // Inline code `code`
  text = text.replace(/`([^`]+)`/g, "$1");
  // Bold/italic **text**, *text*, __text__, _text_
  text = text.replace(/(\*\*\*|\*\*|\*|___|__|_)(.+?)\1/g, "$2");
  // Heading markdown (# ## ### dst) di awal baris
  text = text.replace(/^#{1,6}\s+/gm, "");
  // Link markdown [teks](url) -> ambil teksnya aja
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  // Blockquote >
  text = text.replace(/^>\s?/gm, "");
  // List marker -, *, + di awal baris
  text = text.replace(/^[\s]*[-*+]\s+/gm, "");
  // Angka list "1. " di awal baris
  text = text.replace(/^\s*\d+\.\s+/gm, "");
  // Emoji & simbol non-alfanumerik yang suka keikut kebaca aneh
  text = text.replace(
    /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2190}-\u{21FF}\u{2B00}-\u{2BFF}\u{FE00}-\u{FE0F}\u{200D}]/gu,
    " "
  );
  // Rapikan whitespace berlebih
  text = text.replace(/\n{2,}/g, ". ").replace(/\n/g, " ").replace(/\s{2,}/g, " ").trim();

  return text;
}

interface UseSpeechSynthesisReturn {
  isSpeaking: boolean;
  isSupported: boolean | null;
  speak: (text: string) => void;
  stop: () => void;
}

/** Wrapper Web Speech API (SpeechSynthesis) buat baca teks otomatis, gratis & native browser. */
export function useSpeechSynthesis(lang: string = "id-ID"): UseSpeechSynthesisReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState<boolean | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- cek dukungan browser API sekali pas mount
    setIsSupported(typeof window !== "undefined" && "speechSynthesis" in window);
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const stop = useCallback(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

      window.speechSynthesis.cancel(); // hentikan ucapan sebelumnya biar gak numpuk

      const cleaned = cleanTextForSpeech(text);
      if (!cleaned) return;

      const utterance = new SpeechSynthesisUtterance(cleaned);
      utterance.lang = lang;
      utterance.rate = 1;
      utterance.pitch = 1;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    },
    [lang]
  );

  return { isSpeaking, isSupported, speak, stop };
}

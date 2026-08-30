"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Bersihin teks dari markup markdown & simbol yang bikin TTS ngeja aneh
 * (misal "**penting**" jangan dibaca "bintang bintang penting bintang bintang").
 */
export function cleanTextForSpeech(raw: string): string {
  let text = raw;

  // 1. Blok kode ```...``` dibuang total
  text = text.replace(/```[\s\S]*?```/g, " ");
  // 2. Inline code `code`
  text = text.replace(/`([^`]+)`/g, "$1");
  // 3. Bold/italic **text**, *text*, ___text___
  text = text.replace(/(\*\*\*|\*\*|\*|___|__|_)(.+?)\1/g, "$2");
  // 4. Heading markdown (# ## ### dst)
  text = text.replace(/^#{1,6}\s+/gm, "");
  // 5. Link markdown [teks](url)
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  // 6. Blockquote & List markers
  text = text.replace(/^>\s?/gm, "");
  text = text.replace(/^[\s]*[-*+]\s+/gm, "");
  text = text.replace(/^\s*\d+\.\s+/gm, "");

  // 7. Hapus garis pemisah horizontal & simbol bintang
  text = text.replace(/^[-*_]{3,}\s*$/gm, " ");
  text = text.replace(/\*/g, "");

  // 8. Hapus tanda baca tanpa menghapus harakat/karakter Arab
  text = text.replace(/[:;()"[\]{}~`^]/g, " ");
  text = text.replace(/\s+-\s+/g, " ");

  // 9. Hapus Emoji saja (tetap mempertahankan teks Arab & Latin)
  text = text.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, " ");

  // 10. Rapikan whitespace
  text = text
    .replace(/\n{2,}/g, ". ")
    .replace(/\n/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim();

  return text;
}

interface UseSpeechSynthesisReturn {
  isSpeaking: boolean;
  isSupported: boolean | null;
  speak: (text: string) => void;
  stop: () => void;
}

/** Wrapper Web Speech API (SpeechSynthesis) buat baca teks otomatis, gratis & native browser. */
export function useSpeechSynthesis(
  lang: string = "id-ID",
): UseSpeechSynthesisReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState<boolean | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- cek dukungan browser API sekali pas mount
    setIsSupported(
      typeof window !== "undefined" && "speechSynthesis" in window,
    );
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
      if (typeof window === "undefined" || !("speechSynthesis" in window))
        return;

      window.speechSynthesis.cancel();

      const cleaned = cleanTextForSpeech(text);
      if (!cleaned) return;

      // Cek apakah teks mengandung karakter Arab
      const hasArabic = /[\u0600-\u06FF]/.test(cleaned);

      if (hasArabic) {
        // Jika ada teks Arab, pisahkan menjadi per baris/kalimat
        const chunks = cleaned
          .split(/(?<=[.!?\n])|\n/)
          .filter((c) => c.trim().length > 0);

        chunks.forEach((chunk) => {
          const uttr = new SpeechSynthesisUtterance(chunk);
          // Jika potongan kalimat ini Arab, pakai bahasa Arab
          if (/[\u0600-\u06FF]/.test(chunk)) {
            uttr.lang = "ar-SA";
          } else {
            uttr.lang = lang; // id-ID
          }
          window.speechSynthesis.speak(uttr);
        });
      } else {
        // Teks biasa tanpa Arab
        const utterance = new SpeechSynthesisUtterance(cleaned);
        utterance.lang = lang;
        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);
        window.speechSynthesis.speak(utterance);
      }
    },
    [lang],
  );

  return { isSpeaking, isSupported, speak, stop };
}

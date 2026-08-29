"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseSpeechRecognitionOptions {
  lang?: string;
  onResult: (transcript: string) => void;
  onError?: (message: string) => void;
}

interface UseSpeechRecognitionReturn {
  isListening: boolean;
  /** null = belum dicek (SSR/belum mount), true/false = hasil cek di browser */
  isSupported: boolean | null;
  start: () => void;
  stop: () => void;
}

/**
 * Wrapper Web Speech API (SpeechRecognition) native browser — gratis, gak
 * butuh API key/model transkripsi terpisah. Cuma jalan optimal di
 * Chrome/Edge (Chromium); Firefox & Safari dukungannya terbatas/gak ada.
 */
export function useSpeechRecognition({
  lang = "id-ID",
  onResult,
  onError,
}: UseSpeechRecognitionOptions): UseSpeechRecognitionReturn {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState<boolean | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any;
    const SpeechRecognitionCtor = w.SpeechRecognition || w.webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- cek dukungan browser API sekali pas mount
      setIsSupported(false);
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = lang;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (event: any) => {
      const transcript = event.results?.[0]?.[0]?.transcript;
      if (transcript) onResult(transcript);
    };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onerror = (event: any) => {
      setIsListening(false);
      if (event?.error === "not-allowed" || event?.error === "permission-denied") {
        onError?.("Izin mikrofon ditolak. Aktifkan izin mikrofon di browser buat pakai fitur suara.");
      } else if (event?.error === "no-speech") {
        onError?.("Gak kedengeran suara. Coba lagi ya.");
      } else {
        onError?.("Gagal merekam suara. Coba lagi.");
      }
    };
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    setIsSupported(true);

    return () => {
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      recognitionRef.current = null;
    };
  }, [lang, onResult, onError]);

  const start = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch {
        // "already started" kalau dipanggil dobel cepat — abaikan aman
      }
    }
  }, [isListening]);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  return { isListening, isSupported, start, stop };
}

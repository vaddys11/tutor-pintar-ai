"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  apiChat,
  apiCreateSession,
  apiExportPdf,
  apiGetGuardrailStatus,
  apiGetMessages,
  apiListSessions,
  apiRenameSession,
} from "@/lib/api";
import { JENJANG_OPTIONS, QUIZ_TRIGGER_MESSAGE, type Message, type SessionItem } from "@/lib/types";

interface ChatContextValue {
  sessions: SessionItem[];
  sessionsLoading: boolean;
  activeSessionId: string | null;
  messages: Message[];
  jenjang: string;
  setJenjang: (jenjang: string) => void;
  isSending: boolean;
  blockedCount: number;
  error: string | null;
  clearError: () => void;
  createNewSession: () => Promise<void>;
  selectSession: (sessionId: string) => Promise<void>;
  renameSession: (sessionId: string, title: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  sendQuizRequest: () => Promise<void>;
  exportPdf: () => Promise<void>;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [jenjang, setJenjang] = useState<string>(JENJANG_OPTIONS[0]);
  const [isSending, setIsSending] = useState(false);
  const [blockedCount, setBlockedCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const refreshSessions = useCallback(async () => {
    try {
      const data = await apiListSessions();
      setSessions(data);
      return data;
    } catch {
      // Backend belum jalan / Supabase belum terhubung -> sidebar tetap kosong, gak nge-block UI
      setSessions([]);
      return [];
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch daftar sesi sekali pas mount, pola standar
    refreshSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createNewSession = useCallback(async () => {
    setError(null);
    try {
      const { session_id } = await apiCreateSession(jenjang);
      setActiveSessionId(session_id);
      setMessages([]);
      setBlockedCount(0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal bikin sesi baru");
    }
  }, [jenjang]);

  const selectSession = useCallback(
    async (sessionId: string) => {
      setError(null);
      setActiveSessionId(sessionId);
      try {
        const [msgs, guard] = await Promise.all([
          apiGetMessages(sessionId),
          apiGetGuardrailStatus(sessionId),
        ]);
        setMessages(
          msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content }))
        );
        setBlockedCount(guard.blocked_count);
        const meta = sessions.find((s) => s.session_id === sessionId);
        if (meta) setJenjang(meta.jenjang);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Gagal muat riwayat sesi");
      }
    },
    [sessions]
  );

  const renameSession = useCallback(
    async (sessionId: string, title: string) => {
      try {
        await apiRenameSession(sessionId, title);
        await refreshSessions();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Gagal rename sesi");
      }
    },
    [refreshSessions]
  );

  const sendMessageInternal = useCallback(
    async (text: string, mode: "chat" | "quiz") => {
      setError(null);
      let sid = activeSessionId;

      // Auto-bikin sesi kalau user langsung ngetik tanpa pencet "Sesi Baru" dulu
      if (!sid) {
        try {
          const { session_id } = await apiCreateSession(jenjang);
          sid = session_id;
          setActiveSessionId(sid);
        } catch (e) {
          setError(e instanceof Error ? e.message : "Gagal bikin sesi");
          return;
        }
      }

      setMessages((prev) => [...prev, { role: "user", content: text }]);
      setIsSending(true);
      try {
        const res = await apiChat(sid, jenjang, text, mode);
        setMessages((prev) => [...prev, { role: "assistant", content: res.reply, model: res.model }]);
        if (res.blocked) setBlockedCount((c) => c + 1);
        await refreshSessions(); // biar judul/urutan sidebar ke-update (auto-title dari backend)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Gagal kirim pesan, coba lagi.");
        setMessages((prev) => prev.slice(0, -1)); // rollback bubble user kalau request total gagal
      } finally {
        setIsSending(false);
      }
    },
    [activeSessionId, jenjang, refreshSessions]
  );

  const sendMessage = useCallback((text: string) => sendMessageInternal(text, "chat"), [sendMessageInternal]);
  const sendQuizRequest = useCallback(
    () => sendMessageInternal(QUIZ_TRIGGER_MESSAGE, "quiz"),
    [sendMessageInternal]
  );

  const exportPdf = useCallback(async () => {
    if (!activeSessionId) return;
    setError(null);
    try {
      const blob = await apiExportPdf(activeSessionId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `catatan-belajar-${activeSessionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal ekspor PDF");
    }
  }, [activeSessionId]);

  return (
    <ChatContext.Provider
      value={{
        sessions,
        sessionsLoading,
        activeSessionId,
        messages,
        jenjang,
        setJenjang,
        isSending,
        blockedCount,
        error,
        clearError,
        createNewSession,
        selectSession,
        renameSession,
        sendMessage,
        sendQuizRequest,
        exportPdf,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat(): ChatContextValue {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat() harus dipakai di dalam <ChatProvider>");
  return ctx;
}

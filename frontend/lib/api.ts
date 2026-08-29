import type { SessionItem } from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function handleJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // respons bukan JSON, pakai detail default
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function apiCreateSession(jenjang: string): Promise<{ session_id: string }> {
  const res = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jenjang }),
  });
  return handleJson(res);
}

export async function apiListSessions(): Promise<SessionItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/sessions`, { cache: "no-store" });
  return handleJson(res);
}

export async function apiGetMessages(
  sessionId: string
): Promise<{ role: string; content: string }[]> {
  const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/messages`, {
    cache: "no-store",
  });
  return handleJson(res);
}

export async function apiRenameSession(sessionId: string, title: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return handleJson(res);
}

export async function apiDeleteSession(sessionId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
    method: "DELETE",
  });
  return handleJson(res);
}

export async function apiGetGuardrailStatus(sessionId: string): Promise<{ blocked_count: number }> {
  const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/guardrail`, {
    cache: "no-store",
  });
  return handleJson(res);
}

export async function apiChat(
  sessionId: string,
  jenjang: string,
  message: string,
  mode: "chat" | "quiz" = "chat"
): Promise<{ reply: string; model: string | null; blocked: boolean }> {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, jenjang, message, mode }),
  });
  return handleJson(res);
}

export async function apiExportPdf(sessionId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}/api/export-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.blob();
}

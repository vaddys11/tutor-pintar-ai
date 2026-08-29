import { Avatar } from "./Avatar";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  model?: string | null;
}

export function MessageBubble({ role, content, model }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex items-end gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar role={role} />
      <div className={`flex max-w-[78%] flex-col ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`whitespace-pre-wrap break-words px-4 py-3 leading-relaxed shadow-sm ${
            isUser
              ? "rounded-2xl rounded-br-md bg-gradient-to-br from-indigo-500 to-purple-500 text-white shadow-indigo-500/20"
              : "rounded-2xl rounded-bl-md border border-slate-200 bg-white text-slate-800"
          }`}
        >
          {content}
        </div>
        {!isUser && model && (
          <span className="mt-1 px-1 text-xs text-slate-400">🤖 {model}</span>
        )}
      </div>
    </div>
  );
}

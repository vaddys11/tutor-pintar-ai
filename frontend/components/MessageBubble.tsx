import { Avatar } from "./Avatar";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  model?: string | null;
}

// Fungsi sederhana untuk merender teks markdown mentah jadi HTML rapi
function renderSimpleMarkdown(text: string) {
  return text.split("\n").map((line, index) => {
    // 1. Render Garis Pemisah (---)
    if (line.trim() === "---") {
      return <hr key={index} className="my-3 border-slate-200" />;
    }

    // 2. Parse Format Teks (Bold & Italic)
    // Mengubah **teks** jadi <strong> dan *teks* jadi <em>
    const parts = line.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    const parsedLine = parts.map((part, pIdx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={pIdx} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("*") && part.endsWith("*")) {
        return (
          <em key={pIdx} className="italic">
            {part.slice(1, -1)}
          </em>
        );
      }
      return part;
    });

    return (
      <p key={index} className="min-h-[1.5em] mb-1 last:mb-0">
        {parsedLine}
      </p>
    );
  });
}

export function MessageBubble({ role, content, model }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={`flex items-end gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}
    >
      <Avatar role={role} />
      <div
        className={`flex max-w-[88%] min-w-0 flex-col sm:max-w-[78%] ${isUser ? "items-end" : "items-start"}`}
      >
        <div
          className={`break-words px-4 py-3 leading-relaxed shadow-sm ${
            isUser
              ? "whitespace-pre-wrap rounded-2xl rounded-br-md bg-gradient-to-br from-indigo-500 to-purple-500 text-white shadow-indigo-500/20"
              : "rounded-2xl rounded-bl-md border border-slate-200 bg-white text-slate-800"
          }`}
        >
          {isUser ? content : renderSimpleMarkdown(content)}
        </div>
        {!isUser && model && (
          <span className="mt-1 px-1 text-xs text-slate-400">🤖 {model}</span>
        )}
      </div>
    </div>
  );
}

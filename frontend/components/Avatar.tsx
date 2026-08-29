import { Bot, GraduationCap } from "lucide-react";

export function Avatar({ role }: { role: "user" | "assistant" }) {
  const isBot = role === "assistant";
  return (
    <div
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full shadow-sm ${
        isBot
          ? "bg-gradient-to-br from-indigo-400 to-indigo-700 text-white"
          : "bg-gradient-to-br from-amber-400 to-amber-600 text-white"
      }`}
    >
      {isBot ? <Bot size={18} /> : <GraduationCap size={18} />}
    </div>
  );
}

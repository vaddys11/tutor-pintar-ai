import { Sidebar } from "@/components/Sidebar";
import { ChatWindow } from "@/components/ChatWindow";

export default function Home() {
  return (
    <main className="flex h-screen w-full overflow-hidden">
      <Sidebar />
      <ChatWindow />
    </main>
  );
}

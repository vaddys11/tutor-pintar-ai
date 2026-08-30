"use client";

import { useState } from "react";
import { Sidebar } from "./Sidebar";
import { ChatWindow } from "./ChatWindow";
import { ModuleManagerModal } from "./ModuleManagerModal";

export function AppShell() {
  const [moduleManagerOpen, setModuleManagerOpen] = useState(false);

  return (
    <main className="flex h-screen w-full overflow-hidden">
      <Sidebar onOpenModuleManager={() => setModuleManagerOpen(true)} />
      <ChatWindow />
      <ModuleManagerModal open={moduleManagerOpen} onClose={() => setModuleManagerOpen(false)} />
    </main>
  );
}

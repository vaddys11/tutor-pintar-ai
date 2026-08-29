import type { Metadata } from "next";
import "./globals.css";
import { ChatProvider } from "@/context/ChatContext";

export const metadata: Metadata = {
  title: "Tutor Pintar AI",
  description: "Pendamping belajar interaktif dengan metode Socratic",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="id" className="h-full antialiased">
      <body className="min-h-full font-sans">
        <ChatProvider>{children}</ChatProvider>
      </body>
    </html>
  );
}

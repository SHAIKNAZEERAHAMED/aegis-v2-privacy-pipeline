import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Aegis — AI-Resistant Video Privacy",
  description: "Capture, cloak, protect. Video that stays legible to people, not to recognition models.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body min-h-screen antialiased">{children}</body>
    </html>
  );
}

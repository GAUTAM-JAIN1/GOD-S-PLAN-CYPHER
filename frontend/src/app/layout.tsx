import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Voxera — Deterministic Voice AI Workbench & Human Co-Pilot",
  description: "Industrial-grade No-Code Multi-Domain Voice AI Agent Builder, Acoustic-Pydantic Guardrail Runtime, and Mobile-Connected Human Whisper Co-Pilot.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="h-screen w-screen overflow-hidden bg-[#F7F8FA] text-[#151619] font-sans antialiased">
        {children}
      </body>
    </html>
  );
}

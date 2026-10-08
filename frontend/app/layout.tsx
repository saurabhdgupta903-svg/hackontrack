import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sach? — Is this forward true?",
  description: "Multilingual fact-checking web application for WhatsApp forwards, screenshots, voice notes, PDFs, and links against official government archives.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
      </head>
      <body className="min-h-screen bg-[#FAFAF7] text-[#1A1A1A] antialiased selection:bg-neutral-200">
        {children}
      </body>
    </html>
  );
}

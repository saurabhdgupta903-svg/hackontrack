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
      <body className="min-h-screen bg-wa-bg text-wa-text antialiased selection:bg-[#c5ecbd]">
        {children}
      </body>
    </html>
  );
}

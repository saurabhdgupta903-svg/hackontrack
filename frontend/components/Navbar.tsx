"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Globe, MessageSquare } from "lucide-react";
import { SUPPORTED_LANGUAGES, LanguageCode, UI_STRINGS } from "@/lib/i18n";
import { fetchChannelStatus, ChannelStatus } from "@/lib/api";

interface NavbarProps {
  currentLang: LanguageCode;
  onLanguageChange: (lang: LanguageCode) => void;
}

export default function Navbar({ currentLang, onLanguageChange }: NavbarProps) {
  const pathname = usePathname();
  const [channelStatus, setChannelStatus] = useState<ChannelStatus | null>(null);
  const strings = UI_STRINGS[currentLang] || UI_STRINGS.en;

  useEffect(() => {
    fetchChannelStatus().then(setChannelStatus).catch(() => {});
  }, []);

  const navLinks = [
    { href: "/", label: strings.navCheck },
    { href: "/how-it-works", label: strings.navHowItWorks },
    { href: "/history", label: strings.navHistory },
    { href: "/about", label: strings.navAbout },
  ];

  return (
    <header className="border-b border-neutral-200 bg-[#FAFAF7] sticky top-0 z-40">
      <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Brand & Tagline */}
        <div className="flex items-baseline gap-3">
          <Link href="/" className="group flex items-baseline gap-2">
            <span className="font-serif text-2xl font-semibold tracking-tight text-[#1A1A1A]">
              Sach?
            </span>
            <span className="text-xs uppercase tracking-wider text-neutral-500 font-mono hidden sm:inline">
              सच?
            </span>
          </Link>
          <span className="text-sm text-neutral-500 hidden md:inline">
            / Is this forward true?
          </span>
        </div>

        {/* Center / Right Nav */}
        <div className="flex items-center gap-3 sm:gap-6">
          <nav className="flex items-center gap-1 sm:gap-2 text-sm">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-2.5 py-1.5 rounded-md transition-colors ${
                    isActive
                      ? "text-[#1A1A1A] font-medium bg-neutral-200/60"
                      : "text-neutral-600 hover:text-[#1A1A1A] hover:bg-neutral-100"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* WhatsApp Channel Indicator */}
          <div className="hidden lg:flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md border border-neutral-200 bg-white" title={channelStatus?.status_message}>
            <MessageSquare className="w-3.5 h-3.5 text-emerald-700" />
            <span className="text-neutral-600">WhatsApp:</span>
            <span className={`font-medium ${channelStatus?.is_live ? "text-emerald-700" : "text-neutral-700"}`}>
              {channelStatus?.is_live ? "Live" : "Webhook Ready"}
            </span>
          </div>

          {/* Language Switcher */}
          <div className="flex items-center gap-1 text-sm bg-white border border-neutral-200 rounded-md px-2 py-1">
            <Globe className="w-4 h-4 text-neutral-500 flex-shrink-0" />
            <select
              value={currentLang}
              onChange={(e) => onLanguageChange(e.target.value as LanguageCode)}
              aria-label="Select Interface Language"
              className="bg-transparent text-xs sm:text-sm text-[#1A1A1A] focus:outline-none cursor-pointer pr-1"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.native}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </header>
  );
}

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
    <header className="border-b border-[#d1d7db] bg-wa-bar sticky top-0 z-40">
      <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Brand & Tagline */}
        <div className="flex items-baseline gap-3">
          <Link href="/" className="group flex items-baseline gap-2">
            <span className="font-serif text-2xl font-semibold tracking-tight text-wa-text">
              Sach?
            </span>
            <span className="text-xs uppercase tracking-wider text-wa-text-muted font-mono hidden sm:inline">
              सच?
            </span>
          </Link>
          <span className="text-sm text-wa-text-muted hidden md:inline">
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
                  className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-full transition-colors whitespace-nowrap text-xs sm:text-sm ${
                    isActive
                      ? "text-wa-text font-medium bg-[#e9edef]"
                      : "text-wa-text-muted hover:text-wa-text hover:bg-black/5"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* WhatsApp Channel Indicator */}
          <div className="hidden lg:flex items-center gap-1.5 text-xs px-3 py-1 rounded-full border border-[#d1d7db] bg-white" title={channelStatus?.status_message}>
            <MessageSquare className="w-3.5 h-3.5 text-wa-accent" />
            <span className="text-wa-text-muted">WhatsApp:</span>
            <span className={`font-medium ${channelStatus?.is_live ? "text-wa-accent" : "text-wa-text"}`}>
              {channelStatus?.is_live ? "Live" : "Webhook Ready"}
            </span>
          </div>

          {/* Language Switcher */}
          <div className="flex items-center gap-1 text-sm bg-white border border-[#d1d7db] rounded-full px-3 py-1">
            <Globe className="w-4 h-4 text-wa-text-muted flex-shrink-0" />
            <select
              value={currentLang}
              onChange={(e) => onLanguageChange(e.target.value as LanguageCode)}
              aria-label="Select Interface Language"
              className="bg-transparent text-xs sm:text-sm text-wa-text focus:outline-none cursor-pointer pr-1"
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

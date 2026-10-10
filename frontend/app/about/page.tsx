"use client";

import React, { useState } from "react";
import Navbar from "@/components/Navbar";
import { LanguageCode } from "@/lib/i18n";
import {
  Layers,
  Cpu,
  Search,
  Server,
  AlertTriangle,
  HeartHandshake,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";

export default function AboutPage() {
  const [currentLang, setCurrentLang] = useState<LanguageCode>("en");

  return (
    <div className="min-h-screen flex flex-col bg-wa-bg">
      <Navbar currentLang={currentLang} onLanguageChange={setCurrentLang} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-6 sm:py-10">
        <div className="mb-8">
          <span className="text-xs uppercase font-mono tracking-wider text-wa-text-muted">
            Documentation & System Architecture
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-wa-text mt-1">
            About Sach? Fact-Checking System
          </h1>
          <p className="mt-2 text-sm sm:text-base text-wa-text-muted leading-relaxed">
            An open, evidence-grounded fact verification platform built for the Indian
            information ecosystem. Here is an honest breakdown of what is built, how it
            operates, and where its boundaries lie.
          </p>
        </div>

        <div className="space-y-6">
          {/* Section 1: Technology Stack */}
          <section className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent">
            <h2 className="text-lg font-serif font-semibold text-wa-text flex items-center gap-2 mb-3">
              <Layers className="w-5 h-5 text-wa-accent" />
              <span>Technology Stack</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="border border-[#b5deb0] p-2.5 rounded-xl bg-wa-bubble-dark/40">
                <strong className="text-wa-text block mb-1">Frontend</strong>
                <p className="text-neutral-700 text-xs leading-relaxed">
                  Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide icons.
                  Designed for WCAG AA compliance, 360px mobile viewports, and zero-flicker Server-Sent Events.
                </p>
              </div>
              <div className="border border-[#b5deb0] p-2.5 rounded-xl bg-wa-bubble-dark/40">
                <strong className="text-wa-text block mb-1">Backend</strong>
                <p className="text-neutral-700 text-xs leading-relaxed">
                  FastAPI (Python async), Uvicorn, Pydantic v2 schemas, SQLAlchemy with aiosqlite / asyncpg.
                  Streaming SSE endpoints for live progress bars.
                </p>
              </div>
              <div className="border border-[#b5deb0] p-2.5 rounded-xl bg-wa-bubble-dark/40">
                <strong className="text-wa-text block mb-1">Text & Document Extraction</strong>
                <p className="text-neutral-700 text-xs leading-relaxed">
                  PyMuPDF for fast digital PDF text extraction; Trafilatura for ad-free article parsing;
                  Gemini Multimodal OCR for scanned circulars and screenshots.
                </p>
              </div>
              <div className="border border-[#b5deb0] p-2.5 rounded-xl bg-wa-bubble-dark/40">
                <strong className="text-wa-text block mb-1">Storage & Privacy</strong>
                <p className="text-neutral-700 text-xs leading-relaxed">
                  SQLite/Postgres cache (24-hour TTL on search results to protect API quotas),
                  automatic regex redaction of Indian phone numbers and personal emails.
                </p>
              </div>
            </div>
          </section>

          {/* Section 2: AI/ML Models & Algorithms */}
          <section className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent">
            <h2 className="text-lg font-serif font-semibold text-wa-text flex items-center gap-2 mb-3">
              <Cpu className="w-5 h-5 text-wa-accent" />
              <span>AI/ML Models and Algorithms</span>
            </h2>
            <ul className="space-y-3 text-sm text-neutral-700">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-wa-accent flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-wa-text">Google Gemini Multimodal (Flash & Pro): </strong>
                  Powers image screenshot OCR, atomic claim extraction with original sentence spans,
                  structured JSON judging, and fallback multilingual voice transcription.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-wa-accent flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-wa-text">Sarvam AI Suite (Saarika, Mayura, Bulbul): </strong>
                  Specialized models for Indian languages: Saarika for Hindi/regional Speech-to-Text,
                  Mayura for Indic translation, and Bulbul for natural audio readout.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-wa-accent flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-wa-text">Retrieval-Augmented Verification (RAG): </strong>
                  The LLM is strictly prohibited from guessing or using internal hallucinations.
                  Every judgment must cite a passage from the retrieved allowlisted set.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-wa-accent flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-wa-text">Citation Verification Algorithm: </strong>
                  Post-LLM validation stage that cross-checks cited URLs against the retrieved allowlist
                  and validates that quoted passages exist verbatim in the scraped text.
                </div>
              </li>
            </ul>
          </section>

          {/* Section 3: Architecture Diagram */}
          <section className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent">
            <h2 className="text-lg font-serif font-semibold text-wa-text flex items-center gap-2 mb-3">
              <Server className="w-5 h-5 text-wa-accent" />
              <span>System Architecture</span>
            </h2>
            <div className="bg-wa-bubble-dark text-wa-text p-3 sm:p-4 rounded-xl font-mono text-[13px] border border-[#b5deb0] overflow-x-auto leading-relaxed">
              {`[User Input: Text / Image / Voice / PDF / URL / WhatsApp Webhook]
                          │
                          ▼
            [1. INGESTION SUBSYSTEM]
      ├─ PyMuPDF (Digital PDFs)
      ├─ Gemini Multimodal OCR (Images & Scanned PDFs)
      ├─ Sarvam Saarika / Gemini Audio (Voice Notes)
      └─ Trafilatura (Article Scraping)
                          │
                          ▼
            [2. CLAIM EXTRACTION]
      ├─ Drops greetings, emotional appeals & forward chain noise
      ├─ Produces atomic checkable claims + original message spans
                          │
                          ▼
            [3. STRICT ALLOWLIST RETRIEVAL]
      ├─ Google Fact Check Tools API (claims:search)
      ├─ Allowlist Web Search (pib.gov.in, rbi.org.in, IFCN fact-checkers)
      ├─ Trafilatura page cleaner + 24-Hour SQL cache
      └─ Hard Rule: If 0 allowlist sources found -> 'Cannot be confirmed'
                          │
                          ▼
            [4. STRUCTURED JUDGE (Gemini JSON Schema)]
      ├─ Evidence-grounded evaluation only
      └─ Returns 1 of 5 verdicts: Verified, False, Outdated, Partly supported, Cannot be confirmed
                          │
                          ▼
            [5. CITATION VERIFICATION & REASONING]
      ├─ Verifies cited URLs exist in retrieved set
      └─ Substring match validation on quoted evidence passages
                          │
                          ▼
            [6. PLAIN-LANGUAGE EXPLANATION & TTS]
      ├─ 6th-grade reading level in native Indic language (HI, MR, TA, BN, TE, GU, EN)
      ├─ Sarvam Bulbul / Web Speech API audio readout
                          │
                          ▼
      [Next.js Reactive UI / WhatsApp Direct Reply]`}
            </div>
          </section>

          {/* Section 4: Dataset and Source Allowlist */}
          <section className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent">
            <h2 className="text-lg font-serif font-semibold text-wa-text flex items-center gap-2 mb-3">
              <Search className="w-5 h-5 text-wa-accent" />
              <span>Data Sources and Strict Allowlist</span>
            </h2>
            <p className="text-sm text-wa-text/80 mb-4 leading-relaxed">
              Sach? requires no fine-tuning or proprietary training dataset because it is purely
              retrieval-grounded. To eliminate bias and fake news amplification, search is restricted
              to our strict domain allowlist configured in <code className="bg-wa-bubble-dark px-1.5 py-0.5 rounded text-wa-text text-xs border border-[#b5deb0]">backend/config.py</code>:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div className="border border-[#b5deb0] p-3 rounded-xl bg-wa-bubble-dark/40">
                <strong className="text-wa-text block mb-1">Government & Statutory</strong>
                <ul className="text-wa-text/80 space-y-0.5">
                  <li>pib.gov.in</li>
                  <li>rbi.org.in</li>
                  <li>mohfw.gov.in</li>
                  <li>eci.gov.in</li>
                  <li>imd.gov.in</li>
                  <li>india.gov.in</li>
                </ul>
              </div>
              <div className="border border-[#b5deb0] p-3 rounded-xl bg-wa-bubble-dark/40">
                <strong className="text-wa-text block mb-1">Certified Fact-Checkers</strong>
                <ul className="text-wa-text/80 space-y-0.5">
                  <li>altnews.in</li>
                  <li>boomlive.in</li>
                  <li>factly.in</li>
                  <li>vishvasnews.com</li>
                  <li>newschecker.in</li>
                  <li>thip.media</li>
                </ul>
              </div>
              <div className="border border-[#b5deb0] p-3 rounded-xl bg-wa-bubble-dark/40">
                <strong className="text-wa-text block mb-1">Wire & Public Media</strong>
                <ul className="text-wa-text/80 space-y-0.5">
                  <li>ptinews.com</li>
                  <li>aninews.in</li>
                  <li>newsonair.gov.in</li>
                  <li>sansad.in</li>
                  <li>who.int</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Section 5: Current Implementation Status & Scale */}
          <section className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent">
            <h2 className="text-lg font-serif font-semibold text-wa-text flex items-center gap-2 mb-3">
              <Server className="w-5 h-5 text-wa-accent" />
              <span>Current Status & Scaling Roadmap</span>
            </h2>
            <div className="space-y-3 text-sm text-wa-text/80 leading-relaxed">
              <p>
                <strong className="text-wa-text">Working in this prototype: </strong>
                Full multimodal ingestion (Text, Screenshot OCR, Voice notes, PDF parsing, URL extraction),
                atomic claim extraction, live allowlist retrieval with 24h SQLite/Postgres caching,
                strict JSON schema judging with Gemini, citation verification, and multilingual 6th-grade
                Indic explanations with audio readouts.
              </p>
              <p>
                <strong className="text-wa-text">Production Scaling Roadmap:</strong>
              </p>
              <ul className="list-disc pl-5 space-y-1 text-xs">
                <li>Asynchronous task queuing via Celery / Redis for high-throughput batching.</li>
                <li>WhatsApp Business Cloud API webhook auto-responder for direct chat forwarding.</li>
                <li>Vector caching of frequently forwarded claims (e.g. viral election hoaxes) to deliver sub-second responses.</li>
                <li>Escalation loop for borderline verdicts to human editorial desks and certified IFCN fact-checkers.</li>
              </ul>
            </div>
          </section>

          {/* Section 6: Limitations & Accountability */}
          <section className="bg-[#fffbeb] border border-amber-200/80 rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)]">
            <h2 className="text-lg font-serif font-semibold text-amber-950 flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-amber-700" />
              <span>Limitations and Known Boundaries</span>
            </h2>
            <div className="text-sm text-amber-950/80 space-y-2 leading-relaxed">
              <p>
                Sach? is a verification assistant, not an absolute arbiter of reality. It can only evaluate
                claims against information currently published on indexed allowlisted websites.
              </p>
              <p>
                If a developing event has not yet been addressed by official press releases, government gazettes,
                or certified fact-checking desks, the system explicitly returns <strong>Cannot be confirmed</strong>.
                It will never fabricate a conclusion.
              </p>
              <p className="text-xs text-amber-900/60 pt-2 border-t border-amber-200/60">
                Found an inaccurate evaluation? Every claim card includes a &ldquo;Report a wrong verdict&rdquo; button
                to submit corrections with source citations.
              </p>
            </div>
          </section>

          {/* Section 7: UN SDG Mapping */}
          <section className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent">
            <h2 className="text-lg font-serif font-semibold text-wa-text flex items-center gap-2 mb-4">
              <HeartHandshake className="w-5 h-5 text-wa-accent" />
              <span>United Nations Sustainable Development Goals (SDG) Mapping</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="border border-[#b5deb0] p-3 rounded-xl bg-wa-bubble-dark/40">
                <span className="font-mono text-xs text-wa-accent bg-white/80 border border-[#b5deb0] px-2 py-0.5 rounded-full font-medium inline-block">
                  SDG 4: Quality Education
                </span>
                <h3 className="font-serif font-semibold text-wa-text mt-2 mb-1">
                  Digital Media Literacy
                </h3>
                <p className="text-xs text-wa-text/80 leading-relaxed">
                  Educates citizens in regional languages on how to recognize disinformation, inspect official citations, and understand public notices.
                </p>
              </div>

              <div className="border border-[#b5deb0] p-3 rounded-xl bg-wa-bubble-dark/40">
                <span className="font-mono text-xs text-wa-accent bg-white/80 border border-[#b5deb0] px-2 py-0.5 rounded-full font-medium inline-block">
                  SDG 9: Industry & Innovation
                </span>
                <h3 className="font-serif font-semibold text-wa-text mt-2 mb-1">
                  Responsible GenAI Tech
                </h3>
                <p className="text-xs text-wa-text/80 leading-relaxed">
                  Demonstrates hallucination-resilient generative AI architectures using citation verification and strict domain-bound RAG.
                </p>
              </div>

              <div className="border border-[#b5deb0] p-3 rounded-xl bg-wa-bubble-dark/40">
                <span className="font-mono text-xs text-wa-accent bg-white/80 border border-[#b5deb0] px-2 py-0.5 rounded-full font-medium inline-block">
                  SDG 16: Peace & Strong Institutions
                </span>
                <h3 className="font-serif font-semibold text-wa-text mt-2 mb-1">
                  Democratic Trust & Stability
                </h3>
                <p className="text-xs text-wa-text/80 leading-relaxed">
                  Curbs viral communal incitement, medical panics, and financial hoaxes that destabilize democratic discourse and public health.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

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
    <div className="min-h-screen flex flex-col bg-[#FAFAF7]">
      <Navbar currentLang={currentLang} onLanguageChange={setCurrentLang} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-10 sm:py-16">
        <div className="mb-10">
          <span className="text-xs uppercase font-mono tracking-wider text-neutral-500">
            Documentation & System Architecture
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[#1A1A1A] mt-1">
            About Sach? Fact-Checking System
          </h1>
          <p className="mt-2 text-sm sm:text-base text-neutral-600 leading-relaxed">
            An open, evidence-grounded fact verification platform built for the Indian
            information ecosystem. Here is an honest breakdown of what is built, how it
            operates, and where its boundaries lie.
          </p>
        </div>

        <div className="space-y-12">
          {/* Section 1: Technology Stack */}
          <section className="bg-white border border-neutral-200 rounded-md p-6">
            <h2 className="text-lg font-serif font-semibold text-[#1A1A1A] flex items-center gap-2 mb-4">
              <Layers className="w-5 h-5 text-[#1B4D3E]" />
              <span>Technology Stack</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="border border-neutral-100 p-3 rounded bg-[#FAFAF7]">
                <strong className="text-neutral-800 block mb-1">Frontend</strong>
                <p className="text-neutral-600 text-xs leading-relaxed">
                  Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide icons.
                  Designed for WCAG AA compliance, 360px mobile viewports, and zero-flicker Server-Sent Events.
                </p>
              </div>
              <div className="border border-neutral-100 p-3 rounded bg-[#FAFAF7]">
                <strong className="text-neutral-800 block mb-1">Backend</strong>
                <p className="text-neutral-600 text-xs leading-relaxed">
                  FastAPI (Python async), Uvicorn, Pydantic v2 schemas, SQLAlchemy with aiosqlite / asyncpg.
                  Streaming SSE endpoints for live progress bars.
                </p>
              </div>
              <div className="border border-neutral-100 p-3 rounded bg-[#FAFAF7]">
                <strong className="text-neutral-800 block mb-1">Text & Document Extraction</strong>
                <p className="text-neutral-600 text-xs leading-relaxed">
                  PyMuPDF for fast digital PDF text extraction; Trafilatura for ad-free article parsing;
                  Gemini Multimodal OCR for scanned circulars and screenshots.
                </p>
              </div>
              <div className="border border-neutral-100 p-3 rounded bg-[#FAFAF7]">
                <strong className="text-neutral-800 block mb-1">Storage & Privacy</strong>
                <p className="text-neutral-600 text-xs leading-relaxed">
                  SQLite/Postgres cache (24-hour TTL on search results to protect API quotas),
                  automatic regex redaction of Indian phone numbers and personal emails.
                </p>
              </div>
            </div>
          </section>

          {/* Section 2: AI/ML Models & Algorithms */}
          <section className="bg-white border border-neutral-200 rounded-md p-6">
            <h2 className="text-lg font-serif font-semibold text-[#1A1A1A] flex items-center gap-2 mb-4">
              <Cpu className="w-5 h-5 text-[#1B4D3E]" />
              <span>AI/ML Models and Algorithms</span>
            </h2>
            <ul className="space-y-3 text-sm text-neutral-600">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-neutral-800">Google Gemini Multimodal (Flash & Pro): </strong>
                  Powers image screenshot OCR, atomic claim extraction with original sentence spans,
                  structured JSON judging, and fallback multilingual voice transcription.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-neutral-800">Sarvam AI Suite (Saarika, Mayura, Bulbul): </strong>
                  Specialized models for Indian languages: Saarika for Hindi/regional Speech-to-Text,
                  Mayura for Indic translation, and Bulbul for natural audio readout.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-neutral-800">Retrieval-Augmented Verification (RAG): </strong>
                  The LLM is strictly prohibited from guessing or using internal hallucinations.
                  Every judgment must cite a passage from the retrieved allowlisted set.
                </div>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-neutral-800">Citation Verification Algorithm: </strong>
                  Post-LLM validation stage that cross-checks cited URLs against the retrieved allowlist
                  and validates that quoted passages exist verbatim in the scraped text.
                </div>
              </li>
            </ul>
          </section>

          {/* Section 3: Architecture Diagram */}
          <section className="bg-white border border-neutral-200 rounded-md p-6">
            <h2 className="text-lg font-serif font-semibold text-[#1A1A1A] flex items-center gap-2 mb-4">
              <Server className="w-5 h-5 text-[#1B4D3E]" />
              <span>System Architecture</span>
            </h2>
            <div className="bg-[#1A1A1A] text-neutral-200 p-4 sm:p-6 rounded font-mono text-xs overflow-x-auto leading-relaxed">
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
          <section className="bg-white border border-neutral-200 rounded-md p-6">
            <h2 className="text-lg font-serif font-semibold text-[#1A1A1A] flex items-center gap-2 mb-3">
              <Search className="w-5 h-5 text-[#1B4D3E]" />
              <span>Data Sources and Strict Allowlist</span>
            </h2>
            <p className="text-sm text-neutral-600 mb-4 leading-relaxed">
              Sach? requires no fine-tuning or proprietary training dataset because it is purely
              retrieval-grounded. To eliminate bias and fake news amplification, search is restricted
              to our strict domain allowlist configured in <code className="bg-neutral-100 px-1 py-0.5 rounded text-neutral-800">backend/config.py</code>:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div className="border border-neutral-200 p-2.5 rounded bg-[#FAFAF7]">
                <strong className="text-neutral-800 block mb-1">Government & Statutory</strong>
                <ul className="text-neutral-600 space-y-0.5">
                  <li>pib.gov.in</li>
                  <li>rbi.org.in</li>
                  <li>mohfw.gov.in</li>
                  <li>eci.gov.in</li>
                  <li>imd.gov.in</li>
                  <li>india.gov.in</li>
                </ul>
              </div>
              <div className="border border-neutral-200 p-2.5 rounded bg-[#FAFAF7]">
                <strong className="text-neutral-800 block mb-1">Certified Fact-Checkers</strong>
                <ul className="text-neutral-600 space-y-0.5">
                  <li>altnews.in</li>
                  <li>boomlive.in</li>
                  <li>factly.in</li>
                  <li>vishvasnews.com</li>
                  <li>newschecker.in</li>
                  <li>thip.media</li>
                </ul>
              </div>
              <div className="border border-neutral-200 p-2.5 rounded bg-[#FAFAF7]">
                <strong className="text-neutral-800 block mb-1">Wire & Public Media</strong>
                <ul className="text-neutral-600 space-y-0.5">
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
          <section className="bg-white border border-neutral-200 rounded-md p-6">
            <h2 className="text-lg font-serif font-semibold text-[#1A1A1A] flex items-center gap-2 mb-3">
              <Server className="w-5 h-5 text-[#1B4D3E]" />
              <span>Current Status & Scaling Roadmap</span>
            </h2>
            <div className="space-y-3 text-sm text-neutral-600 leading-relaxed">
              <p>
                <strong className="text-neutral-800">Working in this prototype: </strong>
                Full multimodal ingestion (Text, Screenshot OCR, Voice notes, PDF parsing, URL extraction),
                atomic claim extraction, live allowlist retrieval with 24h SQLite/Postgres caching,
                strict JSON schema judging with Gemini, citation verification, and multilingual 6th-grade
                Indic explanations with audio readouts.
              </p>
              <p>
                <strong className="text-neutral-800">Production Scaling Roadmap:</strong>
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
          <section className="bg-rose-50/50 border border-rose-200 rounded-md p-6">
            <h2 className="text-lg font-serif font-semibold text-rose-950 flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-rose-800" />
              <span>Limitations and Known Boundaries</span>
            </h2>
            <div className="text-sm text-neutral-700 space-y-2 leading-relaxed">
              <p>
                Sach? is a verification assistant, not an absolute arbiter of reality. It can only evaluate
                claims against information currently published on indexed allowlisted websites.
              </p>
              <p>
                If a developing event has not yet been addressed by official press releases, government gazettes,
                or certified fact-checking desks, the system explicitly returns <strong>Cannot be confirmed</strong>.
                It will never fabricate a conclusion.
              </p>
              <p className="text-xs text-neutral-500 pt-2 border-t border-rose-200/60">
                Found an inaccurate evaluation? Every claim card includes a &ldquo;Report a wrong verdict&rdquo; button
                to submit corrections with source citations.
              </p>
            </div>
          </section>

          {/* Section 7: UN SDG Mapping */}
          <section className="bg-white border border-neutral-200 rounded-md p-6">
            <h2 className="text-lg font-serif font-semibold text-[#1A1A1A] flex items-center gap-2 mb-4">
              <HeartHandshake className="w-5 h-5 text-[#1B4D3E]" />
              <span>United Nations Sustainable Development Goals (SDG) Mapping</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="border border-neutral-200 p-3 rounded">
                <span className="font-mono text-xs text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded font-medium">
                  SDG 4: Quality Education
                </span>
                <h3 className="font-serif font-semibold text-[#1A1A1A] mt-2 mb-1">
                  Digital Media Literacy
                </h3>
                <p className="text-xs text-neutral-600 leading-relaxed">
                  Educates citizens in regional languages on how to recognize disinformation, inspect official citations, and understand public notices.
                </p>
              </div>

              <div className="border border-neutral-200 p-3 rounded">
                <span className="font-mono text-xs text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded font-medium">
                  SDG 9: Industry & Innovation
                </span>
                <h3 className="font-serif font-semibold text-[#1A1A1A] mt-2 mb-1">
                  Responsible GenAI Tech
                </h3>
                <p className="text-xs text-neutral-600 leading-relaxed">
                  Demonstrates hallucination-resilient generative AI architectures using citation verification and strict domain-bound RAG.
                </p>
              </div>

              <div className="border border-neutral-200 p-3 rounded">
                <span className="font-mono text-xs text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded font-medium">
                  SDG 16: Peace & Strong Institutions
                </span>
                <h3 className="font-serif font-semibold text-[#1A1A1A] mt-2 mb-1">
                  Democratic Trust & Stability
                </h3>
                <p className="text-xs text-neutral-600 leading-relaxed">
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

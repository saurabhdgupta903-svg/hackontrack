"use client";

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import { LanguageCode } from "@/lib/i18n";
import { FileSearch, Scissors, Database, Scale, CheckCheck } from "lucide-react";

const PIPELINE_STEPS = [
  {
    step: 1,
    title: "Ingest and Multimodal Extraction",
    icon: FileSearch,
    tag: "OCR • Speech-to-Text • Trafilatura • PyMuPDF",
    description:
      "When a user drops an image, audio clip, PDF, web link, or forwarded message, the engine ingests the raw artifact. Digital PDFs are parsed via PyMuPDF; scanned circulars and screenshots undergo multimodal OCR via Gemini; voice notes are transcribed using Sarvam AI Saarika (falling back to Gemini); and web links are stripped of ads and navigation by trafilatura.",
  },
  {
    step: 2,
    title: "Claim Extraction and De-noising",
    icon: Scissors,
    tag: "Atomic Propositions • Noise Filtering",
    description:
      "Viral forwards are packed with emotional manipulation, greetings, blessings, and chain calls ('Share with 10 groups before midnight!'). The claim extractor strips all rhetorical noise and breaks the content down into atomic, testable propositions while preserving the exact original span from the message.",
  },
  {
    step: 3,
    title: "Strict Allowlist Retrieval",
    icon: Database,
    tag: "PIB • RBI • BOOM • Alt News • 24h Cache",
    description:
      "Every extracted claim is queried across Google Fact Check Tools API and targeted search restricted strictly to our domain allowlist (pib.gov.in, rbi.org.in, mohfw.gov.in, who.int, certified IFCN fact-checkers). Web pages are fetched in real-time, cleaned, and cached in a 24-hour database to protect API quotas. Hard rule: if no source clears the allowlist, the answer is 'Cannot be confirmed' — never a guess.",
  },
  {
    step: 4,
    title: "Evidence-Grounded Judging",
    icon: Scale,
    tag: "JSON Schema • No Extrapolation • Date Auditing",
    description:
      "The LLM evaluates the claim under strict system instructions: it is restricted exclusively to the retrieved evidence passages. It determines one of five exact verdicts (Verified, False, Outdated, Partly supported, Cannot be confirmed) and explicitly states what is right, what is wrong or missing, and dates of policy change.",
  },
  {
    step: 5,
    title: "Citation Verification & Indic Explanation",
    icon: CheckCheck,
    tag: "Hallucination Defense • 6th-Grade Indic Readout",
    description:
      "Before outputting, the system cross-verifies every cited URL against the actual retrieved list and confirms that quoted passages exist verbatim in the scraped text. It then synthesizes a plain 2-3 sentence explanation at a 6th-grade reading level in the user's native language (Hindi, Marathi, Tamil, Bengali, Telugu, Gujarati, or English) with an optional audio readout.",
  },
];

export default function HowItWorksPage() {
  const [currentLang, setCurrentLang] = useState<LanguageCode>("en");
  const [activeStep, setActiveStep] = useState(1);

  useEffect(() => {
    const handleScroll = () => {
      const stepElements = document.querySelectorAll(".pipeline-step-item");
      stepElements.forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        if (rect.top <= window.innerHeight * 0.45 && rect.bottom >= window.innerHeight * 0.2) {
          setActiveStep(index + 1);
        }
      });
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-wa-bg text-wa-text">
      <Navbar currentLang={currentLang} onLanguageChange={setCurrentLang} />

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-8 sm:py-12">
        <div className="mb-10">
          <span className="text-xs uppercase font-mono tracking-wider text-wa-text-muted">
            Pipeline Architecture
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-wa-text mt-1">
            How Sach? verifies a forward
          </h1>
          <p className="mt-2 text-sm sm:text-base text-wa-text/80 leading-relaxed">
            Every query runs through a 5-stage verification funnel. No AI guesses, no
            hallucinated URLs, and zero responses without traceable official citations.
          </p>
        </div>

        {/* Vertical Pipeline with scroll indicator */}
        <div className="relative pl-6 sm:pl-10 space-y-8 sm:space-y-10">
          {/* Vertical continuous line */}
          <div
            className="absolute left-[13px] sm:left-[21px] top-4 bottom-4 w-0.5 bg-[#b5deb0] transition-colors"
            aria-hidden="true"
          />

          {PIPELINE_STEPS.map((step) => {
            const Icon = step.icon;
            const isActive = activeStep >= step.step;
            const isCurrent = activeStep === step.step;

            return (
              <div
                key={step.step}
                className="pipeline-step-item relative group"
                id={`step-${step.step}`}
              >
                {/* Step Circle Node */}
                <div
                  className={`absolute -left-[30px] sm:-left-[42px] top-1 w-7 h-7 sm:w-9 sm:h-9 rounded-full border flex items-center justify-center font-mono text-xs sm:text-sm font-semibold transition-all duration-300 ${
                    isCurrent
                      ? "bg-wa-accent border-wa-accent text-white ring-4 ring-wa-accent/20"
                      : isActive
                      ? "bg-wa-accent border-wa-accent text-white"
                      : "bg-white border-[#d1d7db] text-wa-text-muted"
                  }`}
                >
                  {step.step}
                </div>

                {/* Step Content */}
                <div
                  className={`bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] transition-all duration-200 border ${
                    isCurrent
                      ? "border-wa-accent/40"
                      : "border-transparent"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-mono text-wa-accent bg-white/80 border border-[#b5deb0] px-2 py-0.5 rounded-full font-medium">
                      {step.tag}
                    </span>
                    <span className="text-xs text-wa-text-muted font-mono">
                      Phase 0{step.step}
                    </span>
                  </div>

                  <h2 className="text-lg font-serif font-semibold text-wa-text flex items-center gap-2">
                    <Icon className="w-5 h-5 text-wa-accent flex-shrink-0" />
                    <span>{step.title}</span>
                  </h2>

                  <p className="mt-3 text-sm text-wa-text/80 leading-relaxed font-sans">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Closing note */}
        <div className="mt-12 bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent text-xs text-wa-text/80">
          <p className="font-semibold text-wa-text mb-1">
            Accountability and Reproducibility:
          </p>
          <p className="leading-relaxed">
            All code in Sach? is modular and unit-tested against real viral claims. You can inspect
            the exact domain allowlist in <code className="bg-wa-bubble-dark px-1.5 py-0.5 rounded text-wa-text text-xs border border-[#b5deb0]">backend/config.py</code>.
          </p>
        </div>
      </main>
    </div>
  );
}

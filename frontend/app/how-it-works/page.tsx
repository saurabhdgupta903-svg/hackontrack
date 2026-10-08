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
    <div className="min-h-screen flex flex-col bg-[#FAFAF7]">
      <Navbar currentLang={currentLang} onLanguageChange={setCurrentLang} />

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-10 sm:py-16">
        <div className="mb-12">
          <span className="text-xs uppercase font-mono tracking-wider text-neutral-500">
            Pipeline Architecture
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[#1A1A1A] mt-1">
            How Sach? verifies a forward
          </h1>
          <p className="mt-2 text-sm sm:text-base text-neutral-600 leading-relaxed">
            Every query runs through a 5-stage verification funnel. No AI guesses, no
            hallucinated URLs, and zero responses without traceable official citations.
          </p>
        </div>

        {/* Vertical Pipeline with scroll indicator */}
        <div className="relative pl-6 sm:pl-10 space-y-12">
          {/* Vertical continuous line */}
          <div
            className="absolute left-[13px] sm:left-[21px] top-4 bottom-4 w-0.5 bg-neutral-200 transition-colors"
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
                  className={`absolute -left-[30px] sm:-left-[42px] top-1 w-7 h-7 sm:w-9 sm:h-9 rounded-full border flex items-center justify-center font-mono text-xs sm:text-sm transition-all duration-300 ${
                    isCurrent
                      ? "bg-[#1B4D3E] border-[#1B4D3E] text-white ring-4 ring-[#1B4D3E]/10"
                      : isActive
                      ? "bg-[#1B4D3E] border-[#1B4D3E] text-white"
                      : "bg-white border-neutral-300 text-neutral-500"
                  }`}
                >
                  {step.step}
                </div>

                {/* Step Content */}
                <div
                  className={`bg-white border rounded-md p-5 sm:p-6 transition-all duration-200 ${
                    isCurrent
                      ? "border-[#1B4D3E]/60 shadow-sm"
                      : "border-neutral-200"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                      {step.tag}
                    </span>
                    <span className="text-xs text-neutral-400 font-mono">
                      Phase 0{step.step}
                    </span>
                  </div>

                  <h2 className="text-lg font-serif font-semibold text-[#1A1A1A] flex items-center gap-2">
                    <Icon className="w-5 h-5 text-[#1B4D3E] flex-shrink-0" />
                    <span>{step.title}</span>
                  </h2>

                  <p className="mt-3 text-sm text-neutral-600 leading-relaxed font-sans">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Closing note */}
        <div className="mt-16 p-5 bg-white border border-neutral-200 rounded-md text-xs text-neutral-600">
          <p className="font-medium text-neutral-800 mb-1">
            Accountability and Reproducibility:
          </p>
          <p className="leading-relaxed">
            All code in Sach? is modular and unit-tested against real viral claims. You can inspect
            the exact domain allowlist in <code className="bg-neutral-100 px-1 py-0.5 rounded text-neutral-800">backend/config.py</code>.
          </p>
        </div>
      </main>
    </div>
  );
}

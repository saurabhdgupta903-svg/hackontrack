"use client";

import React, { useState } from "react";
import Navbar from "@/components/Navbar";
import CheckInput from "@/components/CheckInput";
import ProgressBar from "@/components/ProgressBar";
import ResultView from "@/components/ResultView";
import { LanguageCode, UI_STRINGS } from "@/lib/i18n";
import { FactCheckResponse } from "@/lib/api";

export default function HomePage() {
  const [currentLang, setCurrentLang] = useState<LanguageCode>("auto");
  const [isLoading, setIsLoading] = useState(false);
  const [progressState, setProgressState] = useState<{
    stage: string;
    message: string;
    percent: number;
  } | null>(null);
  const [resultData, setResultData] = useState<FactCheckResponse | null>(null);

  const [globalError, setGlobalError] = useState<string | null>(null);

  const strings = UI_STRINGS[currentLang] || UI_STRINGS.en;

  const handleStartCheck = () => {
    setIsLoading(true);
    setResultData(null);
    setGlobalError(null);
    setProgressState({
      stage: "initializing",
      message: "Receiving forward and validating input...",
      percent: 5,
    });
  };

  const handleProgress = (stage: string, message: string, percent: number) => {
    setProgressState({ stage, message, percent });
  };

  const handleComplete = (data: FactCheckResponse) => {
    setIsLoading(false);
    setProgressState(null);
    setGlobalError(null);
    setResultData(data);
  };

  const handleError = (errorMsg: string) => {
    setIsLoading(false);
    setProgressState(null);
    setGlobalError(errorMsg);
  };

  return (
    <div className="min-h-screen flex flex-col bg-wa-bg">
      <Navbar currentLang={currentLang} onLanguageChange={setCurrentLang} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-6 sm:py-10">
        {/* Headline & Description in one line / short paragraph */}
        <section className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-wa-text tracking-tight">
            {strings.tagline}
          </h1>
          <p className="mt-2 text-sm sm:text-base text-wa-text-muted max-w-2xl leading-relaxed">
            {strings.subtitle}
          </p>
        </section>

        {/* Input Card */}
        <CheckInput
          currentLang={currentLang}
          onStartCheck={handleStartCheck}
          onProgress={handleProgress}
          onComplete={handleComplete}
          onError={handleError}
          isLoading={isLoading}
        />

        {/* Global Error Banner */}
        {globalError && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-300 rounded-xl text-rose-800 text-sm flex items-start justify-between gap-3 shadow-xs" role="alert">
            <div className="flex items-start gap-2.5">
              <span className="font-semibold text-rose-900 mt-0.5">Error:</span>
              <p className="leading-relaxed">{globalError}</p>
            </div>
            <button
              type="button"
              onClick={() => setGlobalError(null)}
              className="text-rose-500 hover:text-rose-700 text-xs font-semibold px-2 py-1 rounded"
              aria-label="Dismiss error"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Real-time SSE Progress Status */}
        {isLoading && progressState && (
          <ProgressBar
            stage={progressState.stage}
            message={progressState.message}
            progress={progressState.percent}
          />
        )}

        {/* Results Section */}
        {resultData && <ResultView data={resultData} currentLang={currentLang} />}
      </main>

      <footer className="border-t border-[#d1d7db] py-4 text-center text-xs text-wa-text-muted bg-wa-bar">
        <div className="max-w-4xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>Sach? — GenAI Multimodal Fact-Checking System</span>
          <span>Verified exclusively via official government portals & IFCN fact-checkers</span>
        </div>
      </footer>
    </div>
  );
}

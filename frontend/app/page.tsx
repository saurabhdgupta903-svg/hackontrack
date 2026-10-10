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

  const strings = UI_STRINGS[currentLang] || UI_STRINGS.en;

  const handleStartCheck = () => {
    setIsLoading(true);
    setResultData(null);
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
    setResultData(data);
  };

  const handleError = (_errorMsg: string) => {
    setIsLoading(false);
    setProgressState(null);
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

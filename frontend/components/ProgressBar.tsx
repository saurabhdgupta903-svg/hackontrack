"use client";

import React from "react";
import { Loader2 } from "lucide-react";

interface ProgressBarProps {
  stage: string;
  message: string;
  progress: number;
}

export default function ProgressBar({ stage, message, progress }: ProgressBarProps) {
  return (
    <div
      className="w-full bg-white border border-neutral-200 rounded-md p-4 mb-6 shadow-sm"
      role="region"
      aria-live="polite"
      aria-label="Fact check progress"
    >
      <div className="flex items-center justify-between text-sm mb-2">
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-emerald-800" />
          <span className="font-medium text-[#1A1A1A]">{message}</span>
        </div>
        <span className="font-mono text-xs text-neutral-500">{progress}%</span>
      </div>

      {/* Progress Track */}
      <div className="w-full bg-neutral-100 rounded-full h-1.5 overflow-hidden">
        <div
          className="bg-emerald-800 h-1.5 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(100, Math.max(5, progress))}%` }}
        />
      </div>

      <div className="mt-2 text-xs text-neutral-500 flex justify-between font-mono">
        <span>Step: {stage}</span>
        <span>Strict Allowlist Verification</span>
      </div>
    </div>
  );
}

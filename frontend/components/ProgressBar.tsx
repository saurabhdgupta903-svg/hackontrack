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
      className="w-full bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 mb-6 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent"
      role="region"
      aria-live="polite"
      aria-label="Fact check progress"
    >
      <div className="flex items-center justify-between text-sm mb-2">
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-wa-accent" />
          <span className="font-medium text-wa-text">{message}</span>
        </div>
        <span className="font-mono text-xs text-wa-text-muted">{progress}%</span>
      </div>

      {/* Progress Track */}
      <div className="w-full bg-black/10 rounded-full h-1.5 overflow-hidden">
        <div
          className="bg-wa-accent h-1.5 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(100, Math.max(5, progress))}%` }}
        />
      </div>

      <div className="mt-2 text-xs text-wa-text-muted flex justify-between font-mono">
        <span>Step: {stage}</span>
        <span>Strict Allowlist Verification</span>
      </div>
    </div>
  );
}

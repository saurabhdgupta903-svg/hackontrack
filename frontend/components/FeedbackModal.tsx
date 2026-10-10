"use client";

import React, { useState } from "react";
import { X, Send, Check } from "lucide-react";
import { submitFeedback, VerdictType } from "@/lib/api";

interface FeedbackModalProps {
  checkId: string;
  claimId: string;
  currentVerdict: VerdictType;
  isOpen: boolean;
  onClose: () => void;
}

export default function FeedbackModal({
  checkId,
  claimId,
  currentVerdict,
  isOpen,
  onClose,
}: FeedbackModalProps) {
  const [expectedVerdict, setExpectedVerdict] = useState<VerdictType>("Verified");
  const [correctionUrl, setCorrectionUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      await submitFeedback({
        check_id: checkId,
        claim_id: claimId,
        reported_verdict: currentVerdict,
        expected_verdict: expectedVerdict,
        correction_url: correctionUrl.trim(),
        notes: notes.trim(),
      });
      setIsSubmitted(true);
      setTimeout(() => {
        setIsSubmitted(false);
        onClose();
      }, 1800);
    } catch (err: any) {
      setErrorMsg("Failed to record feedback. Please check backend connection.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-title"
    >
      <div className="bg-white rounded-2xl border border-[#d1d7db] max-w-lg w-full p-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-[#e9edef] pb-3 mb-4">
          <h2 id="feedback-title" className="font-serif text-lg font-semibold text-wa-text">
            Report a wrong verdict
          </h2>
          <button
            onClick={onClose}
            className="text-wa-text-muted hover:text-wa-text p-1.5 rounded-full hover:bg-neutral-100 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {isSubmitted ? (
          <div className="py-8 text-center text-wa-accent">
            <Check className="w-10 h-10 mx-auto mb-2 text-wa-accent" />
            <p className="font-medium text-base text-wa-text">Correction submitted!</p>
            <p className="text-xs text-wa-text-muted mt-1">
              Thank you for helping keep the system accurate and accountable.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-mono uppercase text-wa-text-muted mb-1">
                Current Verdict: <strong className="text-wa-text">{currentVerdict}</strong>
              </label>
              <label className="block text-xs text-wa-text font-medium mb-1">
                What should the correct verdict be?
              </label>
              <select
                value={expectedVerdict}
                onChange={(e) => setExpectedVerdict(e.target.value as VerdictType)}
                className="w-full p-2.5 border border-[#d1d7db] rounded-xl bg-white text-wa-text focus:outline-none focus:ring-2 focus:ring-wa-accent"
              >
                <option value="Verified">Verified (Official sources confirm it)</option>
                <option value="False">False (Contradicts facts)</option>
                <option value="Outdated">Outdated (Was true in past, changed now)</option>
                <option value="Partly supported">Partly supported (Partly accurate, partly misleading)</option>
                <option value="Cannot be confirmed">Cannot be confirmed (Insufficient official records)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-wa-text font-medium mb-1">
                Authoritative source link or gazette notification (optional)
              </label>
              <input
                type="url"
                value={correctionUrl}
                onChange={(e) => setCorrectionUrl(e.target.value)}
                placeholder="https://pib.gov.in/PressRelease..."
                className="w-full p-2.5 border border-[#d1d7db] rounded-xl bg-white text-wa-text placeholder:text-wa-text-muted focus:outline-none focus:ring-2 focus:ring-wa-accent"
              />
            </div>

            <div>
              <label className="block text-xs text-wa-text font-medium mb-1">
                Why is the current verdict wrong? (context / date changed)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Explain what was missed or how the regulation changed..."
                className="w-full p-2.5 border border-[#d1d7db] rounded-xl bg-white text-wa-text placeholder:text-wa-text-muted focus:outline-none focus:ring-2 focus:ring-wa-accent resize-y"
              />
            </div>

            {errorMsg && (
              <p className="text-xs text-rose-700 bg-rose-50 p-2.5 rounded-xl border border-rose-200">{errorMsg}</p>
            )}

            <div className="flex justify-end gap-2 pt-3 border-t border-[#e9edef]">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-wa-text-muted hover:text-wa-text rounded-full transition-colors font-medium text-xs sm:text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-wa-accent text-white rounded-full hover:bg-[#008f6f] flex items-center gap-1.5 font-medium text-xs sm:text-sm shadow-sm transition-all disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit Correction</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

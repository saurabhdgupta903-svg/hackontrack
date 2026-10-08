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
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-title"
    >
      <div className="bg-white rounded-md border border-neutral-200 max-w-lg w-full p-6 shadow-lg">
        <div className="flex items-center justify-between border-b border-neutral-100 pb-3 mb-4">
          <h2 id="feedback-title" className="font-serif text-lg font-semibold text-[#1A1A1A]">
            Report a wrong verdict
          </h2>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-neutral-700 p-1 rounded-md"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {isSubmitted ? (
          <div className="py-8 text-center text-emerald-800">
            <Check className="w-10 h-10 mx-auto mb-2 text-emerald-600" />
            <p className="font-medium text-base">Correction submitted!</p>
            <p className="text-xs text-neutral-500 mt-1">
              Thank you for helping keep the system accurate and accountable.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-mono uppercase text-neutral-500 mb-1">
                Current Verdict: <strong className="text-neutral-800">{currentVerdict}</strong>
              </label>
              <label className="block text-xs text-neutral-700 font-medium mb-1">
                What should the correct verdict be?
              </label>
              <select
                value={expectedVerdict}
                onChange={(e) => setExpectedVerdict(e.target.value as VerdictType)}
                className="w-full p-2 border border-neutral-300 rounded-md bg-white text-[#1A1A1A]"
              >
                <option value="Verified">Verified (Official sources confirm it)</option>
                <option value="False">False (Contradicts facts)</option>
                <option value="Outdated">Outdated (Was true in past, changed now)</option>
                <option value="Partly supported">Partly supported (Partly accurate, partly misleading)</option>
                <option value="Cannot be confirmed">Cannot be confirmed (Insufficient official records)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-neutral-700 font-medium mb-1">
                Authoritative source link or gazette notification (optional)
              </label>
              <input
                type="url"
                value={correctionUrl}
                onChange={(e) => setCorrectionUrl(e.target.value)}
                placeholder="https://pib.gov.in/PressRelease..."
                className="w-full p-2 border border-neutral-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-xs text-neutral-700 font-medium mb-1">
                Why is the current verdict wrong? (context / date changed)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Explain what was missed or how the regulation changed..."
                className="w-full p-2 border border-neutral-300 rounded-md resize-y"
              />
            </div>

            {errorMsg && (
              <p className="text-xs text-rose-700 bg-rose-50 p-2 rounded-md">{errorMsg}</p>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-neutral-100">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-2 text-neutral-600 hover:text-neutral-900 rounded-md"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-[#1B4D3E] text-white rounded-md hover:bg-[#143A2F] flex items-center gap-1.5 disabled:opacity-50"
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

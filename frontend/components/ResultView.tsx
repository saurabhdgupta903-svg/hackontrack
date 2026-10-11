"use client";

import React, { useState } from "react";
import {
  Volume2,
  VolumeX,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  AlertOctagon,
  Calendar,
  CheckCircle2,
  Flag,
} from "lucide-react";
import VerdictBadge from "@/components/VerdictBadge";
import FeedbackModal from "@/components/FeedbackModal";
import { FactCheckResponse, ClaimResult, EvidenceItem } from "@/lib/api";
import { LanguageCode, UI_STRINGS } from "@/lib/i18n";

interface ResultViewProps {
  data: FactCheckResponse;
  currentLang: LanguageCode;
}

export default function ResultView({ data, currentLang }: ResultViewProps) {
  const [expandedEvidence, setExpandedEvidence] = useState<Record<string, boolean>>({});
  const [playingClaimId, setPlayingClaimId] = useState<string | null>(null);
  const [feedbackClaim, setFeedbackClaim] = useState<ClaimResult | null>(null);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  const strings = UI_STRINGS[currentLang] || UI_STRINGS.en;

  // Cleanup audio & speechSynthesis on unmount
  React.useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const toggleEvidence = (claimId: string) => {
    setExpandedEvidence((prev) => ({
      ...prev,
      [claimId]: !prev[claimId],
    }));
  };

  const handlePlayAudio = (claim: ClaimResult) => {
    // 1. If currently playing this claim, stop
    if (playingClaimId === claim.claim_id) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setPlayingClaimId(null);
      return;
    }

    // Stop any existing playback
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    // 2. If base64 audio returned by Sarvam / backend TTS
    if (claim.audio_base64) {
      const mime = claim.audio_mime || "audio/wav";
      const audio = new Audio(`data:${mime};base64,${claim.audio_base64}`);
      audioRef.current = audio;
      audio.onended = () => setPlayingClaimId(null);
      audio.onerror = () => setPlayingClaimId(null);
      audio.play().catch(() => {});
      setPlayingClaimId(claim.claim_id);
      return;
    }

    // 3. Fallback: Browser Web Speech API
    if ("speechSynthesis" in window) {
      const textToSpeak = claim.explanation;
      const utterance = new SpeechSynthesisUtterance(textToSpeak);

      // Map language code for Indic voices
      const langMap: Record<string, string> = {
        hi: "hi-IN",
        mr: "mr-IN",
        ta: "ta-IN",
        bn: "bn-IN",
        te: "te-IN",
        gu: "gu-IN",
        en: "en-IN",
      };
      utterance.lang = langMap[currentLang] || (currentLang === "auto" ? "hi-IN" : "en-US");
      utterance.rate = 0.95;

      utterance.onend = () => setPlayingClaimId(null);
      utterance.onerror = () => setPlayingClaimId(null);

      window.speechSynthesis.speak(utterance);
      setPlayingClaimId(claim.claim_id);
    }
  };

  return (
    <section className="w-full space-y-4" aria-label="Fact check results">
      {/* Top Overall Summary Banner */}
      <div className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent">
        <div>
          <span className="text-xs uppercase font-mono tracking-wider text-wa-text-muted block mb-1">
            Summary Verdict
          </span>
          <p className="text-lg sm:text-xl font-serif text-wa-text font-medium leading-snug">
            {data.summary.summary_text}
          </p>
          <div className="flex items-center gap-3 mt-2 text-xs text-wa-text-muted">
            <span>Input: {data.input_type.toUpperCase()}</span>
            <span>•</span>
            <span>Language: {data.detected_language}</span>
            <span>•</span>
            <span>As of: {data.claims[0]?.as_of_date || "Current"}</span>
          </div>
        </div>

        <VerdictBadge verdict={data.summary.dominant_verdict} size="lg" className="self-start sm:self-center" />
      </div>

      {/* Claims List */}
      <div className="space-y-4">
        <h2 className="text-sm font-mono uppercase text-wa-text-muted tracking-wider">
          Individual Claims Breakdown ({data.claims.length})
        </h2>

        {data.claims.length === 0 ? (
          <div className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-5 text-center text-wa-text-muted text-sm shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent">
            No checkable factual claims detected in this message.
          </div>
        ) : (
          data.claims.map((claim, idx) => {
            const isExpanded = !!expandedEvidence[claim.claim_id];
            const isPlaying = playingClaimId === claim.claim_id;

            return (
              <article
                key={claim.claim_id}
                className="bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-4 transition-all duration-200 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent motion-reduce:transition-none"
                style={{
                  animation: `fadeSlideUp 250ms ease-out ${idx * 60}ms forwards`,
                }}
              >
                {/* Header: Original Quote & Verdict Badge */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-[#c5ecbd] pb-2.5 mb-2.5">
                  <div className="flex-1">
                    <span className="text-xs font-mono text-wa-text-muted uppercase">
                      Claim #{idx + 1}
                    </span>
                    <blockquote className="mt-1 text-sm sm:text-base font-serif italic text-wa-text border-l-2 border-wa-accent/70 pl-3">
                      &ldquo;{claim.original_span}&rdquo;
                    </blockquote>
                  </div>

                  <VerdictBadge verdict={claim.verdict} size="md" className="flex-shrink-0" />
                </div>

                {/* Plain-Language Explanation */}
                <div className="my-2.5">
                  <p className="text-base text-wa-text leading-relaxed font-sans">
                    {claim.explanation}
                  </p>

                  {/* Fallback English translation if viewing in Indic script */}
                  {currentLang !== "en" && claim.explanation_en && claim.explanation_en !== claim.explanation && (
                    <p className="mt-2 text-xs text-wa-text-muted border-t border-[#c5ecbd] pt-2 font-sans">
                      <span className="font-medium text-wa-text">English: </span>
                      {claim.explanation_en}
                    </p>
                  )}
                </div>

                {/* Specifics: What is right / What is wrong */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-3 text-xs bg-wa-bubble-dark/60 p-2.5 rounded-xl border border-[#b5deb0]">
                  <div>
                    <span className="font-medium text-wa-text block mb-0.5">
                      What official records say:
                    </span>
                    <p className="text-neutral-700 leading-normal">{claim.what_is_right}</p>
                  </div>
                  <div>
                    <span className="font-medium text-wa-text block mb-0.5">
                      What is false or missing:
                    </span>
                    <p className="text-neutral-700 leading-normal">{claim.what_is_wrong_or_missing}</p>
                  </div>
                </div>

                {claim.date_changed && (
                  <div className="my-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5 flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>Changed Date: {claim.date_changed}</span>
                  </div>
                )}

                {/* Actions: Audio Listen + Evidence Expand + Report */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-2.5 border-t border-[#c5ecbd] text-xs">
                  <div className="flex items-center gap-2">
                    {/* Listen Audio Button */}
                    <button
                      type="button"
                      onClick={() => handlePlayAudio(claim)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors ${
                        isPlaying
                          ? "bg-rose-50 border-rose-300 text-rose-800 hover:bg-rose-100"
                          : "bg-white/70 border-[#c5ecbd] text-wa-text hover:bg-white"
                      }`}
                      aria-label={isPlaying ? "Stop audio" : "Listen to explanation audio"}
                    >
                      {isPlaying ? (
                        <>
                          <VolumeX className="w-3.5 h-3.5 text-rose-700" />
                          <span>{strings.stopAudio}</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3.5 h-3.5 text-wa-text-muted" />
                          <span>{strings.listenAudio}</span>
                        </>
                      )}
                    </button>

                    {/* Expand Evidence Button */}
                    <button
                      type="button"
                      onClick={() => toggleEvidence(claim.claim_id)}
                      className="inline-flex items-center gap-1 text-wa-text-muted hover:text-wa-text px-3 py-1.5 rounded-full hover:bg-black/5"
                    >
                      <span>
                        {strings.evidenceSources} ({claim.evidence.length})
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  {/* Report Correction Button */}
                  <button
                    type="button"
                    onClick={() => setFeedbackClaim(claim)}
                    className="inline-flex items-center gap-1 text-wa-text-muted hover:text-wa-text transition-colors"
                  >
                    <Flag className="w-3 h-3" />
                    <span>{strings.reportWrong}</span>
                  </button>
                </div>

                {/* Expandable Verified Evidence List */}
                {isExpanded && (
                  <div className="mt-3 pt-2.5 border-t border-[#c5ecbd] space-y-2.5">
                    <p className="text-xs text-wa-text-muted font-mono">
                      Every cited source passed domain allowlisting and citation verification:
                    </p>

                    {claim.evidence.length === 0 ? (
                      <p className="text-xs text-wa-text-muted italic">
                        No allowlisted official source confirmed this claim.
                      </p>
                    ) : (
                      claim.evidence.map((ev, eIdx) => (
                        <div
                          key={eIdx}
                          className="bg-wa-bubble-dark/40 border border-[#b5deb0] rounded-xl p-2.5 text-xs space-y-1.5"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-mono font-medium text-wa-text">
                              {ev.source_name}
                            </span>
                            <span className="text-wa-text-muted font-mono text-[11px]">
                              {ev.date || "Recent"}
                            </span>
                          </div>

                          <p className="text-neutral-700 italic border-l-2 border-[#b5deb0] pl-2 leading-relaxed">
                            &ldquo;{ev.quote_or_passage}&rdquo;
                          </p>

                          <div className="flex items-center justify-between pt-1">
                            {ev.is_verified_citation ? (
                              <span className="text-[11px] text-emerald-800 font-mono flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                                Verbatim Match Verified
                              </span>
                            ) : (
                              <span className="text-[11px] text-amber-800 font-mono flex items-center gap-1" title="URL from allowlisted domain, but quote could not be matched verbatim in source page text">
                                <AlertOctagon className="w-3 h-3 text-amber-700" />
                                Unverified Passage (Allowlisted Domain)
                              </span>
                            )}
                            <a
                              href={ev.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-wa-accent hover:underline font-mono inline-flex items-center gap-1 text-[11px]"
                            >
                              <span>Open source</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </article>
            );
          })
        )}
      </div>

      {/* Feedback Modal */}
      {feedbackClaim && (
        <FeedbackModal
          checkId={data.id}
          claimId={feedbackClaim.claim_id}
          currentVerdict={feedbackClaim.verdict}
          isOpen={true}
          onClose={() => setFeedbackClaim(null)}
        />
      )}
    </section>
  );
}

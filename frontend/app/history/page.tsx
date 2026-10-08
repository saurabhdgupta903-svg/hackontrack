"use client";

import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import VerdictBadge from "@/components/VerdictBadge";
import { fetchHistory, deleteCheckById, HistoryItem } from "@/lib/api";
import { LanguageCode, UI_STRINGS } from "@/lib/i18n";
import { Trash2, Clock, Inbox, Loader2 } from "lucide-react";

export default function HistoryPage() {
  const [currentLang, setCurrentLang] = useState<LanguageCode>("en");
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const strings = UI_STRINGS[currentLang] || UI_STRINGS.en;

  const loadHistory = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const items = await fetchHistory();
      setHistoryItems(items);
    } catch {
      setErrorMsg("Could not connect to history storage.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteCheckById(id);
      setHistoryItems((prev) => prev.filter((item) => item.id !== id));
    } catch {
      alert("Failed to delete record.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#FAFAF7]">
      <Navbar currentLang={currentLang} onLanguageChange={setCurrentLang} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-10 sm:py-14">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-serif font-bold text-[#1A1A1A]">
              Verification History
            </h1>
            <p className="mt-1 text-sm text-neutral-600">
              Past checks performed on this instance. Phone numbers and personal emails are redacted.
            </p>
          </div>
          <span className="text-xs font-mono text-neutral-500 bg-white border border-neutral-200 px-3 py-1.5 rounded-md">
            {historyItems.length} records saved
          </span>
        </div>

        {/* Loading Skeletons */}
        {isLoading && (
          <div className="space-y-3" aria-label="Loading history records">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="bg-white border border-neutral-200 rounded-md p-4 animate-pulse"
              >
                <div className="h-4 bg-neutral-200 rounded w-1/4 mb-3" />
                <div className="h-4 bg-neutral-100 rounded w-3/4 mb-2" />
                <div className="h-3 bg-neutral-100 rounded w-1/2" />
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {!isLoading && errorMsg && (
          <div className="bg-rose-50 border border-rose-200 rounded-md p-4 text-sm text-rose-800">
            {errorMsg}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !errorMsg && historyItems.length === 0 && (
          <div className="bg-white border border-neutral-200 rounded-md p-12 text-center">
            <Inbox className="w-10 h-10 mx-auto text-neutral-400 mb-3" />
            <h2 className="text-base font-serif font-semibold text-[#1A1A1A]">
              No checks saved yet
            </h2>
            <p className="text-xs text-neutral-500 mt-1 max-w-sm mx-auto">
              {strings.noHistory}
            </p>
          </div>
        )}

        {/* History List */}
        {!isLoading && historyItems.length > 0 && (
          <div className="space-y-3">
            {historyItems.map((item) => (
              <article
                key={item.id}
                className="bg-white border border-neutral-200 rounded-md p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:border-neutral-300 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5 text-xs text-neutral-500 font-mono">
                    <span className="uppercase px-1.5 py-0.5 bg-neutral-100 rounded">
                      {item.input_type}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : "Recent"}
                    </span>
                  </div>

                  <p className="text-sm font-sans font-medium text-[#1A1A1A] truncate mb-1">
                    &ldquo;{item.snippet}&rdquo;
                  </p>

                  <p className="text-xs text-neutral-600 line-clamp-1">
                    {item.summary_text}
                  </p>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-center flex-shrink-0">
                  <VerdictBadge verdict={item.dominant_verdict} size="sm" />

                  <button
                    onClick={() => handleDelete(item.id)}
                    disabled={deletingId === item.id}
                    className="p-1.5 text-neutral-400 hover:text-rose-700 hover:bg-rose-50 rounded-md transition-colors"
                    aria-label={`Delete record ${item.id}`}
                    title="Delete record"
                  >
                    {deletingId === item.id ? (
                      <Loader2 className="w-4 h-4 animate-spin text-rose-700" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

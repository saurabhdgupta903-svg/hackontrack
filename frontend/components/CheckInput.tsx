"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  FileText,
  Image as ImageIcon,
  Mic,
  FileCode,
  Link2,
  Upload,
  Square,
  AlertCircle,
  X,
  LucideIcon
} from "lucide-react";
import { LanguageCode, UI_STRINGS } from "@/lib/i18n";
import { FactCheckResponse } from "@/lib/api";

type TabType = "text" | "image" | "voice" | "pdf" | "url";

interface CheckInputProps {
  currentLang: LanguageCode;
  onStartCheck: () => void;
  onProgress: (stage: string, message: string, percent: number) => void;
  onComplete: (data: FactCheckResponse) => void;
  onError: (errorMsg: string) => void;
  isLoading: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CheckInput({
  currentLang,
  onStartCheck,
  onProgress,
  onComplete,
  onError,
  isLoading,
}: CheckInputProps) {
  const [activeTab, setActiveTab] = useState<TabType>("text");
  const [textInput, setTextInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [inlineError, setInlineError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const strings = UI_STRINGS[currentLang] || UI_STRINGS.en;

  // Cleanup object URL
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  // Handle voice recording timer
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => {
          if (prev >= 120) {
            stopRecording();
            setInlineError("Voice note reached the 2-minute limit.");
            return 120;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      setRecordingSeconds(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording]);

  const clearForm = () => {
    setTextInput("");
    setUrlInput("");
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setInlineError(null);
  };

  const validateFile = (file: File, type: TabType): boolean => {
    setInlineError(null);
    const sizeMb = file.size / (1024 * 1024);

    if (type === "image") {
      if (sizeMb > 10) {
        setInlineError("Image exceeds 10 MB limit. Please upload a smaller image.");
        return false;
      }
      if (!file.type.startsWith("image/")) {
        setInlineError("Please upload an image file (JPG, PNG, or WebP).");
        return false;
      }
    } else if (type === "pdf") {
      if (sizeMb > 10) {
        setInlineError("PDF exceeds 10 MB limit.");
        return false;
      }
      if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
        setInlineError("Please upload a valid PDF document.");
        return false;
      }
    } else if (type === "voice") {
      if (sizeMb > 15) {
        setInlineError("Voice note too long. Audio limit is 15 MB (~2 minutes).");
        return false;
      }
      if (!file.type.startsWith("audio/") && !/\.(mp3|ogg|opus|wav|m4a)$/i.test(file.name)) {
        setInlineError("Please upload an audio file (.mp3, .ogg, .opus, .m4a, or .wav).");
        return false;
      }
    }
    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file, activeTab)) {
        setSelectedFile(file);
        if (activeTab === "image") {
          setPreviewUrl(URL.createObjectURL(file));
        }
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file, activeTab)) {
        setSelectedFile(file);
        if (activeTab === "image") {
          setPreviewUrl(URL.createObjectURL(file));
        }
      }
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    if (activeTab === "image" && e.clipboardData.files.length > 0) {
      const file = e.clipboardData.files[0];
      if (file.type.startsWith("image/")) {
        if (validateFile(file, "image")) {
          setSelectedFile(file);
          setPreviewUrl(URL.createObjectURL(file));
        }
      }
    }
  };

  const startRecording = async () => {
    setInlineError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const audioFile = new File([audioBlob], `voice-note-${Date.now()}.webm`, {
          type: "audio/webm",
        });
        setSelectedFile(audioFile);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = recorder;
      recorder.start(250);
      setIsRecording(true);
    } catch (err) {
      setInlineError("Microphone access denied or not available. You can upload an audio file instead.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Submit via SSE stream
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setInlineError(null);

    // Validation
    if (activeTab === "text" && !textInput.trim()) {
      setInlineError("Please paste or type the message you received.");
      return;
    }
    if (activeTab === "url") {
      if (!urlInput.trim()) {
        setInlineError("Please enter a link to check.");
        return;
      }
      if (!/^https?:\/\//i.test(urlInput.trim())) {
        setInlineError("Please enter a complete URL starting with http:// or https://");
        return;
      }
    }
    if ((activeTab === "image" || activeTab === "voice" || activeTab === "pdf") && !selectedFile) {
      setInlineError(`Please select or upload a ${activeTab === "image" ? "screenshot" : activeTab} first.`);
      return;
    }

    onStartCheck();

    const formData = new FormData();
    formData.append("input_type", activeTab);
    formData.append("target_language", currentLang);

    if (activeTab === "text") {
      formData.append("text", textInput.trim());
    } else if (activeTab === "url") {
      formData.append("url", urlInput.trim());
    } else if (selectedFile) {
      formData.append("file", selectedFile);
    }

    try {
      const response = await fetch(`${API_BASE}/api/check/stream`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      if (!reader) throw new Error("No response body");

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6).trim();
            try {
              const eventData = JSON.parse(jsonStr);
              if (eventData.error) {
                setInlineError(eventData.error);
                onError(eventData.error);
                return;
              }
              if (eventData.progress !== undefined) {
                onProgress(eventData.stage, eventData.message, eventData.progress);
              }
              if (eventData.stage === "complete" && eventData.data) {
                onComplete(eventData.data);
                return;
              }
            } catch (pErr) {
              // ignore partial json
            }
          }
        }
      }
    } catch (err: any) {
      const msg = err.message || "Failed to process request. Please try again.";
      setInlineError(msg);
      onError(msg);
    }
  };

  const tabs: { id: TabType; label: string; icon: LucideIcon }[] = [
    { id: "text", label: strings.tabText, icon: FileText },
    { id: "image", label: strings.tabImage, icon: ImageIcon },
    { id: "voice", label: strings.tabVoice, icon: Mic },
    { id: "pdf", label: strings.tabPdf, icon: FileCode },
    { id: "url", label: strings.tabLink, icon: Link2 },
  ];

  return (
    <div className="w-full bg-wa-bubble rounded-[4px_12px_12px_12px] p-3 sm:p-5 mb-6 shadow-[0_1px_0.5px_rgba(0,0,0,0.13)] border border-transparent" onPaste={handlePaste}>
      {/* Input Type Tabs */}
      <div className="flex border-b border-[#c5ecbd] mb-5 overflow-x-auto gap-1" role="tablist">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => {
                setActiveTab(tab.id);
                setInlineError(null);
              }}
              disabled={isLoading}
              className={`flex items-center gap-2 px-3 sm:px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap min-h-[44px] ${
                isActive
                  ? "border-wa-accent text-wa-accent"
                  : "border-transparent text-wa-text-muted hover:text-wa-text"
              } disabled:opacity-50`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSubmit}>
        {/* Tab 1: Text */}
        {activeTab === "text" && (
          <div>
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={strings.placeholderText}
              disabled={isLoading}
              rows={5}
              aria-label="Forwarded message text"
              className="w-full p-3 bg-white border border-[#d1d7db] rounded-2xl text-wa-text placeholder-neutral-400 focus:outline-none focus:ring-1 focus:ring-wa-accent focus:border-wa-accent text-base leading-relaxed resize-y shadow-xs"
            />
            <div className="flex justify-between items-center text-xs text-wa-text-muted mt-2 font-mono">
              <span>{textInput.length} characters</span>
              <span>Drop chain greetings & noise automatically</span>
            </div>
          </div>
        )}

        {/* Tab 2: Image */}
        {activeTab === "image" && (
          <div>
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[#c5ecbd] rounded-2xl p-6 text-center hover:border-wa-accent transition-colors cursor-pointer bg-white/70"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={handleFileChange}
              />
              <Upload className="w-8 h-8 mx-auto text-neutral-400 mb-2" />
              <p className="text-sm text-wa-text font-medium mb-1">
                {selectedFile ? selectedFile.name : strings.dragDropImage}
              </p>
              <p className="text-xs text-wa-text-muted">
                Supports WhatsApp screenshots, banners, newspaper clippings (PNG, JPG, WebP up to 10MB)
              </p>
            </div>

            {previewUrl && (
              <div className="mt-3 relative inline-block border border-neutral-200 rounded-md overflow-hidden max-h-48">
                <img src={previewUrl} alt="Screenshot preview" className="max-h-48 object-contain" />
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                    setPreviewUrl(null);
                  }}
                  className="absolute top-1 right-1 bg-neutral-900/70 text-white rounded-full p-1 hover:bg-neutral-900"
                  aria-label="Remove image"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Voice Note */}
        {activeTab === "voice" && (
          <div className="space-y-4">
            <div className="border border-[#c5ecbd] rounded-2xl p-4 bg-white/70 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isLoading}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-colors min-h-[44px] ${
                    isRecording
                      ? "bg-rose-700 text-white hover:bg-rose-800"
                      : "bg-wa-accent text-white hover:bg-wa-accent-hover"
                  }`}
                >
                  {isRecording ? (
                    <>
                      <Square className="w-4 h-4 fill-current" />
                      <span>{strings.recordStop} ({recordingSeconds}s)</span>
                    </>
                  ) : (
                    <>
                      <Mic className="w-4 h-4" />
                      <span>{strings.recordStart}</span>
                    </>
                  )}
                </button>
                {isRecording && (
                  <span className="flex h-3 w-3 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
                  </span>
                )}
              </div>

              <span className="text-xs text-wa-text-muted uppercase font-mono">or upload file</span>

              <div>
                <input
                  type="file"
                  id="voice-file"
                  accept="audio/*,.mp3,.ogg,.opus,.m4a,.wav"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <label
                  htmlFor="voice-file"
                  className="inline-flex items-center gap-1.5 px-4 py-2 border border-[#d1d7db] rounded-full text-sm text-wa-text bg-white hover:bg-neutral-50 cursor-pointer min-h-[44px]"
                >
                  <Upload className="w-4 h-4" />
                  <span>Choose audio file</span>
                </label>
              </div>
            </div>

            {selectedFile && (
              <div className="text-xs text-wa-text flex items-center justify-between p-2.5 bg-white/70 border border-[#c5ecbd] rounded-xl">
                <span>Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  className="text-neutral-400 hover:text-neutral-700"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: PDF */}
        {activeTab === "pdf" && (
          <div>
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[#c5ecbd] rounded-2xl p-6 text-center hover:border-wa-accent transition-colors cursor-pointer bg-white/70"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf,.pdf"
                className="hidden"
                onChange={handleFileChange}
              />
              <FileCode className="w-8 h-8 mx-auto text-neutral-400 mb-2" />
              <p className="text-sm text-wa-text font-medium mb-1">
                {selectedFile ? selectedFile.name : strings.dragDropPdf}
              </p>
              <p className="text-xs text-wa-text-muted">
                Government notices, circulars, circular PDFs (up to 10MB)
              </p>
            </div>
            {selectedFile && (
              <div className="mt-2 text-xs text-wa-text flex items-center justify-between p-2.5 bg-white/70 border border-[#c5ecbd] rounded-xl">
                <span>Attached: {selectedFile.name}</span>
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  className="text-neutral-400 hover:text-neutral-700"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 5: Link */}
        {activeTab === "url" && (
          <div>
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder={strings.placeholderUrl}
              disabled={isLoading}
              aria-label="Article or viral URL"
              className="w-full p-3 bg-white border border-[#d1d7db] rounded-full text-wa-text placeholder-neutral-400 focus:outline-none focus:ring-1 focus:ring-wa-accent focus:border-wa-accent text-base shadow-xs"
            />
            <p className="text-xs text-wa-text-muted mt-2">
              Clean article extraction via trafilatura. (Sites with paywalls or logins cannot be opened).
            </p>
          </div>
        )}

        {/* Inline Error Notice */}
        {inlineError && (
          <div
            className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2.5 text-sm text-rose-800"
            role="alert"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-rose-700" />
            <div className="flex-1 leading-normal">{inlineError}</div>
          </div>
        )}

        {/* Submit Actions */}
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-[#c5ecbd]/60">
          <p className="text-xs text-wa-text-muted font-sans max-w-md hidden sm:block">
            {strings.officialWarning}
          </p>

          <div className="flex items-center gap-2 ml-auto">
            {(textInput || urlInput || selectedFile) && (
              <button
                type="button"
                onClick={clearForm}
                disabled={isLoading}
                className="px-4 py-2 text-sm text-wa-text-muted hover:text-wa-text rounded-full min-h-[44px]"
              >
                {strings.clear}
              </button>
            )}
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2.5 bg-wa-accent text-white rounded-full text-sm font-medium hover:bg-wa-accent-hover transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-wa-accent disabled:opacity-50 min-h-[44px] flex items-center gap-2 shadow-sm"
            >
              <span>{isLoading ? strings.checking : strings.checkButton}</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

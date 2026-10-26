"use client";

import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { UploadCloud, CheckCircle2, AlertCircle, Link2, ArrowRight, X } from "lucide-react";
import { Button } from "./ui/button";

interface UploadProps {
  apiUrl?: string;
  onUploadSuccess: (data: {
    sessionId: string;
    filename: string;
    chunkCount: number;
    pageCount: number;
  }) => void;
  className?: string;
}

const MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024; // 100 MB max allowed (server enforces Free/Pro tier limits)
const ALLOWED_EXTENSIONS = [".pdf", ".md", ".txt", ".docx", ".pptx", ".xlsx", ".html"];

const PROGRESS_STEPS = [
  "Cutting into chunks…",
  "Mapping cross-references…",
  "Teaching the index…",
];

export function Upload({
  apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  onUploadSuccess,
  className = "",
}: UploadProps) {
  const { getToken } = useAuth();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progressStepIdx, setProgressStepIdx] = useState(0);
  const [progressPercent, setProgressPercent] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{ count: number; filename: string } | null>(null);
  const [animatedCount, setAnimatedCount] = useState(0);

  const [isUrlMode, setIsUrlMode] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [isSubmittingUrl, setIsSubmittingUrl] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Rotating progress step simulation during upload
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isUploading) {
      setProgressPercent(15);
      interval = setInterval(() => {
        setProgressStepIdx((prev) => (prev + 1) % PROGRESS_STEPS.length);
        setProgressPercent((prev) => Math.min(prev + 25, 90));
      }, 700);
    } else {
      setProgressPercent(0);
      setProgressStepIdx(0);
    }
    return () => clearInterval(interval);
  }, [isUploading]);

  // Rolling count-up animation on success
  useEffect(() => {
    if (successInfo) {
      let start = 0;
      const target = successInfo.count;
      const duration = 600;
      const stepTime = Math.max(Math.floor(duration / (target || 1)), 15);
      const timer = setInterval(() => {
        start += Math.ceil(target / 25);
        if (start >= target) {
          setAnimatedCount(target);
          clearInterval(timer);
        } else {
          setAnimatedCount(start);
        }
      }, stepTime);
      return () => clearInterval(timer);
    }
  }, [successInfo]);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return "That's a big one. Free takes up to 10 MB — Pro takes 100.";
    }
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return "Couldn't read this file — it may be corrupt or password-protected. Nothing was saved.";
    }
    return null;
  };

  const handleFile = async (file: File) => {
    setErrorMessage(null);
    setSuccessInfo(null);

    const validationError = validateFile(file);
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    setIsUploading(true);

    try {
      const token = await getToken().catch(() => null);
      const formData = new FormData();
      formData.append("file", file);

      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`${apiUrl.replace(/\/$/, "")}/v1/ingest`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        const code = errJson?.detail?.error?.code;
        if (code === "plan_limit_reached" || code === "doc_too_large" || res.status === 413 || res.status === 402) {
          throw new Error(errJson?.detail?.error?.message || "That's a big one. Free takes up to 10 MB — Pro takes 100.");
        }
        if (code === "doc_unreadable") {
          throw new Error("Couldn't read this file — it may be corrupt or password-protected. Nothing was saved.");
        }
        if (res.status === 404 || res.status >= 500) {
          throw new Error(`Backend service is not running or unreachable (${res.status}). The API server at ${apiUrl} has not been deployed yet.`);
        }
        throw new Error(errJson?.detail?.error?.message || "Couldn't read this file — it may be corrupt or password-protected. Nothing was saved.");
      }

      const data = await res.json();
      const chunkCount = data.chunk_count || 0;
      const pageCount = data.page_count || 1;
      const filename = data.filename || file.name;
      const sessionId = data.session_id;

      setSuccessInfo({ count: chunkCount, filename });

      onUploadSuccess({
        sessionId,
        filename,
        chunkCount,
        pageCount,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg === "Load failed" || msg === "Failed to fetch" || msg.toLowerCase().includes("networkerror")) {
        setErrorMessage("Could not connect to the backend server. Please ensure the backend is running.");
      } else {
        setErrorMessage(msg);
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setErrorMessage(null);
    setSuccessInfo(null);
    setIsSubmittingUrl(true);

    try {
      const token = await getToken().catch(() => null);
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`${apiUrl.replace(/\/$/, "")}/v1/ingest/url`, {
        method: "POST",
        headers,
        body: JSON.stringify({ url: urlInput.trim() }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        const code = errJson?.detail?.error?.code;
        if (code === "url_blocked") {
          throw new Error("That link points somewhere private — we don't fetch those. Safety thing.");
        }
        if (res.status === 404 || res.status >= 500) {
          throw new Error(`Backend service is not running or unreachable (${res.status}). The API server at ${apiUrl} has not been deployed yet.`);
        }
        throw new Error(errJson?.detail?.error?.message || "Couldn't read from that URL. Check the link and try again.");
      }

      const data = await res.json();
      const chunkCount = data.chunk_count || 0;
      const pageCount = data.page_count || 1;
      const filename = data.title || urlInput.trim();
      const sessionId = data.session_id;

      setSuccessInfo({ count: chunkCount, filename });
      setUrlInput("");
      setIsUrlMode(false);

      onUploadSuccess({
        sessionId,
        filename,
        chunkCount,
        pageCount,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg === "Load failed" || msg === "Failed to fetch" || msg.toLowerCase().includes("networkerror")) {
        setErrorMessage("Could not connect to the backend server. Please ensure the backend is running.");
      } else {
        setErrorMessage(msg);
      }
    } finally {
      setIsSubmittingUrl(false);
    }
  };

  return (
    <div className={`relative ${className}`}>
      {successInfo && (
        <div className="mb-3 px-3.5 py-2.5 rounded-interactive bg-accent-primary/10 border border-accent-primary/30 text-ink-primary text-xs font-medium flex items-center justify-between shadow-xs animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-accent-primary flex-shrink-0" />
            <span>
              <strong className="font-mono">{animatedCount}</strong> chunks ready — ask away.
            </span>
          </div>
          <button
            type="button"
            onClick={() => setSuccessInfo(null)}
            className="text-ink-ghost hover:text-ink-primary text-xs font-mono ml-2 p-0.5 rounded cursor-pointer transition-transform duration-120 hover:scale-110 active:scale-90"
            aria-label="Dismiss banner"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="mb-3 px-3.5 py-2.5 rounded-interactive bg-danger/10 border-l-4 border-l-danger border border-border text-ink-primary text-xs font-medium flex items-center justify-between shadow-xs animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-danger flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-ink-ghost hover:text-ink-primary text-xs font-mono ml-2 p-0.5 rounded cursor-pointer transition-transform duration-120 hover:scale-110 active:scale-90"
            aria-label="Dismiss error"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Mode Switcher */}
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-[11px] font-mono text-gray-warm uppercase tracking-wider">
          {isUrlMode ? "Web Link" : "File Upload"}
        </span>
        <button
          type="button"
          onClick={() => {
            setIsUrlMode(!isUrlMode);
            setErrorMessage(null);
          }}
          className="text-xs text-accent-primary hover:underline font-medium inline-flex items-center gap-1 transition-all duration-150 hover:translate-x-0.5 active:scale-95"
        >
          {isUrlMode ? "Upload file instead" : "Paste a URL instead"}
        </button>
      </div>

      {isUrlMode ? (
        /* URL Input Form */
        <form
          onSubmit={handleUrlSubmit}
          className="flex items-center gap-2 p-2 rounded-interactive border border-border bg-bg-surface"
        >
          <div className="relative flex-1">
            <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-ghost" />
            <input
              type="url"
              required
              placeholder="https://example.com/handbook.html"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-input bg-bg-sunken border border-border text-ink-primary placeholder:text-ink-ghost focus:outline-none focus:ring-1 focus:ring-accent-primary"
            />
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={isSubmittingUrl || !urlInput.trim()}
            className="text-xs h-8 px-3"
          >
            {isSubmittingUrl ? "Fetching…" : "Fetch"}
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </form>
      ) : (
        /* Drag & Drop Target with Waving Border on Drag-over */
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
              handleFile(e.dataTransfer.files[0]);
            }
          }}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`group relative rounded-interactive p-6 text-center cursor-pointer transition-all duration-200 ease-out bg-bg-surface motion-reduce:transform-none ${
            isDragging
              ? "waving-border bg-accent-primary/5 scale-[1.01] shadow-sm"
              : "border border-dashed border-border hover:border-accent-primary/60 hover:bg-bg-sunken/40 hover:-translate-y-0.5 hover:shadow-xs active:translate-y-0"
          } ${isUploading ? "pointer-events-none opacity-90" : ""}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.md,.txt,.docx,.pptx,.xlsx,.html"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFile(e.target.files[0]);
              }
            }}
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center gap-2">
            {isUploading ? (
              <div className="w-full max-w-xs space-y-3">
                <div className="w-full bg-bg-sunken h-1.5 rounded-full overflow-hidden border border-border">
                  <div
                    className="bg-accent-primary h-full transition-all duration-300 ease-out"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-gray-warm">
                  <span>{PROGRESS_STEPS[progressStepIdx]}</span>
                  <span className="text-ink-ghost">{progressPercent}%</span>
                </div>
              </div>
            ) : (
              <>
                <div className="w-10 h-10 rounded-full bg-bg-sunken border border-border text-accent-primary flex items-center justify-center transition-all duration-200 ease-out group-hover:scale-110 group-hover:-translate-y-1 group-hover:border-accent-primary/40 group-hover:shadow-xs">
                  <UploadCloud className="w-5 h-5 transition-transform duration-200 group-hover:scale-105" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-ink-primary font-display">
                    {isDragging ? "Looks like a document. Let it go." : "Drop a document"}
                  </h3>
                  <p className="text-xs text-gray-warm mt-1">
                    PDF, Word, PowerPoint, Excel, Markdown, or paste a URL
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

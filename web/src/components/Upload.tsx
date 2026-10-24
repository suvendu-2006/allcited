"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

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

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB cap per plan
const ALLOWED_EXTENSIONS = [".pdf", ".md", ".txt", ".docx", ".pptx", ".xlsx", ".html"];

export function Upload({ apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000", onUploadSuccess, className = "" }: UploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<{ count: number; filename: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds 20 MB plan limit`;
    }
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported format. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`;
    }
    return null;
  };

  const handleFile = async (file: File) => {
    setErrorMessage(null);
    setSuccessToast(null);

    const validationError = validateFile(file);
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${apiUrl.replace(/\/$/, "")}/v1/ingest`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        const msg = errJson?.detail?.error?.message || errJson?.detail || `Upload failed (HTTP ${res.status})`;
        throw new Error(msg);
      }

      const data = await res.json();
      const chunkCount = data.chunk_count || 0;
      const pageCount = data.page_count || 1;
      const filename = data.filename || file.name;
      const sessionId = data.session_id;

      setSuccessToast({ count: chunkCount, filename });

      onUploadSuccess({
        sessionId,
        filename,
        chunkCount,
        pageCount,
      });

      // Clear success toast after 4s
      setTimeout(() => {
        setSuccessToast(null);
      }, 4000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(msg);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Toast Notification Banner */}
      {successToast && (
        <div className="mb-3 px-3 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs font-medium flex items-center justify-between shadow-sm animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            <span>
              ✅ {successToast.count} chunks ready for &quot;{successToast.filename}&quot;
            </span>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {errorMessage && (
        <div className="mb-3 px-3 py-2 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs font-medium flex items-center justify-between shadow-sm animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-rose-500 hover:text-rose-700 text-sm font-bold ml-2"
          >
            ×
          </button>
        </div>
      )}

      {/* Drag & Drop Target */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-4 text-center cursor-pointer transition-all ${
          isDragging
            ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 scale-[1.01]"
            : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900"
        } ${isUploading ? "pointer-events-none opacity-80" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.txt,.docx,.pptx,.xlsx,.html"
          onChange={onFileChange}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center gap-2">
          {isUploading ? (
            <>
              <div className="w-9 h-9 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 flex items-center justify-center animate-spin">
                <Loader2 className="w-5 h-5" />
              </div>
              <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
                Parsing, chunking, and embedding document...
              </p>
            </>
          ) : (
            <>
              <div className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center">
                <UploadCloud className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-800 dark:text-slate-200">
                  <span className="text-blue-600 dark:text-blue-400 hover:underline">Click to upload</span> or drag and drop
                </p>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                  PDF, MD, TXT, DOCX, PPTX, XLSX (up to 20 MB)
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

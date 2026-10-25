"use client";

import React, { useState } from "react";
import { CheckCircle2, AlertCircle, Copy, Check, X } from "lucide-react";

export interface ToastItem {
  id: string;
  type: "success" | "error" | "info";
  message: string;
  requestId?: string;
}

interface ToastProps {
  toast: ToastItem | null;
  onClose?: () => void;
}

export function Toast({ toast, onClose }: ToastProps) {
  const [copied, setCopied] = useState(false);

  if (!toast) return null;

  const handleCopyRequestId = () => {
    if (toast.requestId) {
      navigator.clipboard.writeText(toast.requestId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isError = toast.type === "error";

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-slide-up flex flex-col items-center max-w-md w-full px-4 pointer-events-none">
      <div
        className={`pointer-events-auto flex items-start gap-3 w-full p-4 rounded-interactive shadow-xl border bg-bg-surface text-ink-primary ${
          isError
            ? "border-l-4 border-l-danger border-border"
            : "border-l-4 border-l-accent-primary border-border"
        }`}
      >
        <div className="flex-shrink-0 mt-0.5">
          {isError ? (
            <AlertCircle className="w-4 h-4 text-danger" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-accent-primary" />
          )}
        </div>

        <div className="flex-1 text-xs leading-relaxed">
          <p className="font-medium text-ink-primary">{toast.message}</p>
          {toast.requestId && (
            <div className="mt-1.5 flex items-center gap-1.5 font-mono text-[11px] text-gray-warm">
              <span>id: {toast.requestId}</span>
              <button
                type="button"
                onClick={handleCopyRequestId}
                aria-label="Copy request id"
                className="inline-flex items-center gap-0.5 hover:text-ink-primary underline transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-accent-primary" />
                    <span>copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>copy</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="flex-shrink-0 text-ink-ghost hover:text-ink-primary transition-colors text-xs p-0.5 rounded cursor-pointer"
            aria-label="Close toast"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

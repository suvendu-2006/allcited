"use client";

import React, { useState } from "react";
import { AlertCircle, RefreshCw, Copy, Check, Sparkles } from "lucide-react";
import { Button } from "./ui/button";

interface ErrorStateProps {
  code?: string;
  message?: string;
  requestId?: string;
  onRetry?: () => void;
  onOpenSettings?: () => void;
  onOpenUpgrade?: () => void;
}

export const ERROR_MESSAGES: Record<string, string> = {
  doc_unreadable: "Couldn't read that file — corrupt or password-protected. Nothing was saved.",
  doc_too_large: "That's past the size limit for your plan. (Free: 20 MB · Pro: 100 MB.)",
  free_tier_busy: "Our free brain is swamped right now. Try again in a minute — or plug in your own key in Settings and skip the line.",
  ollama_unreachable: "Can't reach your local Ollama. Is it running? (ollama serve)",
  url_blocked: "That link points somewhere private — we don't fetch those. Safety thing.",
  injection_flagged: "Heads up: this document contains text trying to give me instructions. I've treated it as data. The answer stands.",
  plan_limit_reached: "That's a Pro move. Upgrade to keep going.",
  session_expired: "This conversation's gone cold. Re-upload the document and we're back.",
  offline: "You're offline. Your last conversation is still here — ask away when you're back.",
  generic: "Something broke on our side. It's noted — try again, and if it repeats, the trace ID below helps us find it.",
};

export function getHumanError(code?: string, fallbackMessage?: string): string {
  if (code && ERROR_MESSAGES[code]) {
    return ERROR_MESSAGES[code];
  }
  return fallbackMessage || ERROR_MESSAGES.generic;
}

export function ErrorState({
  code,
  message,
  requestId,
  onRetry,
  onOpenSettings,
  onOpenUpgrade,
}: ErrorStateProps) {
  const [copied, setCopied] = useState(false);
  const displayMessage = getHumanError(code, message);

  const handleCopyRequestId = () => {
    if (requestId) {
      navigator.clipboard.writeText(requestId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isBusy = code === "free_tier_busy";
  const isPlanLimit = code === "plan_limit_reached";

  return (
    <div className="my-4 rounded-interactive border border-border border-l-4 border-l-danger bg-bg-surface p-4 shadow-sm animate-fade-in">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium text-ink-primary leading-relaxed">
            {displayMessage}
          </p>

          {/* Action buttons depending on error type */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="gap-1.5 text-xs h-7"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Try again</span>
              </Button>
            )}

            {isBusy && onOpenSettings && (
              <Button
                variant="default"
                size="sm"
                onClick={onOpenSettings}
                className="gap-1.5 text-xs h-7"
              >
                <Sparkles className="w-3 h-3" />
                <span>Bring your own key</span>
              </Button>
            )}

            {isPlanLimit && onOpenUpgrade && (
              <Button
                variant="default"
                size="sm"
                onClick={onOpenUpgrade}
                className="gap-1.5 text-xs h-7"
              >
                <span>Upgrade to Pro</span>
              </Button>
            )}

            {requestId && (
              <div className="inline-flex items-center gap-1.5 font-mono text-[11px] text-gray-warm ml-auto">
                <span>trace: {requestId}</span>
                <button
                  type="button"
                  onClick={handleCopyRequestId}
                  aria-label="Copy trace ID"
                  className="hover:text-ink-primary underline transition-colors"
                >
                  {copied ? (
                    <Check className="w-3 h-3 text-accent-primary inline" />
                  ) : (
                    <Copy className="w-3 h-3 inline" />
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

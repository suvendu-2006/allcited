"use client";

import React, { useState } from "react";
import { AlertCircle, RefreshCw, Copy, Check, Sparkles } from "lucide-react";
import { Button } from "./ui/button";
import { ERROR_MESSAGES } from "@/lib/copy";

export { ERROR_MESSAGES };

interface ErrorStateProps {
  code?: string;
  message?: string;
  requestId?: string;
  onRetry?: () => void;
  onOpenSettings?: () => void;
  onOpenUpgrade?: () => void;
}

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

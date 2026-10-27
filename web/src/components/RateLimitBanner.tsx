"use client";

import React, { useState, useEffect } from "react";
import { AlertCircle, Clock, Zap } from "lucide-react";
import Link from "next/link";

interface RateLimitBannerProps {
  resetAt: number;
  onReset: () => void;
  onOpenSettings?: () => void;
}

function formatRemaining(ms: number) {
  if (ms <= 0) return "00:00";
  const totalSec = Math.floor(ms / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function RateLimitBanner({ resetAt, onReset, onOpenSettings }: RateLimitBannerProps) {
  const [timeRemaining, setTimeRemaining] = useState<number>(() =>
    Math.max(0, resetAt - Date.now())
  );

  useEffect(() => {
    const update = () => {
      const diff = Math.max(0, resetAt - Date.now());
      setTimeRemaining(diff);
      if (diff <= 0) {
        onReset();
      }
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [resetAt, onReset]);

  return (
    <div className="mx-4 mb-3 p-3 rounded-interactive border border-accent-primary/40 bg-accent-primary/10 text-ink-primary text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 animate-fade-in shadow-xs">
      <div className="flex items-center gap-2">
        <AlertCircle className="w-4 h-4 text-accent-primary shrink-0" />
        <span className="font-mono">
          Free beta limit reached (10 questions / hour).
        </span>
      </div>

      <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
        <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-accent-primary bg-bg-surface px-2 py-0.5 rounded border border-accent-primary/30 tabular-nums">
          <Clock className="w-3 h-3 text-accent-primary" />
          <span>Resets in {formatRemaining(timeRemaining)}</span>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/pricing"
            className="font-mono text-[11px] text-accent-primary font-medium hover:underline flex items-center gap-1"
          >
            Upgrade to Pro
          </Link>
          {onOpenSettings && (
            <>
              <span className="text-border">·</span>
              <button
                type="button"
                onClick={onOpenSettings}
                className="font-mono text-[11px] text-gray-warm hover:text-ink-primary hover:underline flex items-center gap-1 cursor-pointer"
              >
                <Zap className="w-3 h-3 text-amber-500" />
                <span>Use BYOK</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

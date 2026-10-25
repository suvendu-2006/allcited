"use client";

import React, { useState, useEffect } from "react";
import { CitationChip } from "./CitationChip";
import { motion, AnimatePresence } from "framer-motion";

export function LiveMiniDemo() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [displayedText, setDisplayedText] = useState("");
  const [showCitations, setShowCitations] = useState(false);
  const [activeReceipt, setActiveReceipt] = useState<string | null>(null);

  const fullText =
    "Full-time personnel accrue 24 annual paid leave days. You may carry forward a maximum of 8 unused annual leave days into the following calendar year. Any surplus beyond 8 days lapses automatically on March 31. Upon voluntary departure, remaining leave is settled as per rule 63.7.4.";

  const runDemoStream = () => {
    setIsStreaming(true);
    setDisplayedText("");
    setShowCitations(false);
    setActiveReceipt(null);

    const words = fullText.split(" ");
    let index = 0;

    const interval = setInterval(() => {
      index++;
      if (index <= words.length) {
        setDisplayedText(words.slice(0, index).join(" "));
      } else {
        clearInterval(interval);
        setIsStreaming(false);
        setShowCitations(true);
      }
    }, 45);
  };

  // Trigger demo once on mount
  useEffect(() => {
    runDemoStream();
  }, []);

  return (
    <div className="rounded-interactive border border-border bg-bg-surface p-6 sm:p-8 shadow-md relative overflow-hidden space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border/70">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#28C840] dark:bg-[#5AD46F] animate-pulse" />
          <span className="font-mono text-xs font-semibold text-ink-primary">
            Live Inline Demo: &ldquo;Acme Employee Handbook.md&rdquo;
          </span>
          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
            Zero signup · No API key needed
          </span>
        </div>

        <button
          type="button"
          onClick={runDemoStream}
          disabled={isStreaming}
          className="inline-flex items-center gap-1.5 font-mono text-xs text-accent-primary hover:underline disabled:opacity-50"
        >
          <span className={isStreaming ? "animate-spin inline-block" : ""}>↻</span>
          <span>Replay stream</span>
        </button>
      </div>

      {/* Query */}
      <div className="p-3 rounded-[6px] bg-bg-sunken border border-border/60 text-xs font-mono text-ink-primary flex items-center justify-between">
        <span>Q: &ldquo;Can I carry my leaves forward?&rdquo;</span>
        <span className="text-gray-warm text-[10px]">route: lookup (42ms)</span>
      </div>

      {/* Streamed Answer with Stamped Citations */}
      <div className="text-xs sm:text-sm leading-relaxed text-ink-primary min-h-[72px]">
        <span>{displayedText}</span>
        {isStreaming && (
          <span className="inline-block w-1.5 h-4 ml-1 bg-accent-hot animate-pulse align-middle" />
        )}

        {showCitations && (
          <span className="inline-block ml-1">
            <CitationChip
              citation={{
                label: "S1",
                chunk_id: "demo_c1",
                text_preview: "Section 2.1: A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year.",
                page: 23,
                section_path: ["Leave Policy", "Carry Forward"],
              }}
              onClick={() => setActiveReceipt("S1")}
            />
            <CitationChip
              citation={{
                label: "S2",
                chunk_id: "demo_c2",
                text_preview: "Rule 63.7.4: Leave settlement on resignation is capped at a monetary reimbursement equivalent to 15 gross working days.",
                is_two_hop: true,
                section_path: ["Rule 63.7.4", "Encashment"],
              }}
              onClick={() => setActiveReceipt("S2")}
            />
          </span>
        )}
      </div>

      {/* Clicked Receipt Callout */}
      <AnimatePresence>
        {activeReceipt && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="p-3 rounded-interactive border border-accent-primary/40 bg-accent-primary/5 text-xs font-mono space-y-1"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-accent-primary">
                [{activeReceipt}] Verified Source Excerpt:
              </span>
              <button
                type="button"
                onClick={() => setActiveReceipt(null)}
                className="text-gray-warm hover:text-ink-primary"
              >
                ✕
              </button>
            </div>
            <p className="font-sans text-xs text-ink-primary leading-relaxed">
              {activeReceipt === "S1"
                ? "2.1 Leave Entitlements · p.23: 'A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year. Any surplus beyond 8 days will automatically lapse on March 31.'"
                : "Rule 63.7.4 Leave Encashment on Resignation · p.45: 'Upon voluntary resignation or formal separation, accrued annual leave encashment is strictly capped at a monetary reimbursement equivalent to 15 gross working days.'"}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* "Nothing Stored" Pledge under demo per §6.6 */}
      <div className="pt-3 border-t border-border/70 grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-[10.5px] text-gray-warm text-center sm:text-left">
        <div className="flex items-center gap-1.5">
          <span className="text-accent-primary font-bold">✓</span>
          <span>Ephemeral RAM only — vanishes on exit</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-accent-primary font-bold">✓</span>
          <span>BYOK kept strictly in client browser</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-accent-primary font-bold">✓</span>
          <span>Zero telemetry on file contents</span>
        </div>
      </div>
    </div>
  );
}

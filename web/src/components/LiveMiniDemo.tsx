"use client";

import React, { useState, useEffect } from "react";
import { CitationChip } from "./CitationChip";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Check, X } from "lucide-react";

export function LiveMiniDemo() {
  const shouldReduceMotion = useReducedMotion();
  const [isStreaming, setIsStreaming] = useState(false);
  const [displayedText, setDisplayedText] = useState("");
  const [showCitations, setShowCitations] = useState(false);
  const [activeReceipt, setActiveReceipt] = useState<string | null>(null);

  const fullText =
    "You can carry forward a maximum of 8 unused annual leave days into the next calendar year. Any surplus beyond 8 days automatically lapses on March 31.";

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

  useEffect(() => {
    runDemoStream();
  }, []);

  return (
    <div className="rounded-interactive border border-border bg-bg-surface p-6 sm:p-8 shadow-md relative overflow-hidden space-y-5">
      {/* Demo box header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border/70">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-status-cache animate-pulse" />
          <span className="font-mono text-xs font-semibold text-ink-primary">
            Sample: Employee Handbook
          </span>
        </div>

        <button
          type="button"
          onClick={runDemoStream}
          disabled={isStreaming}
          className="inline-flex items-center gap-1.5 font-mono text-xs text-accent-primary hover:underline hover:scale-105 active:scale-95 transition-all duration-120 cursor-pointer disabled:opacity-50"
        >
          <span className={isStreaming ? "animate-spin inline-block" : ""}>↻</span>
          <span>Replay</span>
        </button>
      </div>

      {/* Query */}
      <div className="p-3 rounded-[6px] bg-bg-sunken border border-border/60 text-xs font-mono text-ink-primary flex items-center justify-between">
        <span>Q: Can I carry my leaves forward?</span>
        <span className="text-gray-warm text-[10px] tracking-wide">
          searching → re-reading → writing
        </span>
      </div>

      {/* Streamed Answer with Stamped Citations */}
      <div className="text-xs sm:text-sm leading-relaxed text-ink-primary min-h-[56px]">
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
                text_preview:
                  "Section 2.1: A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year.",
                page: 23,
                section_path: ["Leave Policy", "Carry Forward"],
              }}
              onClick={() => setActiveReceipt("S1")}
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
            transition={shouldReduceMotion ? { duration: 0.08 } : { duration: 0.2 }}
            className="p-3 rounded-interactive border border-accent-primary/40 bg-accent-primary/5 text-xs font-mono space-y-1"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-accent-primary">
                [{activeReceipt}] Carry Forward · 2.1 Leave Policy · p.23
              </span>
              <motion.button
                type="button"
                whileHover={shouldReduceMotion ? undefined : { scale: 1.15 }}
                whileTap={shouldReduceMotion ? undefined : { scale: 0.88 }}
                onClick={() => setActiveReceipt(null)}
                className="text-gray-warm hover:text-ink-primary p-0.5 rounded cursor-pointer"
                aria-label="Close quote"
              >
                <X className="w-3 h-3" />
              </motion.button>
            </div>
            <p className="font-sans text-xs text-ink-primary leading-relaxed">
              &ldquo;A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year. Any surplus beyond 8 days will automatically lapse on March 31.&rdquo;
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="pt-3 border-t border-border/70 grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-[10.5px] text-gray-warm text-center sm:text-left">
        <div className="flex items-center gap-1.5">
          <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
          <span>Your file is deleted when you leave</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
          <span>Your own key stays in your browser</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
          <span>We never look at your files</span>
        </div>
      </div>
    </div>
  );
}

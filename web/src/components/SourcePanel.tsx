"use client";

import React, { useEffect, useRef, useState } from "react";
import { Citation } from "@/lib/sse";
import { X, Sparkles, Check, Copy, AlertTriangle } from "lucide-react";

interface SourcePanelProps {
  citations: Citation[];
  activeLabel?: string | null;
  isStaleSession?: boolean;
  onClose: () => void;
  onSelectCitation?: (label: string) => void;
  onReupload?: () => void;
}

export function SourcePanel({
  citations,
  activeLabel,
  isStaleSession = false,
  onClose,
  onSelectCitation,
  onReupload,
}: SourcePanelProps) {
  const [copiedLabel, setCopiedLabel] = useState<string | null>(null);
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Scroll to active citation card when activeLabel changes
  useEffect(() => {
    if (activeLabel && cardRefs.current.has(activeLabel)) {
      const el = cardRefs.current.get(activeLabel);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [activeLabel]);

  // Handle Escape key to close per §4.2
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedLabel(label);
    setTimeout(() => setCopiedLabel(null), 2000);
  };

  const twoHopCount = citations.filter((c) => Boolean(c.is_two_hop)).length;

  return (
    <aside
      role="complementary"
      aria-label="Source receipts panel"
      className="w-full sm:w-[380px] border-l border-border bg-bg-surface h-full flex flex-col shadow-2xl z-30 transition-transform duration-200 ease-out"
    >
      {/* Panel Header per §4 copy freeze */}
      <div className="p-4 border-b border-border flex items-center justify-between flex-shrink-0 bg-bg-surface/80 backdrop-blur-xs">
        <div>
          <h3 className="font-semibold text-sm text-ink-primary font-display flex items-center gap-2">
            The receipts
          </h3>
          <p className="font-mono text-[11px] text-gray-warm mt-0.5">
            {citations.length} passages
            {twoHopCount > 0 ? ` · ${twoHopCount} added by cross-reference` : ""}
          </p>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close receipts panel (Esc)"
          className="p-1.5 rounded-[4px] text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken transition-colors focus:outline-none focus:ring-1 focus:ring-accent-primary"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Stale Session Banner per §4 */}
      {isStaleSession && (
        <div className="m-3 p-3 rounded-interactive border border-danger/30 bg-danger/10 text-xs text-ink-primary space-y-2 animate-fade-in">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-danger flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              This conversation&apos;s gone cold (sessions vanish after 2 hours). Re-upload and I&apos;m right back.
            </p>
          </div>
          {onReupload && (
            <button
              type="button"
              onClick={onReupload}
              className="text-xs font-semibold text-accent-primary hover:underline"
            >
              Re-upload now →
            </button>
          )}
        </div>
      )}

      {/* Source Cards Viewport */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {citations.length === 0 ? (
          /* Empty State per §4 copy freeze */
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-gray-warm">
            <div className="w-12 h-12 rounded-full bg-bg-sunken border border-border flex items-center justify-center mb-3">
              <span className="font-mono text-xs text-ink-ghost">[ ]</span>
            </div>
            <p className="text-xs leading-relaxed max-w-[240px]">
              Ask something first — the receipts will pile up here.
            </p>
          </div>
        ) : (
          citations.map((c) => {
            const isSelected = activeLabel === c.label;
            const isTwoHop = Boolean(c.is_two_hop);
            const isOcr = Boolean(c.is_ocr) || c.label.includes("(OCR)");

            // Chunk label formatting per §4 (no bare § prefix)
            const sectionName = c.section_path?.length ? c.section_path.slice(-1)[0] : "";
            const pageStr = c.page_number || c.page ? `p.${c.page_number || c.page}` : "";
            const chunkLabel = [sectionName ? sectionName : "", pageStr].filter(Boolean).join(" · ");

            return (
              <div
                key={c.label}
                ref={(el) => {
                  if (el) cardRefs.current.set(c.label, el);
                  else cardRefs.current.delete(c.label);
                }}
                onClick={() => onSelectCitation?.(c.label)}
                className={`p-3.5 rounded-interactive border text-xs transition-all duration-120 cursor-pointer ${
                  isSelected
                    ? isTwoHop
                      ? "border-l-[3px] border-l-[#FEBC2E] dark:border-l-[#FCC64B] bg-[#FEBC2E]/5 border-border shadow-sm ring-1 ring-[#FEBC2E]/30"
                      : "border-l-[3px] border-l-accent-cite bg-accent-cite/5 border-border shadow-sm ring-1 ring-accent-cite/30"
                    : "border-border bg-bg-surface hover:bg-bg-sunken/40"
                }`}
              >
                {/* Header line: Mono badge + Label + Copy */}
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-border/60">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span
                      className={`font-mono font-semibold px-1.5 py-0.5 rounded-[4px] text-[11px] ${
                        isTwoHop
                          ? "bg-[#FEBC2E]/20 text-[#8F5B00] dark:text-[#FCC64B]"
                          : isOcr
                          ? "bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200"
                          : "bg-accent-cite/15 text-accent-cite"
                      }`}
                    >
                      [{c.label.replace(/\s*\(OCR\)/gi, "")}]
                    </span>

                    {chunkLabel && (
                      <span className="font-mono text-[11px] text-ink-primary font-medium">
                        {chunkLabel}
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    title="Copy passage quote"
                    onClick={(e) => {
                      e.stopPropagation();
                      copyToClipboard(c.text_preview, c.label);
                    }}
                    className="p-1 rounded-[4px] hover:bg-bg-sunken text-ink-ghost hover:text-ink-primary transition-colors ml-1"
                  >
                    {copiedLabel === c.label ? (
                      <Check className="w-3.5 h-3.5 text-accent-primary" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>

                {/* Two-Hop Tag per §4 */}
                {isTwoHop && (
                  <div className="mb-2.5 p-2 rounded-[4px] bg-[#FEBC2E]/10 border border-[#FEBC2E]/30 text-ink-primary text-[11px] animate-fade-in">
                    <div className="font-semibold font-mono flex items-center gap-1 text-[#8F5B00] dark:text-[#FCC64B] mb-0.5">
                      <Sparkles className="w-3 h-3" />
                      Two-hop cross reference
                    </div>
                    <p className="leading-snug text-gray-warm">
                      {c.added_reason || "pulled in because the answer cites rule 63.7.4"}
                    </p>
                  </div>
                )}

                {/* OCR Tag per §4 */}
                {isOcr && (
                  <div className="mb-2 font-mono text-[10px] text-amber-800 dark:text-amber-300">
                    (OCR — read from a scan, double-check me)
                  </div>
                )}

                {/* Verbatim Passage Excerpt */}
                <div className="text-ink-primary leading-relaxed whitespace-pre-wrap font-sans bg-bg-sunken/50 p-2.5 rounded-[4px] border border-border/50 text-[12.5px]">
                  {c.text_preview}
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}

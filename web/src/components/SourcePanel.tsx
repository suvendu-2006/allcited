"use client";

import React, { useEffect, useRef, useState } from "react";
import { Citation } from "@/lib/sse";
import { X, Check, Copy } from "lucide-react";

interface SourcePanelProps {
  citations: Citation[];
  documentName?: string | null;
  activeLabel?: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectCitation?: (label: string) => void;
}

export function SourcePanel({
  citations,
  documentName,
  activeLabel,
  isOpen,
  onClose,
  onSelectCitation,
}: SourcePanelProps) {
  const [copiedLabel, setCopiedLabel] = useState<string | null>(null);
  const [expandedLabels, setExpandedLabels] = useState<Set<string>>(new Set());
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

  // Handle Escape key to close per §6.9
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedLabel(label);
    setTimeout(() => setCopiedLabel(null), 2000);
  };

  const toggleExpand = (label: string) => {
    setExpandedLabels((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  };

  const twoHopCount = citations.filter((c) => Boolean(c.is_two_hop)).length;

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          aria-hidden="true"
          className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 sm:hidden transition-opacity"
        />
      )}

      {/* Receipts Drawer (360px per §6.9 verbatim) */}
      <aside
        role="complementary"
        aria-label="Source receipts drawer"
        className={`fixed top-0 right-0 bottom-0 w-full sm:w-[360px] bg-bg-surface border-l border-border h-full flex flex-col shadow-2xl z-50 transition-transform duration-200 ease-out select-text ${
          isOpen ? "translate-x-0" : "translate-x-full pointer-events-none"
        }`}
      >
        {/* Panel Header per §6.9: Doc title appears once */}
        <div className="p-4 border-b border-border flex items-center justify-between flex-shrink-0 bg-bg-surface/90 backdrop-blur-sm">
          <div className="min-w-0 pr-2">
            <h3 className="font-semibold text-sm text-ink-primary font-display tracking-tight flex items-center gap-2">
              The receipts
            </h3>
            {documentName && (
              <p
                title={documentName}
                className="font-mono text-[11px] text-gray-warm truncate mt-0.5"
              >
                From: {documentName}
              </p>
            )}
            <p className="font-mono text-[10px] text-ink-ghost mt-0.5">
              {citations.length} {citations.length === 1 ? "passage" : "passages"}
              {twoHopCount > 0 ? ` · ${twoHopCount} cross-referenced` : ""}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close receipts drawer (Esc)"
            className="p-1.5 rounded-[4px] text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken transition-colors focus:outline-none focus:ring-1 focus:ring-accent-primary flex-shrink-0 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Source Cards Viewport */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
          {citations.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-gray-warm">
              <div className="w-12 h-12 rounded-full bg-bg-sunken border border-border flex items-center justify-center mb-3">
                <span className="font-mono text-xs text-ink-ghost">[ ]</span>
              </div>
              <p className="text-xs leading-relaxed max-w-[240px]">
                Click any citation in the answer to view its verified source passage here.
              </p>
            </div>
          ) : (
            citations.map((c) => {
              const cleanLabel = c.label.replace(/\s*\(OCR\)/gi, "").trim();
              const isSelected =
                activeLabel === c.label ||
                activeLabel === cleanLabel ||
                activeLabel === `[${cleanLabel}]`;
              const isTwoHop = Boolean(c.is_two_hop);
              const isOcr = Boolean(c.is_ocr) || c.label.includes("(OCR)");
              const isExpanded = expandedLabels.has(c.label);

              // Section & page label (Doc title appears only once in panel header per §6.9)
              const sectionName = c.section_path?.length ? c.section_path.slice(-1)[0] : "";
              const pageStr = c.page_number || c.page ? `p.${c.page_number || c.page}` : "";
              const chunkLabel = [sectionName, pageStr].filter(Boolean).join(" · ");

              return (
                <div
                  key={c.label}
                  ref={(el) => {
                    if (el) cardRefs.current.set(c.label, el);
                    else cardRefs.current.delete(c.label);
                  }}
                  onClick={() => onSelectCitation?.(c.label)}
                  className={`p-3.5 rounded-r-[6px] text-xs transition-all duration-120 cursor-pointer bg-bg-sunken border-t-0 border-r-0 border-b-0 ${
                    isTwoHop
                      ? isSelected
                        ? "border-l-[3px] border-l-[#FEBC2E] dark:border-l-[#FCC64B] -translate-y-[1px] shadow-sm ring-1 ring-[#FEBC2E]/30"
                        : "border-l-[3px] border-l-[#FEBC2E]/70 dark:border-l-[#FCC64B]/70 hover:border-l-[#FEBC2E]"
                      : isSelected
                      ? "border-l-[3px] border-l-[#CC5A3F] dark:border-l-[#E8765A] -translate-y-[1px] shadow-sm ring-1 ring-[#CC5A3F]/30 dark:ring-[#E8765A]/40"
                      : "border-l-[3px] border-l-[#CC5A3F]/70 dark:border-l-[#E8765A]/70 hover:border-l-[#CC5A3F] dark:hover:border-l-[#E8765A]"
                  }`}
                >
                  {/* Header: [S#] + section · page + copy */}
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-border/40">
                    <div className="flex items-center gap-2 min-w-0 pr-2">
                      <span
                        className={`font-mono font-semibold text-[11px] ${
                          isTwoHop
                            ? "text-[#8F5B00] dark:text-[#FCC64B]"
                            : "text-[#CC5A3F] dark:text-[#E8765A]"
                        }`}
                      >
                        [{cleanLabel}]
                      </span>

                      {chunkLabel && (
                        <span className="font-mono text-[11px] text-gray-warm truncate">
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
                      className="p-1 rounded-[4px] hover:bg-bg-surface text-ink-ghost hover:text-ink-primary transition-colors flex-shrink-0 cursor-pointer"
                    >
                      {copiedLabel === c.label ? (
                        <Check className="w-3.5 h-3.5 text-accent-primary" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  {/* Two-Hop Note per §6.9 */}
                  {isTwoHop && (
                    <div className="mb-2 text-[11px] font-mono text-[#8F5B00] dark:text-[#FCC64B] flex items-center gap-1">
                      <span>✦</span>
                      <span>{c.added_reason || "Cross-referenced passage"}</span>
                    </div>
                  )}

                  {/* OCR Note per §4 */}
                  {isOcr && (
                    <div className="mb-2 font-mono text-[10px] text-amber-800 dark:text-amber-300">
                      (OCR — read from scan)
                    </div>
                  )}

                  {/* Excerpt with 6-line clamp & fade mask per §6.9 (no inner boxes) */}
                  {isExpanded ? (
                    <div>
                      <div className="text-ink-primary font-sans text-[13px] leading-relaxed whitespace-pre-wrap select-text">
                        {c.text_preview}
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleExpand(c.label);
                        }}
                        className="text-xs font-mono text-accent-primary hover:underline cursor-pointer pt-2 block"
                      >
                        Show less ↑
                      </button>
                    </div>
                  ) : (
                    <div>
                      <div
                        className="line-clamp-6 text-ink-primary font-sans text-[13px] leading-relaxed select-text"
                        style={{
                          maskImage:
                            "linear-gradient(to bottom, black 65%, transparent 100%)",
                          WebkitMaskImage:
                            "linear-gradient(to bottom, black 65%, transparent 100%)",
                        }}
                      >
                        {c.text_preview}
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleExpand(c.label);
                        }}
                        className="text-xs font-mono text-accent-primary hover:underline cursor-pointer pt-1.5 block"
                      >
                        Read the full passage →
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
}

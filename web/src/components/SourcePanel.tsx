"use client";

import React, { useEffect, useRef, useState } from "react";
import { Citation } from "@/lib/sse";
import { X, Check, Copy, Sparkles } from "lucide-react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

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
  const shouldReduceMotion = useReducedMotion();

  // Scroll to active citation card when activeLabel changes
  useEffect(() => {
    if (activeLabel && cardRefs.current.has(activeLabel)) {
      const el = cardRefs.current.get(activeLabel);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [activeLabel]);

  // Close on Escape key
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
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="drawer-backdrop"
            onClick={onClose}
            aria-hidden="true"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: shouldReduceMotion ? 0.08 : 0.2 }}
            className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 sm:hidden"
          />
        )}
      </AnimatePresence>

      {/* Receipts Drawer */}
      <motion.aside
        role="complementary"
        aria-label="Source receipts drawer"
        initial={false}
        animate={{
          x: isOpen ? "0%" : "100%",
          opacity: isOpen ? 1 : shouldReduceMotion ? 0 : 1,
        }}
        transition={{
          duration: shouldReduceMotion ? 0.08 : 0.32,
          ease: [0.16, 1, 0.3, 1],
        }}
        className={`fixed top-0 right-0 bottom-0 w-full sm:w-[360px] bg-bg-surface border-l border-border h-full flex flex-col shadow-2xl z-50 select-text ${
          isOpen ? "pointer-events-auto" : "pointer-events-none"
        }`}
      >
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

          <motion.button
            type="button"
            onClick={onClose}
            aria-label="Close receipts drawer (Esc)"
            whileHover={{ rotate: shouldReduceMotion ? 0 : 90, scale: shouldReduceMotion ? 1 : 1.05 }}
            whileTap={{ scale: shouldReduceMotion ? 1 : 0.9 }}
            className="p-1.5 rounded-[4px] text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken transition-colors duration-150 ease-out focus:outline-none focus:ring-1 focus:ring-accent-primary flex-shrink-0 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </motion.button>
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
            citations.map((c, index) => {
              const cleanLabel = c.label.replace(/\s*\(OCR\)/gi, "").trim();
              const isSelected =
                activeLabel === c.label ||
                activeLabel === cleanLabel ||
                activeLabel === `[${cleanLabel}]`;
              const isTwoHop = Boolean(c.is_two_hop);
              const isOcr = Boolean(c.is_ocr) || c.label.includes("(OCR)");
              const isExpanded = expandedLabels.has(c.label);

              // Section & page label
              const sectionName = c.section_path?.length ? c.section_path.slice(-1)[0] : "";
              const pageNum = c.page_number != null ? c.page_number : c.page != null ? c.page : null;
              const pageStr = pageNum != null ? `p.${pageNum}` : "";
              const chunkLabel = [c.doc_name, sectionName, pageStr].filter(Boolean).join(" · ");

              return (
                <motion.div
                  key={c.label}
                  ref={(el) => {
                    if (el) cardRefs.current.set(c.label, el);
                    else cardRefs.current.delete(c.label);
                  }}
                  onClick={() => onSelectCitation?.(c.label)}
                  initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: shouldReduceMotion ? 0.08 : 0.24,
                    delay: shouldReduceMotion ? 0 : index * 0.05,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  whileHover={{ y: shouldReduceMotion ? 0 : -2 }}
                  whileTap={{ scale: shouldReduceMotion ? 1 : 0.99 }}
                  className={`relative p-3.5 rounded-interactive text-xs transition-colors duration-150 ease-out cursor-pointer bg-bg-sunken border-t-0 border-r-0 border-b-0 group overflow-hidden ${
                    isTwoHop
                      ? isSelected
                        ? "border-l-[3px] border-l-status-twohop shadow-sm ring-1 ring-status-twohop/40"
                        : "border-l-[3px] border-l-status-twohop/70 hover:border-l-status-twohop hover:shadow-xs"
                      : isSelected
                      ? "border-l-[3px] border-l-accent-primary shadow-sm ring-1 ring-accent-primary/40"
                      : "border-l-[3px] border-l-accent-primary/70 hover:border-l-accent-primary hover:shadow-xs"
                  }`}
                >
                  {/* Active card left border height grow 0 -> 100% (240ms) */}
                  {isSelected && (
                    <motion.span
                      initial={{ scaleY: 0 }}
                      animate={{ scaleY: 1 }}
                      transition={{ duration: shouldReduceMotion ? 0.08 : 0.24, ease: "easeOut" }}
                      className={`absolute left-0 top-0 bottom-0 w-[3px] origin-top ${
                        isTwoHop ? "bg-status-twohop" : "bg-accent-primary"
                      }`}
                    />
                  )}
                  {/* Header: [S#] + section · page + copy */}
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-border/40">
                    <div className="flex items-center gap-2 min-w-0 pr-2">
                      <span
                        className={`font-mono font-semibold text-[11px] ${
                          isTwoHop
                            ? "text-status-twohop"
                            : "text-accent-primary"
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

                    <motion.button
                      type="button"
                      title="Copy passage quote"
                      whileHover={{ scale: shouldReduceMotion ? 1 : 1.15 }}
                      whileTap={{ scale: shouldReduceMotion ? 1 : 0.85 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        copyToClipboard(c.text_preview, c.label);
                      }}
                      className="p-1 rounded-[4px] hover:bg-bg-surface text-ink-ghost hover:text-ink-primary transition-colors duration-120 flex-shrink-0 cursor-pointer"
                    >
                      {copiedLabel === c.label ? (
                        <Check className="w-3.5 h-3.5 text-accent-primary animate-in zoom-in-75 duration-150" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </motion.button>
                  </div>

                  {isTwoHop && (
                    <div className="mb-2 text-[11px] font-mono text-status-twohop flex items-center gap-1">
                      <Sparkles className="w-3 h-3 flex-shrink-0 transition-transform duration-200 group-hover:rotate-12" />
                      <span>{c.added_reason || "Cross-referenced passage"}</span>
                    </div>
                  )}

                  {isOcr && (
                    <div className="mb-2 font-mono text-[10px] text-amber-800 dark:text-amber-300">
                      (OCR — read from scan)
                    </div>
                  )}

                  {isExpanded ? (
                    <div>
                      <div className="text-ink-primary font-sans text-[13px] leading-relaxed whitespace-pre-wrap select-text animate-fade-in">
                        {c.text_preview}
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleExpand(c.label);
                        }}
                        className="text-xs font-mono text-accent-primary hover:underline cursor-pointer pt-2 flex items-center gap-1 group/btn"
                      >
                        <span>Show less</span>
                        <span className="transition-transform duration-150 group-hover/btn:-translate-y-0.5">↑</span>
                      </button>
                    </div>
                  ) : (
                    <div>
                      <div
                        className={
                          (c.text_preview?.length || 0) > 180
                            ? "line-clamp-6 text-ink-primary font-sans text-[13px] leading-relaxed select-text"
                            : "text-ink-primary font-sans text-[13px] leading-relaxed select-text"
                        }
                        style={
                          (c.text_preview?.length || 0) > 180
                            ? {
                                maskImage:
                                  "linear-gradient(to bottom, black 65%, transparent 100%)",
                                WebkitMaskImage:
                                  "linear-gradient(to bottom, black 65%, transparent 100%)",
                              }
                            : undefined
                        }
                      >
                        {c.text_preview}
                      </div>
                      {(c.text_preview?.length || 0) > 180 && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleExpand(c.label);
                          }}
                          className="text-xs font-mono text-accent-primary hover:underline cursor-pointer pt-1.5 flex items-center gap-1 group/btn"
                        >
                          <span>Read the full passage</span>
                          <span className="transition-transform duration-150 group-hover/btn:translate-x-0.5">→</span>
                        </button>
                      )}
                    </div>
                  )}
                </motion.div>
              );
            })
          )}
        </div>
      </motion.aside>
    </>
  );
}

"use client";

import React, { useEffect, useRef, useState } from "react";
import { Citation } from "@/lib/sse";
import { X, Sparkles, CheckCircle2, Copy, Check } from "lucide-react";

interface SourcePanelProps {
  citations: Citation[];
  activeLabel?: string | null;
  onClose: () => void;
  onSelectCitation?: (label: string) => void;
}

export function SourcePanel({
  citations,
  activeLabel,
  onClose,
  onSelectCitation,
}: SourcePanelProps) {
  const [filterTwoHop, setFilterTwoHop] = useState(false);
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

  // Handle Escape key to close
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

  const filteredCitations = filterTwoHop
    ? citations.filter((c) => Boolean(c.is_two_hop))
    : citations;

  const twoHopCount = citations.filter((c) => Boolean(c.is_two_hop)).length;

  return (
    <aside className="w-80 md:w-96 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 h-full flex flex-col shadow-2xl z-20 animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between flex-shrink-0">
        <div>
          <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            Verified Source Receipts
          </h3>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
            {citations.length} cited {citations.length === 1 ? "passage" : "passages"} from document
          </p>
        </div>

        <button
          type="button"
          onClick={onClose}
          title="Close source panel (Esc)"
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Filter Tabs */}
      {twoHopCount > 0 && (
        <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-950/50 flex gap-1.5 text-xs">
          <button
            type="button"
            onClick={() => setFilterTwoHop(false)}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
              !filterTwoHop
                ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-xs border border-slate-200 dark:border-slate-700"
                : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            All Sources ({citations.length})
          </button>
          <button
            type="button"
            onClick={() => setFilterTwoHop(true)}
            className={`px-2.5 py-1 rounded-md font-medium flex items-center gap-1 transition-colors cursor-pointer ${
              filterTwoHop
                ? "bg-purple-100 dark:bg-purple-950 text-purple-800 dark:text-purple-300 shadow-xs border border-purple-300 dark:border-purple-800"
                : "text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/30"
            }`}
          >
            <Sparkles className="w-3 h-3" />
            Two-Hop Additions ({twoHopCount})
          </button>
        </div>
      )}

      {/* Source Cards Viewport */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {filteredCitations.map((c) => {
          const isSelected = activeLabel === c.label;
          const isTwoHop = Boolean(c.is_two_hop);
          const isOcr = Boolean(c.is_ocr) || c.label.includes("(OCR)");

          return (
            <div
              key={c.label}
              ref={(el) => {
                if (el) cardRefs.current.set(c.label, el);
                else cardRefs.current.delete(c.label);
              }}
              onClick={() => onSelectCitation?.(c.label)}
              className={`p-3.5 rounded-xl border text-xs transition-all cursor-pointer ${
                isSelected
                  ? isOcr
                    ? "border-amber-500 ring-2 ring-amber-500/20 bg-amber-50/60 dark:bg-amber-950/30 shadow-md"
                    : isTwoHop
                    ? "border-purple-500 ring-2 ring-purple-500/20 bg-purple-50/60 dark:bg-purple-950/30 shadow-md"
                    : "border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/60 dark:bg-blue-950/30 shadow-md"
                  : isOcr
                  ? "border-amber-200 dark:border-amber-900/60 bg-amber-50/20 dark:bg-amber-950/10 hover:border-amber-300"
                  : isTwoHop
                  ? "border-purple-200 dark:border-purple-900/60 bg-purple-50/20 dark:bg-purple-950/10 hover:border-purple-300"
                  : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              {/* Card Meta Bar */}
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-1.5">
                  <span
                    className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                      isOcr
                        ? "bg-amber-100 dark:bg-amber-900/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-700"
                        : isTwoHop
                        ? "bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-700"
                        : "bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700"
                    }`}
                  >
                    [{c.label}]
                  </span>
                  {isOcr && (
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                      OCR
                    </span>
                  )}
                  <span className="font-mono text-[10px] text-slate-400">
                    {c.chunk_id.replace(/^sess_[^_]+_/, "")}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400">
                  {c.page && <span>Page {c.page}</span>}
                  <button
                    type="button"
                    title="Copy excerpt"
                    onClick={(e) => {
                      e.stopPropagation();
                      copyToClipboard(c.text_preview, c.label);
                    }}
                    className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    {copiedLabel === c.label ? (
                      <Check className="w-3 h-3 text-emerald-500" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
              </div>

              {/* Section Hierarchy */}
              {c.section_path && c.section_path.length > 0 && (
                <div className="mb-2 text-[11px] font-medium text-slate-600 dark:text-slate-300 flex items-center gap-1 truncate">
                  <span className="text-slate-400">§</span>
                  <span>{c.section_path.join(" > ")}</span>
                </div>
              )}

              {/* Two-Hop Distinction Badge */}
              {isTwoHop && (
                <div className="mb-2.5 p-2 rounded-lg bg-purple-100/80 dark:bg-purple-950/60 border border-purple-200 dark:border-purple-800/60 text-purple-900 dark:text-purple-200 text-[11px]">
                  <div className="font-semibold flex items-center gap-1 mb-0.5 text-purple-800 dark:text-purple-300">
                    <Sparkles className="w-3 h-3" />
                    Two-Hop Cross-Reference
                  </div>
                  <p className="leading-snug">
                    {c.added_reason || "Referenced definition added to verify citation."}
                  </p>
                </div>
              )}

              {/* Text Excerpt */}
              <div className="text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-wrap font-sans bg-slate-50 dark:bg-slate-950/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800/60">
                {c.text_preview}
              </div>
            </div>
          );
        })}

        {filteredCitations.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            No source passages matching filter.
          </div>
        )}
      </div>
    </aside>
  );
}

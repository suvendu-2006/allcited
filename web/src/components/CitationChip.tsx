"use client";

import React, { useState } from "react";
import { Citation } from "@/lib/sse";
import { Sparkles } from "lucide-react";

interface CitationChipProps {
  citation: Citation;
  isPinned?: boolean;
  onClick?: (citation: Citation) => void;
}

export function CitationChip({ citation, isPinned = false, onClick }: CitationChipProps) {
  const [isHovered, setIsHovered] = useState(false);

  const isTwoHop = Boolean(citation.is_two_hop);
  const isOcr = Boolean(citation.is_ocr) || citation.label.includes("(OCR)");

  // Clean label (strip (OCR) if present for clean display)
  const cleanLabel = citation.label.replace(/\s*\(OCR\)/gi, "").trim();

  // Section or page snippet
  const pageNum = citation.page_number != null ? citation.page_number : citation.page != null ? citation.page : null;
  const sectionText = citation.section_path?.length
    ? citation.section_path.slice(-1)[0]
    : pageNum != null
    ? `p.${pageNum}`
    : "";

  return (
    <span className="relative inline-block mx-0.5 align-baseline group">
      <button
        type="button"
        onClick={() => onClick?.(citation)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`inline-flex items-center gap-1 px-1.5 py-0.5 font-mono text-[12px] font-medium rounded-[4px] cursor-pointer transition-all duration-150 ease-out select-none motion-reduce:transform-none ${
          isHovered ? "-translate-y-0.5 shadow-xs" : "translate-y-0"
        } ${
          isPinned
            ? "scale-105 ring-2 ring-accent-cite shadow-sm"
            : "active:scale-95 active:translate-y-0"
        } ${
          isTwoHop
            ? "bg-status-twohop/15 dark:bg-status-twohop/20 text-status-twohop border border-status-twohop/40 hover:ring-1 hover:ring-status-twohop/30"
            : isOcr
            ? "bg-amber-100/70 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-800 hover:ring-1 hover:ring-amber-500/30"
            : "bg-accent-cite/10 dark:bg-accent-cite/20 text-accent-cite dark:text-accent-cite border border-accent-cite/30 dark:border-accent-cite/40 hover:ring-1 hover:ring-accent-cite/30"
        }`}
      >
        {isTwoHop && (
          <Sparkles className="w-2.5 h-2.5 flex-shrink-0 transition-transform duration-200 ease-out group-hover:rotate-12 group-hover:scale-110" />
        )}
        <span className="relative">
          [{cleanLabel}]
          {/* Animated underline left to right on hover */}
          <span
            className={`absolute bottom-0 left-0 h-[1px] bg-current transition-all duration-150 ease-out ${
              isHovered ? "w-full" : "w-0"
            }`}
          />
        </span>

        {sectionText && (
          <span className="text-[10px] opacity-75 hidden sm:inline max-w-[80px] truncate transition-opacity duration-150 group-hover:opacity-100">
            {sectionText}
          </span>
        )}

        {isOcr && (
          <span className="text-[9px] font-bold uppercase tracking-wider px-1 rounded bg-amber-200 dark:bg-amber-900/60 text-amber-900 dark:text-amber-200 transition-transform duration-150 group-hover:scale-105">
            OCR
          </span>
        )}
      </button>
    </span>
  );
}

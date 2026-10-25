"use client";

import React, { useState } from "react";
import { Citation } from "@/lib/sse";

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
  const sectionText = citation.section_path?.length
    ? citation.section_path.slice(-1)[0]
    : citation.page_number
    ? `p.${citation.page_number}`
    : "";

  return (
    <span className="relative inline-block mx-0.5 align-baseline group">
      <button
        type="button"
        onClick={() => onClick?.(citation)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`inline-flex items-center gap-1 px-1.5 py-0.5 font-mono text-[12px] font-medium rounded-[4px] cursor-pointer transition-all duration-120 select-none ${
          isHovered ? "-translate-y-[1px]" : "translate-y-0"
        } ${
          isPinned
            ? "scale-105 ring-2 ring-accent-cite shadow-sm"
            : "active:scale-95"
        } ${
          isTwoHop
            ? "bg-[#FEBC2E]/15 dark:bg-[#FCC64B]/20 text-[#8F5B00] dark:text-[#FCC64B] border border-[#FEBC2E]/40"
            : isOcr
            ? "bg-amber-100/70 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-800"
            : "bg-accent-cite/10 dark:bg-accent-cite/20 text-accent-cite dark:text-accent-cite border border-accent-cite/30 dark:border-accent-cite/40"
        }`}
      >
        {isTwoHop && <span className="text-[10px] flex-shrink-0">✦</span>}
        <span className="relative">
          [{cleanLabel}]
          {/* Animated underline left to right on hover */}
          <span
            className={`absolute bottom-0 left-0 h-[1px] bg-current transition-all duration-120 ${
              isHovered ? "w-full" : "w-0"
            }`}
          />
        </span>

        {sectionText && (
          <span className="text-[10px] opacity-75 hidden sm:inline max-w-[80px] truncate">
            {sectionText}
          </span>
        )}

        {isOcr && (
          <span className="text-[9px] font-bold uppercase tracking-wider px-1 rounded bg-amber-200 dark:bg-amber-900/60 text-amber-900 dark:text-amber-200">
            OCR
          </span>
        )}
      </button>
    </span>
  );
}

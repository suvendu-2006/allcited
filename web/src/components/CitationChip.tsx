"use client";

import React, { useState } from "react";
import { Citation } from "@/lib/sse";
import { Link2, Sparkles } from "lucide-react";

interface CitationChipProps {
  citation: Citation;
  onClick?: (citation: Citation) => void;
}

export function CitationChip({ citation, onClick }: CitationChipProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const isTwoHop = Boolean(citation.is_two_hop);
  const isOcr = Boolean(citation.is_ocr) || citation.label.includes("(OCR)");
  const sectionText = citation.section_path?.length ? citation.section_path.join(" > ") : "";

  return (
    <span className="relative inline-block mx-0.5 align-baseline">
      <button
        type="button"
        onClick={() => onClick?.(citation)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 text-xs font-semibold rounded cursor-pointer transition-colors ${
          isOcr
            ? "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700 hover:bg-amber-200"
            : isTwoHop
            ? "bg-purple-100 dark:bg-purple-950/60 text-purple-750 dark:text-purple-300 border border-purple-300 dark:border-purple-700 hover:bg-purple-200"
            : "bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-300 dark:border-blue-700 hover:bg-blue-200"
        }`}
      >
        {isTwoHop ? <Sparkles className="w-2.5 h-2.5" /> : <Link2 className="w-2.5 h-2.5" />}
        <span>[{citation.label}]</span>
        {isOcr && !citation.label.includes("(OCR)") && (
          <span className="text-[9px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-300 bg-amber-200 dark:bg-amber-900/80 px-1 py-0.2 rounded ml-0.5">
            OCR
          </span>
        )}
      </button>

      {showTooltip && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-2.5 text-xs bg-slate-900 text-slate-100 rounded-lg shadow-xl border border-slate-700 pointer-events-none animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-800 font-medium">
            <span className="text-blue-400 flex items-center gap-1">
              {isTwoHop ? <Sparkles className="w-3 h-3 text-purple-400" /> : <Link2 className="w-3 h-3" />}
              Source {citation.label}
            </span>
            {citation.page && <span className="text-slate-400">Page {citation.page}</span>}
          </div>

          {sectionText && (
            <p className="text-[11px] text-slate-400 mb-1 line-clamp-1 italic">
              {sectionText}
            </p>
          )}

          {isTwoHop && citation.added_reason && (
            <p className="text-[11px] text-purple-300 mb-1.5 bg-purple-950/50 p-1 rounded border border-purple-900/60">
              {citation.added_reason}
            </p>
          )}

          <p className="text-slate-200 line-clamp-3 leading-relaxed">
            {citation.text_preview}
          </p>

          <div className="absolute left-1/2 -bottom-1 -translate-x-1/2 w-2 h-2 bg-slate-900 border-r border-b border-slate-700 rotate-45" />
        </div>
      )}
    </span>
  );
}

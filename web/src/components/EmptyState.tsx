"use client";

import React from "react";
import { CitationChip } from "./CitationChip";
import { FileQuestion, ArrowRight } from "lucide-react";

interface EmptyStateProps {
  onSelectSampleQuestion: (question: string) => void;
  isGuest?: boolean;
}

const SAMPLE_QUESTIONS = [
  "What can I carry forward?",
  "What does rule 63.7.4 actually say?",
  "Summarize section 4 like I'm new",
];

export function EmptyState({ onSelectSampleQuestion, isGuest }: EmptyStateProps) {
  return (
    <div className="dot-grid rounded-interactive border border-border/60 p-8 sm:p-12 my-6 text-center relative overflow-hidden bg-bg-surface/30">
      <div className="mb-6 flex justify-center">
        <div className="animate-bounce [animation-duration:6s] inline-block shadow-sm">
          <CitationChip
            citation={{
              label: "S1",
              chunk_id: "demo-chunk-1",
              text_preview: "A maximum of 8 unused annual leave days may be carried forward...",
              page: 23,
              section_path: ["Leave Policy", "Carry Forward"],
            }}
          />
        </div>
      </div>

      <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-ink-primary font-display mb-2">
        Nothing here yet. That&apos;s fixable.
      </h2>
      <p className="text-sm text-gray-warm max-w-lg mx-auto mb-4 leading-relaxed">
        Drop a document anywhere on this page, or try one of these on the sample handbook:
      </p>

      {isGuest && (
        <p className="font-sans text-xs text-ink-ghost max-w-md mx-auto mb-6 leading-relaxed">
          Guest mode: nothing is saved. Sign in anytime to keep documents.
        </p>
      )}

      <div className="flex flex-wrap items-center justify-center gap-2 max-w-xl mx-auto">
        {SAMPLE_QUESTIONS.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => onSelectSampleQuestion(question)}
            className="group inline-flex items-center gap-2 px-3.5 py-2 rounded-interactive border border-border bg-bg-surface hover:bg-bg-sunken text-xs font-medium text-ink-primary shadow-xs transition-all duration-120 hover:border-accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary"
          >
            <FileQuestion className="w-3.5 h-3.5 text-accent-primary opacity-70 group-hover:opacity-100" />
            <span>{question}</span>
            <ArrowRight className="w-3 h-3 text-ink-ghost transition-transform duration-120 group-hover:translate-x-1 group-hover:text-accent-primary" />
          </button>
        ))}
      </div>
    </div>
  );
}

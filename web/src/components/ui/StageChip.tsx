"use client";

import React from "react";

export type StageType = "searching" | "reranking" | "twohop" | "caching" | "composing";

interface StageChipProps {
  stage: StageType;
  label: string;
  isActive?: boolean;
  isCompleted?: boolean;
}

export function StageChip({
  stage,
  label,
  isActive = false,
  isCompleted = false,
}: StageChipProps) {
  // Styles per stage according to §3.1 & §3.2
  const getStageStyle = () => {
    switch (stage) {
      case "searching":
        return isActive
          ? "border-status-retrieve bg-status-retrieve/15 text-ink-primary dark:text-status-retrieve"
          : "border-transparent text-ink-ghost";
      case "reranking":
        return isActive
          ? "border-status-rerank bg-status-rerank/15 text-ink-primary dark:text-status-rerank"
          : "border-transparent text-ink-ghost";
      case "twohop":
        return isActive
          ? "border-status-twohop bg-status-twohop/15 text-ink-primary dark:text-status-twohop"
          : "border-transparent text-ink-ghost";
      case "caching":
        return isActive
          ? "border-status-cache bg-status-cache/15 text-ink-primary dark:text-status-cache"
          : "border-transparent text-ink-ghost";
      case "composing":
        return isActive
          ? "border-accent-primary bg-accent-primary/15 text-ink-primary dark:text-accent-primary"
          : "border-transparent text-ink-ghost";
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 font-mono text-[11.5px] rounded-[4px] border transition-all duration-200 ${getStageStyle()} ${
        isCompleted ? "opacity-40" : ""
      } ${isActive ? "scale-[1.02] shadow-2xs" : "scale-100"}`}
    >
      {isActive && (
        <span className="flex items-center gap-0.5">
          <span className="w-1 h-1 rounded-full bg-current animate-pulse" />
          <span className="w-1 h-1 rounded-full bg-current animate-pulse [animation-delay:150ms]" />
          <span className="w-1 h-1 rounded-full bg-current animate-pulse [animation-delay:300ms]" />
        </span>
      )}
      <span>{label}</span>
    </span>
  );
}

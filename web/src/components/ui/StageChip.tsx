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
          ? "border-[#2D62FF] dark:border-[#6E97FF] bg-[#2D62FF]/15 dark:bg-[#6E97FF]/25 text-ink-primary dark:text-[#6E97FF]"
          : "border-transparent text-ink-ghost";
      case "reranking":
        return isActive
          ? "border-[#FF5F57] dark:border-[#FF8177] bg-[#FF5F57]/15 dark:bg-[#FF8177]/25 text-ink-primary dark:text-[#FF8177]"
          : "border-transparent text-ink-ghost";
      case "twohop":
        return isActive
          ? "border-[#FEBC2E] dark:border-[#FCC64B] bg-[#FEBC2E]/15 dark:bg-[#FCC64B]/25 text-ink-primary dark:text-[#FCC64B]"
          : "border-transparent text-ink-ghost";
      case "caching":
        return isActive
          ? "border-[#28C840] dark:border-[#5AD46F] bg-[#28C840]/15 dark:bg-[#5AD46F]/25 text-ink-primary dark:text-[#5AD46F]"
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
      }`}
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

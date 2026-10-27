"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useDocumentVisibility } from "@/lib/useVisibility";

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
  const shouldReduceMotion = useReducedMotion();
  const isVisible = useDocumentVisibility();

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
    <motion.span
      animate={{
        opacity: isCompleted ? 0.45 : 1,
        scale: isActive && !shouldReduceMotion ? 1.02 : 1,
      }}
      transition={{ duration: shouldReduceMotion ? 0.08 : 0.2 }}
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 font-mono text-[11.5px] rounded-[4px] border transition-colors duration-200 ${getStageStyle()}`}
    >
      {isActive && (
        <span className="flex items-center gap-1">
          <motion.span
            animate={
              !shouldReduceMotion && isVisible
                ? { scale: [1, 1.3, 1] }
                : { scale: 1 }
            }
            transition={{
              duration: 1.2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className="w-1.5 h-1.5 rounded-full bg-current"
          />
        </span>
      )}
      <span>{label}</span>
    </motion.span>
  );
}

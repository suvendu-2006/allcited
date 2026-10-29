"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Square, Sparkles } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { useDocumentVisibility } from "@/lib/useVisibility";

interface ComposerProps {
  onSend: (message: string) => void;
  onAbort?: () => void;
  isGenerating?: boolean;
  disabled?: boolean;
  placeholder?: string;
  isPrecisionMode?: boolean;
  onTogglePrecision?: (enabled: boolean) => void;
  isPro?: boolean;
}

export function Composer({
  onSend,
  onAbort,
  isGenerating = false,
  disabled = false,
  placeholder = "Ask your document anything…",
  isPrecisionMode = false,
  onTogglePrecision,
  isPro = false,
}: ComposerProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const shouldReduceMotion = useReducedMotion();
  const isVisible = useDocumentVisibility();

  useEffect(() => {
    if (!isGenerating && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isGenerating]);

  // Auto-resize textarea up to 160px
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isGenerating || disabled) return;
    onSend(trimmed);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const canSend = Boolean(input.trim()) && !disabled && !isGenerating;

  return (
    <motion.div
      animate={{
        borderColor: isFocused ? "var(--accent-primary)" : "var(--border)",
        boxShadow: isFocused ? "0 0 0 3px rgba(166, 54, 47, 0.15)" : "0 1px 2px rgba(0, 0, 0, 0.04)",
      }}
      transition={{ duration: shouldReduceMotion ? 0.08 : 0.2 }}
      className={`relative border border-border rounded-interactive bg-bg-surface p-2.5 ${
        disabled ? "opacity-60 transition-opacity duration-120 cursor-not-allowed" : ""
      }`}
    >
      <textarea
        ref={textareaRef}
        rows={1}
        value={input}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        disabled={disabled}
        placeholder={placeholder}
        className="w-full resize-none bg-transparent px-2 py-1 text-sm outline-none text-ink-primary placeholder:text-ink-ghost max-h-40 min-h-[38px] leading-relaxed"
      />

      <div className="flex items-center justify-between pt-1 px-1">
        <div className="flex items-center gap-2">
          {onTogglePrecision && (
            <motion.button
              type="button"
              onClick={() => onTogglePrecision(!isPrecisionMode)}
              aria-label="Toggle Precision Mode"
              title={
                isPrecisionMode
                  ? "Precision Mode ON: deep neural re-ranking across candidate passages"
                  : isPro
                  ? "Precision Mode: deep neural re-ranking (Pro enabled)"
                  : "Precision Mode: deep neural re-ranking"
              }
              whileHover={{ scale: shouldReduceMotion ? 1 : 1.04 }}
              whileTap={{ scale: shouldReduceMotion ? 1 : 0.95 }}
              transition={{ type: "spring", stiffness: 420, damping: 32 }}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono transition-colors duration-120 cursor-pointer ${
                isPrecisionMode
                  ? "bg-accent-primary/15 text-accent-primary border border-accent-primary/40 font-medium shadow-xs"
                  : "text-gray-warm hover:text-ink-primary border border-transparent hover:border-border"
              }`}
            >
              <Sparkles className="w-3 h-3 text-accent-primary" />
              <span>Precision</span>
              {isPrecisionMode && <span className="text-[9px] font-bold">ON</span>}
            </motion.button>
          )}
        </div>

        {isGenerating ? (
          <motion.button
            type="button"
            onClick={onAbort}
            whileHover={{ scale: shouldReduceMotion ? 1 : 1.04 }}
            whileTap={{ scale: shouldReduceMotion ? 1 : 0.95 }}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-[6px] bg-danger text-white text-xs font-medium hover:brightness-110 shadow-xs cursor-pointer"
          >
            <Square className="w-3 h-3 fill-current animate-pulse" />
            <span>Stop answering</span>
          </motion.button>
        ) : (
          <motion.button
            type="button"
            onClick={handleSubmit}
            disabled={!input.trim() || disabled}
            aria-label="Send question"
            whileHover={canSend ? { scale: shouldReduceMotion ? 1 : 1.05 } : undefined}
            whileTap={canSend ? { scale: shouldReduceMotion ? 1 : 0.96 } : undefined}
            animate={
              canSend && !shouldReduceMotion && isVisible
                ? { scale: [1, 1.02, 1] }
                : { scale: 1 }
            }
            transition={
              canSend && !shouldReduceMotion && isVisible
                ? { duration: 3, repeat: Infinity, ease: "easeInOut" }
                : { duration: 0.15 }
            }
            className="group w-8 h-8 rounded-interactive bg-accent-primary text-primary-foreground flex items-center justify-center hover:brightness-95 hover:shadow-sm disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
          >
            <ArrowUp className="w-4 h-4 transition-transform duration-150 ease-out group-hover:-translate-y-0.5" />
          </motion.button>
        )}
      </div>
    </motion.div>
  );
}

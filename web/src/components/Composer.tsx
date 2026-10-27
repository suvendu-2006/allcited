"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Square, Sparkles } from "lucide-react";

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

  return (
    <div
      className={`relative border border-border rounded-interactive bg-bg-surface shadow-xs transition-all duration-120 p-2.5 ${
        isFocused
          ? "border-accent-primary ring-2 ring-accent-primary/20"
          : "hover:border-border"
      } ${disabled ? "opacity-60 transition-opacity duration-120 cursor-not-allowed" : ""}`}
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
            <button
              type="button"
              onClick={() => onTogglePrecision(!isPrecisionMode)}
              aria-label="Toggle Precision Mode"
              title={
                isPro
                  ? "Precision Mode: reranks 50 passages before answering"
                  : "Precision Mode (Pro feature: reranks 50 passages)"
              }
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono transition-all duration-120 cursor-pointer ${
                isPrecisionMode
                  ? "bg-accent-primary/15 text-accent-primary border border-accent-primary/40 font-medium shadow-xs"
                  : "text-gray-warm hover:text-ink-primary border border-transparent hover:border-border"
              }`}
            >
              <Sparkles className="w-3 h-3 text-accent-primary" />
              <span>Precision</span>
              {isPrecisionMode && <span className="text-[9px] font-bold">ON</span>}
            </button>
          )}

          <span
            className={`font-mono text-[11px] text-gray-warm transition-opacity duration-120 ${
              isFocused ? "opacity-100" : "opacity-0 sm:opacity-80"
            }`}
          >
            ↵ to send · ⇧↵ for a new line
          </span>
        </div>

        {isGenerating ? (
          <button
            type="button"
            onClick={onAbort}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-[6px] bg-danger text-white text-xs font-medium hover:brightness-110 hover:scale-105 active:scale-95 transition-all duration-150 shadow-xs cursor-pointer motion-reduce:transform-none"
          >
            <Square className="w-3 h-3 fill-current animate-pulse" />
            <span>Stop answering</span>
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!input.trim() || disabled}
            aria-label="Send question"
            className="group w-8 h-8 rounded-interactive bg-accent-primary text-primary-foreground flex items-center justify-center hover:brightness-95 hover:scale-105 hover:shadow-sm active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none transition-all duration-150 motion-reduce:transform-none cursor-pointer"
          >
            <ArrowUp className="w-4 h-4 transition-transform duration-150 ease-out group-hover:-translate-y-0.5" />
          </button>
        )}
      </div>
    </div>
  );
}

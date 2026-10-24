"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Square } from "lucide-react";

interface ComposerProps {
  onSend: (message: string) => void;
  onAbort?: () => void;
  isGenerating?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function Composer({
  onSend,
  onAbort,
  isGenerating = false,
  disabled = false,
  placeholder = "Ask anything grounded in your document...",
}: ComposerProps) {
  const [input, setInput] = useState("");
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
    <div className="relative border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 shadow-sm focus-within:border-blue-500 dark:focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all p-2">
      <textarea
        ref={textareaRef}
        rows={1}
        value={input}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? "Please upload or select a document first..." : placeholder}
        className="w-full resize-none bg-transparent px-3 py-1.5 text-sm outline-none text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 max-h-40 min-h-[38px]"
      />

      <div className="flex items-center justify-between pt-1 px-1">
        <span className="text-[11px] text-slate-400 dark:text-slate-500">
          Press <kbd className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">Shift+Enter</kbd> for line break
        </span>

        {isGenerating ? (
          <button
            type="button"
            onClick={onAbort}
            title="Stop generation"
            className="w-8 h-8 rounded-full bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 flex items-center justify-center hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors shadow-sm cursor-pointer"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!input.trim() || disabled}
            title="Send query"
            className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600 transition-colors shadow-sm cursor-pointer disabled:cursor-not-allowed"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

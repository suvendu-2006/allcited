"use client";

import React from "react";
import { useTheme } from "@/lib/theme";
import { ThemeToggleLogo } from "./ThemeToggleLogo";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={(e) => toggleTheme(e)}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      className={`relative inline-flex items-center justify-center w-9 h-9 rounded-interactive border border-border bg-bg-surface hover:bg-bg-sunken text-ink-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary cursor-pointer ${className}`}
    >
      <ThemeToggleLogo theme={theme} />
    </button>
  );
}

"use client";

import React from "react";
import { useTheme } from "@/lib/theme";
import { ThemeToggleLogo } from "./ThemeToggleLogo";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={() => toggleTheme()}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      className={`relative inline-flex items-center justify-center p-0.5 rounded-full text-ink-primary hover:opacity-80 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary cursor-pointer active:scale-95 ${className}`}
    >
      <ThemeToggleLogo theme={theme} />
    </button>
  );
}

"use client";

import React from "react";
import { Sun, Moon } from "lucide-react";
import { motion } from "framer-motion";

interface ThemeToggleLogoProps {
  theme: "light" | "dark";
  className?: string;
}

/**
 * ThemeToggleLogo Slot v2 (§6.5)
 *
 * Designed as a one-file swap for the owner's custom toggle-icon reference.
 * Currently renders an accessible morphing sun/moon emblem with a 90° rotation on click.
 */
export function ThemeToggleLogo({ theme, className = "" }: ThemeToggleLogoProps) {
  const isDark = theme === "dark";

  return (
    <motion.div
      key={theme}
      initial={{ rotate: -90, scale: 0.85, opacity: 0 }}
      animate={{ rotate: 0, scale: 1, opacity: 1 }}
      exit={{ rotate: 90, scale: 0.85, opacity: 0 }}
      transition={{ type: "spring", stiffness: 420, damping: 28 }}
      className={`relative flex items-center justify-center ${className}`}
    >
      {isDark ? (
        <Sun className="w-4 h-4 text-accent-hot transition-transform hover:rotate-45" />
      ) : (
        <Moon className="w-4 h-4 text-accent-primary transition-transform hover:-rotate-12" />
      )}
    </motion.div>
  );
}

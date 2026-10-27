"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";

interface ThemeToggleLogoProps {
  theme: "light" | "dark";
  className?: string;
}

/**
 * Circular Orbit Dial Theme Toggle Logo
 * Modeled after the Awwwards Site of the Day reference:
 * - Minimalist wire circle perimeter track.
 * - Orbiting satellite dot that smoothly translates and rotates along the orbit
 *   when toggling between light (sun) and dark (moon) phases.
 */
export function ThemeToggleLogo({ theme, className = "" }: ThemeToggleLogoProps) {
  const isDark = theme === "dark";
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      className={`relative w-8 h-8 rounded-full border border-ink-primary/60 dark:border-ink-primary/70 flex items-center justify-center transition-colors duration-200 select-none ${className}`}
      aria-hidden="true"
    >
      {/* Orbiting Satellite Dot */}
      <motion.div
        className="absolute inset-0 flex items-center justify-center pointer-events-none"
        animate={{
          rotate: isDark ? 210 : 35,
        }}
        transition={
          shouldReduceMotion
            ? { duration: 0.08 }
            : {
                type: "spring",
                stiffness: 280,
                damping: 24,
              }
        }
      >
        {/* The dot positioned near the perimeter */}
        <div
          className={`w-1.5 h-1.5 rounded-full border border-current ${
            isDark
              ? "bg-accent-primary border-accent-primary shadow-[0_0_6px_rgba(232,118,90,0.8)]"
              : "bg-transparent border-ink-primary"
          }`}
          style={{
            transform: "translateY(-9px)",
          }}
        />
      </motion.div>
    </div>
  );
}

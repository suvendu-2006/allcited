"use client";

import React, { useState, useEffect } from "react";
import { useTheme } from "@/lib/theme";

interface InteractiveOrbitClockProps {
  className?: string;
}

/**
 * Live Time Clock & Orbit Theme Toggle
 * - Displays accurate real-time live local time (no simulated time scrubbing).
 * - Clicking the circular orbit dial cleanly toggles between Light and Dark mode.
 * - Satellite dot smoothly transitions along the wire orbit between day and night.
 */
export function InteractiveOrbitClock({ className = "" }: InteractiveOrbitClockProps) {
  const { theme, toggleTheme } = useTheme();

  // Real local live time
  const [time, setTime] = useState<{ h: number; m: number }>({
    h: 12,
    m: 0,
  });

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime({ h: now.getHours(), m: now.getMinutes() });
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const formattedHours = String(time.h).padStart(2, "0");
  const formattedMinutes = String(time.m).padStart(2, "0");
  const isDark = theme === "dark";

  // Satellite dot position along circular perimeter (radius = 12.5px)
  // Light mode (day): Top (0, -12.5px)
  // Dark mode (night): Bottom (0, 12.5px)
  const dotY = isDark ? 12.5 : -12.5;

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Real Live Local Time Digits */}
      <div className="flex flex-col text-right leading-tight">
        <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-gray-warm">
          LIVE TIME
        </span>

        <div className="font-mono text-[11px] font-bold text-ink-primary tracking-wider tabular-nums flex items-center justify-end gap-1">
          <span>{formattedHours}</span>
          <span className="opacity-70 animate-pulse">.</span>
          <span>{formattedMinutes}</span>
        </div>
      </div>

      {/* Circular Orbit Dial (Clean Minimalist Wire Circle Theme Toggle) */}
      <button
        type="button"
        onClick={() => toggleTheme()}
        aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
        title={`Click to switch to ${isDark ? "light" : "dark"} theme`}
        className="relative w-8 h-8 rounded-full border border-ink-primary/25 dark:border-ink-primary/35 bg-transparent flex items-center justify-center transition-all duration-200 cursor-pointer hover:border-accent-primary/60 hover:scale-105 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary"
      >
        {/* Orbiting Satellite Dot */}
        <div
          className="absolute w-2.5 h-2.5 rounded-full pointer-events-none transition-transform duration-300 ease-out flex items-center justify-center"
          style={{
            transform: `translate3d(0px, ${dotY}px, 0)`,
          }}
        >
          <div
            className={`w-2 h-2 rounded-full border transition-all duration-300 ${
              isDark
                ? "bg-accent-primary border-accent-primary shadow-[0_0_6px_rgba(232,118,90,0.85)] scale-110"
                : "bg-ink-primary border-bg-surface shadow-[0_0_4px_rgba(26,25,24,0.4)] scale-100"
            }`}
          />
        </div>
      </button>
    </div>
  );
}

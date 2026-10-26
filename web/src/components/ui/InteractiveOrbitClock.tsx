"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useTheme } from "@/lib/theme";
import { executeThemeTransition } from "../ThemeTransitionOverlay";

interface InteractiveOrbitClockProps {
  className?: string;
}

/**
 * Interactive Orbit Theme Dial
 * - 60fps/120fps hardware-accelerated draggable satellite dot on circular wire orbit.
 * - Minimalist, pure circular orbit dial without text clutter (no time numbers, no label).
 * - Dragging around the circle switches theme:
 *     Top (0°) / Day -> Light Theme
 *     Bottom (180°) / Night -> Dark Theme
 * - Direct click toggles between light and dark themes with the equilateral triangle transition.
 */
export function InteractiveOrbitClock({ className = "" }: InteractiveOrbitClockProps) {
  const { theme, setTheme } = useTheme();
  const dialRef = useRef<HTMLButtonElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  const [currentAngle, setCurrentAngle] = useState<number>(theme === "dark" ? 180 : 0);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const initialThemeOnDrag = useRef<"light" | "dark">(theme);
  const currentTargetTheme = useRef<"light" | "dark">(theme);

  const rafId = useRef<number | null>(null);
  const pendingCoords = useRef<{ x: number; y: number } | null>(null);
  const pointerStartPos = useRef<{ x: number; y: number; time: number } | null>(null);

  // Sync angle when theme changes externally
  useEffect(() => {
    if (!isDragging) {
      setCurrentAngle(theme === "dark" ? 180 : 0);
      currentTargetTheme.current = theme;
    }
  }, [theme, isDragging]);

  // Compute angle from client coordinates relative to dial center
  const getAngleFromCoords = useCallback((clientX: number, clientY: number) => {
    if (!dialRef.current) return 0;
    const rect = dialRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const dx = clientX - centerX;
    const dy = clientY - centerY;

    const rad = Math.atan2(dy, dx);
    let deg = (rad * 180) / Math.PI;
    deg = (deg + 90 + 360) % 360; // 0 deg is Top
    return deg;
  }, []);

  const applyThemeAtAngle = useCallback(
    (deg: number) => {
      setCurrentAngle(deg);
      // Top half (270° to 90°) is Light; Bottom half (90° to 270°) is Dark
      const shouldBeDark = deg >= 90 && deg < 270;
      const targetTheme = shouldBeDark ? "dark" : "light";

      if (currentTargetTheme.current !== targetTheme) {
        currentTargetTheme.current = targetTheme;
        // Direct silent switch while dragging to preserve 60/120fps fluid drag
        setTheme(targetTheme, false);
      }
    },
    [setTheme]
  );

  const processDrag = useCallback(() => {
    if (!pendingCoords.current) {
      rafId.current = null;
      return;
    }
    const { x, y } = pendingCoords.current;
    const deg = getAngleFromCoords(x, y);
    applyThemeAtAngle(deg);
    rafId.current = null;
  }, [getAngleFromCoords, applyThemeAtAngle]);

  const handlePointerDown = (e: React.PointerEvent<HTMLButtonElement>) => {
    pointerStartPos.current = { x: e.clientX, y: e.clientY, time: Date.now() };
    initialThemeOnDrag.current = theme;
    currentTargetTheme.current = theme;

    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      // Ignore
    }
    setIsDragging(true);

    const deg = getAngleFromCoords(e.clientX, e.clientY);
    applyThemeAtAngle(deg);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!isDragging) return;
    pendingCoords.current = { x: e.clientX, y: e.clientY };
    if (!rafId.current) {
      rafId.current = requestAnimationFrame(processDrag);
    }
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!isDragging) return;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      // Ignore
    }
    setIsDragging(false);

    if (rafId.current) {
      cancelAnimationFrame(rafId.current);
      rafId.current = null;
    }

    const start = pointerStartPos.current;
    const isClick =
      start &&
      Math.hypot(e.clientX - start.x, e.clientY - start.y) < 6 &&
      Date.now() - start.time < 300;

    if (isClick) {
      // Simple click -> toggle theme
      const nextTheme = theme === "dark" ? "light" : "dark";
      const isDark = nextTheme === "dark";
      executeThemeTransition(isDark, () => {
        setTheme(nextTheme, false);
        setCurrentAngle(isDark ? 180 : 0);
      });
    } else if (currentTargetTheme.current !== initialThemeOnDrag.current) {
      // Drag flipped theme -> trigger triangle transition
      const isDark = currentTargetTheme.current === "dark";
      executeThemeTransition(isDark, () => {
        setTheme(currentTargetTheme.current, false);
      });
    }
  };

  // Dot position along circular perimeter (radius = 12.5px)
  const dialRadius = 12.5;
  const rad = ((currentAngle - 90) * Math.PI) / 180;
  const dotX = dialRadius * Math.cos(rad);
  const dotY = dialRadius * Math.sin(rad);

  const isDarkTarget = currentAngle >= 90 && currentAngle < 270;

  return (
    <div className={`flex items-center select-none ${className}`}>
      <button
        ref={dialRef}
        type="button"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        className={`relative w-8 h-8 rounded-full border border-ink-primary/25 dark:border-ink-primary/35 bg-transparent flex items-center justify-center transition-transform duration-100 touch-none cursor-pointer ${
          isDragging
            ? "cursor-grabbing scale-105"
            : "cursor-grab hover:border-accent-primary/60 hover:scale-105 active:scale-95"
        }`}
      >
        {/* Orbiting Satellite Dot */}
        <div
          ref={dotRef}
          className="absolute w-2.5 h-2.5 rounded-full pointer-events-none transition-transform duration-75 flex items-center justify-center"
          style={{
            transform: `translate3d(${dotX}px, ${dotY}px, 0)`,
          }}
        >
          <div
            className={`w-2 h-2 rounded-full border transition-colors ${
              isDarkTarget
                ? "bg-accent-primary border-accent-primary shadow-[0_0_6px_rgba(232,118,90,0.85)]"
                : "bg-ink-primary border-bg-surface shadow-[0_0_4px_rgba(26,25,24,0.4)]"
            } ${isDragging ? "scale-125" : ""}`}
          />
        </div>
      </button>
    </div>
  );
}

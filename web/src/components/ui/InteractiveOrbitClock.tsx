"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useTheme } from "@/lib/theme";
import { executeThemeTransition } from "../ThemeTransitionOverlay";

interface InteractiveOrbitClockProps {
  className?: string;
}

/**
 * Interactive Orbit Clock & Time Controller
 * - 60fps/120fps hardware-accelerated draggable satellite dot on circular wire orbit.
 * - Smoothly updates time in real-time as user drags around the 24-hour cycle.
 * - While dragging: silently flips theme classes without stutter or layout lag.
 * - On release / click: triggers the crisp screen-center triangle transition if theme changed.
 * - Label indicates "LOCAL TIME" or "TIME TRAVELLER" (with ↺ reset).
 */
export function InteractiveOrbitClock({ className = "" }: InteractiveOrbitClockProps) {
  const { theme, setTheme } = useTheme();
  const dialRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  // Time state: hours and minutes
  const [hours, setHours] = useState<number>(11);
  const [minutes, setMinutes] = useState<number>(30);
  const [isTimeTraveller, setIsTimeTraveller] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Real local time reference
  const realTimeRef = useRef<{ h: number; m: number }>({ h: 11, m: 30 });
  const isTimeTravellerRef = useRef(false);
  isTimeTravellerRef.current = isTimeTraveller;

  // Track theme at start of drag to know if it flipped
  const initialThemeOnDrag = useRef<"light" | "dark">(theme);
  const currentTargetTheme = useRef<"light" | "dark">(theme);

  // Animation frame throttle ref
  const rafId = useRef<number | null>(null);
  const pendingCoords = useRef<{ x: number; y: number } | null>(null);

  // Initialize and run real-time clock tick
  useEffect(() => {
    const updateRealTime = () => {
      const now = new Date();
      const h = now.getHours();
      const m = now.getMinutes();
      realTimeRef.current = { h, m };

      if (!isTimeTravellerRef.current) {
        setHours(h);
        setMinutes(m);
      }
    };

    updateRealTime();
    const interval = setInterval(updateRealTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Update theme ref when theme prop updates
  useEffect(() => {
    currentTargetTheme.current = theme;
  }, [theme]);

  /**
   * 24-Hour Cycle Angle Mapping:
   * 12:00 Noon (brightest day) = 0° (Top, 12 o'clock)
   * 18:00 Sunset = 90° (Right, 3 o'clock)
   * 00:00 Midnight = 180° (Bottom, 6 o'clock)
   * 06:00 Sunrise = 270° (Left, 9 o'clock)
   * Daytime: 06:00 to 17:59 -> Light theme
   * Nighttime: 18:00 to 05:59 -> Dark theme
   */
  const totalMinutes = hours * 60 + minutes;
  const offsetFromNoon = (totalMinutes - 720 + 1440) % 1440;
  const currentAngleDeg = (offsetFromNoon / 1440) * 360;

  // Convert an angle in degrees [0, 360) to hours and minutes
  const angleToTime = useCallback((deg: number) => {
    const normalized = (deg % 360 + 360) % 360;
    const minsFromNoon = Math.round((normalized / 360) * 1440);
    const finalMinutes = (minsFromNoon + 720) % 1440;
    const h = Math.floor(finalMinutes / 60);
    const m = finalMinutes % 60;
    return { h, m };
  }, []);

  // Compute angle from event client coordinates relative to dial center
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

  // Apply time and theme smoothly during drag (silent class switch)
  const applyTimeAtAngle = useCallback(
    (deg: number, triggerAnimation = false) => {
      const { h, m } = angleToTime(deg);
      setHours(h);
      setMinutes(m);
      setIsTimeTraveller(true);

      const shouldBeDark = h >= 18 || h < 6;
      const targetTheme = shouldBeDark ? "dark" : "light";

      if (currentTargetTheme.current !== targetTheme) {
        currentTargetTheme.current = targetTheme;
        if (triggerAnimation) {
          executeThemeTransition(shouldBeDark, () => {
            setTheme(targetTheme, false);
          });
        } else {
          // Direct silent switch while dragging to preserve 60/120fps fluid drag
          setTheme(targetTheme, false);
        }
      }
    },
    [angleToTime, setTheme]
  );

  // Process dragging via requestAnimationFrame
  const processDrag = useCallback(() => {
    if (!pendingCoords.current) {
      rafId.current = null;
      return;
    }
    const { x, y } = pendingCoords.current;
    const deg = getAngleFromCoords(x, y);
    applyTimeAtAngle(deg, false);
    rafId.current = null;
  }, [getAngleFromCoords, applyTimeAtAngle]);

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    setIsDragging(true);
    initialThemeOnDrag.current = theme;

    const deg = getAngleFromCoords(e.clientX, e.clientY);
    applyTimeAtAngle(deg, false);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    pendingCoords.current = { x: e.clientX, y: e.clientY };
    if (!rafId.current) {
      rafId.current = requestAnimationFrame(processDrag);
    }
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
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

    // If theme flipped during drag or on direct click, launch the triangle animation on finish
    if (currentTargetTheme.current !== initialThemeOnDrag.current) {
      const isDark = currentTargetTheme.current === "dark";
      executeThemeTransition(isDark, () => {
        setTheme(currentTargetTheme.current, false);
      });
    }
  };

  // Reset back to actual real local time
  const resetToRealTime = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    const { h, m } = realTimeRef.current;
    setHours(h);
    setMinutes(m);
    setIsTimeTraveller(false);

    const shouldBeDark = h >= 18 || h < 6;
    const targetTheme = shouldBeDark ? "dark" : "light";
    if (theme !== targetTheme) {
      executeThemeTransition(shouldBeDark, () => {
        setTheme(targetTheme, false);
      });
    }
  };

  const formattedHours = String(hours).padStart(2, "0");
  const formattedMinutes = String(minutes).padStart(2, "0");
  const isDarkTarget = hours >= 18 || hours < 6;

  // Dot position along the circular wire perimeter (radius = 12.5px)
  const dialRadius = 12.5;
  const rad = ((currentAngleDeg - 90) * Math.PI) / 180;
  const dotX = dialRadius * Math.cos(rad);
  const dotY = dialRadius * Math.sin(rad);

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Time Digits & State Label */}
      <div className="flex flex-col text-right leading-tight">
        {isTimeTraveller ? (
          <button
            type="button"
            onClick={resetToRealTime}
            title="Click to reset to real local time"
            className="group flex items-center justify-end gap-1 font-mono text-[9px] uppercase tracking-[0.14em] text-accent-primary font-bold hover:underline transition-all"
          >
            <span>TIME TRAVELLER</span>
            <span className="text-[10px] group-hover:rotate-180 transition-transform duration-300">
              ↺
            </span>
          </button>
        ) : (
          <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-gray-warm">
            LOCAL TIME
          </span>
        )}

        <div className="font-mono text-[11px] font-bold text-ink-primary tracking-wider tabular-nums flex items-center justify-end gap-1">
          <span>{formattedHours}</span>
          <span className={isTimeTraveller ? "text-accent-primary animate-pulse" : "opacity-70"}>
            .
          </span>
          <span>{formattedMinutes}</span>
        </div>
      </div>

      {/* Circular Orbit Dial (Minimalist Wire Circle, Clean & Unshadowed) */}
      <div
        ref={dialRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        title={
          isTimeTraveller
            ? "Drag dot to travel time & shift theme (Click ↺ to reset)"
            : "Click or drag dot around the circle to change time & theme"
        }
        className={`relative w-8 h-8 rounded-full border border-ink-primary/25 dark:border-ink-primary/35 bg-transparent flex items-center justify-center transition-transform duration-100 touch-none ${
          isDragging
            ? "cursor-grabbing scale-105"
            : "cursor-grab hover:border-accent-primary/60 hover:scale-102"
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
      </div>
    </div>
  );
}

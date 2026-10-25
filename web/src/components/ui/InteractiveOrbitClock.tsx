"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useTheme } from "@/lib/theme";
import { executeThemeTransition } from "../ThemeTransitionOverlay";

interface InteractiveOrbitClockProps {
  className?: string;
}

/**
 * Interactive Orbit Clock & Time Controller
 * - Circular orbit dial with a draggable satellite dot.
 * - Clicking and dragging the dot rotates it around the 24-hour cycle.
 * - Changing the time dynamically changes the theme (Day = Light, Night = Dark)
 *   and fires the screen-center expanding triangle transition.
 * - When moved away from real time, header displays "TIME TRAVELLER".
 * - Clicking "TIME TRAVELLER" smoothly snaps back to real local time.
 */
export function InteractiveOrbitClock({ className = "" }: InteractiveOrbitClockProps) {
  const { theme, setTheme } = useTheme();
  const dialRef = useRef<HTMLDivElement>(null);

  // Time state: hours and minutes
  const [hours, setHours] = useState<number>(11);
  const [minutes, setMinutes] = useState<number>(30);
  const [isTimeTraveller, setIsTimeTraveller] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Real local time reference
  const realTimeRef = useRef<{ h: number; m: number }>({ h: 11, m: 30 });
  const isTimeTravellerRef = useRef(false);
  isTimeTravellerRef.current = isTimeTraveller;

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
  // Offset relative to noon (720 min)
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

  // Update theme based on chosen time
  const syncThemeWithTime = useCallback(
    (h: number) => {
      const shouldBeDark = h >= 18 || h < 6;
      const targetTheme = shouldBeDark ? "dark" : "light";
      if (theme !== targetTheme) {
        executeThemeTransition(shouldBeDark, () => {
          setTheme(targetTheme, false);
        });
      }
    },
    [theme, setTheme]
  );

  // Compute angle from mouse/touch event relative to dial center
  const getAngleFromEvent = useCallback((clientX: number, clientY: number) => {
    if (!dialRef.current) return 0;
    const rect = dialRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const dx = clientX - centerX;
    const dy = clientY - centerY;

    // Angle relative to positive X-axis in radians: -PI to +PI
    const rad = Math.atan2(dy, dx);
    let deg = (rad * 180) / Math.PI;
    // Rotate coordinate system so 0 deg is at the Top (dy < 0, dx = 0)
    deg = (deg + 90 + 360) % 360;
    return deg;
  }, []);

  // Handle pointer down (click or drag start)
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    setIsDragging(true);

    const deg = getAngleFromEvent(e.clientX, e.clientY);
    const { h, m } = angleToTime(deg);
    setHours(h);
    setMinutes(m);
    setIsTimeTraveller(true);
    syncThemeWithTime(h);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    const deg = getAngleFromEvent(e.clientX, e.clientY);
    const { h, m } = angleToTime(deg);
    setHours(h);
    setMinutes(m);
    setIsTimeTraveller(true);
    syncThemeWithTime(h);
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      // Safely ignore pointer capture release if not captured
    }
    setIsDragging(false);
  };

  // Reset back to actual real local time
  const resetToRealTime = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    const { h, m } = realTimeRef.current;
    setHours(h);
    setMinutes(m);
    setIsTimeTraveller(false);
    syncThemeWithTime(h);
  };

  const formattedHours = String(hours).padStart(2, "0");
  const formattedMinutes = String(minutes).padStart(2, "0");
  const isDarkTarget = hours >= 18 || hours < 6;

  // Dot position along the circle perimeter (radius = 13px)
  const dialRadius = 13;
  // In our coordinate system, 0 deg is Top, rotating clockwise
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

      {/* Circular Orbit Dial (Draggable Satellite) */}
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
        className={`relative w-8 h-8 rounded-full border border-ink-primary/50 dark:border-ink-primary/60 flex items-center justify-center transition-all duration-150 touch-none ${
          isDragging
            ? "cursor-grabbing ring-2 ring-accent-primary/60 scale-105"
            : "cursor-grab hover:border-accent-primary hover:scale-102"
        }`}
        style={{
          boxShadow: isDarkTarget
            ? "0 0 10px rgba(232, 118, 90, 0.25) inset"
            : "0 0 10px rgba(232, 176, 75, 0.2) inset",
        }}
      >
        {/* Subtle center crosshair / axis guide */}
        <div className="w-1 h-1 rounded-full bg-ink-primary/20 pointer-events-none" />

        {/* Orbiting Draggable Satellite Dot */}
        <div
          className="absolute w-2.5 h-2.5 rounded-full pointer-events-none transition-transform duration-75 flex items-center justify-center"
          style={{
            transform: `translate(${dotX}px, ${dotY}px)`,
          }}
        >
          <div
            className={`w-2 h-2 rounded-full border ${
              isDarkTarget
                ? "bg-accent-primary border-accent-primary shadow-[0_0_8px_rgba(232,118,90,0.9)]"
                : "bg-ink-primary border-bg-surface shadow-[0_0_6px_rgba(154,91,0,0.5)]"
            } ${isDragging ? "scale-125" : ""}`}
          />
        </div>
      </div>
    </div>
  );
}

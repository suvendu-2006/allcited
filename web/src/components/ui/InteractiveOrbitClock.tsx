"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useTheme } from "@/lib/theme";

interface InteractiveOrbitClockProps {
  className?: string;
}

/**
 * Standard 12-Hour Clock Angle Mapping:
 * 12:00 = 0° (Top, 12 o'clock)
 * 03:00 = 90° (Right, 3 o'clock)
 * 06:00 = 180° (Bottom, 6 o'clock)
 * 09:00 = 270° (Left, 9 o'clock)
 */
function angleToTime(deg: number, isPM: boolean) {
  const normalized = ((deg % 360) + 360) % 360;
  const totalMinutes12 = Math.round((normalized / 360) * 720) % 720;
  const rawH = Math.floor(totalMinutes12 / 60);
  const m = totalMinutes12 % 60;
  let h24: number;
  if (isPM) {
    h24 = rawH === 0 ? 12 : rawH + 12;
  } else {
    h24 = rawH === 0 ? 0 : rawH;
  }
  return { h: h24, m };
}

function timeToAngle(h: number, m: number) {
  const hour12 = h % 12;
  return ((hour12 + m / 60) / 12) * 360;
}

function isNearRealTime(h: number, m: number, realH: number, realM: number) {
  const targetTotal = h * 60 + m;
  const realTotal = realH * 60 + realM;
  const diff = Math.abs(targetTotal - realTotal);
  const circularDiff = Math.min(diff, 1440 - diff);
  return circularDiff <= 10; // within 10 minutes of real local time
}

export function InteractiveOrbitClock({ className = "" }: InteractiveOrbitClockProps) {
  const { theme, setTheme } = useTheme();
  const dialRef = useRef<HTMLDivElement>(null);

  // Time state (24-hour internally: 0..23)
  const [hours, setHours] = useState<number>(12);
  const [minutes, setMinutes] = useState<number>(0);
  const [isTimeTraveller, setIsTimeTraveller] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Live real time reference
  const realTimeRef = useRef<{ h: number; m: number }>({ h: 12, m: 0 });
  const isTimeTravellerRef = useRef(false);
  isTimeTravellerRef.current = isTimeTraveller;

  const isPmRef = useRef(false);
  const lastAngleRef = useRef(0);
  const pointerStartRef = useRef<{ x: number; y: number } | null>(null);
  const hasMovedRef = useRef(false);
  const currentTargetTheme = useRef<"light" | "dark">(theme);

  // Real-time clock tick: updates live time when not time-travelling
  useEffect(() => {
    const updateRealTime = () => {
      const now = new Date();
      const h = now.getHours();
      const m = now.getMinutes();
      realTimeRef.current = { h, m };

      if (!isTimeTravellerRef.current) {
        setHours(h);
        setMinutes(m);
        isPmRef.current = h >= 12;
      }
    };

    updateRealTime();
    const interval = setInterval(updateRealTime, 1000);
    return () => clearInterval(interval);
  }, []);

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

  // Reset back to real local time
  const resetToRealTime = useCallback(
    (e?: React.MouseEvent) => {
      e?.stopPropagation();
      const { h, m } = realTimeRef.current;
      setHours(h);
      setMinutes(m);
      isPmRef.current = h >= 12;
      setIsTimeTraveller(false);

      const shouldBeDark = h >= 18 || h < 6;
      const targetTheme = shouldBeDark ? "dark" : "light";
      if (theme !== targetTheme) {
        currentTargetTheme.current = targetTheme;
        setTheme(targetTheme, false);
      }
    },
    [theme, setTheme]
  );

  // Toggle theme on direct click/tap of the dot or circle
  const toggleTheme = useCallback(() => {
    const nextDark = theme !== "dark";
    const targetTheme = nextDark ? "dark" : "light";
    currentTargetTheme.current = targetTheme;
    setTheme(targetTheme, false);

    // Synchronize hours to match the toggled theme (flip AM/PM if out of theme phase)
    if (nextDark) {
      if (hours >= 6 && hours < 18) {
        setHours((prev) => (prev + 12) % 24);
        isPmRef.current = !isPmRef.current;
      }
    } else {
      if (hours >= 18 || hours < 6) {
        setHours((prev) => (prev + 12) % 24);
        isPmRef.current = !isPmRef.current;
      }
    }
  }, [theme, setTheme, hours]);

  // Apply time and theme dynamically as the dot rotates
  const applyTimeAtAngle = useCallback(
    (deg: number) => {
      // Check for crossing 12 o'clock boundary (0 deg) to flip AM/PM
      const prev = lastAngleRef.current;
      if (prev > 300 && deg < 60) {
        // Clockwise crossing 12 o'clock
        isPmRef.current = !isPmRef.current;
      } else if (prev < 60 && deg > 300) {
        // Counter-clockwise crossing 12 o'clock
        isPmRef.current = !isPmRef.current;
      }
      lastAngleRef.current = deg;

      const { h, m } = angleToTime(deg, isPmRef.current);
      const real = realTimeRef.current;
      const nearReal = isNearRealTime(h, m, real.h, real.m);

      if (nearReal) {
        setHours(real.h);
        setMinutes(real.m);
        isPmRef.current = real.h >= 12;
        setIsTimeTraveller(false);
      } else {
        setHours(h);
        setMinutes(m);
        setIsTimeTraveller(true);
      }

      // DYNAMIC THEME SWITCH ON ROTATION
      const shouldBeDark = h >= 18 || h < 6;
      const targetTheme = shouldBeDark ? "dark" : "light";
      if (currentTargetTheme.current !== targetTheme) {
        currentTargetTheme.current = targetTheme;
        setTheme(targetTheme, false);
      }
    },
    [setTheme]
  );

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    pointerStartRef.current = { x: e.clientX, y: e.clientY };
    hasMovedRef.current = false;
    lastAngleRef.current = getAngleFromCoords(e.clientX, e.clientY);

    const onPointerMoveWindow = (moveEvent: PointerEvent) => {
      if (!pointerStartRef.current) return;
      const dx = moveEvent.clientX - pointerStartRef.current.x;
      const dy = moveEvent.clientY - pointerStartRef.current.y;

      if (!hasMovedRef.current) {
        if (Math.hypot(dx, dy) >= 3) {
          hasMovedRef.current = true;
          setIsDragging(true);
        }
      }

      if (hasMovedRef.current) {
        const deg = getAngleFromCoords(moveEvent.clientX, moveEvent.clientY);
        applyTimeAtAngle(deg);
      }
    };

    const onPointerUpWindow = () => {
      window.removeEventListener("pointermove", onPointerMoveWindow);
      window.removeEventListener("pointerup", onPointerUpWindow);
      window.removeEventListener("pointercancel", onPointerUpWindow);

      const wasDragging = hasMovedRef.current;
      pointerStartRef.current = null;
      hasMovedRef.current = false;
      setIsDragging(false);

      if (!wasDragging) {
        toggleTheme();
      }
    };

    window.addEventListener("pointermove", onPointerMoveWindow);
    window.addEventListener("pointerup", onPointerUpWindow);
    window.addEventListener("pointercancel", onPointerUpWindow);
  };

  const currentAngleDeg = timeToAngle(hours, minutes);
  const isDark = theme === "dark";

  // Dot position along the circular wire perimeter (radius = 12.5px)
  const dialRadius = 12.5;
  const rad = ((currentAngleDeg - 90) * Math.PI) / 180;
  const dotX = dialRadius * Math.cos(rad);
  const dotY = dialRadius * Math.sin(rad);

  return (
    <div className={`flex items-center gap-1.5 sm:gap-2 select-none flex-shrink-0 ${className}`}>
      {/* Time Traveller Mode Pill */}
      {isTimeTraveller && (
        <button
          type="button"
          onClick={resetToRealTime}
          title="Time traveller active · Click to return to local time"
          className="group flex items-center justify-end gap-1 font-mono text-[8.5px] sm:text-[9px] uppercase tracking-[0.1em] sm:tracking-[0.14em] text-accent-primary font-bold hover:underline transition-all cursor-pointer flex-shrink-0 animate-fade-in"
        >
          <span>TIME TRAVELLER</span>
          <span className="text-[10px] group-hover:rotate-180 transition-transform duration-300">
            ↺
          </span>
        </button>
      )}

      {/* Circular Orbit Dial (Minimalist Wire Circle with Microanimations) */}
      <div
        ref={dialRef}
        data-testid="orbit-clock-dial"
        onPointerDown={handlePointerDown}
        title={
          isTimeTraveller
            ? "Time travel active. Drag dot to rotate time & shift theme (Click ↺ to reset)"
            : "Click dot to toggle theme or drag around circle to shift theme"
        }
        className={`relative w-7 h-7 sm:w-8 sm:h-8 rounded-full border border-ink-primary/25 dark:border-ink-primary/35 bg-transparent flex items-center justify-center transition-all duration-200 touch-none cursor-pointer flex-shrink-0 ${
          isDragging
            ? "cursor-grabbing scale-110 border-accent-primary/80 shadow-[0_0_8px_rgba(232,118,90,0.3)]"
            : "cursor-grab hover:border-accent-primary/60 hover:scale-105 active:scale-95"
        }`}
      >
        {/* Orbiting Satellite Dot with Microanimation Pulse & Glow */}
        <div
          className="absolute w-2.5 h-2.5 rounded-full pointer-events-none transition-transform duration-75 flex items-center justify-center"
          style={{
            transform: `translate3d(${dotX}px, ${dotY}px, 0)`,
          }}
        >
          <div
            className={`w-2 h-2 rounded-full border transition-all duration-200 ${
              isDark
                ? "bg-accent-primary border-accent-primary animate-orbit-pulse"
                : "bg-ink-primary border-bg-surface animate-orbit-pulse-light"
            } ${isDragging ? "scale-125 !animate-none shadow-[0_0_12px_rgba(232,118,90,0.9)]" : ""}`}
          />
        </div>
      </div>
    </div>
  );
}

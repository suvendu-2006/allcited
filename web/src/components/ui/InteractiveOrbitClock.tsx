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

  // Live real time reference & total minutes accumulator (0..1439)
  const realTimeRef = useRef<{ h: number; m: number }>({ h: 12, m: 0 });
  const totalMinutesRef = useRef<number>(12 * 60);
  const isTimeTravellerRef = useRef(false);
  isTimeTravellerRef.current = isTimeTraveller;

  const lastAngleRef = useRef(0);
  const pointerStartRef = useRef<{ x: number; y: number } | null>(null);
  const hasMovedRef = useRef(false);

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
        totalMinutesRef.current = h * 60 + m;
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
    deg = (deg + 90 + 360) % 360; // 0 deg is Top (12 o'clock)
    return deg;
  }, []);

  // Reset back to real local time
  const resetToRealTime = useCallback(
    (e?: React.MouseEvent) => {
      e?.stopPropagation();
      const { h, m } = realTimeRef.current;
      setHours(h);
      setMinutes(m);
      totalMinutesRef.current = h * 60 + m;
      setIsTimeTraveller(false);
      if (typeof window !== "undefined") {
        sessionStorage.removeItem("allcited_theme_manual");
      }

      const shouldBeDark = h >= 18 || h < 6;
      const targetTheme = shouldBeDark ? "dark" : "light";
      setTheme(targetTheme, false);
    },
    [setTheme]
  );

  // Toggle theme on direct click/tap of the dot or circle
  const toggleTheme = useCallback(() => {
    const nextDark = theme !== "dark";
    const targetTheme = nextDark ? "dark" : "light";
    setTheme(targetTheme, false);

    // Synchronize clock time by 12 hours (flip Day <-> Night while keeping dot angle aligned)
    const newTotal = (totalMinutesRef.current + 720) % 1440;
    totalMinutesRef.current = newTotal;
    const h = Math.floor(newTotal / 60);
    const m = Math.floor(newTotal % 60);
    setHours(h);
    setMinutes(m);
    setIsTimeTraveller(true);
  }, [theme, setTheme]);

  // Apply continuous rotational movement to clock time
  const applyRotationDelta = useCallback(
    (currentAngle: number) => {
      // Calculate shortest angular delta (-180 to +180)
      let deltaDeg = currentAngle - lastAngleRef.current;
      while (deltaDeg > 180) deltaDeg -= 360;
      while (deltaDeg < -180) deltaDeg += 360;
      lastAngleRef.current = currentAngle;

      // In a 12-hour clock face: 360° = 720 minutes => 1° = 2 minutes
      const deltaMinutes = deltaDeg * 2;
      let newTotal = (totalMinutesRef.current + deltaMinutes) % 1440;
      if (newTotal < 0) newTotal += 1440;
      totalMinutesRef.current = newTotal;

      const h = Math.floor(newTotal / 60);
      const m = Math.floor(newTotal % 60);

      const real = realTimeRef.current;
      const nearReal = isNearRealTime(h, m, real.h, real.m);

      if (nearReal) {
        setHours(real.h);
        setMinutes(real.m);
        setIsTimeTraveller(false);
      } else {
        setHours(h);
        setMinutes(m);
        setIsTimeTraveller(true);
      }

      // Authentic Clock Theme: 6:00 AM to 6:00 PM is Day (Light), 6:00 PM to 6:00 AM is Night (Dark)
      const isNight = h >= 18 || h < 6;
      const targetTheme = isNight ? "dark" : "light";
      setTheme(targetTheme, false);
    },
    [setTheme]
  );

  const applyRotationDeltaRef = useRef(applyRotationDelta);
  applyRotationDeltaRef.current = applyRotationDelta;

  const toggleThemeRef = useRef(toggleTheme);
  toggleThemeRef.current = toggleTheme;

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
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
        applyRotationDeltaRef.current(deg);
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
        toggleThemeRef.current();
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
          aria-label="Time traveller active. Click to return to local time"
          className="group flex items-center justify-end gap-1 font-mono text-[8.5px] sm:text-[9px] uppercase tracking-[0.1em] sm:tracking-[0.14em] text-accent-primary font-bold hover:underline transition-all cursor-pointer flex-shrink-0 animate-fade-in"
        >
          <span>TIME TRAVELLER</span>
          <span className="text-[10px] group-hover:rotate-180 transition-transform duration-300">
            ↺
          </span>
        </button>
      )}

      {/* Circular Orbit Dial (Minimalist Wire Circle with Microanimations - No Title Tooltips) */}
      <div
        ref={dialRef}
        data-testid="orbit-clock-dial"
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggleTheme();
          }
        }}
        onPointerDown={handlePointerDown}
        aria-label="Orbit clock theme switcher"
        className={`relative w-7 h-7 sm:w-8 sm:h-8 rounded-full border border-ink-primary/25 dark:border-ink-primary/35 bg-transparent flex items-center justify-center transition-all duration-200 touch-none cursor-pointer flex-shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2 ${
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

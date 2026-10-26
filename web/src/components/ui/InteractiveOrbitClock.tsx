"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useTheme } from "@/lib/theme";

interface InteractiveOrbitClockProps {
  className?: string;
}

/**
 * 24-Hour Cycle Angle Mapping:
 * 12:00 Noon = 0° (Top, 12 o'clock)
 * 18:00 Sunset = 90° (Right, 3 o'clock)
 * 00:00 Midnight = 180° (Bottom, 6 o'clock)
 * 06:00 Sunrise = 270° (Left, 9 o'clock)
 */
function angleToTime(deg: number) {
  const normalized = ((deg % 360) + 360) % 360;
  const minsFromNoon = Math.round((normalized / 360) * 1440);
  const finalMinutes = (minsFromNoon + 720) % 1440;
  const h = Math.floor(finalMinutes / 60);
  const m = finalMinutes % 60;
  return { h, m };
}

function timeToAngle(h: number, m: number) {
  const totalMinutes = h * 60 + m;
  const offsetFromNoon = (totalMinutes - 720 + 1440) % 1440;
  return (offsetFromNoon / 1440) * 360;
}

function isNearRealTime(h: number, m: number, realH: number, realM: number) {
  const targetTotal = h * 60 + m;
  const realTotal = realH * 60 + realM;
  const diff = Math.abs(targetTotal - realTotal);
  const circularDiff = Math.min(diff, 1440 - diff);
  return circularDiff <= 8; // within 8 minutes of real time
}

export function InteractiveOrbitClock({ className = "" }: InteractiveOrbitClockProps) {
  const { theme, setTheme } = useTheme();
  const dialRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  // Time state
  const [hours, setHours] = useState<number>(12);
  const [minutes, setMinutes] = useState<number>(0);
  const [isTimeTraveller, setIsTimeTraveller] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Live real time reference
  const realTimeRef = useRef<{ h: number; m: number }>({ h: 12, m: 0 });
  const isTimeTravellerRef = useRef(false);
  isTimeTravellerRef.current = isTimeTraveller;

  const currentTargetTheme = useRef<"light" | "dark">(theme);
  const rafId = useRef<number | null>(null);
  const pendingCoords = useRef<{ x: number; y: number } | null>(null);
  const pointerStartPos = useRef<{ x: number; y: number; time: number } | null>(null);

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
      setIsTimeTraveller(false);

      const shouldBeDark = h >= 18 || h < 6;
      const targetTheme = shouldBeDark ? "dark" : "light";
      if (theme !== targetTheme) {
        setTheme(targetTheme, false);
      }
    },
    [theme, setTheme]
  );

  // Apply time and theme based on dial angle
  const applyTimeAtAngle = useCallback(
    (deg: number) => {
      const { h, m } = angleToTime(deg);
      const real = realTimeRef.current;
      const nearReal = isNearRealTime(h, m, real.h, real.m);

      if (nearReal) {
        // User dragged back to their local time: automatically switch back to LOCAL TIME!
        setHours(real.h);
        setMinutes(real.m);
        setIsTimeTraveller(false);
      } else {
        setHours(h);
        setMinutes(m);
        setIsTimeTraveller(true);
      }

      const shouldBeDark = h >= 18 || h < 6;
      const targetTheme = shouldBeDark ? "dark" : "light";

      if (currentTargetTheme.current !== targetTheme) {
        currentTargetTheme.current = targetTheme;
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
    applyTimeAtAngle(deg);
    rafId.current = null;
  }, [getAngleFromCoords, applyTimeAtAngle]);

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    pointerStartPos.current = { x: e.clientX, y: e.clientY, time: Date.now() };

    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      // Ignore
    }
    setIsDragging(true);

    const deg = getAngleFromCoords(e.clientX, e.clientY);
    applyTimeAtAngle(deg);
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

    const start = pointerStartPos.current;
    const isClick =
      start &&
      Math.hypot(e.clientX - start.x, e.clientY - start.y) < 6 &&
      Date.now() - start.time < 300;

    if (isClick) {
      // Direct click toggles between noon (light) and midnight (dark)
      const shouldBeDark = theme !== "dark";
      const targetTheme = shouldBeDark ? "dark" : "light";
      const travelHours = shouldBeDark ? 0 : 12;
      const travelMinutes = 0;

      const real = realTimeRef.current;
      const nearReal = isNearRealTime(travelHours, travelMinutes, real.h, real.m);

      setHours(nearReal ? real.h : travelHours);
      setMinutes(nearReal ? real.m : travelMinutes);
      setIsTimeTraveller(!nearReal);
      setTheme(targetTheme, false);
    }
  };

  const currentAngleDeg = timeToAngle(hours, minutes);
  const formattedHours = String(hours).padStart(2, "0");
  const formattedMinutes = String(minutes).padStart(2, "0");
  const isDarkTarget = hours >= 18 || hours < 6;

  // Dot position along the circular wire perimeter (radius = 12.5px)
  const dialRadius = 12.5;
  const rad = ((currentAngleDeg - 90) * Math.PI) / 180;
  const dotX = dialRadius * Math.cos(rad);
  const dotY = dialRadius * Math.sin(rad);

  return (
    <div className={`flex items-center gap-2.5 sm:gap-3 select-none ${className}`}>
      {/* Time Digits & State Label */}
      <div className="flex flex-col text-right leading-tight">
        {isTimeTraveller ? (
          <button
            type="button"
            onClick={resetToRealTime}
            title="Click to reset to real local time"
            className="group flex items-center justify-end gap-1 font-mono text-[9px] uppercase tracking-[0.14em] text-accent-primary font-bold hover:underline transition-all cursor-pointer"
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

      {/* Circular Orbit Dial (Minimalist Wire Circle) */}
      <div
        ref={dialRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        title={
          isTimeTraveller
            ? "Drag dot or click to toggle theme (Click ↺ to reset to real time)"
            : "Click or drag dot around the circle to change time & theme"
        }
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
      </div>
    </div>
  );
}

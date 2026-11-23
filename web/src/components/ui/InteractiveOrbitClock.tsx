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

function normalizeDelta(deltaDeg: number) {
  let delta = deltaDeg;
  while (delta > 180) delta -= 360;
  while (delta < -180) delta += 360;
  return delta;
}

function getShortestRotationTarget(currentAngle: number, targetDegMod360: number) {
  const currentMod = ((currentAngle % 360) + 360) % 360;
  const diff = normalizeDelta(targetDegMod360 - currentMod);
  return currentAngle + diff;
}

export function InteractiveOrbitClock({ className = "" }: InteractiveOrbitClockProps) {
  const { theme, setTheme } = useTheme();
  const dialRef = useRef<HTMLDivElement>(null);
  const orbitArmRef = useRef<HTMLDivElement>(null);

  // Time travelling & drag interaction state
  const [isTimeTraveller, setIsTimeTraveller] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [angleDeg, setAngleDeg] = useState<number>(0);

  // Live real time reference & continuous angle reference
  const realTimeRef = useRef<{ h: number; m: number }>({ h: 12, m: 0 });
  const totalMinutesRef = useRef<number>(12 * 60);
  const currentAngleRef = useRef<number>(0);

  const isTimeTravellerRef = useRef(false);
  isTimeTravellerRef.current = isTimeTraveller;

  const isDraggingRef = useRef(false);
  isDraggingRef.current = isDragging;

  const lastAngleRef = useRef(0);
  const pointerStartRef = useRef<{ x: number; y: number } | null>(null);
  const hasMovedRef = useRef(false);
  const currentThemeRef = useRef(theme);
  currentThemeRef.current = theme;

  // Real-time clock tick: updates live time when not time-travelling and not dragging
  useEffect(() => {
    const now = new Date();
    const initH = now.getHours();
    const initM = now.getMinutes();
    realTimeRef.current = { h: initH, m: initM };
    totalMinutesRef.current = initH * 60 + initM;
    const initialAngle = timeToAngle(initH, initM);
    currentAngleRef.current = initialAngle;
    setAngleDeg(initialAngle);

    const updateRealTime = () => {
      const n = new Date();
      const h = n.getHours();
      const m = n.getMinutes();
      realTimeRef.current = { h, m };

      if (!isTimeTravellerRef.current && !isDraggingRef.current) {
        totalMinutesRef.current = h * 60 + m;
        const targetDeg = timeToAngle(h, m);
        const targetAngle = getShortestRotationTarget(currentAngleRef.current, targetDeg);
        currentAngleRef.current = targetAngle;
        setAngleDeg(targetAngle);
        if (orbitArmRef.current) {
          orbitArmRef.current.style.transition = "transform 400ms ease-out";
          orbitArmRef.current.style.transform = `rotate(${targetAngle}deg)`;
        }
      }
    };

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
      totalMinutesRef.current = h * 60 + m;
      setIsTimeTraveller(false);
      if (typeof window !== "undefined") {
        sessionStorage.removeItem("allcited_theme_manual");
      }

      const shouldBeDark = h >= 18 || h < 6;
      const targetTheme = shouldBeDark ? "dark" : "light";
      setTheme(targetTheme, false);

      const targetDeg = timeToAngle(h, m);
      const targetAngle = getShortestRotationTarget(currentAngleRef.current, targetDeg);
      currentAngleRef.current = targetAngle;
      setAngleDeg(targetAngle);
      if (orbitArmRef.current) {
        orbitArmRef.current.style.transition = "transform 450ms cubic-bezier(0.25, 1, 0.5, 1)";
        orbitArmRef.current.style.transform = `rotate(${targetAngle}deg)`;
      }
    },
    [setTheme]
  );

  // Toggle theme on direct click/tap of the dot or circle
  const toggleTheme = useCallback(() => {
    const nextDark = currentThemeRef.current !== "dark";
    const targetTheme = nextDark ? "dark" : "light";
    setTheme(targetTheme, false);

    // Synchronize clock time by 12 hours (flip Day <-> Night)
    const newTotal = (totalMinutesRef.current + 720) % 1440;
    totalMinutesRef.current = newTotal;
    setIsTimeTraveller(true);

    // Smoothly spin 360° around the circular wire into the new theme
    const nextAngle = currentAngleRef.current + 360;
    currentAngleRef.current = nextAngle;
    setAngleDeg(nextAngle);
    if (orbitArmRef.current) {
      orbitArmRef.current.style.transition = "transform 550ms cubic-bezier(0.34, 1.3, 0.64, 1)";
      orbitArmRef.current.style.transform = `rotate(${nextAngle}deg)`;
    }
  }, [setTheme]);

  // Apply continuous rotational movement to clock time & orbit angle
  const applyRotationDelta = useCallback(
    (currentAngle: number) => {
      const deltaDeg = normalizeDelta(currentAngle - lastAngleRef.current);
      lastAngleRef.current = currentAngle;

      // Update continuous rotation angle directly on the DOM for zero-lag 120fps motion
      currentAngleRef.current += deltaDeg;
      if (orbitArmRef.current) {
        orbitArmRef.current.style.transition = "none";
        orbitArmRef.current.style.transform = `rotate(${currentAngleRef.current}deg)`;
      }

      // In a 12-hour clock face: 360° = 720 minutes => 1° = 2 minutes
      const deltaMinutes = deltaDeg * 2;
      let newTotal = (totalMinutesRef.current + deltaMinutes) % 1440;
      if (newTotal < 0) newTotal += 1440;
      totalMinutesRef.current = newTotal;

      const h = Math.floor(newTotal / 60);
      const m = Math.floor(newTotal % 60);

      const real = realTimeRef.current;
      const nearReal = isNearRealTime(h, m, real.h, real.m);
      setIsTimeTraveller(!nearReal);

      // Authentic Clock Theme: 6:00 AM to 6:00 PM is Day (Light), 6:00 PM to 6:00 AM is Night (Dark)
      const isNight = h >= 18 || h < 6;
      const targetTheme = isNight ? "dark" : "light";
      if (targetTheme !== currentThemeRef.current) {
        setTheme(targetTheme, false);
      }
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

    // Disable CSS transition immediately so the dot tracks pointer with zero latency
    if (orbitArmRef.current) {
      orbitArmRef.current.style.transition = "none";
    }

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
      } else {
        // Sync final time state
        const currentTotal = totalMinutesRef.current;
        const h = Math.floor(currentTotal / 60);
        const m = Math.floor(currentTotal % 60);
        const real = realTimeRef.current;
        const nearReal = isNearRealTime(h, m, real.h, real.m);

        if (nearReal) {
          totalMinutesRef.current = real.h * 60 + real.m;
          setIsTimeTraveller(false);
          const targetDeg = timeToAngle(real.h, real.m);
          const targetAngle = getShortestRotationTarget(currentAngleRef.current, targetDeg);
          currentAngleRef.current = targetAngle;
          setAngleDeg(targetAngle);
          if (orbitArmRef.current) {
            orbitArmRef.current.style.transition = "transform 350ms cubic-bezier(0.25, 1, 0.5, 1)";
            orbitArmRef.current.style.transform = `rotate(${targetAngle}deg)`;
          }
        } else {
          setAngleDeg(currentAngleRef.current);
          setIsTimeTraveller(true);
        }
      }
    };

    window.addEventListener("pointermove", onPointerMoveWindow);
    window.addEventListener("pointerup", onPointerUpWindow);
    window.addEventListener("pointercancel", onPointerUpWindow);
  };

  const isDark = theme === "dark";
  const dialRadius = 12.5;

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
        {/* Orbital Rotation Arm (Hardware-Accelerated Pure Circular Path) */}
        <div
          ref={orbitArmRef}
          className="absolute inset-0 pointer-events-none flex items-center justify-center will-change-transform"
          style={{
            transform: `rotate(${angleDeg}deg)`,
            transition: isDragging
              ? "none"
              : "transform 400ms cubic-bezier(0.25, 1, 0.5, 1)",
          }}
        >
          {/* Orbiting Satellite Dot along the Circular Wire Perimeter */}
          <div
            className="absolute flex items-center justify-center pointer-events-none"
            style={{
              top: "50%",
              left: "50%",
              transform: `translate(-50%, -50%) translateY(-${dialRadius}px)`,
            }}
          >
            <div
              className={`w-2 h-2 rounded-full border transition-all duration-200 ${
                isDark
                  ? "bg-accent-primary border-accent-primary animate-orbit-pulse"
                  : "bg-ink-primary border-bg-surface animate-orbit-pulse-light"
              } ${
                isDragging
                  ? "scale-125 !animate-none shadow-[0_0_12px_rgba(232,118,90,0.9)]"
                  : ""
              }`}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

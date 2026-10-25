"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { playToggleClick } from "@/lib/keyboardSound";

interface TransitionEventDetail {
  onComplete?: (nextDark: boolean) => void;
  nextDark?: boolean;
}

const THEME_EVENT_NAME = "allcited:trigger-theme-transition";

type TransitionCallback = (nextDark?: boolean, onComplete?: (nextDark: boolean) => void) => void;
let activeTrigger: TransitionCallback | null = null;

export function registerThemeTransition(fn: TransitionCallback) {
  activeTrigger = fn;
  return () => {
    if (activeTrigger === fn) activeTrigger = null;
  };
}

/**
 * Global trigger to launch the simultaneous theme shift and screen-center expanding triangle animation.
 * Immediately applies theme classes while the equilateral triangle expands smoothly from the center.
 */
export function executeThemeTransition(
  targetDark?: boolean,
  onComplete?: (nextDark: boolean) => void
): void {
  if (typeof window === "undefined") return;

  if (activeTrigger) {
    activeTrigger(targetDark, onComplete);
    return;
  }

  window.dispatchEvent(
    new CustomEvent<TransitionEventDetail>(THEME_EVENT_NAME, {
      detail: { nextDark: targetDark, onComplete },
    })
  );
}

export function ThemeTransitionOverlay() {
  const [isActive, setIsActive] = useState(false);
  const [isNextDark, setIsNextDark] = useState(false);
  const isAnimatingRef = useRef(false);

  const startAnimation = useCallback(
    (explicitNextDark?: boolean, onComplete?: (nextDark: boolean) => void) => {
      if (isAnimatingRef.current) return;
      isAnimatingRef.current = true;

      const currentIsDark = document.documentElement.classList.contains("dark");
      const nextDark = explicitNextDark !== undefined ? explicitNextDark : !currentIsDark;

      setIsNextDark(nextDark);
      setIsActive(true);

      // 1. Simultaneous theme conversion across app
      if (nextDark) {
        document.documentElement.classList.add("dark");
        localStorage.setItem("allcited_theme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        localStorage.setItem("allcited_theme", "light");
      }

      // Silent trigger
      playToggleClick();
      onComplete?.(nextDark);

      // 2. Hardware 380ms GPU compositor animation
      const tFinish = setTimeout(() => {
        setIsActive(false);
        isAnimatingRef.current = false;
      }, 400);

      return () => {
        clearTimeout(tFinish);
        isAnimatingRef.current = false;
      };
    },
    []
  );

  useEffect(() => {
    const unregister = registerThemeTransition((targetDark, cb) => {
      startAnimation(targetDark, cb);
    });

    const handleEvent = (event: Event) => {
      const customEvent = event as CustomEvent<TransitionEventDetail>;
      startAnimation(customEvent.detail?.nextDark, customEvent.detail?.onComplete);
    };

    window.addEventListener(THEME_EVENT_NAME, handleEvent);
    return () => {
      unregister();
      window.removeEventListener(THEME_EVENT_NAME, handleEvent);
    };
  }, [startAnimation]);

  if (!isActive) return null;

  // Mode-relative edge styling:
  // - Dark Mode target: Crisp dark perimeter edge with subtle warm vermillion halo
  // - Light Mode target: Luminous warm white perimeter edge with subtle amber halo
  const strokeColor = isNextDark ? "#2A2826" : "#FFFFFF";
  const haloColor = isNextDark ? "rgba(232, 118, 90, 0.35)" : "rgba(232, 176, 75, 0.4)";
  const innerFill = isNextDark ? "rgba(13, 12, 11, 0.03)" : "rgba(245, 242, 234, 0.04)";
  const vertexColor = isNextDark ? "#E8765A" : "#9A5B00";

  return (
    <div
      id="allcited-screen-center-triangle-overlay"
      aria-hidden="true"
      className="fixed inset-0 z-[999999] pointer-events-none select-none flex items-center justify-center overflow-hidden"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: "100vw",
        height: "100vh",
        contain: "strict",
      }}
    >
      <style>{`
        @keyframes allcitedTriangleLifecycle {
          0% {
            transform: translate3d(0, 0, 0) scale3d(0.08, 0.08, 1) rotate(0deg);
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          65% {
            opacity: 0.85;
          }
          100% {
            transform: translate3d(0, 0, 0) scale3d(12, 12, 1) rotate(8deg);
            opacity: 0;
          }
        }

        .allcited-triangle-lifecycle {
          animation: allcitedTriangleLifecycle 380ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
          transform-origin: center center;
          will-change: transform, opacity;
          backface-visibility: hidden;
          -webkit-backface-visibility: hidden;
        }
      `}</style>

      {/* Screen-Center Expanding Triangle Container with Hardware 3D Compositing */}
      <div className="relative flex items-center justify-center allcited-triangle-lifecycle">
        <svg
          viewBox="-120 -120 240 240"
          className="overflow-visible pointer-events-none"
          style={{
            width: "220px",
            height: "220px",
          }}
        >
          {/* Subtle luminous halo edge */}
          <polygon
            points="0,-115.47 100,57.74 -100,57.74"
            fill="none"
            stroke={haloColor}
            strokeWidth={isNextDark ? 6 : 7}
            vectorEffect="non-scaling-stroke"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Precision geometric edge with non-scaling stroke */}
          <polygon
            points="0,-115.47 100,57.74 -100,57.74"
            fill={innerFill}
            stroke={strokeColor}
            strokeWidth={isNextDark ? 2 : 2.5}
            vectorEffect="non-scaling-stroke"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Precision vertex accents */}
          <circle cx="0" cy="-115.47" r="3" fill={vertexColor} vectorEffect="non-scaling-stroke" />
          <circle cx="100" cy="57.74" r="3" fill={vertexColor} vectorEffect="non-scaling-stroke" />
          <circle cx="-100" cy="57.74" r="3" fill={vertexColor} vectorEffect="non-scaling-stroke" />
        </svg>
      </div>
    </div>
  );
}

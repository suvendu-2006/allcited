"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";

/**
 * Ember Aurora Hero Background (§6.1 v2.1)
 *
 * Implements the 4-layer stacked "Ink & Ember" hero:
 * - L1 Base: Warm Ink #0D0C0B (dark) / Paper #F5F2EA (light).
 * - L2 Three Drifting Ember Glows:
 *   - Vermillion (#E8765A) @ 12% top-left (60vmax, 16s loop)
 *   - Amber (#E8B04B) @ 8% right (45vmax, 20s loop)
 *   - Deep Seal (#A6362F) @ 6% bottom (35vmax, 22s loop)
 *   (Light theme renders same glows at 1/3 opacity)
 * - L3 SVG Film Grain Overlay (feTurbulence fractalNoise 4% opacity).
 * - L4 Cursor Spotlight (vermillion @ 5%, 30vmax, 200ms lerp).
 * - Scrim gradient guaranteeing WCAG AA contrast >= 4.5:1 over text zone.
 */
export function EmberAurora() {
  const shouldReduceMotion = useReducedMotion();
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (shouldReduceMotion) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      if (
        e.clientX >= rect.left &&
        e.clientX <= rect.right &&
        e.clientY >= rect.top &&
        e.clientY <= rect.bottom
      ) {
        setMousePos({
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
        });
      }
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [shouldReduceMotion]);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0"
    >
      {/* L1: Base Warm-Ink / Paper (#0D0C0B dark / #F5F2EA light) */}
      <div className="absolute inset-0 bg-[#F5F2EA] dark:bg-[#0D0C0B] transition-colors duration-500" />

      {/* L2: Three Drifting Ember Glows per §6.1 */}
      {/* Glow 1: Vermillion (#E8765A) Top-Left */}
      <motion.div
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: ["-6%", "4%", "-4%", "-6%"],
                y: ["-4%", "6%", "-2%", "-4%"],
              }
        }
        transition={{
          duration: 16,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute -top-[10vmax] -left-[10vmax] w-[60vmax] h-[60vmax] rounded-full blur-[90px] opacity-4 dark:opacity-12 bg-[#E8765A] will-change-transform"
      />

      {/* Glow 2: Amber (#E8B04B) Right */}
      <motion.div
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: ["4%", "-6%", "2%", "4%"],
                y: ["6%", "-4%", "5%", "6%"],
              }
        }
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute top-[10vmax] -right-[15vmax] w-[45vmax] h-[45vmax] rounded-full blur-[90px] opacity-3 dark:opacity-8 bg-[#E8B04B] will-change-transform"
      />

      {/* Glow 3: Deep Seal (#A6362F) Bottom */}
      <motion.div
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: ["-5%", "5%", "-3%", "-5%"],
                y: ["3%", "-5%", "4%", "3%"],
              }
        }
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute -bottom-[10vmax] left-[25vmax] w-[35vmax] h-[35vmax] rounded-full blur-[90px] opacity-2 dark:opacity-6 bg-[#A6362F] will-change-transform"
      />

      {/* L3: SVG Film Grain Overlay (feTurbulence fractalNoise) per §6.1 */}
      <svg
        className="absolute inset-0 w-full h-full opacity-4 mix-blend-overlay"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="ember-grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.8"
            numOctaves="3"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#ember-grain)" />
      </svg>

      {/* L4: Pointer-Following Spotlight Glow per §6.1 */}
      {mousePos && !shouldReduceMotion && (
        <div
          className="absolute w-[30vmax] h-[30vmax] rounded-full blur-[80px] opacity-3 dark:opacity-5 bg-[#E8765A] transition-transform duration-200 ease-out will-change-transform"
          style={{
            transform: `translate(${mousePos.x - 200}px, ${mousePos.y - 200}px)`,
          }}
        />
      )}

      {/* Scrim Gradient to guarantee WCAG AA contrast over text zone per §6.1 */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-bg-base/35 to-bg-base/90 pointer-events-none" />
    </div>
  );
}

// Alias for backward compatibility
export const DeepSeaAurora = EmberAurora;

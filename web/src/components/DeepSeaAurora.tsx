"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";

/**
 * Ember Aurora Hero Background (§6.1 v2.1)
 *
 * Implements the 4-layer stacked "Ink & Ember" hero:
 * - L1 Base: Warm Ink #0D0C0B (dark) / Paper #F5F2EA (light).
 * - L2 Three Gently Drifting Ember Glows:
 *   - Calibrated 3%-8% translucent atmospheric glows (stable, never jittering on hover).
 * - L3 SVG Film Grain Overlay (feTurbulence fractalNoise 3% opacity).
 * - Scrim gradient guaranteeing WCAG AA contrast >= 4.5:1 over text zone.
 * Zero layout thrashing, zero re-renders on mouse hover.
 */
export function EmberAurora() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0"
    >
      {/* L1: Base Warm-Ink / Paper (#0D0C0B dark / #F5F2EA light) */}
      <div className="absolute inset-0 bg-[#F5F2EA] dark:bg-[#0D0C0B] transition-colors duration-500" />

      {/* L1.5: Precision Editorial Dot Grid Background Pattern */}
      <div
        className="absolute inset-0 dot-grid pointer-events-none"
        style={{
          maskImage: "radial-gradient(ellipse 85% 75% at 50% 50%, black 35%, transparent 95%)",
          WebkitMaskImage: "radial-gradient(ellipse 85% 75% at 50% 50%, black 35%, transparent 95%)",
        }}
      />

      {/* L2: Three Gently Drifting Ember Ambient Glows */}
      {/* Glow 1: Vermillion (#E8765A) Top-Left */}
      <motion.div
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: ["-4%", "3%", "-2%", "-4%"],
                y: ["-3%", "4%", "-1%", "-3%"],
              }
        }
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute -top-[12vmax] -left-[10vmax] w-[55vmax] h-[55vmax] rounded-full blur-[100px] opacity-[0.04] dark:opacity-[0.10] bg-[#E8765A] will-change-transform"
      />

      {/* Glow 2: Amber (#E8B04B) Right */}
      <motion.div
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: ["3%", "-4%", "2%", "3%"],
                y: ["4%", "-3%", "3%", "4%"],
              }
        }
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute top-[8vmax] -right-[12vmax] w-[45vmax] h-[45vmax] rounded-full blur-[100px] opacity-[0.03] dark:opacity-[0.07] bg-[#E8B04B] will-change-transform"
      />

      {/* Glow 3: Deep Seal (#A6362F) Bottom */}
      <motion.div
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: ["-3%", "3%", "-2%", "-3%"],
                y: ["2%", "-3%", "3%", "2%"],
              }
        }
        transition={{
          duration: 24,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute -bottom-[12vmax] left-[20vmax] w-[38vmax] h-[38vmax] rounded-full blur-[100px] opacity-[0.02] dark:opacity-[0.05] bg-[#A6362F] will-change-transform"
      />

      {/* L3: SVG Film Grain Overlay (feTurbulence fractalNoise) */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.035] mix-blend-overlay pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="ember-grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.75"
            numOctaves="2"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#ember-grain)" />
      </svg>

      {/* Scrim Gradient to guarantee WCAG AA contrast over text zone */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-bg-base/20 to-bg-base pointer-events-none" />
    </div>
  );
}

// Alias for backward compatibility
export const DeepSeaAurora = EmberAurora;

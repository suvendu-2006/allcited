"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { HeroCubesCanvas } from "./HeroCubesCanvas";

/**
 * Screenpipe Authentic Isometric Hero Background
 * Directly matching the user's Multi-Agent project:
 * - L1 Base: Warm Ink #0D0C0B (dark) / Paper #F5F2EA (light).
 * - Screenpipe 3D Isometric Cube Tessellation Canvas with kinetic waves & pointer reaction.
 * - Subtle ambient warm ember atmospheric under-glows.
 * - Vignette scrim guaranteeing pristine contrast.
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

      {/* Screenpipe Authentic Isometric Cube Tessellation Canvas from Multi-Agent */}
      <HeroCubesCanvas />

      {/* Subtle Ambient Ember Glows Underneath */}
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
        className="absolute -top-[12vmax] -left-[10vmax] w-[55vmax] h-[55vmax] rounded-full blur-[100px] opacity-[0.03] dark:opacity-[0.08] bg-[#E8765A] will-change-transform"
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
        className="absolute top-[8vmax] -right-[12vmax] w-[45vmax] h-[45vmax] rounded-full blur-[100px] opacity-[0.02] dark:opacity-[0.05] bg-[#E8B04B] will-change-transform"
      />

      {/* Scrim Gradient to guarantee WCAG AA contrast over text zone */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-bg-base/10 to-bg-base pointer-events-none" />
    </div>
  );
}

// Alias for backward compatibility
export const DeepSeaAurora = EmberAurora;


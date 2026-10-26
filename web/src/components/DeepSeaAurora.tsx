"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { HeroCubesCanvas } from "./HeroCubesCanvas";

/**
 * Screenpipe Authentic Isometric Hero Background
 * - Unified 3D Isometric Cube Tessellation Canvas (HeroCubesCanvas) across both Light and Dark modes.
 * - Light Mode: Studio off-white canvas (#F6F6F2) with crisp isometric tumbling cubes and interactive ripples.
 * - Dark Mode: Restored Warm-Ink (#0D0C0B) with subtle ambient ember glows (#E8765A, #E8B04B) and dark isometric grid.
 */
export function EmberAurora() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0"
    >
      {/* Light Mode Studio Base Canvas */}
      <div
        className="absolute inset-0 transition-colors duration-500 bg-[#F6F6F2] dark:hidden"
        style={{
          background:
            "radial-gradient(ellipse 95% 80% at 50% 38%, #FAFBFB 0%, #F5F5F0 50%, #ECECE6 100%)",
        }}
      />

      {/* Dark Mode Warm-Ink Base Canvas (#0D0C0B) */}
      <div
        className="hidden dark:block absolute inset-0 transition-colors duration-500 bg-[#0D0C0B]"
        style={{
          background:
            "radial-gradient(ellipse 95% 80% at 50% 38%, #141312 0%, #0D0C0B 50%, #080807 100%)",
        }}
      />

      {/* 3D Isometric Cube Tessellation Canvas (Universal: Light & Dark Mode) */}
      <HeroCubesCanvas />

      {/* Dark Mode ONLY: Ambient Drifting Ember Glows */}
      <div className="hidden dark:block absolute inset-0 pointer-events-none">
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
          className="absolute -top-[12vmax] -left-[10vmax] w-[55vmax] h-[55vmax] rounded-full blur-[100px] opacity-[0.08] bg-[#E8765A] will-change-transform"
        />

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
          className="absolute top-[8vmax] -right-[12vmax] w-[45vmax] h-[45vmax] rounded-full blur-[100px] opacity-[0.05] bg-[#E8B04B] will-change-transform"
        />
      </div>

      {/* Scrim Gradient for text contrast */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-bg-base/5 to-bg-base dark:via-bg-base/10 pointer-events-none" />
    </div>
  );
}

// Alias for backward compatibility
export const DeepSeaAurora = EmberAurora;

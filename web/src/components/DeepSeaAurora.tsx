"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { HeroCubesCanvas } from "./HeroCubesCanvas";

/**
 * Screenpipe Authentic Isometric Hero Background
 * - Light Mode: Clean neutral canvas (#F6F6F3 with studio radial illumination) & pure monochromatic cube relief
 * - Dark Mode: Restored Warm-Ink (#0D0C0B) with subtle ambient ember glows (#E8765A, #E8B04B) and warm kinetic tessellation
 */
export function EmberAurora() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0"
    >
      {/* Light Mode: Clean Neutral Studio Canvas matching Screenpipe */}
      <div
        className="absolute inset-0 transition-colors duration-500 bg-[#F6F6F3] dark:hidden"
        style={{
          background:
            "radial-gradient(ellipse 100% 85% at 50% 35%, #FAFBFB 0%, #F6F6F3 40%, #EEEEEC 100%)",
        }}
      />

      {/* Dark Mode: Restored Warm-Ink Base (#0D0C0B) */}
      <div
        className="hidden dark:block absolute inset-0 transition-colors duration-500 bg-[#0D0C0B]"
        style={{
          background:
            "radial-gradient(ellipse 95% 80% at 50% 38%, #141312 0%, #0D0C0B 50%, #080807 100%)",
        }}
      />

      {/* 3D Isometric Cube Tessellation Canvas */}
      <HeroCubesCanvas />

      {/* Dark Mode ONLY: Ambient Drifting Ember Glows */}
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
        className="hidden dark:block absolute -top-[12vmax] -left-[10vmax] w-[55vmax] h-[55vmax] rounded-full blur-[100px] opacity-[0.08] bg-[#E8765A] will-change-transform"
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
        className="hidden dark:block absolute top-[8vmax] -right-[12vmax] w-[45vmax] h-[45vmax] rounded-full blur-[100px] opacity-[0.05] bg-[#E8B04B] will-change-transform"
      />

      {/* Dark Mode ONLY: Scrim Gradient for text contrast */}
      <div className="hidden dark:block absolute inset-0 bg-gradient-to-b from-transparent via-bg-base/10 to-bg-base pointer-events-none" />
    </div>
  );
}

// Alias for backward compatibility
export const DeepSeaAurora = EmberAurora;


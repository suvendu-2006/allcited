"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { HeroCubesCanvas } from "./HeroCubesCanvas";

/**
 * Screenpipe Authentic Isometric Hero Background
 * - Light Mode: Exact Screenpipe 3D isometric cube relief vector pattern (41px x 71px tile) with studio radial illumination
 * - Dark Mode: Restored Warm-Ink (#0D0C0B) with subtle ambient ember glows (#E8765A, #E8B04B) and dark isometric grid
 */
export function EmberAurora() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0"
    >
      {/* Light Mode: Exact Screenpipe 3D Isometric Cube Relief Vector Pattern */}
      <div className="absolute inset-0 dark:hidden">
        <svg
          className="w-full h-full block"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="none"
        >
          <defs>
            <pattern
              id="screenpipe-cubes-pattern"
              width="41"
              height="71"
              patternUnits="userSpaceOnUse"
            >
              {/* Cube 1 (centered at 20.5, 35.5) */}
              <polygon
                points="20.5,11.835 41,23.665 20.5,35.5 0,23.665"
                fill="#F3F3F0"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="0,23.665 20.5,35.5 20.5,59.165 0,47.335"
                fill="#EFEFEA"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="20.5,35.5 41,23.665 41,47.335 20.5,59.165"
                fill="#F1F1EC"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />

              {/* Cube 2 corners (tiled at 0,0 / 41,0 / 0,71 / 41,71) */}
              <polygon
                points="0,-23.665 20.5,-11.835 0,0 -20.5,-11.835"
                fill="#F3F3F0"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="-20.5,-11.835 0,0 0,23.665 -20.5,11.835"
                fill="#EFEFEA"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="0,0 20.5,-11.835 20.5,11.835 0,23.665"
                fill="#F1F1EC"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />

              <polygon
                points="41,-23.665 61.5,-11.835 41,0 20.5,-11.835"
                fill="#F3F3F0"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="20.5,-11.835 41,0 41,23.665 20.5,11.835"
                fill="#EFEFEA"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="41,0 61.5,-11.835 61.5,11.835 41,23.665"
                fill="#F1F1EC"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />

              <polygon
                points="0,47.335 20.5,59.165 0,71 -20.5,59.165"
                fill="#F3F3F0"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="-20.5,59.165 0,71 0,94.665 -20.5,82.835"
                fill="#EFEFEA"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="0,71 20.5,59.165 20.5,82.835 0,94.665"
                fill="#F1F1EC"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />

              <polygon
                points="41,47.335 61.5,59.165 41,71 20.5,59.165"
                fill="#F3F3F0"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="20.5,59.165 41,71 41,94.665 20.5,82.835"
                fill="#EFEFEA"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
              <polygon
                points="41,71 61.5,59.165 61.5,82.835 41,94.665"
                fill="#F1F1EC"
                stroke="#ECECE7"
                strokeWidth="0.5"
                strokeLinejoin="round"
              />
            </pattern>

            {/* Studio Radial Illumination Overlay matching Screenpipe */}
            <radialGradient id="screenpipe-studio-light" cx="50%" cy="35%" r="60%">
              <stop offset="0%" stopColor="#FAFBFB" stopOpacity="0.35" />
              <stop offset="60%" stopColor="#FAFBFB" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#E8E8E3" stopOpacity="0.2" />
            </radialGradient>
          </defs>

          {/* Base Neutral Canvas */}
          <rect width="100%" height="100%" fill="#F0F0EB" />
          {/* Tiled Screenpipe Isometric Cubes */}
          <rect width="100%" height="100%" fill="url(#screenpipe-cubes-pattern)" />
          {/* Studio Radial Vignette */}
          <rect width="100%" height="100%" fill="url(#screenpipe-studio-light)" />
        </svg>
      </div>

      {/* Dark Mode ONLY: Restored Warm-Ink Base (#0D0C0B) and Grid */}
      <div className="hidden dark:block absolute inset-0">
        <div
          className="absolute inset-0 bg-[#0D0C0B]"
          style={{
            background:
              "radial-gradient(ellipse 95% 80% at 50% 38%, #141312 0%, #0D0C0B 50%, #080807 100%)",
          }}
        />

        {/* 3D Isometric Cube Tessellation Canvas (Dark Mode) */}
        <HeroCubesCanvas />

        {/* Ambient Drifting Ember Glows */}
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

        {/* Scrim Gradient for text contrast */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-bg-base/10 to-bg-base pointer-events-none" />
      </div>
    </div>
  );
}

// Alias for backward compatibility
export const DeepSeaAurora = EmberAurora;


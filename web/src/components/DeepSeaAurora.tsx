"use client";

import React from "react";
import { HeroCubesCanvas } from "./HeroCubesCanvas";

/**
 * Screenpipe Authentic Isometric Hero Background
 * Directly matching Screenpipe (Image 2):
 * - Clean neutral canvas: #F6F6F3 with subtle studio radial illumination (#FAFAFA center to #EDEDEA edges)
 * - Pure monochromatic isometric 3D cube relief with top-face white specular highlights
 * - Zero colored blobs (no orange/amber contamination)
 */
export function EmberAurora() {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0"
    >
      {/* L1: Clean Neutral Studio Canvas matching Screenpipe */}
      <div
        className="absolute inset-0 transition-colors duration-500 bg-[#F6F6F3] dark:bg-[#0D0C0B]"
        style={{
          background:
            "radial-gradient(ellipse 100% 85% at 50% 35%, #FAFBFB 0%, #F6F6F3 40%, #EEEEEC 100%)",
        }}
      />
      <div
        className="hidden dark:block absolute inset-0 transition-colors duration-500"
        style={{
          background:
            "radial-gradient(ellipse 95% 80% at 50% 38%, #141312 0%, #0D0C0B 50%, #080807 100%)",
        }}
      />

      {/* Screenpipe Authentic Isometric Cube Tessellation Canvas */}
      <HeroCubesCanvas />
    </div>
  );
}

// Alias for backward compatibility
export const DeepSeaAurora = EmberAurora;


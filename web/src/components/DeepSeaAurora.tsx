"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";

export function DeepSeaAurora() {
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
      {/* L1: Base petrol (#041A16 dark / #FAF8ED light) */}
      <div className="absolute inset-0 bg-[#FAF8ED] dark:bg-[#041A16] transition-colors duration-500" />

      {/* L2: Three Drifting Aurora Glows per §6.1 */}
      {/* Glow 1: Teal (#31C7A5) Top-Left */}
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
        className="absolute -top-[10vmax] -left-[10vmax] w-[60vmax] h-[60vmax] rounded-full blur-[90px] opacity-25 dark:opacity-15 bg-[#034F46] dark:bg-[#31C7A5] will-change-transform"
      />

      {/* Glow 2: Mint (#5AD46F) Right */}
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
        className="absolute top-[10vmax] -right-[15vmax] w-[45vmax] h-[45vmax] rounded-full blur-[90px] opacity-20 dark:opacity-10 bg-[#28C840] dark:bg-[#5AD46F] will-change-transform"
      />

      {/* Glow 3: Amber (#E8B04B) Bottom */}
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
        className="absolute -bottom-[10vmax] left-[25vmax] w-[35vmax] h-[35vmax] rounded-full blur-[90px] opacity-15 dark:opacity-8 bg-[#FEBC2E] dark:bg-[#E8B04B] will-change-transform"
      />

      {/* L3: SVG Film Grain Overlay (feTurbulence fractalNoise) per §6.1 */}
      <svg
        className="absolute inset-0 w-full h-full opacity-4 mix-blend-overlay"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="aurora-grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.8"
            numOctaves="3"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#aurora-grain)" />
      </svg>

      {/* L4: Pointer-Following Spotlight Glow per §6.1 */}
      {mousePos && !shouldReduceMotion && (
        <div
          className="absolute w-[30vmax] h-[30vmax] rounded-full blur-[80px] opacity-15 dark:opacity-8 bg-accent-primary transition-transform duration-200 ease-out will-change-transform"
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

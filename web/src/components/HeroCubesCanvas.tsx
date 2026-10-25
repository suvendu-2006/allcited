"use client";

import React, { useEffect, useRef } from "react";

/**
 * Screenpipe Authentic Isometric Cube Tessellation Canvas
 * Directly ported from the user's Multi-Agent project.
 * Renders the 3D isometric tumbling-cube / rhombic geometric grid with
 * kinetic ambient waves and interactive pointer ripple reactions.
 */
export function HeroCubesCanvas() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let dpr = 1;
    let animId = 0;

    let isDark = false;
    let monoRgb: [number, number, number] = [26, 25, 24];

    const updateColors = () => {
      isDark = document.documentElement.classList.contains("dark");
      monoRgb = isDark ? [239, 234, 217] : [26, 25, 24];
    };

    updateColors();
    const observer = new MutationObserver(updateColors);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

    // Screenpipe geometric constants
    const h = 34 * Math.sqrt(3); // Column horizontal spacing (~58.89px)
    const angleRad = (e: number) => (Math.PI / 180) * (60 * e - 90);
    const vertices = [0, 1, 2, 3, 4, 5].map((e) => [
      34 * Math.cos(angleRad(e)),
      34 * Math.sin(angleRad(e)),
    ]);
    // 3 isometric rhombus faces per cube (-1 represents the cube center)
    const faces = [
      [0, 1, -1, 5],
      [1, 2, 3, -1],
      [5, -1, 3, 4],
    ];

    const resize = () => {
      dpr = Math.min(2, window.devicePixelRatio || 1);
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = Math.max(1, Math.round(width * dpr));
      canvas.height = Math.max(1, Math.round(height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
    const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);
    let time = 0;
    let mouseX = 0;
    let mouseY = 0;
    let curX = 0;
    let curY = 0;
    let hasMouse = false;

    const onPointerMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
      hasMouse = true;
    };
    window.addEventListener("pointermove", onPointerMove);

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      const centerX = 0.5 * width;
      const centerY = 0.44 * height;
      if (!hasMouse) {
        curX = centerX;
        curY = centerY;
      } else {
        curX += (mouseX - curX) * 0.08;
        curY += (mouseY - curY) * 0.08;
      }

      const [rVal, gVal, bVal] = monoRgb;
      const cols = Math.ceil(width / h) + 2;
      const rows = Math.ceil(height / 51) + 2;

      for (let r = -1; r < rows; r++) {
        const y = 51 * r;
        for (let c = -1; c < cols; c++) {
          const x = c * h + ((r & 1) ? h / 2 : 0);
          const distCenter = Math.hypot(x - centerX, y - centerY);
          const distPointer = Math.hypot(x - curX, y - curY);

          // Kinetic ambient wave + interactive pointer ripple
          const wave = Math.sin(time * 1.5 - 0.012 * distCenter);
          const pointerWave = hasMouse
            ? Math.sin(time * 3.2 - 0.025 * distPointer) * Math.max(0, 1 - distPointer / 420)
            : 0;
          const k = clamp01((wave + pointerWave * 0.8 + 1) / 2);

          const yDist = clamp01(1 - distCenter / (0.85 * Math.max(width, height)));
          const baseAlpha = isDark ? 0.02 : 0.012;
          const faceAlphas = [
            lerp(baseAlpha, baseAlpha * 3.2, k),
            lerp(baseAlpha * 3.2, baseAlpha, k),
            baseAlpha * 1.8 + baseAlpha * k,
          ];

          for (let f = 0; f < 3; f++) {
            const face = faces[f];
            ctx.beginPath();
            for (let pt = 0; pt < 4; pt++) {
              const idx = face[pt];
              const px = idx < 0 ? x : x + vertices[idx][0];
              const py = idx < 0 ? y : y + vertices[idx][1];
              if (pt === 0) ctx.moveTo(px, py);
              else ctx.lineTo(px, py);
            }
            ctx.closePath();
            ctx.fillStyle = `rgba(${rVal},${gVal},${bVal},${faceAlphas[f]})`;
            ctx.fill();
            ctx.lineWidth = 0.75;
            const strokeAlpha = (isDark ? 0.08 : 0.055) + 0.04 * yDist;
            ctx.strokeStyle = `rgba(${rVal},${gVal},${bVal},${strokeAlpha})`;
            ctx.stroke();
          }
        }
      }

      time += 0.018;
    };

    const handleResize = () => {
      resize();
      render();
    };

    resize();
    render();
    window.addEventListener("resize", handleResize);

    const loop = () => {
      render();
      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("pointermove", onPointerMove);
      observer.disconnect();
    };
  }, []);

  return (
    <>
      {/* 3D Isometric Tessellation Canvas - Pure Neutral Monochromatic Grid */}
      <canvas
        ref={canvasRef}
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 opacity-80 dark:opacity-75"
        style={{ display: "block", width: "100%", height: "100%" }}
      />
      {/* Soft edge vignette to smoothly blend into the section borders */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 opacity-40 dark:opacity-60"
        style={{
          background:
            "radial-gradient(ellipse 85% 75% at 50% 50%, transparent 35%, var(--bg-base) 100%)",
        }}
      />
    </>
  );
}

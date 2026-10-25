/**
 * Water-Drop Sea Ripple Wave Animation Engine
 *
 * Implements a physics-based water droplet impact and concentric propagating
 * sea ripple wave animation across the viewport.
 *
 * - Impact: Droplet strikes at the toggle dial's coordinates (x, y).
 * - Concentric Ripples: 3-4 organic liquid wave crests expand outward across the sea.
 * - Theme Wash: Site shifts into the new theme as the primary liquid crest sweeps through.
 * - Fluid Dissipation: Ripples dampen smoothly as they reach the outer horizon.
 * - Universal Browser Compatibility: Hardware-accelerated Canvas 2D overlay;
 *   100% reliable across Chrome, Safari on macOS, Firefox, and mobile.
 */

interface RippleCoordinates {
  x: number;
  y: number;
}

export function executeWaterDropRipple(
  coords: RippleCoordinates | null,
  isDarkNext: boolean,
  applyTheme: () => void
): void {
  if (typeof window === "undefined" || typeof document === "undefined") {
    applyTheme();
    return;
  }

  // Check prefers-reduced-motion
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    applyTheme();
    return;
  }

  const originX = coords?.x ?? window.innerWidth - 45;
  const originY = coords?.y ?? 28;

  const width = window.innerWidth;
  const height = window.innerHeight;
  const maxRadius = Math.hypot(
    Math.max(originX, width - originX),
    Math.max(originY, height - originY)
  ) * 1.15;

  // Create full-screen Canvas overlay
  const canvas = document.createElement("canvas");
  canvas.className = "water-ripple-canvas";
  canvas.style.position = "fixed";
  canvas.style.inset = "0";
  canvas.style.width = "100vw";
  canvas.style.height = "100vh";
  canvas.style.pointerEvents = "none";
  canvas.style.zIndex = "99999";
  document.body.appendChild(canvas);

  const rawCtx = canvas.getContext("2d");
  if (!rawCtx) {
    canvas.remove();
    applyTheme();
    return;
  }
  const ctx = rawCtx;

  // Handle Retina displays
  const dpr = window.devicePixelRatio || 1;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  let themeApplied = false;
  const startTime = performance.now();
  const totalDuration = 880; // ms

  // Ripple configuration
  const waveCount = 4;
  const waveSpacing = 65; // px between concentric wave crests

  function easeOutCubic(t: number): number {
    return 1 - Math.pow(1 - t, 3);
  }

  function renderFrame(now: number) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / totalDuration, 1);
    const easeProgress = easeOutCubic(progress);

    // Apply the theme at ~35% when the primary wave has covered the immediate area
    if (!themeApplied && progress >= 0.32) {
      applyTheme();
      themeApplied = true;

      // Update meta theme-color
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        metaThemeColor.setAttribute("content", isDarkNext ? "#0D0C0B" : "#F5F2EA");
      }
    }

    ctx.clearRect(0, 0, width, height);

    const primaryRadius = easeProgress * maxRadius;

    // Draw concentric ripples from outermost to innermost
    for (let i = 0; i < waveCount; i++) {
      const ringRadius = primaryRadius - i * waveSpacing;
      if (ringRadius <= 0) continue;

      // Ring progress and amplitude decay
      const ringFraction = ringRadius / maxRadius;
      const ringProgress = Math.max(0, 1 - ringFraction);
      // Fade out near the end of the total animation
      const globalFade = 1 - Math.pow(progress, 4);
      const ringOpacity = Math.sin(ringProgress * Math.PI) * 0.45 * globalFade;

      if (ringOpacity <= 0.005) continue;

      ctx.save();

      // Fluid harmonic wave contour (undulating water crest)
      ctx.beginPath();
      const points = 64;
      const harmonicAmp = Math.max(1.5, (1 - ringFraction) * 4);
      const phase = elapsed * 0.006 + i * 1.2;

      for (let p = 0; p <= points; p++) {
        const theta = (p / points) * Math.PI * 2;
        const offset =
          Math.sin(theta * 5 + phase) * harmonicAmp +
          Math.cos(theta * 3 - phase) * (harmonicAmp * 0.6);
        const r = Math.max(0, ringRadius + offset);
        const px = originX + r * Math.cos(theta);
        const py = originY + r * Math.sin(theta);

        if (p === 0) {
          ctx.moveTo(px, py);
        } else {
          ctx.lineTo(px, py);
        }
      }
      ctx.closePath();

      // Palette: glowing ember crests into dark; deep ink / paper ripples into light
      if (isDarkNext) {
        // Switching into dark: ember & vermillion liquid ripples
        if (i === 0) {
          // Primary leading wave: vibrant vermillion crest
          ctx.strokeStyle = `rgba(232, 118, 90, ${ringOpacity.toFixed(3)})`;
          ctx.lineWidth = 3.5;
          ctx.shadowColor = "rgba(232, 118, 90, 0.5)";
          ctx.shadowBlur = 12;
        } else if (i === 1) {
          // Secondary crest: golden amber ripple
          ctx.strokeStyle = `rgba(232, 176, 75, ${(ringOpacity * 0.85).toFixed(3)})`;
          ctx.lineWidth = 2.5;
          ctx.shadowColor = "rgba(232, 176, 75, 0.35)";
          ctx.shadowBlur = 8;
        } else {
          // Inner ripples: subtle deep warm seal
          ctx.strokeStyle = `rgba(166, 54, 47, ${(ringOpacity * 0.6).toFixed(3)})`;
          ctx.lineWidth = 1.8;
          ctx.shadowBlur = 0;
        }
      } else {
        // Switching into light: deep ink water ripples with warm paper highlight
        if (i === 0) {
          ctx.strokeStyle = `rgba(26, 25, 24, ${(ringOpacity * 0.9).toFixed(3)})`;
          ctx.lineWidth = 3.5;
          ctx.shadowColor = "rgba(26, 25, 24, 0.35)";
          ctx.shadowBlur = 10;
        } else if (i === 1) {
          ctx.strokeStyle = `rgba(154, 91, 0, ${(ringOpacity * 0.75).toFixed(3)})`;
          ctx.lineWidth = 2.5;
          ctx.shadowColor = "rgba(154, 91, 0, 0.25)";
          ctx.shadowBlur = 6;
        } else {
          ctx.strokeStyle = `rgba(113, 113, 106, ${(ringOpacity * 0.5).toFixed(3)})`;
          ctx.lineWidth = 1.8;
          ctx.shadowBlur = 0;
        }
      }

      ctx.stroke();

      // Subtle water wash fill behind primary wave
      if (i === 0 && ringOpacity > 0.05) {
        ctx.fillStyle = isDarkNext
          ? `rgba(13, 12, 11, ${(ringOpacity * 0.2).toFixed(3)})`
          : `rgba(245, 242, 234, ${(ringOpacity * 0.25).toFixed(3)})`;
        ctx.fill();
      }

      ctx.restore();
    }

    // Impact droplet splash ring at the origin during the first 220ms
    if (elapsed < 220) {
      const dropProgress = elapsed / 220;
      const dropRadius = dropProgress * 28;
      const dropOpacity = (1 - dropProgress) * 0.7;

      ctx.save();
      ctx.beginPath();
      ctx.arc(originX, originY, dropRadius, 0, Math.PI * 2);
      ctx.strokeStyle = isDarkNext
        ? `rgba(232, 118, 90, ${dropOpacity.toFixed(3)})`
        : `rgba(26, 25, 24, ${dropOpacity.toFixed(3)})`;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    }

    if (progress < 1) {
      requestAnimationFrame(renderFrame);
    } else {
      // Clean up canvas
      if (!themeApplied) applyTheme();
      canvas.remove();
    }
  }

  requestAnimationFrame(renderFrame);
}

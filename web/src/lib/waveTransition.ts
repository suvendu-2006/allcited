/**
 * Theme Wave Transition Engine
 * According to ALLCITED.md §5
 *
 * Implements View Transitions API + WAAPI animated clip-path wave
 * with 5 morphing keyframes and seamless fallbacks.
 */

interface WaveCoordinates {
  x: number;
  y: number;
}

/**
 * Generate an 8-segment cubic bezier path approximating a wavy disc.
 * M + 8 C segments + Z
 */
function generateWavyDiscPath(
  cx: number,
  cy: number,
  baseRadius: number,
  amplitudeRatio: number,
  phaseRad: number
): string {
  if (baseRadius <= 0.1) {
    // Zero-radius point
    return `M ${cx} ${cy} ` +
      Array.from({ length: 8 }, () => `C ${cx} ${cy} ${cx} ${cy} ${cx} ${cy}`).join(" ") +
      " Z";
  }

  const N = 8;
  const step = (Math.PI * 2) / N;
  const points: { x: number; y: number }[] = [];

  // Compute 8 perimeter points modulated by sine wave
  for (let i = 0; i < N; i++) {
    const theta = i * step;
    // 3 wave crests around the circumference
    const r = baseRadius * (1 + amplitudeRatio * Math.sin(3 * theta + phaseRad));
    points.push({
      x: cx + r * Math.cos(theta),
      y: cy + r * Math.sin(theta),
    });
  }

  // Generate cubic control points (circle-tangent approximation factor k = 4/3 * tan(pi/(2*N)))
  const k = (4 / 3) * Math.tan(Math.PI / (2 * N));
  let d = `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)} `;

  for (let i = 0; i < N; i++) {
    const nextIdx = (i + 1) % N;
    const p0 = points[i];
    const p1 = points[nextIdx];

    const theta0 = i * step;
    const theta1 = (i + 1) * step;

    // Tangent vectors perpendicular to radius
    const cp1x = p0.x - k * baseRadius * Math.sin(theta0);
    const cp1y = p0.y + k * baseRadius * Math.cos(theta0);

    const cp2x = p1.x + k * baseRadius * Math.sin(theta1);
    const cp2y = p1.y - k * baseRadius * Math.cos(theta1);

    d += `C ${cp1x.toFixed(2)} ${cp1y.toFixed(2)}, ${cp2x.toFixed(2)} ${cp2y.toFixed(2)}, ${p1.x.toFixed(2)} ${p1.y.toFixed(2)} `;
  }

  d += "Z";
  return d;
}

export function executeThemeWave(
  coords: WaveCoordinates | null,
  isDarkNext: boolean,
  applyTheme: () => void
): void {
  // 1. Fallback for reduced motion or no document
  if (typeof window === "undefined" || typeof document === "undefined") {
    applyTheme();
    return;
  }

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // View Transitions API check
  const hasViewTransition = "startViewTransition" in document;

  if (!hasViewTransition || prefersReduced) {
    // 250ms CSS crossfade fallback
    applyTheme();
    return;
  }

  // 2. Wrap class flip in document.startViewTransition
  const transition = (document as unknown as { startViewTransition: (cb: () => void) => { ready: Promise<void> } }).startViewTransition(() => {
    applyTheme();
    // Update theme-color meta tag per §5.5
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute("content", isDarkNext ? "#06211D" : "#FAF8ED");
    }
  });

  // 3. Animate the transition
  transition.ready.then(() => {
    const x = coords?.x ?? window.innerWidth / 2;
    const y = coords?.y ?? 40;

    // Farthest corner distance
    const maxDistX = Math.max(x, window.innerWidth - x);
    const maxDistY = Math.max(y, window.innerHeight - y);
    const maxRadius = Math.hypot(maxDistX, maxDistY) * 1.1;

    // Precompute 5 keyframe paths
    // Radius growing 0.12R -> 0.95R with wave crest phase rotating ~140 deg
    // Crest amplitude 6% decaying to 2%
    const keyframeConfigs = [
      { r: 0.05 * maxRadius, amp: 0.06, phase: 0 },
      { r: 0.28 * maxRadius, amp: 0.05, phase: (35 * Math.PI) / 180 },
      { r: 0.55 * maxRadius, amp: 0.04, phase: (70 * Math.PI) / 180 },
      { r: 0.82 * maxRadius, amp: 0.03, phase: (105 * Math.PI) / 180 },
      { r: 1.15 * maxRadius, amp: 0.015, phase: (140 * Math.PI) / 180 },
    ];

    try {
      const pathKeyframes = keyframeConfigs.map((cfg) =>
        `path("${generateWavyDiscPath(x, y, cfg.r, cfg.amp, cfg.phase)}")`
      );

      document.documentElement.animate(
        {
          clipPath: [
            `path("${generateWavyDiscPath(x, y, 0, 0, 0)}")`,
            ...pathKeyframes,
          ],
        },
        {
          duration: 750,
          easing: "cubic-bezier(0.22, 1, 0.36, 1)",
          pseudoElement: "::view-transition-new(root)",
        }
      );
    } catch {
      // Fallback to circle clip-path animation if WAAPI path syntax is unsupported
      document.documentElement.animate(
        {
          clipPath: [
            `circle(0px at ${x}px ${y}px)`,
            `circle(${maxRadius}px at ${x}px ${y}px)`,
          ],
        },
        {
          duration: 750,
          easing: "cubic-bezier(0.22, 1, 0.36, 1)",
          pseudoElement: "::view-transition-new(root)",
        }
      );
    }
  });
}

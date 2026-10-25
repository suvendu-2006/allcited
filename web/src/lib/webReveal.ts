/**
 * The Web Reveal Theme Toggle Engine (§6.5)
 *
 * Implements the 4-phase expanding spider-web mesh theme reveal:
 * - Phase 1 · Bloom (0-180ms): Radial spokes draw outward from toggle coordinates.
 * - Phase 2 · Spread (180-650ms): Concentric spiral rings expand across the viewport,
 *   revealing the new theme through the web cells via View Transitions clip-path.
 * - Phase 3 · Edge Pass (650-850ms): Web sweeps past the farthest corner.
 * - Phase 4 · Dissolve (850-950ms): Web threads dissolve; 600ms faint web watermark in hero.
 */

interface WebCoordinates {
  x: number;
  y: number;
}

export function executeWebReveal(
  coords: WebCoordinates | null,
  isDarkNext: boolean,
  applyTheme: () => void
): void {
  if (typeof window === "undefined" || typeof document === "undefined") {
    applyTheme();
    return;
  }

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const hasViewTransition = "startViewTransition" in document;

  if (!hasViewTransition || prefersReduced) {
    applyTheme();
    return;
  }

  const x = coords?.x ?? window.innerWidth / 2;
  const y = coords?.y ?? 40;

  // Max distance to farthest corner
  const maxDistX = Math.max(x, window.innerWidth - x);
  const maxDistY = Math.max(y, window.innerHeight - y);
  const maxRadius = Math.hypot(maxDistX, maxDistY) * 1.1;

  // 1. Create temporary SVG Web Overlay container
  const overlaySvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  overlaySvg.setAttribute("class", "web-reveal-overlay");
  overlaySvg.style.position = "fixed";
  overlaySvg.style.inset = "0";
  overlaySvg.style.width = "100vw";
  overlaySvg.style.height = "100vh";
  overlaySvg.style.pointerEvents = "none";
  overlaySvg.style.zIndex = "10000";

  const spokeCount = 10;
  const ringCount = 8;
  const strokeColor = isDarkNext ? "#31C7A5" : "#034F46";

  // Generate radial spokes
  for (let i = 0; i < spokeCount; i++) {
    const angle = (i * 2 * Math.PI) / spokeCount;
    const endX = x + maxRadius * Math.cos(angle);
    const endY = y + maxRadius * Math.sin(angle);

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", String(x));
    line.setAttribute("y1", String(y));
    line.setAttribute("x2", String(endX));
    line.setAttribute("y2", String(endY));
    line.setAttribute("stroke", strokeColor);
    line.setAttribute("stroke-width", "1.5");
    line.setAttribute("stroke-opacity", "0.6");
    line.setAttribute("stroke-dasharray", String(maxRadius));
    line.setAttribute("stroke-dashoffset", String(maxRadius));
    overlaySvg.appendChild(line);
  }

  // Generate concentric spiral polygon rings
  for (let r = 1; r <= ringCount; r++) {
    const ringRadius = (maxRadius * r) / ringCount;
    const points: string[] = [];

    for (let i = 0; i < spokeCount; i++) {
      const angle = (i * 2 * Math.PI) / spokeCount;
      const px = x + ringRadius * Math.cos(angle);
      const py = y + ringRadius * Math.sin(angle);
      points.push(`${px.toFixed(1)},${py.toFixed(1)}`);
    }

    const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    polygon.setAttribute("points", points.join(" "));
    polygon.setAttribute("fill", "none");
    polygon.setAttribute("stroke", strokeColor);
    polygon.setAttribute("stroke-width", "1.5");
    polygon.setAttribute("stroke-opacity", "0.6");
    polygon.style.opacity = "0";
    overlaySvg.appendChild(polygon);
  }

  document.body.appendChild(overlaySvg);

  // 2. Animate SVG Spokes & Rings
  const lines = overlaySvg.querySelectorAll("line");
  const polygons = overlaySvg.querySelectorAll("polygon");

  // Animate spokes drawing (Phase 1 Bloom: 0–180ms)
  lines.forEach((line) => {
    line.animate(
      [
        { strokeDashoffset: String(maxRadius) },
        { strokeDashoffset: "0" },
      ],
      {
        duration: 350,
        easing: "cubic-bezier(0.22, 1, 0.36, 1)",
        fill: "forwards",
      }
    );
  });

  // Animate concentric rings spreading (Phase 2: 180–650ms)
  polygons.forEach((poly, idx) => {
    poly.animate(
      [
        { opacity: "0", transform: "scale(0.2)", transformOrigin: `${x}px ${y}px` },
        { opacity: "0.6", transform: "scale(1)", transformOrigin: `${x}px ${y}px` },
      ],
      {
        duration: 450,
        delay: 80 + idx * 45,
        easing: "cubic-bezier(0.22, 1, 0.36, 1)",
        fill: "forwards",
      }
    );
  });

  // 3. View Transitions API: Reveals the new theme inside the expanding circular/web cell
  const transition = (
    document as unknown as {
      startViewTransition: (cb: () => void) => { ready: Promise<void> };
    }
  ).startViewTransition(() => {
    applyTheme();
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute("content", isDarkNext ? "#06211D" : "#FAF8ED");
    }
  });

  transition.ready.then(() => {
    // Reveal clip-path expands with the web
    document.documentElement.animate(
      [
        { clipPath: `circle(0px at ${x}px ${y}px)` },
        { clipPath: `circle(${maxRadius * 0.4}px at ${x}px ${y}px)`, offset: 0.4 },
        { clipPath: `circle(${maxRadius}px at ${x}px ${y}px)` },
      ],
      {
        duration: 850,
        easing: "cubic-bezier(0.22, 1, 0.36, 1)",
        pseudoElement: "::view-transition-new(root)",
      }
    );

    // Phase 4: Dissolve (850-950ms)
    setTimeout(() => {
      overlaySvg.animate(
        [{ opacity: "1" }, { opacity: "0" }],
        { duration: 150, fill: "forwards" }
      ).onfinish = () => {
        overlaySvg.remove();
      };

      // Faint web watermark in hero for 600ms post-switch per §6.5
      document.documentElement.setAttribute("data-web-afterglow", "true");
      setTimeout(() => {
        document.documentElement.removeAttribute("data-web-afterglow");
      }, 600);
    }, 850);
  });
}

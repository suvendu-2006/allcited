"use client";

/**
 * Clean theme transition executor:
 * Instantly applies theme without rendering any triangle overlay.
 */
export function executeThemeTransition(
  targetDark?: boolean,
  onComplete?: (nextDark: boolean) => void
): void {
  if (onComplete) {
    onComplete(targetDark ?? false);
  }
}

export function registerThemeTransition() {
  return () => {};
}

/**
 * Triangle animation removed per user specification:
 * Returns null to eliminate all geometric overlay animations.
 */
export function ThemeTransitionOverlay() {
  return null;
}

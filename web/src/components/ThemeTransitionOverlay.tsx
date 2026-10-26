"use client";

import { playToggleClick } from "@/lib/keyboardSound";

type TransitionCallback = (nextDark?: boolean, onComplete?: (nextDark: boolean) => void) => void;
let activeTrigger: TransitionCallback | null = null;

export function registerThemeTransition(fn: TransitionCallback) {
  activeTrigger = fn;
  return () => {
    if (activeTrigger === fn) activeTrigger = null;
  };
}

/**
 * Global trigger to apply theme shift directly and cleanly.
 * The triangle animation overlay has been removed per user preference.
 */
export function executeThemeTransition(
  targetDark?: boolean,
  onComplete?: (nextDark: boolean) => void
): void {
  if (typeof window === "undefined") return;

  if (activeTrigger) {
    activeTrigger(targetDark, onComplete);
    return;
  }

  const currentIsDark = document.documentElement.classList.contains("dark");
  const nextDark = targetDark !== undefined ? targetDark : !currentIsDark;

  if (nextDark) {
    document.documentElement.classList.add("dark");
    localStorage.setItem("allcited_theme", "dark");
  } else {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("allcited_theme", "light");
  }

  playToggleClick();
  onComplete?.(nextDark);
}

/**
 * Overlay component rendered in root layout.
 * Returns null — triangle animation disabled.
 */
export function ThemeTransitionOverlay() {
  return null;
}

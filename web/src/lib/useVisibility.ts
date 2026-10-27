"use client";

import { useState, useEffect } from "react";

/**
 * Returns true when document is visible, false when tab is backgrounded (document.hidden).
 * Used across animations in §6.11 to pause ambient loops when the user is away.
 */
export function useDocumentVisibility(): boolean {
  const [isVisible, setIsVisible] = useState(() =>
    typeof document !== "undefined" ? !document.hidden : true
  );

  useEffect(() => {
    if (typeof document === "undefined") return;
    const handleVisibility = () => {
      setIsVisible(!document.hidden);
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, []);

  return isVisible;
}

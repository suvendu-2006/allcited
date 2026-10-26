"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

type Theme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme, animate?: boolean) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "light",
  toggleTheme: () => {},
  setTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // 1. Determine natural theme from current real local time:
    // 6:00 PM to 6:00 AM is Dark Mode; 6:00 AM to 6:00 PM is Light Mode
    const currentHour = new Date().getHours();
    const isNight = currentHour >= 18 || currentHour < 6;
    const timeBasedTheme: Theme = isNight ? "dark" : "light";

    // 2. Check for manual session override, otherwise align with real local time
    const manual = sessionStorage.getItem("allcited_theme_manual");
    const saved = manual ? (localStorage.getItem("allcited_theme") as Theme | null) : null;
    const initial = saved || timeBasedTheme;

    setThemeState(initial);
    if (initial === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    setMounted(true);
  }, []);

  const applyThemeClasses = useCallback((nextTheme: Theme) => {
    setThemeState(nextTheme);
    sessionStorage.setItem("allcited_theme_manual", "true");
    localStorage.setItem("allcited_theme", nextTheme);
    if (nextTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const setTheme = useCallback((nextTheme: Theme) => {
    if (typeof document !== "undefined") {
      const isCurrentlyDark = document.documentElement.classList.contains("dark");
      if (isCurrentlyDark === (nextTheme === "dark")) return;
    }
    applyThemeClasses(nextTheme);
  }, [applyThemeClasses]);

  const toggleTheme = useCallback(() => {
    const isCurrentlyDark = typeof document !== "undefined"
      ? document.documentElement.classList.contains("dark")
      : theme === "dark";
    const nextTheme: Theme = isCurrentlyDark ? "light" : "dark";
    applyThemeClasses(nextTheme);
  }, [applyThemeClasses, theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {mounted ? children : <div style={{ visibility: "hidden" }}>{children}</div>}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

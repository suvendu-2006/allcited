"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ui/ThemeToggle";
import { motion, AnimatePresence } from "framer-motion";

interface NavbarProps {
  onOpenSettings?: () => void;
  apiConnected?: boolean;
}

const NAV_LINKS = [
  { href: "/product", label: "Product", sub: "Architecture & Defenses" },
  { href: "/how-it-works", label: "How it works", sub: "Receipts Anatomy" },
  { href: "/exam", label: "The exam", sub: "46-Question Benchmark" },
  { href: "/pricing", label: "Pricing", sub: "Free & Pro Tiers" },
  { href: "/library", label: "Shelf", sub: "Private Archive" },
  { href: "/dev", label: "/dev", sub: "Design System Tokens", isMono: true },
];

export function Navbar({ onOpenSettings, apiConnected }: NavbarProps) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [localTime, setLocalTime] = useState<string>("11 . 00");

  // Live ticking local clock formatted as "HH . MM" per Awwwards reference
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      setLocalTime(`${hh} . ${mm}`);
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  // Close menu on route change
  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    if (menuOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [menuOpen]);

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-border bg-bg-surface/90 backdrop-blur-md px-4 sm:px-8 h-16 flex items-center justify-between flex-shrink-0 transition-colors select-none">
        {/* Left: Editorial Label per Awwwards Site of the Day reference */}
        <div className="flex items-center gap-6">
          <Link
            href="/"
            className="flex flex-col text-left leading-tight hover:opacity-80 transition-opacity"
          >
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-ink-primary">
              AWWWARDS
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-gray-warm">
              SITE OF THE DAY
            </span>
          </Link>

          {/* Quick desktop links inline */}
          <nav className="hidden lg:flex items-center gap-5 text-xs font-mono text-gray-warm">
            <Link
              href="/product"
              className={`hover:text-ink-primary transition-colors ${
                pathname === "/product" ? "text-ink-primary font-semibold" : ""
              }`}
            >
              Product
            </Link>
            <Link
              href="/how-it-works"
              className={`hover:text-ink-primary transition-colors ${
                pathname === "/how-it-works" ? "text-ink-primary font-semibold" : ""
              }`}
            >
              How it works
            </Link>
            <Link
              href="/exam"
              className={`hover:text-ink-primary transition-colors ${
                pathname === "/exam" ? "text-ink-primary font-semibold" : ""
              }`}
            >
              The exam
            </Link>
          </nav>
        </div>

        {/* Center: Signature Cursive Brand Logo per reference */}
        <Link
          href="/"
          className="absolute left-1/2 -translate-x-1/2 flex items-center justify-center hover:opacity-85 transition-opacity"
        >
          <span className="font-handwriting text-3xl sm:text-4xl text-ink-primary tracking-wide -rotate-2">
            Allcited.
          </span>
        </Link>

        {/* Right: Menu + Local Time + Circular Orbit Theme Toggle */}
        <div className="flex items-center gap-4 sm:gap-6">
          {/* MENU / CONTACT links */}
          <div className="flex flex-col text-right leading-tight">
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              className="font-mono text-[10.5px] uppercase tracking-[0.18em] font-semibold text-ink-primary hover:text-accent-primary transition-colors text-right"
            >
              {menuOpen ? "CLOSE" : "MENU"}
            </button>
            <Link
              href="/pricing"
              className="font-mono text-[9px] uppercase tracking-[0.14em] text-gray-warm hover:text-ink-primary transition-colors text-right"
            >
              PRICING
            </Link>
          </div>

          {/* LOCAL TIME Clock */}
          <div className="hidden sm:flex flex-col text-right leading-tight">
            <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-gray-warm">
              LOCAL TIME
            </span>
            <span className="font-mono text-[11px] font-bold text-ink-primary tracking-wider tabular-nums">
              {localTime}
            </span>
          </div>

          {/* Circular Orbit Dial Theme Toggle */}
          <div className="pl-1">
            <ThemeToggle />
          </div>

          {/* Settings Trigger if available */}
          {onOpenSettings && (
            <button
              type="button"
              onClick={onOpenSettings}
              title="Model Settings"
              className="font-mono text-xs text-ink-ghost hover:text-ink-primary p-1 rounded transition-colors"
            >
              ⚙
            </button>
          )}

          {/* Backend Online Dot indicator */}
          {apiConnected !== undefined && (
            <span
              className={`w-2 h-2 rounded-full ${
                apiConnected ? "bg-[#28C840] dark:bg-[#5AD46F] animate-pulse" : "bg-danger"
              }`}
              title={apiConnected ? "Backend online" : "Backend offline"}
            />
          )}
        </div>
      </header>

      {/* Full-Screen Minimalist Menu Drawer */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
            className="fixed inset-0 top-16 z-50 bg-bg-base/98 backdrop-blur-xl p-6 sm:p-12 flex flex-col justify-between overflow-y-auto"
          >
            <div className="max-w-4xl w-full mx-auto space-y-6 pt-4">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-gray-warm block border-b border-border pb-2">
                Index Navigation
              </span>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {NAV_LINKS.map((link, idx) => {
                  const isActive = pathname === link.href;
                  return (
                    <motion.div
                      key={link.href}
                      initial={{ opacity: 0, x: -16 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.04 + 0.05 }}
                    >
                      <Link
                        href={link.href}
                        onClick={() => setMenuOpen(false)}
                        className={`group block p-4 rounded-interactive border transition-all duration-150 ${
                          isActive
                            ? "bg-bg-surface border-accent-primary/50 shadow-xs"
                            : "bg-bg-surface/50 border-border hover:bg-bg-surface hover:border-ink-primary/30"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span
                            className={`text-xl font-display font-semibold transition-colors ${
                              isActive
                                ? "text-accent-primary"
                                : "text-ink-primary group-hover:text-accent-primary"
                            } ${link.isMono ? "font-mono text-base" : ""}`}
                          >
                            {link.label}
                          </span>
                          <span className="font-mono text-xs text-gray-warm group-hover:translate-x-1 transition-transform">
                            →
                          </span>
                        </div>
                        <span className="font-mono text-[11px] text-gray-warm block mt-1">
                          {link.sub}
                        </span>
                      </Link>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            <div className="max-w-4xl w-full mx-auto pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-gray-warm">
              <div className="flex items-center gap-3">
                <Link
                  href="/?workspace=true"
                  onClick={() => setMenuOpen(false)}
                  className="px-4 py-2 rounded-interactive bg-accent-primary text-primary-foreground font-semibold hover:brightness-95 transition-all text-xs"
                >
                  Open Workspace
                </Link>
                {onOpenSettings && (
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false);
                      onOpenSettings();
                    }}
                    className="px-3 py-2 rounded-interactive border border-border bg-bg-surface hover:bg-bg-sunken text-xs"
                  >
                    Configure Model ⚙
                  </button>
                )}
              </div>

              <div className="text-center sm:text-right font-mono text-[11px] text-ink-ghost">
                Allcited v1.0 · Grounded Truth Architecture
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

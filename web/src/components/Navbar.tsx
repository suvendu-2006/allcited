"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ui/ThemeToggle";
import { Button } from "./ui/button";
import { Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface NavbarProps {
  onOpenSettings?: () => void;
  apiConnected?: boolean;
}

const NAV_LINKS = [
  { href: "/product", label: "Product" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/exam", label: "The exam" },
  { href: "/pricing", label: "Pricing" },
  { href: "/library", label: "Shelf" },
  { href: "/dev", label: "/dev", isMono: true },
];

export function Navbar({ onOpenSettings, apiConnected }: NavbarProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Handle Escape key to close mobile menu
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileMenuOpen(false);
    };
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [mobileMenuOpen]);

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-border bg-bg-surface/85 backdrop-blur-md px-4 sm:px-6 h-14 flex items-center justify-between flex-shrink-0 transition-colors">
        <div className="flex items-center gap-4 sm:gap-6">
          <Link
            href="/"
            className="flex items-center gap-2 hover:opacity-90 transition-opacity"
          >
            <span className="font-display text-lg font-bold tracking-tight text-ink-primary">
              Allcited
            </span>
            <span className="font-mono text-[10px] uppercase tracking-wider px-1.5 py-0.2 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
              v1.0
            </span>
          </Link>

          {/* Desktop Nav with Animated Active Underline per §6.2 */}
          <nav className="hidden md:flex items-center gap-5 text-xs font-medium text-gray-warm">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative py-1 transition-all duration-120 hover:-translate-y-[1px] ${
                    isActive
                      ? "text-ink-primary font-semibold"
                      : "hover:text-ink-primary"
                  } ${link.isMono ? "font-mono" : ""}`}
                >
                  <span>{link.label}</span>
                  {isActive && (
                    <motion.span
                      layoutId="nav-active-pill"
                      className="absolute bottom-0 left-0 right-0 h-[2px] bg-accent-primary rounded-full"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Settings Trigger if handler provided */}
          {onOpenSettings && (
            <button
              type="button"
              onClick={onOpenSettings}
              title="Who does the thinking? (Settings)"
              className="p-1.5 rounded-[6px] text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken transition-colors cursor-pointer font-mono text-xs"
            >
              ⚙
            </button>
          )}

          {/* Theme Toggle with Web Reveal (§6.5) */}
          <ThemeToggle />

          {/* Quick CTA */}
          <Link href="/?workspace=true" className="hidden sm:inline-flex">
            <Button variant="primary" size="sm" className="text-xs h-8">
              Open Allcited
            </Button>
          </Link>

          {/* API Health Dot */}
          {apiConnected !== undefined && (
            <div
              className="hidden lg:flex items-center gap-1.5 pl-1"
              title={apiConnected ? "Backend online" : "Backend offline"}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  apiConnected
                    ? "bg-[#28C840] dark:bg-[#5AD46F] animate-pulse"
                    : "bg-danger"
                }`}
              />
            </div>
          )}

          {/* Mobile Menu Hamburger */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
            className="md:hidden p-1.5 rounded-[6px] text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken transition-colors"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Full-Screen Overlay Nav per §6.2 */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 top-14 z-50 bg-bg-base/95 backdrop-blur-lg md:hidden p-6 flex flex-col justify-between"
          >
            <div className="space-y-4 pt-4">
              {NAV_LINKS.map((link, idx) => {
                const isActive = pathname === link.href;
                return (
                  <motion.div
                    key={link.href}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.04 + 0.05 }}
                  >
                    <Link
                      href={link.href}
                      className={`block text-xl font-display py-2 border-b border-border/40 ${
                        isActive
                          ? "text-accent-primary font-semibold"
                          : "text-ink-primary"
                      } ${link.isMono ? "font-mono text-base" : ""}`}
                    >
                      {link.label}
                    </Link>
                  </motion.div>
                );
              })}
            </div>

            <div className="space-y-3 pb-8">
              <Link href="/?workspace=true" className="w-full block">
                <Button variant="primary" className="w-full text-sm">
                  Open Workspace
                </Button>
              </Link>
              <p className="font-mono text-[11px] text-ink-ghost text-center">
                Built with React 18 · Next.js 14 · Allcited v1.0
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

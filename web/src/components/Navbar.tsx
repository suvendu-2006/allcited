"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { InteractiveOrbitClock } from "./ui/InteractiveOrbitClock";
import { Button } from "./ui/button";

interface NavbarProps {
  onOpenSettings?: () => void;
  apiConnected?: boolean;
  isInApp?: boolean;
}

export function Navbar({ onOpenSettings, isInApp }: NavbarProps) {
  const pathname = usePathname();
  const isAppView = isInApp || pathname === "/exam" || pathname === "/library" || pathname === "/dev";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-bg-surface/90 backdrop-blur-md px-4 sm:px-8 h-16 flex items-center justify-between flex-shrink-0 transition-colors select-none">
      {/* Left: Navigation links per §4D verbatim */}
      <div className="flex items-center gap-6">
        <nav className="flex items-center gap-3 sm:gap-5 text-xs font-mono text-gray-warm">
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
          <Link
            href="/pricing"
            className={`hover:text-ink-primary transition-colors ${
              pathname === "/pricing" ? "text-ink-primary font-semibold" : ""
            }`}
          >
            Pricing
          </Link>
          <Link
            href="/library"
            className={`hover:text-ink-primary transition-colors hidden md:inline-block ${
              pathname === "/library" ? "text-ink-primary font-semibold" : ""
            }`}
          >
            Shelf
          </Link>
        </nav>
      </div>

      {/* Center: Brand Logo Allcited v1.0 per §4D verbatim */}
      <Link
        href="/"
        className="absolute left-1/2 -translate-x-1/2 flex items-center gap-1.5 hover:opacity-85 transition-opacity"
      >
        <span className="font-handwriting text-3xl sm:text-4xl text-ink-primary tracking-wide -rotate-2">
          Allcited.
        </span>
        <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-bg-sunken border border-border text-gray-warm tracking-wider uppercase font-semibold">
          v1.0
        </span>
      </Link>

      {/* Right: Theme Toggle (Interactive Orbit Clock) + Open Allcited Button */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Theme Toggle Dial with accessible label */}
        <InteractiveOrbitClock />

        {/* In-App Settings Button */}
        {isAppView && onOpenSettings && (
          <button
            type="button"
            onClick={onOpenSettings}
            title="Model Settings & Provider Config"
            aria-label="Open model settings"
            className="w-8 h-8 flex items-center justify-center rounded-lg border border-border bg-bg-surface hover:bg-bg-hover text-ink-primary hover:text-accent-primary transition-all shadow-sm active:scale-95"
          >
            <span className="text-base leading-none" aria-hidden="true">
              ⚙
            </span>
          </button>
        )}

        {/* Open Allcited CTA per §4D verbatim */}
        <Link href="/?workspace=true" className="hidden sm:inline-block">
          <Button variant="primary" size="sm" className="text-xs h-8 px-3">
            Open Allcited
          </Button>
        </Link>
      </div>
    </header>
  );
}

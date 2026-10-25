"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { InteractiveOrbitClock } from "./ui/InteractiveOrbitClock";

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
      {/* Left: Clean navigation links */}
      <div className="flex items-center gap-6">
        <nav className="flex items-center gap-4 sm:gap-6 text-xs font-mono text-gray-warm">
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
            className={`hover:text-ink-primary transition-colors hidden sm:inline-block ${
              pathname === "/pricing" ? "text-ink-primary font-semibold" : ""
            }`}
          >
            Pricing
          </Link>
        </nav>
      </div>

      {/* Center: Signature Cursive Brand Logo */}
      <Link
        href="/"
        className="absolute left-1/2 -translate-x-1/2 flex items-center justify-center hover:opacity-85 transition-opacity"
      >
        <span className="font-handwriting text-3xl sm:text-4xl text-ink-primary tracking-wide -rotate-2">
          Allcited.
        </span>
      </Link>

      {/* Right: Interactive Orbit Clock & Time Controller + In-App Settings */}
      <div className="flex items-center gap-3 sm:gap-5">
        {/* Interactive Orbit Clock with draggable satellite dot and time traveler */}
        <InteractiveOrbitClock />

        {/* Settings button: Hidden on landing, prominent & enlarged when in app */}
        {isAppView && onOpenSettings && (
          <button
            type="button"
            onClick={onOpenSettings}
            title="Model Settings & Provider Config"
            aria-label="Open model settings"
            className="w-9 h-9 flex items-center justify-center rounded-lg border border-border bg-bg-surface hover:bg-bg-hover text-ink-primary hover:text-accent-primary transition-all shadow-sm active:scale-95 ml-1"
          >
            <span className="text-lg leading-none" aria-hidden="true">
              ⚙
            </span>
          </button>
        )}
      </div>
    </header>
  );
}

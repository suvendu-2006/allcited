"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import { InteractiveOrbitClock } from "./ui/InteractiveOrbitClock";
import { Button } from "./ui/button";
import { Settings } from "lucide-react";

interface NavbarProps {
  onOpenSettings?: () => void;
  onOpenWorkspace?: () => void;
  apiConnected?: boolean;
  isInApp?: boolean;
}

export function Navbar({ onOpenSettings, onOpenWorkspace, isInApp }: NavbarProps) {
  const pathname = usePathname();
  const isAppView = isInApp || pathname === "/exam" || pathname === "/library" || pathname === "/dev";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-bg-surface/90 backdrop-blur-md px-4 sm:px-8 h-16 flex items-center justify-between flex-shrink-0 transition-colors select-none">
      {/* Left: Navigation links */}
      <div className="flex items-center gap-6">
        <nav className="flex items-center gap-3 sm:gap-5 text-xs font-mono text-gray-warm">
          <Link
            href="/product"
            className={`hover:text-ink-primary hover:-translate-y-[0.5px] transition-all duration-150 ${
              pathname === "/product" ? "text-ink-primary font-semibold" : ""
            }`}
          >
            Product
          </Link>
          <Link
            href="/how-it-works"
            className={`hover:text-ink-primary hover:-translate-y-[0.5px] transition-all duration-150 ${
              pathname === "/how-it-works" ? "text-ink-primary font-semibold" : ""
            }`}
          >
            How it works
          </Link>
          <Link
            href="/exam"
            className={`hover:text-ink-primary hover:-translate-y-[0.5px] transition-all duration-150 ${
              pathname === "/exam" ? "text-ink-primary font-semibold" : ""
            }`}
          >
            The exam
          </Link>
          <Link
            href="/pricing"
            className={`hover:text-ink-primary hover:-translate-y-[0.5px] transition-all duration-150 ${
              pathname === "/pricing" ? "text-ink-primary font-semibold" : ""
            }`}
          >
            Pricing
          </Link>
          <Link
            href="/library"
            className={`hover:text-ink-primary hover:-translate-y-[0.5px] transition-all duration-150 hidden md:inline-block ${
              pathname === "/library" ? "text-ink-primary font-semibold" : ""
            }`}
          >
            Shelf
          </Link>
        </nav>
      </div>

      {/* Center: Brand Logo */}
      <Link
        href="/"
        className="group absolute left-1/2 -translate-x-1/2 flex items-center hover:opacity-90 transition-opacity"
      >
        <span className="font-handwriting text-3xl sm:text-4xl text-ink-primary tracking-wide -rotate-2 inline-block transition-transform duration-200 ease-out group-hover:scale-105 group-hover:-rotate-1">
          Allcited.
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
            className="group/settings w-8 h-8 flex items-center justify-center rounded-interactive border border-border bg-bg-surface hover:bg-bg-sunken text-ink-primary hover:text-accent-primary transition-all duration-150 shadow-xs active:scale-95 cursor-pointer"
          >
            <Settings className="w-4 h-4 text-ink-primary group-hover/settings:rotate-45 group-hover/settings:text-accent-primary transition-transform duration-200 ease-out" aria-hidden="true" />
          </button>
        )}

        {/* Clerk Auth Integration */}
        <SignedOut>
          <SignInButton mode="modal">
            <button
              type="button"
              className="text-xs font-mono text-gray-warm hover:text-ink-primary transition-colors px-2 py-1 cursor-pointer"
            >
              Sign in
            </button>
          </SignInButton>
        </SignedOut>
        <SignedIn>
          <div className="flex items-center">
            <UserButton afterSignOutUrl="/" appearance={{ elements: { avatarBox: "w-7 h-7" } }} />
          </div>
        </SignedIn>

        {onOpenWorkspace ? (
          <Button
            variant="primary"
            size="sm"
            onClick={onOpenWorkspace}
            className="hidden sm:inline-block text-xs h-8 px-3 cursor-pointer shadow-xs"
          >
            Open Allcited
          </Button>
        ) : (
          <Link
            href="/?workspace=true"
            className="hidden sm:inline-flex items-center justify-center rounded-interactive bg-accent-primary text-white hover:opacity-90 transition-opacity text-xs h-8 px-3 font-medium cursor-pointer shadow-xs"
          >
            Open Allcited
          </Link>
        )}
      </div>
    </header>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import { InteractiveOrbitClock } from "./ui/InteractiveOrbitClock";
import { Button } from "./ui/button";
import { Settings, Menu, X } from "lucide-react";

interface NavbarProps {
  onOpenSettings?: () => void;
  onOpenWorkspace?: () => void;
  onGoHome?: () => void;
  apiConnected?: boolean;
  isInApp?: boolean;
}

export function Navbar({ onOpenSettings, onOpenWorkspace, onGoHome, isInApp }: NavbarProps) {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const isAppView = isInApp || pathname === "/exam" || pathname === "/library" || pathname === "/dev";

  // Automatically close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-border bg-bg-surface/90 backdrop-blur-md px-3 sm:px-8 h-16 flex items-center justify-between flex-shrink-0 transition-colors select-none">
        {/* Left: Desktop navigation links (hidden on mobile) */}
        <div className="hidden md:flex items-center gap-6">
          <nav className="flex items-center gap-5 text-xs font-mono text-gray-warm">
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
              className={`hover:text-ink-primary hover:-translate-y-[0.5px] transition-all duration-150 ${
                pathname === "/library" ? "text-ink-primary font-semibold" : ""
              }`}
            >
              Shelf
            </Link>
          </nav>
        </div>

        {/* Brand Logo: Clean on Left on mobile; Centered on desktop */}
        <Link
          href="/"
          onClick={(e) => {
            if (onGoHome) {
              e.preventDefault();
              onGoHome();
            }
          }}
          className="group md:absolute md:left-1/2 md:-translate-x-1/2 flex items-center hover:opacity-90 transition-opacity cursor-pointer flex-shrink-0"
        >
          <span className="font-handwriting text-2xl sm:text-3xl md:text-4xl text-ink-primary tracking-wide -rotate-2 inline-block transition-transform duration-200 ease-out group-hover:scale-105 group-hover:-rotate-1">
            Allcited.
          </span>
        </Link>

        {/* Right: Theme Toggle Dial + Auth + Settings + Mobile Menu Button */}
        <div className="flex items-center gap-1.5 sm:gap-3 flex-shrink-0">
          {/* Theme Toggle Orbit Dial */}
          <InteractiveOrbitClock />

          {/* In-App Settings Button */}
          {isAppView && onOpenSettings && (
            <button
              type="button"
              onClick={onOpenSettings}
              title="Model Settings & Provider Config"
              aria-label="Open model settings"
              className="group/settings w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-interactive border border-border bg-bg-surface hover:bg-bg-sunken text-ink-primary hover:text-accent-primary transition-all duration-150 shadow-xs active:scale-95 cursor-pointer flex-shrink-0"
            >
              <Settings className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-ink-primary group-hover/settings:rotate-45 group-hover/settings:text-accent-primary transition-transform duration-200 ease-out" aria-hidden="true" />
            </button>
          )}

          {/* Clerk Auth Integration */}
          <SignedOut>
            <SignInButton mode="modal">
              <button
                type="button"
                className="text-[11px] sm:text-xs font-mono text-gray-warm hover:text-ink-primary transition-colors px-1.5 sm:px-2 py-1 cursor-pointer whitespace-nowrap"
              >
                Sign in
              </button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <div className="flex items-center flex-shrink-0">
              <UserButton
                afterSignOutUrl="/"
                appearance={{
                  baseTheme: dark,
                  variables: {
                    colorPrimary: "#E8765A",
                    colorBackground: "#171514",
                    colorInputBackground: "#0D0C0B",
                    colorInputText: "#EFEAD9",
                    colorText: "#EFEAD9",
                    colorTextSecondary: "#A8A69A",
                    colorNeutral: "#EFEAD9",
                    colorDanger: "#F0788C",
                    borderRadius: "10px",
                  },
                  elements: {
                    avatarBox: "w-6 h-6 sm:w-7 sm:h-7",
                    userButtonPopoverCard: "bg-[#171514] border border-[rgba(239,234,217,0.14)] shadow-2xl text-[#EFEAD9]",
                    userButtonPopoverActionButton: "hover:bg-[#201D1B] text-[#EFEAD9] text-xs",
                    userButtonPopoverFooter: "bg-[#121110] border-t border-[rgba(239,234,217,0.10)] text-[#A8A69A]",
                  },
                }}
                userProfileProps={{
                  appearance: {
                    baseTheme: dark,
                    variables: {
                      colorPrimary: "#E8765A",
                      colorBackground: "#171514",
                      colorInputBackground: "#0D0C0B",
                      colorInputText: "#EFEAD9",
                      colorText: "#EFEAD9",
                      colorTextSecondary: "#A8A69A",
                      colorNeutral: "#EFEAD9",
                      colorDanger: "#F0788C",
                      borderRadius: "10px",
                    },
                    elements: {
                      rootBox: "text-[#EFEAD9]",
                      card: "bg-[#171514] border border-[rgba(239,234,217,0.14)] shadow-2xl text-[#EFEAD9]",
                      modalBackdrop: "bg-black/80 backdrop-blur-sm",
                      modalContent: "bg-[#171514] border border-[rgba(239,234,217,0.14)] rounded-2xl shadow-2xl",
                      modalCloseButton: "text-[#A8A69A] hover:text-[#EFEAD9] hover:bg-[#201D1B]",
                      navbar: "bg-[#121110] border-r border-[rgba(239,234,217,0.10)]",
                      navbarButton: "text-[#A8A69A] hover:text-[#EFEAD9] hover:bg-[#201D1B]",
                      navbarButtonActive: "bg-[rgba(232,118,90,0.15)] text-[#E8765A]",
                      profileSectionTitle: "text-[#EFEAD9] font-semibold",
                      profileSectionTitleText: "text-[#EFEAD9] font-semibold",
                      profileSectionPrimaryButton: "text-[#E8765A]",
                      formButtonPrimary: "bg-[#E8765A] text-white hover:bg-[#E8765A]/90",
                      formButtonReset: "bg-[#201D1B] text-[#EFEAD9] hover:bg-[#2A2724]",
                      formFieldInput: "bg-[#0D0C0B] border-[rgba(239,234,217,0.16)] text-[#EFEAD9]",
                    },
                  },
                }}
              />
            </div>
          </SignedIn>

          {/* Desktop "Open Allcited" Button */}
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

          {/* Mobile Hamburger Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label={isMobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={isMobileMenuOpen}
            className="md:hidden w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-interactive border border-border bg-bg-surface hover:bg-bg-sunken text-ink-primary transition-all duration-150 shadow-xs active:scale-95 cursor-pointer flex-shrink-0"
          >
            {isMobileMenuOpen ? (
              <X className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-ink-primary" />
            ) : (
              <Menu className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-ink-primary" />
            )}
          </button>
        </div>
      </header>

      {/* Mobile Navigation Drawer / Dropdown */}
      {isMobileMenuOpen && (
        <>
          {/* Backdrop */}
          <div
            onClick={() => setIsMobileMenuOpen(false)}
            aria-hidden="true"
            className="fixed inset-0 top-16 bg-black/40 backdrop-blur-xs z-30 md:hidden animate-fade-in"
          />

          {/* Dropdown Menu Panel */}
          <div className="fixed top-16 left-0 right-0 z-40 bg-bg-surface border-b border-border shadow-xl md:hidden animate-fade-in p-5 space-y-4">
            <nav className="flex flex-col space-y-2 font-mono text-sm text-gray-warm">
              <Link
                href="/product"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`py-2 px-3 rounded-interactive hover:bg-bg-sunken hover:text-ink-primary transition-colors ${
                  pathname === "/product" ? "text-ink-primary font-semibold bg-bg-sunken" : ""
                }`}
              >
                Product
              </Link>
              <Link
                href="/how-it-works"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`py-2 px-3 rounded-interactive hover:bg-bg-sunken hover:text-ink-primary transition-colors ${
                  pathname === "/how-it-works" ? "text-ink-primary font-semibold bg-bg-sunken" : ""
                }`}
              >
                How it works
              </Link>
              <Link
                href="/exam"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`py-2 px-3 rounded-interactive hover:bg-bg-sunken hover:text-ink-primary transition-colors ${
                  pathname === "/exam" ? "text-ink-primary font-semibold bg-bg-sunken" : ""
                }`}
              >
                The exam
              </Link>
              <Link
                href="/pricing"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`py-2 px-3 rounded-interactive hover:bg-bg-sunken hover:text-ink-primary transition-colors ${
                  pathname === "/pricing" ? "text-ink-primary font-semibold bg-bg-sunken" : ""
                }`}
              >
                Pricing
              </Link>
              <Link
                href="/library"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`py-2 px-3 rounded-interactive hover:bg-bg-sunken hover:text-ink-primary transition-colors ${
                  pathname === "/library" ? "text-ink-primary font-semibold bg-bg-sunken" : ""
                }`}
              >
                Shelf
              </Link>
            </nav>

            <div className="pt-3 border-t border-border">
              {onOpenWorkspace ? (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setIsMobileMenuOpen(false);
                    onOpenWorkspace();
                  }}
                  className="w-full text-xs h-9 cursor-pointer shadow-xs"
                >
                  Open Allcited
                </Button>
              ) : (
                <Link
                  href="/?workspace=true"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="w-full flex items-center justify-center rounded-interactive bg-accent-primary text-white hover:opacity-90 transition-opacity text-xs h-9 font-medium cursor-pointer shadow-xs"
                >
                  Open Allcited
                </Link>
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}

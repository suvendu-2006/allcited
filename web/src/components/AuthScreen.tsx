"use client";

import React from "react";
import Link from "next/link";
import { SignIn } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import { motion, useReducedMotion } from "framer-motion";
import { useTheme } from "@/lib/theme";
import { Button } from "./ui/button";
import { DeepSeaAurora } from "./DeepSeaAurora";

interface AuthScreenProps {
  onContinueAsGuest: () => void;
  onBackToHome?: () => void;
}

export function AuthScreen({ onContinueAsGuest, onBackToHome }: AuthScreenProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="relative min-h-screen w-full flex flex-col justify-between bg-bg-base text-ink-primary overflow-y-auto selection:bg-accent-primary/20">
      {/* Ambient background */}
      <DeepSeaAurora />

      {/* Top Header Bar */}
      <header className="relative z-10 w-full px-4 sm:px-8 py-3.5 flex items-center justify-between border-b border-border/60 bg-bg-surface/50 backdrop-blur-md flex-shrink-0">
        <div className="flex items-center gap-3">
          {onBackToHome ? (
            <motion.button
              type="button"
              onClick={onBackToHome}
              whileHover={shouldReduceMotion ? undefined : { x: -2 }}
              whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
              className="text-xs font-mono text-gray-warm hover:text-ink-primary transition-colors flex items-center gap-1 cursor-pointer"
            >
              ← Back to home
            </motion.button>
          ) : (
            <Link
              href="/"
              className="text-xs font-mono text-gray-warm hover:text-ink-primary transition-colors flex items-center gap-1"
            >
              ← Back to home
            </Link>
          )}
        </div>

        {onBackToHome ? (
          <button
            type="button"
            onClick={onBackToHome}
            className="font-handwriting text-2xl text-ink-primary -rotate-2 select-none hover:opacity-90 transition-opacity cursor-pointer"
          >
            Allcited.
          </button>
        ) : (
          <Link href="/" className="font-handwriting text-2xl text-ink-primary -rotate-2 select-none hover:opacity-90 transition-opacity">
            Allcited.
          </Link>
        )}

        <div className="w-16" aria-hidden="true" />
      </header>

      {/* Centered Auth Card Area */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-start sm:justify-center px-4 py-6 sm:py-10 max-w-md w-full mx-auto my-auto">
        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.36, ease: [0.16, 1, 0.3, 1] }}
          className="w-full space-y-5"
        >
          {/* Headline & Explanation */}
          <div className="text-center space-y-1.5">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink-primary font-display">
              Workspace access
            </h1>
            <p className="text-xs sm:text-sm text-gray-warm max-w-sm mx-auto">
              Sign in to keep documents on your shelf, or continue as guest.
            </p>
          </div>

          {/* Clerk SignIn Card Container */}
          <div className="w-full flex justify-center clerk-auth-wrapper">
            <SignIn
              routing="hash"
              appearance={{
                baseTheme: isDark ? dark : undefined,
                variables: {
                  colorBackground: isDark ? "#171514" : "#FFFFFF",
                  colorText: isDark ? "#EFEAD9" : "#1A1918",
                  colorTextSecondary: isDark ? "#A8A69A" : "#71716A",
                  colorInputBackground: isDark ? "#201D1B" : "#ECE8DC",
                  colorInputText: isDark ? "#EFEAD9" : "#1A1918",
                  colorPrimary: isDark ? "#E8765A" : "#A6362F",
                  colorDanger: isDark ? "#F0788C" : "#7F1C34",
                  borderRadius: "10px",
                },
                elements: {
                  rootBox: "w-full max-w-sm",
                  card: "bg-bg-surface border border-border shadow-md rounded-interactive p-6 w-full text-ink-primary overflow-hidden",
                  headerTitle: "text-ink-primary font-display font-semibold text-xl",
                  headerSubtitle: "text-gray-warm text-xs",
                  socialButtonsBlockButton: "border border-border bg-bg-sunken hover:bg-bg-surface text-ink-primary text-xs h-10 transition-colors shadow-2xs",
                  socialButtonsBlockButtonText: "text-ink-primary font-medium border-0 outline-none shadow-none",
                  socialButtonsIconButton: "border border-border bg-bg-sunken hover:bg-bg-surface text-ink-primary transition-colors shadow-2xs",
                  providerIcon__apple: isDark ? { filter: "invert(1) brightness(1.8)" } : {},
                  providerIcon__github: isDark ? { filter: "invert(1) brightness(1.8)" } : {},
                  providerIcon__x: isDark ? { filter: "invert(1) brightness(1.8)" } : {},
                  providerIcon__twitter: isDark ? { filter: "invert(1) brightness(1.8)" } : {},
                  formButtonPrimary: "bg-accent-primary hover:opacity-90 text-white text-xs font-medium h-10 shadow-xs transition-opacity rounded-interactive",
                  formFieldInput: "bg-bg-sunken border border-border text-ink-primary placeholder:text-gray-warm text-xs rounded-interactive focus:border-accent-primary focus:ring-1 focus:ring-accent-primary",
                  formFieldLabel: "text-xs text-ink-primary font-medium",
                  footer: "bg-bg-surface border-t border-border rounded-b-interactive text-ink-primary",
                  footerAction: "bg-bg-surface text-ink-primary",
                  footerActionText: "text-gray-warm text-xs",
                  footerActionLink: "text-accent-primary hover:underline text-xs font-semibold",
                  footerPages: "bg-bg-surface text-ink-primary",
                  footerPagesLink: "text-gray-warm hover:text-ink-primary text-xs",
                  lastAuthenticationStrategyBadge: "bg-bg-sunken text-accent-amber border border-border text-xs px-2 py-0.5 rounded-full shadow-none",
                  identityPreviewText: "text-ink-primary",
                  identityPreviewEditButton: "text-accent-primary",
                  formResendCodeLink: "text-gray-warm text-xs hover:text-accent-primary",
                  alternativeMethodsBlockButton: "text-accent-primary hover:underline text-xs font-semibold bg-transparent border-0 shadow-none",
                  otpCodeField: "bg-transparent border-0 shadow-none",
                  otpCodeFieldInputs: "bg-transparent border-0 shadow-none gap-2",
                  otpCodeFieldInputContainer: "bg-transparent border-0 shadow-none",
                  otpCodeFieldInput: "w-11 h-12 rounded-lg border border-[rgba(26,25,24,0.25)] dark:border-[rgba(239,234,217,0.22)] bg-white dark:bg-[#0D0C0B] text-ink-primary dark:text-[#EFEAD9] font-bold text-xl text-center focus:border-ink-primary dark:focus:border-accent-primary",
                  dividerLine: "bg-border",
                  dividerText: "text-ink-ghost text-xs font-mono",
                },
              }}
            />
          </div>

          {/* Visual Divider */}
          <div className="relative flex items-center justify-center my-3">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative bg-bg-base px-3 text-ink-ghost text-[11px] font-mono uppercase tracking-wider">
              or
            </div>
          </div>

          <div className="space-y-2 pt-0.5 text-center">
            <motion.div
              whileHover={shouldReduceMotion ? undefined : { scale: 1.01 }}
              whileTap={shouldReduceMotion ? undefined : { scale: 0.99 }}
            >
              <Button
                variant="outline"
                size="lg"
                onClick={onContinueAsGuest}
                className="w-full h-11 text-sm font-medium border-border hover:border-ink-primary bg-bg-surface hover:bg-bg-sunken text-ink-primary shadow-xs transition-all cursor-pointer"
              >
                Continue without login
              </Button>
            </motion.div>

            <p className="font-sans text-[11px] text-ink-ghost tracking-tight px-2 leading-relaxed">
              Guest mode: everything works, nothing is saved. Sign in later to keep your documents.
            </p>
          </div>
        </motion.div>
      </main>

      {/* Footer Minimal Notice */}
      <footer className="relative z-10 py-3.5 text-center text-xs text-ink-ghost font-mono border-t border-border/40 bg-bg-surface/30 flex-shrink-0">
        Answers, with receipts · 46-question verification suite
      </footer>
    </div>
  );
}

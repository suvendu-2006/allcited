"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { motion, useReducedMotion } from "framer-motion";
import { useDocumentVisibility } from "@/lib/useVisibility";
import { Check, Sparkles, X } from "lucide-react";

export default function PricingPage() {
  const [betaModalOpen, setBetaModalOpen] = useState(false);
  const isVisible = useDocumentVisibility();
  const shouldReduceMotion = useReducedMotion();

  const handleCheckout = () => {
    setBetaModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-12 sm:py-16 space-y-16">
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-3xl sm:text-5xl font-bold tracking-tight text-ink-primary font-display"
          >
            Free to ask. Paid to go deep.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-sm sm:text-base text-gray-warm leading-relaxed"
          >
            Free tier includes 10 questions per hour during beta. Pro is for big files and heavy use.
          </motion.p>
        </div>

        {/* Pricing Cards */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto items-stretch">
          <div className="p-8 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs space-y-6">
            <div className="space-y-4">
              <div className="flex items-baseline justify-between border-b border-border/60 pb-4">
                <div>
                  <h2 className="text-xl font-bold text-ink-primary font-display">
                    Free
                  </h2>
                  <span className="text-xs text-gray-warm font-mono">for everyone</span>
                </div>
                <div className="text-right">
                  <span className="font-mono text-3xl font-bold text-ink-primary">₹0</span>
                </div>
              </div>

              <p className="text-xs text-gray-warm">
                For reading, asking, and checking answers.
              </p>

              <ul className="space-y-2.5 text-xs text-ink-primary font-mono pt-2">
                {[
                  "10 questions / hour (Free beta tier)",
                  "Files up to 10 MB",
                  "All 6 file types",
                  "Every citation and trace",
                ].map((bullet) => (
                  <li key={bullet} className="flex items-center gap-2">
                    <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="pt-4 border-t border-border/60">
              <Link href="/?workspace=true" className="w-full block">
                <motion.div
                  whileHover={shouldReduceMotion ? undefined : { scale: 1.02 }}
                  whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
                >
                  <Button variant="outline" size="lg" className="w-full text-xs">
                    Start Free
                  </Button>
                </motion.div>
              </Link>
            </div>
          </div>

          <motion.div
            animate={
              isVisible && !shouldReduceMotion
                ? {
                    boxShadow: [
                      "0 4px 20px -2px rgba(3, 79, 70, 0.14)",
                      "0 4px 30px -2px rgba(3, 79, 70, 0.28)",
                      "0 4px 20px -2px rgba(3, 79, 70, 0.14)",
                    ],
                    borderColor: [
                      "rgba(3, 79, 70, 0.6)",
                      "rgba(49, 199, 165, 0.9)",
                      "rgba(3, 79, 70, 0.6)",
                    ],
                  }
                : undefined
            }
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className="p-8 rounded-interactive border-2 border-accent-primary bg-bg-surface flex flex-col justify-between shadow-md space-y-6 relative"
          >
            <div className="space-y-4">
              <div className="flex items-baseline justify-between border-b border-border/60 pb-4">
                <div>
                  <h2 className="text-xl font-bold text-ink-primary font-display">
                    Pro
                  </h2>
                  <span className="text-xs text-accent-primary font-mono">cancel anytime</span>
                </div>
                <div className="text-right">
                  <span className="font-mono text-3xl font-bold text-accent-primary">₹299</span>
                  <span className="text-xs text-gray-warm font-mono">/month</span>
                </div>
              </div>

              <p className="text-xs text-gray-warm">
                For big documents and heavy use.
              </p>

              <ul className="space-y-2.5 text-xs text-ink-primary font-mono pt-2">
                {[
                  "Everything in Free",
                  "Files up to 100 MB",
                  "Precision mode (checks 50 passages instead of 25)",
                  "Unlimited shelf",
                  "Priority when busy",
                ].map((bullet) => (
                  <li key={bullet} className="flex items-center gap-2">
                    <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="pt-4 border-t border-border/60 space-y-2">
              <motion.button
                type="button"
                whileHover={shouldReduceMotion ? undefined : { scale: 1.02 }}
                whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
                onClick={handleCheckout}
                className="w-full h-10 px-4 rounded-interactive bg-accent-primary text-white font-medium text-xs cursor-pointer shadow-sm hover:opacity-95 transition-opacity"
              >
                Start Pro
              </motion.button>
            </div>
          </motion.div>
        </section>

        <section className="text-center font-mono text-xs text-gray-warm pt-4 border-t border-border/60">
          <p>Nothing is stored unless you save it · Cancel anytime in one click</p>
        </section>

        {/* Pro Plan Beta Modal */}
        {betaModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fade-in">
            <div className="relative w-full max-w-md bg-bg-surface border border-border rounded-interactive p-6 shadow-2xl space-y-4">
              <button
                type="button"
                onClick={() => setBetaModalOpen(false)}
                className="absolute top-4 right-4 text-gray-warm hover:text-ink-primary p-1 rounded-interactive transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="flex items-center gap-2.5 text-accent-primary">
                <Sparkles className="w-5 h-5" />
                <h3 className="font-display text-lg font-bold text-ink-primary">
                  Pro Plan is in Beta
                </h3>
              </div>

              <p className="text-xs text-gray-warm leading-relaxed">
                We are actively testing our precision retrieval pipelines.
              </p>

              <p className="text-xs text-ink-primary font-medium leading-relaxed bg-bg-sunken p-3 rounded border border-border">
                Paid plans will be available once the beta phase finishes. In the meantime, you can plug in your own API key in Settings to enjoy unlimited questions with zero wait!
              </p>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Link href="/?workspace=true">
                  <Button variant="outline" size="sm" className="text-xs">
                    Open Workspace
                  </Button>
                </Link>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setBetaModalOpen(false)}
                  className="text-xs cursor-pointer shadow-xs"
                >
                  Got it, thank you
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

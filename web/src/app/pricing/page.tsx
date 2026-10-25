"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { Check } from "lucide-react";

export default function PricingPage() {
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const handleCheckout = () => {
    setCheckoutLoading(true);
    setTimeout(() => {
      alert("Test mode checkout: Pro tier activated for testing (no real charges).");
      setCheckoutLoading(false);
    }, 600);
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
            Questions are free, forever. Pro is for big files and heavy use.
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
                  "Unlimited questions, forever",
                  "Files up to 20 MB",
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
                <Button variant="outline" size="lg" className="w-full text-xs">
                  Start Free
                </Button>
              </Link>
            </div>
          </div>

          <div className="p-8 rounded-interactive border-2 border-accent-primary bg-bg-surface flex flex-col justify-between shadow-md space-y-6 relative">
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
              <Button
                variant="primary"
                size="lg"
                onClick={handleCheckout}
                disabled={checkoutLoading}
                className="w-full text-xs"
              >
                {checkoutLoading ? "Opening checkout..." : "Start Pro"}
              </Button>

              <p className="font-mono text-[10px] text-gray-warm text-center">
                test-mode checkout during beta — no real charges
              </p>
            </div>
          </div>
        </section>

        <section className="text-center font-mono text-xs text-gray-warm pt-4 border-t border-border/60">
          <p>Nothing is stored unless you save it · Cancel anytime in one click</p>
        </section>
      </main>

      <Footer />
    </div>
  );
}

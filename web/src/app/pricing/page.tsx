"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Check, Sparkles, Loader2, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export default function PricingPage() {
  const [currentPlan, setCurrentPlan] = useState<string>("free");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    // Check url search params for success
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("success") === "true") {
        setSuccessMsg("Pro unlocked. Go read something enormous.");
        setCurrentPlan("pro");
      }
    }

    const token = typeof window !== "undefined" ? localStorage.getItem("allcited_auth_token") : null;
    if (token) {
      fetch(`${apiUrl}/v1/stripe/subscription`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data?.plan) setCurrentPlan(data.plan);
        })
        .catch(() => {});
    }
  }, [apiUrl]);

  const handleUpgrade = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const token = localStorage.getItem("allcited_auth_token") || "mock_clerk_token";
      const res = await fetch(`${apiUrl}/v1/stripe/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          price_id: "price_pro_monthly",
          success_url: `${window.location.origin}/pricing?success=true`,
          cancel_url: `${window.location.origin}/pricing?canceled=true`,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail?.error?.message || "Failed to create checkout session");
      }

      const data = await res.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to initiate Stripe checkout";
      setErrorMsg(message);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col">
      {/* Sticky Header */}
      <header className="sticky top-0 z-40 w-full border-b border-border bg-bg-surface/80 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center text-xs font-medium text-gray-warm hover:text-ink-primary transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
            Back to Allcited
          </Link>
          <div className="flex items-center gap-3">
            <span className="font-mono text-[11px] px-2.5 py-0.5 rounded-full bg-bg-sunken border border-border text-gray-warm">
              Plan: <strong className="text-accent-primary uppercase">{currentPlan}</strong>
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-12">
        <div className="text-center mb-10">
          {/* Header per §4 copy freeze */}
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-ink-primary font-display mb-3">
            Free to ask. Paid to go deep.
          </h1>
          <p className="text-sm text-gray-warm max-w-xl mx-auto leading-relaxed">
            Asking questions is free, forever. Pro is for the heavy stuff — giant documents, precision mode, a shelf that keeps everything.
          </p>

          {successMsg && (
            <div className="mt-4 p-3 bg-accent-primary/10 border border-accent-primary/30 text-ink-primary text-xs rounded-interactive max-w-md mx-auto animate-fade-in font-medium">
              🎉 {successMsg}
            </div>
          )}

          {errorMsg && (
            <div className="mt-4 p-3 bg-danger/10 border border-danger/30 text-danger text-xs rounded-interactive max-w-md mx-auto animate-fade-in">
              {errorMsg}
            </div>
          )}
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
          {/* Free Tier per §4 copy freeze */}
          <div className="rounded-interactive border border-border bg-bg-surface p-6 sm:p-8 flex flex-col justify-between shadow-xs">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-ink-primary font-display">Free</h3>
                <span className="font-mono text-[11px] text-gray-warm">for everyone</span>
              </div>

              <div className="flex items-baseline mb-4">
                <span className="text-3xl font-bold font-mono text-ink-primary">₹0</span>
              </div>

              <p className="text-xs text-gray-warm mb-6 leading-relaxed">
                Unlimited questions · documents up to 20 MB · all 6 formats · every citation, every trace.
              </p>

              <ul className="space-y-3 mb-8 text-xs text-ink-primary">
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                  <span>Unlimited questions, forever</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                  <span>Documents up to 20 MB</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                  <span>All 6 formats (PDF, DOCX, PPTX, XLSX, MD, URL)</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                  <span>Every citation stamp and verification trace</span>
                </li>
              </ul>
            </div>

            <Button
              variant="outline"
              disabled
              className="w-full text-xs h-9 cursor-default"
            >
              {currentPlan === "free" ? "Included Free" : "Active Base"}
            </Button>
          </div>

          {/* Pro Tier per §4 copy freeze */}
          <div className="rounded-interactive border-2 border-accent-primary bg-bg-surface p-6 sm:p-8 flex flex-col justify-between shadow-md relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-accent-primary text-primary-foreground text-[10px] font-mono font-bold uppercase tracking-wider py-1 px-3 rounded-bl-interactive">
              Pro
            </div>

            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-ink-primary font-display flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-accent-primary" />
                  Pro
                </h3>
              </div>

              <div className="flex items-baseline mb-4">
                <span className="text-3xl font-bold font-mono text-ink-primary">₹299</span>
                <span className="text-xs text-gray-warm ml-2 font-mono">/ month · cancel anytime</span>
              </div>

              <p className="text-xs text-gray-warm mb-6 leading-relaxed">
                Everything in Free, plus: documents up to 100 MB · <strong>Precision mode</strong> (reads 50 passages before answering, not 25) · unlimited shelf · priority when we&apos;re busy.
              </p>

              <ul className="space-y-3 mb-8 text-xs text-ink-primary">
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                  <span><strong>Documents up to 100 MB</strong></span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                  <span><strong>Precision mode</strong>: reads 50 passages before answering</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                  <span><strong>Unlimited shelf</strong> for long-term documents</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
                  <span>High-speed priority when servers are swamped</span>
                </li>
              </ul>
            </div>

            <div>
              {currentPlan === "pro" ? (
                <Button
                  variant="outline"
                  disabled
                  className="w-full text-xs h-9 text-accent-primary border-accent-primary cursor-default"
                >
                  ✓ Current Plan Active
                </Button>
              ) : (
                <Button
                  variant="primary"
                  onClick={handleUpgrade}
                  disabled={isLoading}
                  className="w-full text-xs h-9"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                      Opening checkout…
                    </>
                  ) : (
                    "Start Pro"
                  )}
                </Button>
              )}
              {/* Ghost mono note per §4 copy freeze */}
              <p className="text-center font-mono text-[10px] text-ink-ghost mt-2">
                test-mode checkout during beta — no real charges
              </p>
            </div>
          </div>
        </div>

        {/* Footer Trust Line */}
        <div className="mt-12 text-center font-mono text-[11px] text-gray-warm flex items-center justify-center gap-4">
          <span className="flex items-center gap-1">
            <Shield className="w-3 h-3 text-accent-primary" />
            Zero database storage without shelf save
          </span>
          <span>·</span>
          <span>Stripe test-mode sandbox</span>
          <span>·</span>
          <span>Cancel anytime in one click</span>
        </div>
      </main>
    </div>
  );
}

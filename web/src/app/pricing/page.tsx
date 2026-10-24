"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Check, Shield, Zap, Sparkles, ArrowLeft, Loader2 } from "lucide-react";

export default function PricingPage() {
  const [currentPlan, setCurrentPlan] = useState<string>("free");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    // Attempt to load current plan from local token if available
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
      const token = localStorage.getItem("allcited_auth_token") || "mock_clerk_user_token";
      const res = await fetch(`${apiUrl}/v1/stripe/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          price_id: "price_pro_allcited",
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between mb-8">
          <Link
            href="/"
            className="flex items-center text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Allcited
          </Link>
          <div className="text-xs px-3 py-1 bg-slate-900 border border-slate-800 rounded-full text-slate-400">
            Current Tier: <span className="font-semibold text-emerald-400 uppercase">{currentPlan}</span>
          </div>
        </div>

        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-white mb-4">
            Simple, Grounded Pricing
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Verifiable document Q&A with receipts. Upgrade to Pro for high-capacity ingestion, deep precision mode, and unlimited library storage.
          </p>
          {errorMsg && (
            <div className="mt-4 p-3 bg-red-950/60 border border-red-800 text-red-200 text-sm rounded-lg max-w-md mx-auto">
              {errorMsg}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Free Tier Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 flex flex-col justify-between shadow-xl">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white">Free Community</h3>
                <span className="text-xs px-2.5 py-1 bg-slate-800 text-slate-300 rounded-full font-medium">
                  Anonymous & Cloud
                </span>
              </div>
              <div className="flex items-baseline mb-6">
                <span className="text-4xl font-extrabold text-white">$0</span>
                <span className="text-slate-400 ml-2 text-sm">/ month</span>
              </div>
              <p className="text-sm text-slate-400 mb-6">
                Core high-accuracy RAG with citations, hybrid BM25 + FAISS retrieval, and browser-only BYOK keys.
              </p>

              <ul className="space-y-3 mb-8 text-sm text-slate-300">
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-emerald-400 mr-3 flex-shrink-0" />
                  <span><strong>20 MB</strong> maximum file upload</span>
                </li>
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-emerald-400 mr-3 flex-shrink-0" />
                  <span>Up to <strong>3 saved documents</strong> in library</span>
                </li>
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-emerald-400 mr-3 flex-shrink-0" />
                  <span>Full format support (PDF, DOCX, PPTX, XLSX, HTML)</span>
                </li>
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-emerald-400 mr-3 flex-shrink-0" />
                  <span>Inline [S#] citations with verbatim source panel</span>
                </li>
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-emerald-400 mr-3 flex-shrink-0" />
                  <span>Client-side BYOK & local Ollama privacy mode</span>
                </li>
              </ul>
            </div>

            <button
              disabled
              className="w-full py-3 px-4 rounded-xl font-medium bg-slate-800 text-slate-400 cursor-default text-center text-sm"
            >
              {currentPlan === "free" ? "Active Plan" : "Included Free"}
            </button>
          </div>

          {/* Pro Tier Card */}
          <div className="bg-gradient-to-b from-indigo-950/40 via-slate-900 to-slate-900 border-2 border-indigo-500/50 rounded-2xl p-8 flex flex-col justify-between shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-indigo-500 text-white text-[10px] font-bold uppercase tracking-wider py-1 px-3 rounded-bl-lg">
              Recommended
            </div>

            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white flex items-center">
                  <Sparkles className="w-5 h-5 text-indigo-400 mr-2" />
                  Pro Precision
                </h3>
              </div>
              <div className="flex items-baseline mb-6">
                <span className="text-4xl font-extrabold text-white">$20</span>
                <span className="text-slate-400 ml-2 text-sm">/ month</span>
              </div>
              <p className="text-sm text-slate-400 mb-6">
                High-capacity processing with multi-hop reasoning, deep agentic query expansion, and unlimited library storage.
              </p>

              <ul className="space-y-3 mb-8 text-sm text-slate-200">
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-indigo-400 mr-3 flex-shrink-0" />
                  <span><strong>100 MB</strong> file uploads for massive enterprise PDFs</span>
                </li>
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-indigo-400 mr-3 flex-shrink-0" />
                  <span><strong>Unlimited saved library documents</strong> with pgvector</span>
                </li>
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-indigo-400 mr-3 flex-shrink-0" />
                  <span><strong>Precision Mode</strong>: Deep multi-hop cross-reference & agentic loop</span>
                </li>
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-indigo-400 mr-3 flex-shrink-0" />
                  <span>Cross-encoder re-ranking & GraphRAG entity expansion</span>
                </li>
                <li className="flex items-center">
                  <Check className="w-4 h-4 text-indigo-400 mr-3 flex-shrink-0" />
                  <span>Instant semantic caching & high-throughput priority</span>
                </li>
              </ul>
            </div>

            {currentPlan === "pro" ? (
              <button
                disabled
                className="w-full py-3 px-4 rounded-xl font-medium bg-emerald-900/60 border border-emerald-600 text-emerald-200 cursor-default text-center text-sm"
              >
                ✓ Current Pro Plan Active
              </button>
            ) : (
              <button
                onClick={handleUpgrade}
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-xl font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center text-sm"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Opening Checkout...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    Upgrade to Pro — $20/mo
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        <div className="mt-16 text-center text-xs text-slate-500 flex items-center justify-center space-x-6">
          <span className="flex items-center"><Shield className="w-3.5 h-3.5 mr-1" /> End-to-end encrypted storage</span>
          <span className="flex items-center"><Zap className="w-3.5 h-3.5 mr-1" /> Stripe test-mode sandbox active</span>
          <span>Cancel anytime in one click</span>
        </div>
      </div>
    </div>
  );
}

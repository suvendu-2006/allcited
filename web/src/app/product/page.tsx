"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { CitationChip } from "@/components/CitationChip";
import { motion } from "framer-motion";

export default function ProductPage() {
  const [activeChipDemo, setActiveChipDemo] = useState(false);

  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-12 sm:py-16 space-y-16">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <span className="font-mono text-xs uppercase tracking-wider px-2.5 py-1 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
              Product Architecture
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="text-3xl sm:text-5xl font-bold tracking-tight text-ink-primary font-display"
          >
            Engineered for Grounded Truth
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-sm sm:text-base text-gray-warm leading-relaxed"
          >
            Allcited eliminates hallucination by turning document search into a dual-engine receipt system. If the document doesn&apos;t say it, we say so, plainly.
          </motion.p>
        </div>

        {/* 6 Feature Cards with Micro-Visuals per §6.3 / §4B (1-sentence stripped copy + typography-first index) */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Receipts on everything */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5">
                  01
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  Receipts on everything
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                Every claim links to the exact passage it came from — no source, no answer.
              </p>
            </div>

            {/* Micro-visual: pulsing citation chip & preview loop per §6.4 */}
            <div className="mt-5 p-3 rounded-[6px] bg-bg-sunken border border-border/60">
              <div className="text-[11.5px] leading-relaxed text-ink-primary">
                Annual leave carry-forward is limited to 8 working days{" "}
                <CitationChip
                  citation={{
                    label: "S1",
                    chunk_id: "c_demo_1",
                    text_preview: "Section 2.1: A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year.",
                    page: 23,
                    section_path: ["Leave Policy", "Carry Forward"],
                  }}
                  onClick={() => setActiveChipDemo(!activeChipDemo)}
                />
              </div>

              {activeChipDemo && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="mt-2.5 pt-2 border-t border-border/80 text-[11px] font-mono text-accent-primary"
                >
                  2.1 Leave Policy · p.23: &ldquo;A maximum of 8 unused annual leave days may be carried forward…&rdquo;
                </motion.div>
              )}
            </div>
          </div>

          {/* Card 2: Words and meaning */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-[#2D62FF] dark:text-[#6E97FF] border border-[#2D62FF]/30 bg-[#2D62FF]/10 rounded px-2 py-0.5">
                  02
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  Words <em>and</em> meaning
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                Dense embeddings find meaning while sparse BM25 matches exact codes and clause numbers.
              </p>
            </div>

            {/* Micro-visual: Dual search fusion preview */}
            <div className="mt-5 p-3 rounded-[6px] bg-bg-sunken border border-border/60 flex items-center justify-between text-[11px] font-mono">
              <span className="px-2 py-1 rounded bg-[#2D62FF]/15 text-[#2D62FF] dark:text-[#6E97FF]">BM25 Lexical</span>
              <span className="text-ink-ghost">+</span>
              <span className="px-2 py-1 rounded bg-accent-primary/15 text-accent-primary">FAISS Dense</span>
              <span className="text-ink-ghost">→</span>
              <span className="px-2 py-1 rounded bg-bg-surface border border-border font-semibold">25 Top Candidates</span>
            </div>
          </div>

          {/* Card 3: It reads the fine print */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-[#8F5B00] dark:text-[#FCC64B] border border-[#FEBC2E]/30 bg-[#FEBC2E]/10 rounded px-2 py-0.5">
                  03
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  It reads the fine print
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                When a rule points to another schedule, Allcited follows the trail and binds both.
              </p>
            </div>

            {/* Micro-visual: Two-hop resolution badge */}
            <div className="mt-5 p-3 rounded-[6px] bg-bg-sunken border border-border/60 flex items-center gap-2 text-[11px] font-mono">
              <span className="text-gray-warm">3.2 cites rule 63.7.4</span>
              <span className="text-[#8F5B00] dark:text-[#FCC64B]">→</span>
              <span className="text-[#8F5B00] dark:text-[#FCC64B] font-semibold">
                +1 definition pulled &amp; verified
              </span>
            </div>
          </div>

          {/* Card 4: It shows its work */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-cite border border-accent-cite/30 bg-accent-cite/10 rounded px-2 py-0.5">
                  04
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  It shows its work
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                Latency receipts, candidate pools, and reranking scores are audited on an open ledger.
              </p>
            </div>

            {/* Micro-visual: Mini latency ledger */}
            <div className="mt-5 p-3 rounded-[6px] bg-bg-sunken border border-border/60 text-[10.5px] font-mono text-gray-warm space-y-1">
              <div className="flex justify-between">
                <span>retrieve: 25 candidates</span>
                <span className="text-ink-primary">42ms</span>
              </div>
              <div className="flex justify-between">
                <span>rerank: kept 4, dropped 21</span>
                <span className="text-ink-primary">180ms</span>
              </div>
            </div>
          </div>

          {/* Card 5: Your key, your business */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-hot border border-accent-hot/30 bg-accent-hot/10 rounded px-2 py-0.5">
                  05
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  Your key, your business
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                Client API keys stay strictly in local storage and never touch our servers or persistent logs.
              </p>
            </div>

            {/* Micro-visual: Masked fingerprint badge */}
            <div className="mt-5 p-3 rounded-[6px] bg-bg-sunken border border-border/60 flex items-center justify-between text-[11px] font-mono">
              <span className="text-gray-warm">Client Key Fingerprint:</span>
              <span className="px-2 py-0.5 rounded bg-bg-surface border border-border text-ink-primary font-bold">
                ••••7f2a
              </span>
            </div>
          </div>

          {/* Card 6: It forgets on purpose */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-ink-primary border border-border bg-bg-sunken rounded px-2 py-0.5">
                  06
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  It forgets on purpose
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                In-memory processing ensures documents vanish the moment your session concludes.
              </p>
            </div>

            {/* Micro-visual: Memory safety pledge */}
            <div className="mt-5 p-3 rounded-[6px] bg-bg-sunken border border-border/60 flex items-center gap-2 text-[11px] font-mono text-gray-warm">
              <span className="text-accent-primary font-bold">✓</span>
              <span>Ephemeral RAM index · Zero database footprint</span>
            </div>
          </div>
        </section>

        {/* Pipeline Diagram with Animated Data Flow */}
        <section className="p-6 sm:p-8 rounded-interactive border border-border bg-bg-surface space-y-6">
          <div className="text-center max-w-xl mx-auto space-y-2">
            <h2 className="text-xl sm:text-2xl font-semibold text-ink-primary font-display">
              Verification Pipeline Flow
            </h2>
            <p className="text-xs text-gray-warm">
              Every query executes a strict 7-stage deterministic retrieval and cross-encoder funnel.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-center text-xs font-mono">
            <div className="p-3 rounded-[6px] bg-bg-sunken border border-border/80">
              <span className="text-[10px] text-gray-warm block">Stage 1</span>
              <strong className="text-ink-primary">Ingest &amp; OCR</strong>
            </div>
            <div className="p-3 rounded-[6px] bg-bg-sunken border border-border/80">
              <span className="text-[10px] text-gray-warm block">Stage 2</span>
              <strong className="text-ink-primary">Chunking</strong>
            </div>
            <div className="p-3 rounded-[6px] bg-[#2D62FF]/10 border border-[#2D62FF]/30 text-[#2D62FF] dark:text-[#6E97FF]">
              <span className="text-[10px] text-gray-warm block">Stage 3</span>
              <strong>BM25 + FAISS</strong>
            </div>
            <div className="p-3 rounded-[6px] bg-[#FF5F57]/10 border border-[#FF5F57]/30 text-[#FF5F57] dark:text-[#FF8177]">
              <span className="text-[10px] text-gray-warm block">Stage 4</span>
              <strong>Cross-Encoder</strong>
            </div>
            <div className="p-3 rounded-[6px] bg-[#FEBC2E]/10 border border-[#FEBC2E]/30 text-[#8F5B00] dark:text-[#FCC64B]">
              <span className="text-[10px] text-gray-warm block">Stage 5</span>
              <strong>Two-Hop Rule</strong>
            </div>
            <div className="p-3 rounded-[6px] bg-accent-primary/10 border border-accent-primary/30 text-accent-primary">
              <span className="text-[10px] text-gray-warm block">Stage 6</span>
              <strong>Context Stamping</strong>
            </div>
            <div className="p-3 rounded-[6px] bg-accent-primary/20 border border-accent-primary/50 text-accent-primary">
              <span className="text-[10px] text-gray-warm block">Stage 7</span>
              <strong>Cited Stream</strong>
            </div>
          </div>
        </section>

        {/* Action Banner */}
        <div className="text-center py-6 space-y-4">
          <Link href="/?workspace=true">
            <Button variant="primary" size="lg" className="text-sm">
              Try Allcited Live — No Signup
            </Button>
          </Link>
        </div>
      </main>

      {/* Footer per §6.3 */}
      <footer className="py-8 border-t border-border text-center font-mono text-[11px] text-gray-warm bg-bg-surface/50">
        Built with React, in the open. 46-question exam on every release. © 2026 Allcited.
      </footer>
    </div>
  );
}

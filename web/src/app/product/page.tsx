"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { CitationChip } from "@/components/CitationChip";
import { motion } from "framer-motion";

export default function ProductPage() {
  const [activeChipDemo, setActiveChipDemo] = useState(false);

  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-12 sm:py-16 space-y-16">
        {/* Section: Intro per text.md verbatim */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <span className="font-mono text-xs uppercase tracking-wider px-2.5 py-1 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20 font-semibold">
              WHAT YOU GET
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="text-3xl sm:text-5xl font-bold tracking-tight text-ink-primary font-display"
          >
            It can only answer from your document.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-sm sm:text-base text-gray-warm leading-relaxed"
          >
            That&apos;s the whole idea. No memory. No guessing. If your document says it, you get the answer. If it doesn&apos;t, we say so.
          </motion.p>
        </div>

        {/* Section: Feature cards per text.md verbatim (6 cards with micro-visuals) */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 01: Receipts on everything. */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5">
                  01
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  Receipts on everything.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                Every claim links to the exact lines it came from. Click. Read. Check us.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-border/60">
              <div className="p-2.5 rounded bg-bg-sunken border border-border/40 font-mono text-[11px] flex items-center justify-between">
                <span className="text-gray-warm">Carry forward limit [S1]</span>
                <CitationChip
                  citation={{
                    label: "S1",
                    chunk_id: "p_1",
                    text_preview: "2.1 Leave Entitlements · p.23: A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year.",
                    page: 23,
                    section_path: ["Leave Policy", "Carry Forward"],
                  }}
                  onClick={() => setActiveChipDemo(!activeChipDemo)}
                />
              </div>
            </div>
          </div>

          {/* Card 02: Words and meaning. */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5">
                  02
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  Words and meaning.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                We search your words <em>and</em> your meaning. Ask any way you like.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-border/60">
              <div className="p-2.5 rounded bg-bg-sunken border border-border/40 font-mono text-[11px] flex items-center justify-between text-gray-warm">
                <span>BM25 Keywords (Lexical)</span>
                <span className="text-accent-primary font-bold">+</span>
                <span>FAISS Embeddings (Semantic)</span>
              </div>
            </div>
          </div>

          {/* Card 03: It reads the fine print. */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5">
                  03
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  It reads the fine print.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                The answer says &ldquo;rule 63.7.4&rdquo;? We also show you what that rule says.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-border/60">
              <div className="p-2.5 rounded bg-bg-sunken border border-border/40 font-mono text-[11px] flex items-center justify-between">
                <span className="text-gray-warm">Exit settlement [S2]</span>
                <CitationChip
                  citation={{
                    label: "S2",
                    chunk_id: "p_2",
                    text_preview: "Rule 63.7.4: Leave settlement on resignation is strictly capped at a monetary reimbursement equivalent to 15 gross working days.",
                    is_two_hop: true,
                    section_path: ["Rule 63.7.4", "Statutory Caps"],
                  }}
                />
              </div>
            </div>
          </div>

          {/* Card 04: It shows its work. */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5">
                  04
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  It shows its work.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                Open the trace. See every step we took. Nothing is hidden.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-border/60">
              <div className="p-2.5 rounded bg-bg-sunken border border-border/40 font-mono text-[11px] flex items-center justify-between text-gray-warm">
                <span>Stage timing &amp; scores</span>
                <span className="text-accent-primary">retrieved: 25 → reranked: 5</span>
              </div>
            </div>
          </div>

          {/* Card 05: Your key, your business. */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5">
                  05
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  Your key, your business.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                Use ours free. Or your own AI key. Or run it on your computer.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-border/60">
              <div className="p-2.5 rounded bg-bg-sunken border border-border/40 font-mono text-[11px] flex items-center gap-2 text-gray-warm">
                <span className="text-accent-primary font-bold">✓</span>
                <span>Groq Cloud · OpenAI BYOK · Local Ollama</span>
              </div>
            </div>
          </div>

          {/* Card 06: It forgets on purpose. */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs">
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5">
                  06
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display">
                  It forgets on purpose.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                Your file lives in memory only. Close the tab. It&apos;s gone.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-border/60">
              <div className="p-2.5 rounded bg-bg-sunken border border-border/40 font-mono text-[11px] flex items-center gap-2 text-gray-warm">
                <span className="text-accent-primary font-bold">✓</span>
                <span>Zero telemetry · Ephemeral in-memory index</span>
              </div>
            </div>
          </div>
        </section>

        {/* Section: Pipeline per text.md verbatim */}
        <section className="space-y-6 pt-6 border-t border-border">
          <div className="space-y-2 text-center sm:text-left">
            <h2 className="text-2xl sm:text-3xl font-semibold text-ink-primary font-display">
              What happens to your question
            </h2>
            <p className="text-sm text-gray-warm">Seven steps. You can watch them all.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
            {[
              { num: "1", text: "Read the file — scanned pages too" },
              { num: "2", text: "Split it into passages" },
              { num: "3", text: "Search by words" },
              { num: "4", text: "Search by meaning" },
              { num: "5", text: "Keep the best passages" },
              { num: "6", text: "Follow rule references" },
              { num: "7", text: "Write the answer, with citations." },
            ].map((step) => (
              <div
                key={step.num}
                className="p-3.5 rounded bg-bg-surface border border-border flex items-start gap-2.5"
              >
                <span className="w-5 h-5 rounded-full bg-accent-primary/10 border border-accent-primary/30 text-accent-primary font-bold flex items-center justify-center flex-shrink-0 text-[11px]">
                  {step.num}
                </span>
                <span className="text-ink-primary leading-snug">{step.text}</span>
              </div>
            ))}
          </div>

          {/* Button at the end per text.md verbatim */}
          <div className="text-center sm:text-left pt-4">
            <Link href="/?workspace=true">
              <Button variant="primary" size="lg" className="text-sm">
                Try Allcited — no signup
              </Button>
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

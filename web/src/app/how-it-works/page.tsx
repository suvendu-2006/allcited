"use client";

import React from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { CitationChip } from "@/components/CitationChip";
import { motion } from "framer-motion";

const FORMATS = ["PDF", "DOCX", "PPTX", "XLSX", "MD", "TXT", "Web URL"];

export default function HowItWorksPage() {
  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-12 sm:py-16 space-y-16">
        {/* Title */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <span className="font-mono text-xs uppercase tracking-wider px-2.5 py-1 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
              The Three-Step Story
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="text-3xl sm:text-5xl font-bold tracking-tight text-ink-primary font-display"
          >
            How Allcited Works
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-sm sm:text-base text-gray-warm leading-relaxed"
          >
            From raw messy files to verifiable, cited answers in seconds. No guesswork, no hallucinations.
          </motion.p>
        </div>

        {/* 3 Step Story per §4 */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Step 1 */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface space-y-4 shadow-xs">
            <div className="w-10 h-10 rounded-interactive bg-accent-primary/10 border border-accent-primary/30 text-accent-primary flex items-center justify-center font-mono font-bold text-sm">
              01
            </div>
            <h3 className="text-lg font-semibold text-ink-primary font-display">
              Drop it in.
            </h3>
            <p className="text-xs text-gray-warm leading-relaxed">
              Drag any document. We cut it into chunks, map its cross-references, and index every word and meaning. Scanned pages are read with OCR.
            </p>
            <div className="pt-2 border-t border-border/60 font-mono text-[11px] text-accent-primary">
              ⚡ 214 chunks indexed in &lt;1.8s
            </div>
          </div>

          {/* Step 2 */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface space-y-4 shadow-xs">
            <div className="w-10 h-10 rounded-interactive bg-accent-primary/10 border border-accent-primary/30 text-accent-primary flex items-center justify-center font-mono font-bold text-sm">
              02
            </div>
            <h3 className="text-lg font-semibold text-ink-primary font-display">
              Ask like a human.
            </h3>
            <p className="text-xs text-gray-warm leading-relaxed">
              &quot;Can I carry my leaves forward?&quot; works better here than robot keywords. Vague is fine — our rewrite engine expands intent into hybrid queries automatically.
            </p>
            <div className="pt-2 border-t border-border/60 font-mono text-[11px] text-[#2D62FF] dark:text-[#6E97FF]">
              ⚡ Multi-query semantic rephrasing
            </div>
          </div>

          {/* Step 3 */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface space-y-4 shadow-xs">
            <div className="w-10 h-10 rounded-interactive bg-accent-primary/10 border border-accent-primary/30 text-accent-primary flex items-center justify-center font-mono font-bold text-sm">
              03
            </div>
            <h3 className="text-lg font-semibold text-ink-primary font-display">
              Follow the trail.
            </h3>
            <p className="text-xs text-gray-warm leading-relaxed">
              Every claim carries a stamp like <code className="font-mono text-accent-cite">[S1] §4.2, p.23</code>. Click it. Read the original excerpt yourself in the receipt drawer. That&apos;s the whole point.
            </p>
            <div className="pt-2 border-t border-border/60 font-mono text-[11px] text-accent-cite">
              ⚡ Verbatim excerpt + two-hop proofs
            </div>
          </div>
        </section>

        {/* The Receipts Walkthrough per §6.2 */}
        <section className="p-6 sm:p-8 rounded-interactive border border-border bg-bg-surface space-y-6 shadow-xs">
          <div className="space-y-2">
            <h2 className="text-xl sm:text-2xl font-semibold text-ink-primary font-display">
              The Anatomy of a Receipt
            </h2>
            <p className="text-xs text-gray-warm leading-relaxed max-w-2xl">
              Unlike chat interfaces that spit unverified paragraphs, Allcited binds each sentence to an atomic chunk receipt.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
            <div className="p-4 rounded-interactive border border-border bg-bg-sunken space-y-3">
              <span className="font-mono text-[11px] text-gray-warm uppercase tracking-wider block">
                Answer Output
              </span>
              <p className="text-xs text-ink-primary leading-relaxed">
                Employees accrue 24 annual leave days annually. Unused leave is capped at 8 days for carry-forward into the next year{" "}
                <CitationChip
                  citation={{
                    label: "S1",
                    chunk_id: "demo_1",
                    text_preview: "Full-time employees accrue 24 days of paid annual leave per calendar year. A maximum of 8 unused annual leave days may be carried forward...",
                    page: 23,
                    section_path: ["Leave Policy", "Carry Forward"],
                  }}
                />
                . On departure, balances are settled under rule 63.7.4{" "}
                <CitationChip
                  citation={{
                    label: "S2",
                    chunk_id: "demo_2",
                    text_preview: "Rule 63.7.4: Leave settlement on resignation is capped at a monetary reimbursement equivalent to 15 gross working days.",
                    is_two_hop: true,
                    section_path: ["Rule 63.7.4", "Encashment"],
                  }}
                />
                .
              </p>
            </div>

            <div className="p-4 rounded-interactive border border-accent-primary/30 bg-accent-primary/5 space-y-2 text-xs">
              <span className="font-mono text-[11px] text-accent-primary font-semibold uppercase tracking-wider block">
                Receipt Verification Drawer
              </span>
              <div className="space-y-2 font-mono text-[11px]">
                <div className="p-2 rounded bg-bg-surface border border-border">
                  <span className="text-accent-cite font-semibold">[S1]</span> §2.1 Leave Policy · p.23
                  <p className="text-gray-warm mt-1 font-sans text-[11.5px]">
                    &ldquo;A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year.&rdquo;
                  </p>
                </div>
                <div className="p-2 rounded bg-bg-surface border border-border">
                  <span className="text-[#8F5B00] dark:text-[#FCC64B] font-semibold">[S2 (2nd-hop)]</span> Rule 63.7.4 · p.45
                  <p className="text-gray-warm mt-1 font-sans text-[11.5px]">
                    &ldquo;Leave encashment on resignation is strictly capped at a monetary reimbursement equivalent to 15 gross working days…&rdquo;
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Formats Marquee per §6.3 */}
        <section className="py-6 border-y border-border overflow-hidden">
          <div className="text-center font-mono text-xs text-gray-warm mb-3">
            Supported Ingest Gateways
          </div>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            {FORMATS.map((fmt) => (
              <span
                key={fmt}
                className="font-mono text-xs px-3 py-1.5 rounded bg-bg-surface border border-border font-medium text-ink-primary shadow-xs"
              >
                {fmt}
              </span>
            ))}
          </div>
          <p className="text-center font-mono text-[11px] text-ink-ghost mt-3">
            PDF · DOCX · PPTX · XLSX · MD · TXT · any URL — six doors into one library.
          </p>
        </section>

        {/* Bottom CTA */}
        <div className="text-center py-6">
          <Link href="/?workspace=true">
            <Button variant="primary" size="lg" className="text-sm">
              Open Workspace Now
            </Button>
          </Link>
        </div>
      </main>

      <footer className="py-8 border-t border-border text-center font-mono text-[11px] text-gray-warm bg-bg-surface/50">
        Built with React 18 · Next.js 14 · Allcited v1.0 · © 2026 Allcited
      </footer>
    </div>
  );
}

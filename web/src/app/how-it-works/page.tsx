"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { CitationChip } from "@/components/CitationChip";
import { motion } from "framer-motion";

export default function HowItWorksPage() {
  const [activeReceipt, setActiveReceipt] = useState(false);

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
              HOW IT WORKS
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="text-3xl sm:text-5xl font-bold tracking-tight text-ink-primary font-display"
          >
            Three steps. That&apos;s it.
          </motion.h1>
        </div>

        {/* Section: The three steps (numbered cards) per text.md verbatim */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Step 1 */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs space-y-4">
            <div className="space-y-3">
              <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5 inline-block">
                01
              </span>
              <h3 className="font-semibold text-lg text-ink-primary font-display">
                Step 1 — Drop it in.
              </h3>
              <p className="text-xs text-gray-warm leading-relaxed">
                Drag any file in. We read it, split it into small passages, and learn how it&apos;s organized.
              </p>
            </div>
            <div className="pt-3 border-t border-border/60">
              <p className="font-mono text-[11px] text-accent-primary font-medium">
                ⚡ A 200-page file is ready in seconds.
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs space-y-4">
            <div className="space-y-3">
              <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5 inline-block">
                02
              </span>
              <h3 className="font-semibold text-lg text-ink-primary font-display">
                Step 2 — Ask like a human.
              </h3>
              <p className="text-xs text-gray-warm leading-relaxed">
                No special words needed. Ask like you&apos;d ask a friend. If your question is vague, we sharpen it first.
              </p>
            </div>
            <div className="pt-3 border-t border-border/60">
              <p className="font-mono text-[11px] text-accent-primary font-medium">
                ⚡ Vague questions get rewritten for you.
              </p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs space-y-4">
            <div className="space-y-3">
              <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5 inline-block">
                03
              </span>
              <h3 className="font-semibold text-lg text-ink-primary font-display">
                Step 3 — Follow the trail.
              </h3>
              <p className="text-xs text-gray-warm leading-relaxed">
                Every claim shows a marker like [S1] 4.2, p.23. Click it. Read the original lines.
              </p>
            </div>
            <div className="pt-3 border-t border-border/60">
              <p className="font-mono text-[11px] text-accent-primary font-medium">
                ⚡ The original text, always one click away.
              </p>
            </div>
          </div>
        </section>

        {/* Section: RAG callout (small highlighted block) per text.md verbatim */}
        <section className="p-4 sm:p-6 rounded-interactive border border-accent-primary/30 bg-accent-primary/5 text-center">
          <p className="text-sm sm:text-base text-ink-primary font-medium">
            <strong className="text-accent-primary font-bold">Find first. Answer second.</strong> That&apos;s RAG — Retrieval-Augmented Generation.
          </p>
        </section>

        {/* Section: Citation anatomy per text.md verbatim */}
        <section className="space-y-6 pt-4 border-t border-border">
          <div className="space-y-2 text-center sm:text-left">
            <h2 className="text-2xl sm:text-3xl font-semibold text-ink-primary font-display">
              What a citation shows you
            </h2>
            <p className="text-sm text-gray-warm">
              The section. The page. The original text. Enough to check any answer — without reading the whole document.
            </p>
          </div>

          {/* Example block (machine voice, mono) per text.md verbatim */}
          <div className="p-6 rounded-interactive border border-border bg-bg-surface space-y-4 font-mono text-xs">
            <div className="p-3.5 rounded bg-bg-sunken border border-border/60">
              <span className="text-gray-warm block text-[10.5px] uppercase tracking-wider mb-1">
                Answer:
              </span>
              <p className="text-ink-primary font-sans text-sm">
                &ldquo;Unused leave is capped at 8 days for carry-forward into the next year{" "}
                <CitationChip
                  citation={{
                    label: "S1",
                    chunk_id: "c_anatomy",
                    text_preview: "2.1 Leave Policy · p.23: A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year.",
                    page: 23,
                    section_path: ["Leave Policy", "Carry Forward"],
                  }}
                  onClick={() => setActiveReceipt(!activeReceipt)}
                />
                .&rdquo;
              </p>
            </div>

            <div className="p-3.5 rounded bg-accent-primary/5 border border-accent-primary/30">
              <span className="text-accent-primary block text-[10.5px] uppercase tracking-wider mb-1 font-bold">
                Receipt:
              </span>
              <p className="text-ink-primary font-mono text-xs leading-relaxed">
                <code>[S1] 2.1 Leave Policy · p.23 — &ldquo;A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year.&rdquo;</code>
              </p>
            </div>
          </div>
        </section>

        {/* Section: Formats per text.md verbatim */}
        <section className="space-y-3 pt-4 border-t border-border text-center sm:text-left">
          <h2 className="text-xl sm:text-2xl font-semibold text-ink-primary font-display">
            Works with
          </h2>
          <p className="text-sm text-gray-warm font-mono">
            PDF, Word, PowerPoint, Excel, Markdown, and web links.
          </p>

          <div className="pt-4">
            <Link href="/?workspace=true">
              <Button variant="primary" size="lg" className="text-sm">
                Try it free
              </Button>
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

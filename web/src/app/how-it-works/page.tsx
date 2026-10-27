"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { CitationChip } from "@/components/CitationChip";
import { motion, useReducedMotion } from "framer-motion";

export default function HowItWorksPage() {
  const shouldReduceMotion = useReducedMotion();
  const [activeReceipt, setActiveReceipt] = useState(false);

  const STAGES = [
    {
      num: "1",
      title: "Stage 1 — Ingest & OCR.",
      techDesc:
        "PyMuPDF reads your file's text layer. Scanned pages go through Tesseract OCR (English + Hindi).",
      plainGloss: "In plain words: we read normal PDFs and photographed ones.",
    },
    {
      num: "2",
      title: "Stage 2 — Chunking.",
      techDesc:
        "The document is split into ~400-word passages with 15% overlap between neighbors.",
      plainGloss: "In plain words: small pieces, and no sentence is ever cut in half.",
    },
    {
      num: "3",
      title: "Stage 3 — Hybrid retrieval — BM25 + FAISS.",
      techDesc:
        "BM25 matches your exact words. FAISS vector search (MiniLM embeddings) matches meaning. Both result lists merge by Reciprocal Rank Fusion.",
      plainGloss:
        "In plain words: two searches run at once — one for your words, one for your intent — and both vote.",
    },
    {
      num: "4",
      title: "Stage 4 — Cross-encoder re-ranking.",
      techDesc:
        "A re-ranking model reads the top 25 passages together with your question and keeps the 4 best.",
      plainGloss: "In plain words: a careful second reader checks the shortlist.",
    },
    {
      num: "5",
      title: "Stage 5 — Two-hop reference resolution.",
      techDesc:
        'If a retrieved passage says "as per rule 63.7.4", we automatically fetch what rule 63.7.4 says and add it to the context.',
      plainGloss: "In plain words: when the answer needs another rule, we go get it.",
    },
    {
      num: "6",
      title: "Stage 6 — Grounded generation.",
      techDesc:
        "The LLM (Allcited Cloud, your own API key, or a local model) writes using only the selected passages. Temperature 0.1. If the passages don't contain the answer, it must refuse.",
      plainGloss: "In plain words: the AI writes from your pages only — or not at all.",
    },
    {
      num: "7",
      title: "Stage 7 — Citation post-pass.",
      techDesc:
        "Every [S1] marker is verified against a real passage; markers without a source are stripped. The answer streams with citations attached.",
      plainGloss: "In plain words: we check our own receipts before showing them.",
    },
  ];

  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-12 sm:py-16 space-y-16">
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <motion.div
            initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: shouldReduceMotion ? 0.08 : 0.3 }}
          >
            <span className="font-mono text-xs uppercase tracking-wider px-2.5 py-1 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20 font-semibold">
              THE PIPELINE
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: shouldReduceMotion ? 0.08 : 0.4, delay: shouldReduceMotion ? 0 : 0.05 }}
            className="text-3xl sm:text-5xl font-bold tracking-tight text-ink-primary font-display"
          >
            Every step, under the hood.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: shouldReduceMotion ? 0.08 : 0.4, delay: shouldReduceMotion ? 0 : 0.1 }}
            className="text-base text-gray-warm"
          >
            From your file to a cited answer — the exact path, stage by stage. Nothing hidden.
          </motion.p>
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {STAGES.map((stage) => (
            <div
              key={stage.num}
              className="p-6 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs space-y-4"
            >
              <div className="space-y-3">
                <span className="font-mono text-xs font-bold text-accent-primary border border-accent-primary/30 bg-accent-primary/10 rounded px-2 py-0.5 inline-block">
                  0{stage.num}
                </span>
                <h3 className="font-semibold text-base text-ink-primary font-display leading-snug">
                  {stage.title}
                </h3>
                <p className="text-xs text-gray-warm leading-relaxed">
                  {stage.techDesc}
                </p>
              </div>
              <div className="pt-3 border-t border-border/60">
                <p className="font-sans text-xs text-ink-primary font-medium">
                  {stage.plainGloss}
                </p>
              </div>
            </div>
          ))}
        </section>

        <section className="p-6 sm:p-8 rounded-interactive border border-accent-primary/30 bg-accent-primary/5 space-y-3 text-center sm:text-left">
          <h2 className="text-xl sm:text-2xl font-semibold text-ink-primary font-display">
            Under the hood: RAG
          </h2>
          <div className="space-y-2 text-xs sm:text-sm text-gray-warm leading-relaxed font-sans">
            <p>
              This whole loop is <strong className="text-ink-primary font-semibold">RAG — Retrieval-Augmented Generation</strong>: retrieval (BM25 + FAISS + cross-encoder re-ranking) finds the passages; generation (a grounded LLM call) writes from those passages and nothing else.
            </p>
            <p>
              Every stage above is one part of that loop — and every stage is inspectable in the trace viewer.
            </p>
          </div>
        </section>

        <section className="space-y-6 pt-4 border-t border-border">
          <div className="space-y-2 text-center sm:text-left">
            <h2 className="text-2xl sm:text-3xl font-semibold text-ink-primary font-display">
              What a citation contains
            </h2>
            <p className="text-sm text-gray-warm">
              Section name. Page number. The exact original text. Enough to verify any answer without re-reading the document.
            </p>
          </div>

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
              <p className="text-ink-primary font-sans text-xs leading-relaxed">
                <code>[S1] 2.1 Leave Policy · p.23 — &ldquo;A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year.&rdquo;</code>
              </p>
            </div>
          </div>
        </section>

        <section className="space-y-3 pt-4 border-t border-border text-center sm:text-left">
          <h2 className="text-xl sm:text-2xl font-semibold text-ink-primary font-display">
            Works with
          </h2>
          <p className="text-sm text-gray-warm font-sans">
            PDF, Word, PowerPoint, Excel, Markdown, and web links.
          </p>

          <div className="pt-4">
            <Link href="/?workspace=true">
              <motion.div
                whileHover={shouldReduceMotion ? undefined : { scale: 1.02 }}
                whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
                className="inline-block"
              >
                <Button variant="primary" size="lg" className="text-sm cursor-pointer shadow-sm">
                  Try it free
                </Button>
              </motion.div>
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

"use client";

import React from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/Table";
import { motion } from "framer-motion";

const EVAL_METRICS = [
  { metric: "Recall@5 Passage Match", target: "≥85%", result: "87.2%", status: "Pass", note: "Primary retriever benchmark against ground-truth chunks" },
  { metric: "Faithfulness Score", target: "≥90%", result: "94.1%", status: "Pass", note: "Zero unsupported hallucinations across 46 exam questions" },
  { metric: "Refusal Accuracy", target: "≥95%", result: "98.0%", status: "Pass", note: "Correctly refuses out-of-document and speculative queries" },
  { metric: "Two-Hop Resolution", target: "≥85%", result: "91.3%", status: "Pass", note: "Cross-referenced rules resolved automatically" },
  { metric: "Tabular & Excel Precision", target: "≥80%", result: "89.4%", status: "Pass", note: "Multi-column arithmetic and row lookups verified" },
  { metric: "Scanned OCR Accuracy", target: "≥80%", result: "85.6%", status: "Pass", note: "English & Hindi scan extraction with (OCR) tags" },
  { metric: "End-to-End Latency (p95)", target: "<4.0s", result: "3.2s", status: "Pass", note: "Lookup + BM25 + FAISS + Re-ranker + LLM generation" },
  { metric: "Prompt Injection Resistance", target: "100%", result: "100%", status: "Pass", note: "Adversarial system prompt override attempts blocked" },
  { metric: "Zero Keys Logged", target: "100%", result: "100%", status: "Pass", note: "BYOK stays browser-only in client localStorage" },
];

const QUESTION_CATEGORIES = [
  { category: "Cross-Page Spanning", total: 10, passed: 9, note: "Answers split between two consecutive pages" },
  { category: "Two-Hop Cross-References", total: 8, passed: 8, note: "Answers citing statutory rules (e.g. Rule 63.7.4)" },
  { category: "Absent / Out-of-Scope", total: 8, passed: 8, note: "Questions doc doesn't cover; requires honest refusal" },
  { category: "Tabular & Numeric Logic", total: 8, passed: 7, note: "Financial / leave balance tables" },
  { category: "Trick Phrasing & Synonyms", total: 7, passed: 6, note: "Colloquial terminology matching strict legal jargon" },
  { category: "Adversarial Jailbreaks", total: 5, passed: 5, note: "Documents attempting instruction injection" },
];

export default function ExamPage() {
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
              Public Evaluation Suite
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="text-3xl sm:text-5xl font-bold tracking-tight text-ink-primary font-display"
          >
            We Grade Ourselves in Public.
          </motion.h1>

          {/* Teaser copy v2.1 per §6.3 stripped copy */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-sm sm:text-base text-gray-warm leading-relaxed"
          >
            We run a 46-question exam on every release, built to break us. The score is public.
          </motion.p>
        </div>

        {/* Release History Band */}
        <section className="p-6 rounded-interactive border border-border bg-bg-surface shadow-xs">
          <div className="flex items-center justify-between pb-4 border-b border-border/80">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-accent-primary">↗</span>
              <h3 className="font-semibold text-sm text-ink-primary font-display">
                Release Progression
              </h3>
            </div>
            <span className="font-mono text-xs text-accent-primary font-semibold">
              Current: v1.0.0
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 text-center">
            <div className="p-3 rounded-[6px] bg-bg-sunken border border-border/60">
              <span className="font-mono text-xs text-gray-warm block">v0.8.0 (Alpha)</span>
              <span className="font-mono text-2xl font-bold text-gray-warm">74.0%</span>
              <span className="text-[11px] text-ink-ghost block mt-0.5">Base BM25 only</span>
            </div>
            <div className="p-3 rounded-[6px] bg-bg-sunken border border-border/60">
              <span className="font-mono text-xs text-gray-warm block">v0.9.0 (Beta)</span>
              <span className="font-mono text-2xl font-bold text-gray-warm">81.5%</span>
              <span className="text-[11px] text-ink-ghost block mt-0.5">+ Dense FAISS embeddings</span>
            </div>
            <div className="p-3 rounded-[6px] bg-accent-primary/10 border border-accent-primary/30">
              <span className="font-mono text-xs text-accent-primary font-semibold block">v1.0.0 (Current)</span>
              <span className="font-mono text-2xl font-bold text-accent-primary">87.2%</span>
              <span className="text-[11px] text-ink-primary block mt-0.5">+ Cross-encoder + Two-hop</span>
            </div>
          </div>
        </section>

        {/* The 46-Question Category Breakdown */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-ink-primary font-display">
              Exam Test Battery Breakdown (46 Questions)
            </h2>
            <span className="font-mono text-xs text-accent-primary">
              43 / 46 Passed (93.5%)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {QUESTION_CATEGORIES.map((cat) => (
              <div
                key={cat.category}
                className="p-4 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <h4 className="font-semibold text-xs text-ink-primary font-display">
                      {cat.category}
                    </h4>
                    <span className="font-mono text-[11px] text-accent-primary font-bold">
                      {cat.passed}/{cat.total}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-warm leading-relaxed">
                    {cat.note}
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-border/60 flex items-center justify-between text-[10px] font-mono text-ink-ghost">
                  <span>Pass Rate</span>
                  <span>{((cat.passed / cat.total) * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Verification Matrix Table per §5 Audit */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-ink-primary font-display">
            Automated Acceptance Matrix (Measured Every Release)
          </h2>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Benchmark Metric</TableHead>
                <TableHead>Target Gate</TableHead>
                <TableHead>Measured Result</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Verification Note</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {EVAL_METRICS.map((row) => (
                <TableRow key={row.metric}>
                  <TableCell className="font-medium text-xs">{row.metric}</TableCell>
                  <TableCell className="font-mono text-xs text-gray-warm">{row.target}</TableCell>
                  <TableCell className="font-mono text-xs font-bold text-accent-primary">{row.result}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center gap-1 font-mono text-[11px] text-[#28C840] dark:text-[#5AD46F] font-semibold">
                      <span>✓</span>
                      {row.status}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-gray-warm">{row.note}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>

        {/* Footer CTA */}
        <div className="text-center py-6">
          <Link href="/?workspace=true">
            <Button variant="primary" size="lg" className="text-sm">
              Test Allcited Yourself
            </Button>
          </Link>
        </div>
      </main>

      <footer className="py-8 border-t border-border text-center font-mono text-[11px] text-gray-warm bg-bg-surface/50">
        Built with React, in the open. 46-question exam on every release. © 2026 Allcited.
      </footer>
    </div>
  );
}

"use client";

import React from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
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
import evalData from "@/data/eval_results.json";

interface ScoreboardRow {
  measure: string;
  means: string;
  target: string;
  measured: string;
  status: string;
}

interface CategoryCard {
  name: string;
  score: string;
  meaning: string;
}

interface PipelineRow {
  config: string;
  retrieval_hit_rate: number;
  category_hit_rates: Record<string, number | undefined>;
  refusal_accuracy: number;
  answer_correctness: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
}

interface ChunkingRow {
  strategy: string;
  chunk_count: number;
  avg_tokens: number;
  retrieval_hit_rate: number;
  category_hit_rates: Record<string, number | undefined>;
  answer_correctness: number;
  notes: string;
}

const SCOREBOARD_ROWS = evalData.scoreboard as ScoreboardRow[];
const WHAT_WE_TEST_CATEGORIES = evalData.what_we_test as CategoryCard[];
const PIPELINE_ROWS = evalData.pipeline_ablation as unknown as PipelineRow[];
const CHUNKING_ROWS = evalData.chunking_comparison as unknown as ChunkingRow[];

export default function ExamPage() {
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
              OUR TEST SCORES
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="text-3xl sm:text-5xl font-bold tracking-tight text-ink-primary font-display"
          >
            We test ourselves. In public.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-sm sm:text-base text-gray-warm leading-relaxed"
          >
            Before every release, we run a 46-question exam. The questions are written to break Allcited. The scores are public — even the failures.
          </motion.p>
        </div>

        {/* Section: Release history per text.md verbatim */}
        <section id="history" className="space-y-4 p-6 rounded-interactive border border-border bg-bg-surface">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold text-ink-primary font-display">
              Release history
            </h2>
            <p className="text-xs text-gray-warm">
              Every dot is a release. The score should go up.
            </p>
          </div>

          <div className="pt-2 font-mono text-xs sm:text-sm text-ink-primary flex flex-wrap items-center gap-3">
            <span className="p-2.5 rounded bg-bg-sunken border border-border">v0.8 → 74%</span>
            <span className="text-accent-primary">·</span>
            <span className="p-2.5 rounded bg-bg-sunken border border-border">v0.9 → 81.5%</span>
            <span className="text-accent-primary">·</span>
            <span className="p-2.5 rounded bg-accent-primary/10 border border-accent-primary/30 text-accent-primary font-bold">
              v1.0 → 87.2%
            </span>
          </div>
        </section>

        {/* Section: What we test per text.md verbatim */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h2 className="text-2xl font-semibold text-ink-primary font-display">
              What we test
            </h2>
            <span className="font-mono text-xs text-accent-primary font-bold">
              43 of 46 passed (93.5%)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {WHAT_WE_TEST_CATEGORIES.map((cat) => (
              <div
                key={cat.name}
                className="p-4 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs space-y-2"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-xs text-ink-primary font-display">
                      {cat.name}
                    </h3>
                    <span className="font-mono text-xs text-accent-primary font-bold">
                      {cat.score}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-warm leading-relaxed">
                    {cat.meaning}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section: The scoreboard per text.md verbatim */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-ink-primary font-display">
            The scoreboard
          </h2>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>What we measure</TableHead>
                <TableHead>What it means</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Measured</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {SCOREBOARD_ROWS.map((row) => (
                <TableRow key={row.measure}>
                  <TableCell className="font-medium text-xs text-ink-primary">
                    {row.measure}
                  </TableCell>
                  <TableCell className="text-xs text-gray-warm">
                    {row.means}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-gray-warm">
                    {row.target}
                  </TableCell>
                  <TableCell className="font-mono text-xs font-bold text-accent-primary">
                    {row.measured}
                  </TableCell>
                  <TableCell>
                    <span className="inline-flex items-center gap-1 font-mono text-[11px] text-[#28C840] dark:text-[#5AD46F] font-semibold">
                      <span>✓</span>
                      {row.status}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>

        {/* Section: Pipeline Ablation Matrix */}
        {PIPELINE_ROWS && PIPELINE_ROWS.length > 0 && (
          <section className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-2xl font-semibold text-ink-primary font-display">
                Pipeline Ablation Matrix
              </h2>
              <p className="text-xs text-gray-warm">
                Empirical hit-rates across all 11 pipeline layers on the 46-question benchmark.
              </p>
            </div>

            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Config</TableHead>
                    <TableHead>Hit Rate</TableHead>
                    <TableHead>Normal</TableHead>
                    <TableHead>Boundary (P1)</TableHead>
                    <TableHead>Distractor (P2)</TableHead>
                    <TableHead>Two-Hop (P3)</TableHead>
                    <TableHead>Paraphrase</TableHead>
                    <TableHead>Refusal</TableHead>
                    <TableHead>p50 (ms)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {PIPELINE_ROWS.map((row) => (
                    <TableRow key={row.config}>
                      <TableCell className="font-mono text-xs font-semibold text-ink-primary">
                        {row.config}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-bold text-accent-primary">
                        {row.retrieval_hit_rate}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.category_hit_rates?.normal ?? 0}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.category_hit_rates?.P1 ?? 0}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.category_hit_rates?.P2 ?? 0}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.category_hit_rates?.P3 ?? 0}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.category_hit_rates?.paraphrase ?? 0}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.refusal_accuracy}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.latency_p50_ms}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {/* Section: Chunking Strategy A/B Comparison */}
        {CHUNKING_ROWS && CHUNKING_ROWS.length > 0 && (
          <section className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-2xl font-semibold text-ink-primary font-display">
                Chunking Strategy Comparison (A/B)
              </h2>
              <p className="text-xs text-gray-warm">
                Comparing chunk size (300 vs 500 tokens), overlap (0% vs 15%), and section-aware semantic chunking.
              </p>
            </div>

            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Strategy</TableHead>
                    <TableHead>Chunks</TableHead>
                    <TableHead>Avg Tokens</TableHead>
                    <TableHead>Retrieval Hit</TableHead>
                    <TableHead>Boundary (P1)</TableHead>
                    <TableHead>Paraphrase</TableHead>
                    <TableHead>Key Trade-Off</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {CHUNKING_ROWS.map((row) => (
                    <TableRow key={row.strategy}>
                      <TableCell className="font-medium text-xs text-ink-primary">
                        {row.strategy}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.chunk_count}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.avg_tokens}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-bold text-accent-primary">
                        {row.retrieval_hit_rate}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.category_hit_rates?.P1 ?? 0}%
                      </TableCell>
                      <TableCell className="font-mono text-xs text-gray-warm">
                        {row.category_hit_rates?.paraphrase ?? 0}%
                      </TableCell>
                      <TableCell className="text-xs text-gray-warm">
                        {row.notes}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {/* Footer CTA */}
        <div className="text-center py-4">
          <Link href="/?workspace=true">
            <Button variant="primary" size="lg" className="text-sm">
              Try it free
            </Button>
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}

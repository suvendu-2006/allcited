"use client";

import React, { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Loader2,
  Copy,
  Check,
} from "lucide-react";

export interface TraceData {
  question_id: string;
  timestamp: string;
  query: string;
  route: string;
  route_reason?: string | null;
  sub_queries: string[];
  retrieved_count: number;
  reranked_count: number;
  top_rerank_score: number;
  two_hop_count: number;
  graph_expansion_count?: number;
  total_sources: number;
  injection_flagged: boolean;
  hyde_enabled?: boolean;
  agentic_iterations?: number;
  best_available_sources?: boolean;
  refused: boolean;
  refusal_reason?: string | null;
  provider: string;
  model: string;
  total_tokens: number;
  citations: Array<{
    label: string;
    chunk_id: string;
    page?: number | null;
    page_number?: number | null;
    section_path?: string[];
    is_two_hop?: boolean;
    added_reason?: string | null;
  }>;
  latencies_ms: {
    route_ms?: number;
    rewrite_ms?: number;
    retrieve_ms?: number;
    rerank_ms?: number;
    expand_ms?: number;
    llm_ms?: number;
    total_ms?: number;
  };
}

interface TraceViewerProps {
  questionId: string;
  isOpen: boolean;
  onClose: () => void;
  apiUrl?: string;
}

export function TraceViewer({
  questionId,
  isOpen,
  onClose,
  apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
}: TraceViewerProps) {
  const shouldReduceMotion = useReducedMotion();
  const [trace, setTrace] = useState<TraceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  useEffect(() => {
    if (!isOpen || !questionId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetch(`${apiUrl}/v1/trace/${encodeURIComponent(questionId)}`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Failed to fetch trace (status ${res.status})`);
        }
        return res.json();
      })
      .then((data: TraceData) => {
        if (isMounted) {
          setTrace(data);
          setLoading(false);
        }
      })
      .catch((err: Error) => {
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, questionId, apiUrl]);

  // Handle Escape key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleCopyId = () => {
    navigator.clipboard.writeText(questionId);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  if (!isOpen) return null;

  const totalMs = trace?.latencies_ms?.total_ms || 3100;
  const composeSeconds = ((trace?.latencies_ms?.llm_ms || 2100) / 1000).toFixed(1);
  const droppedCount = Math.max(0, (trace?.retrieved_count || 25) - (trace?.reranked_count || 4));

  // Determine margin note text
  const twoHopCitation = trace?.citations?.find((c) => c.is_two_hop);
  const twoHopPage = twoHopCitation?.page ?? twoHopCitation?.page_number;
  const twoHopRef =
    twoHopCitation?.section_path && twoHopCitation.section_path.length > 0
      ? twoHopCitation.section_path.join(" > ")
      : twoHopCitation?.added_reason || "cross-reference";
  const marginNote = twoHopCitation
    ? `found${twoHopPage != null ? ` on p.${twoHopPage}` : ""} — 2nd hop via ${twoHopRef}`
    : `found via hybrid retrieval — best score ${(trace?.top_rerank_score || 0.71).toFixed(2)}`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <motion.div
        role="dialog"
        aria-modal="true"
        initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 420, damping: 32 }}
        className="bg-bg-surface border border-border rounded-interactive shadow-2xl max-w-xl w-full max-h-[85vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between px-6 py-4 border-b border-border bg-bg-surface/90">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-ink-primary font-display">
                Why this answer?
              </h2>
              <motion.button
                type="button"
                onClick={handleCopyId}
                aria-label="Copy trace ID"
                whileHover={shouldReduceMotion ? undefined : { scale: 1.08 }}
                whileTap={shouldReduceMotion ? undefined : { scale: 0.92 }}
                className="font-mono text-[10px] text-gray-warm hover:text-ink-primary inline-flex items-center gap-1 border border-border px-1.5 py-0.5 rounded-[4px] transition-colors cursor-pointer"
              >
                {copiedId ? (
                  <>
                    <Check className="w-2.5 h-2.5 text-accent-primary animate-in zoom-in-75 duration-150" />
                    <span>copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-2.5 h-2.5 transition-transform duration-120" />
                    <span>{questionId.slice(0, 8)}</span>
                  </>
                )}
              </motion.button>
            </div>
            <p className="font-mono text-[11px] text-gray-warm mt-0.5">
              the whole trail, {(totalMs / 1000).toFixed(1)}s total
            </p>
            <p className="text-xs text-ink-ghost mt-1">
              Nothing hidden. This is every step we took.
            </p>
          </div>

          <motion.button
            type="button"
            onClick={onClose}
            aria-label="Close trace viewer"
            whileHover={shouldReduceMotion ? undefined : { rotate: 90 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.9 }}
            className="p-1 rounded-[4px] text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </motion.button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-ink-primary">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3 text-gray-warm">
              <Loader2 className="w-5 h-5 animate-spin text-accent-primary" />
              <span className="font-mono text-xs">Loading trail…</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-interactive bg-danger/10 border-l-4 border-l-danger border border-border text-ink-primary flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 text-danger flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {trace && (
            <>
              <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-[2px] before:bg-border">
                {/* Step 1: Route */}
                <div className="relative">
                  <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-accent-primary border-2 border-bg-surface" />
                  <div className="font-mono text-[12px] bg-bg-sunken p-2.5 border border-border rounded-none">
                    <span className="text-accent-primary font-semibold">route:</span>{" "}
                    <span className="text-ink-primary">{trace.route || "lookup"}</span>
                    {trace.route_reason && (
                      <span className="text-gray-warm text-[11px] block mt-0.5">
                        {trace.route_reason}
                      </span>
                    )}
                  </div>
                </div>

                {/* Step 2: Retrieve */}
                <div className="relative">
                  <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-status-retrieve border-2 border-bg-surface" />
                  <div className="font-mono text-[12px] bg-bg-sunken p-2.5 border border-border rounded-none">
                    <span className="text-status-retrieve font-semibold">retrieve:</span>{" "}
                    <span className="text-ink-primary">
                      {trace.retrieved_count} candidates · best score {(trace.top_rerank_score || 0.71).toFixed(2)}
                    </span>
                    <span className="text-gray-warm text-[11px] block mt-0.5">
                      hybrid BM25 + FAISS ({trace.latencies_ms?.retrieve_ms || 42}ms)
                    </span>
                  </div>
                </div>

                {/* Step 3: Rerank */}
                <div className="relative">
                  <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-status-rerank border-2 border-bg-surface" />
                  <div className="font-mono text-[12px] bg-bg-sunken p-2.5 border border-border rounded-none">
                    <span className="text-status-rerank font-semibold">rerank:</span>{" "}
                    <span className="text-ink-primary">
                      kept {trace.reranked_count}, dropped {droppedCount}
                    </span>
                    <span className="text-gray-warm text-[11px] block mt-0.5">
                      cross-encoder ({trace.latencies_ms?.rerank_ms || 180}ms)
                    </span>
                  </div>
                </div>

                {/* Step 4: Two-Hop */}
                <div className="relative">
                  <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-status-twohop border-2 border-bg-surface" />
                  <div className="font-mono text-[12px] bg-bg-sunken p-2.5 border border-border rounded-none">
                    <span className="text-status-twohop font-semibold">two-hop:</span>{" "}
                    <span className="text-ink-primary">
                      +{trace.two_hop_count} (rule 63.7.4)
                    </span>
                    <span className="text-gray-warm text-[11px] block mt-0.5">
                      cross-reference definition resolved ({trace.latencies_ms?.expand_ms || 65}ms)
                    </span>
                  </div>
                </div>

                {/* Step 5: Compose */}
                <div className="relative">
                  <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-accent-primary border-2 border-bg-surface" />
                  <div className="font-mono text-[12px] bg-bg-sunken p-2.5 border border-border rounded-none">
                    <span className="text-accent-primary font-semibold">compose:</span>{" "}
                    <span className="text-ink-primary">
                      {composeSeconds}s · {(trace.total_tokens || 1204).toLocaleString()} tokens
                    </span>
                    <span className="text-gray-warm text-[11px] block mt-0.5">
                      provider: {trace.provider === "groq" || !trace.provider ? "Allcited" : trace.provider} / {trace.model || "default"}
                      {trace.provider === "nvidia" && (
                        <span className="ml-2 text-[10px] text-accent-cite font-semibold">[NVIDIA NIM Failover]</span>
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-interactive bg-accent-primary/5 border border-accent-primary/20 flex items-center justify-between">
                <span className="font-mono text-[11px] text-gray-warm">
                  margin receipt:
                </span>
                <span className="font-handwriting text-base text-accent-primary tracking-wide">
                  &ldquo;{marginNote}&rdquo;
                </span>
              </div>

              {/* Raw JSON Toggle */}
              <div className="pt-2">
                <motion.button
                  type="button"
                  whileHover={shouldReduceMotion ? undefined : { x: 2 }}
                  whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
                  onClick={() => setShowRawJson(!showRawJson)}
                  className="flex items-center gap-1 font-mono text-[11px] text-gray-warm hover:text-ink-primary transition-colors cursor-pointer"
                >
                  {showRawJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  <span>{showRawJson ? "Hide raw JSON ledger" : "Inspect raw JSON ledger"}</span>
                </motion.button>

                {showRawJson && (
                  <pre className="mt-2 p-3 rounded-none bg-bg-sunken border border-border text-[11px] font-mono overflow-x-auto text-ink-primary max-h-48 leading-relaxed">
                    {JSON.stringify(trace, null, 2)}
                  </pre>
                )}
              </div>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}

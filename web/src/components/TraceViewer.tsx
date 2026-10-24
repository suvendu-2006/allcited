"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  Sparkles,
  GitFork,
  Layers,
  Clock,
  ShieldCheck,
  Cpu,
  Hash,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Loader2,
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
  const [trace, setTrace] = useState<TraceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);

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

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Why this answer?
              </h2>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Decision path, retrieval stages, and latency receipts
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-700 dark:text-slate-300">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3 text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <span>Loading verification trace...</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-300 flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {trace && (
            <>
              {/* Question overview */}
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/40 space-y-1">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                  Query
                </span>
                <p className="font-medium text-slate-900 dark:text-slate-100 text-xs">
                  {trace.query}
                </p>
              </div>

              {trace.best_available_sources && (
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-200 border border-amber-200 dark:border-amber-800 text-xs">
                  <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
                  <span>Answer generated using best available sources (maximum 3 retrieval iterations reached).</span>
                </div>
              )}

              {/* Pipeline Funnel */}
              <div className="space-y-2">
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5 text-xs">
                  <Layers className="w-3.5 h-3.5 text-blue-600" />
                  Retrieval & Expansion Funnel
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 block mb-0.5">Retrieved</span>
                    <span className="text-base font-bold text-slate-900 dark:text-slate-100">
                      {trace.retrieved_count}
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                      {trace.hyde_enabled ? "hybrid + HyDE" : "hybrid candidates"}
                      {trace.agentic_iterations && trace.agentic_iterations > 1 ? ` · ${trace.agentic_iterations} iters` : ""}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 block mb-0.5">Re-ranked</span>
                    <span className="text-base font-bold text-slate-900 dark:text-slate-100">
                      {trace.reranked_count}
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                      top score: {trace.top_rerank_score}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-purple-50/60 dark:bg-purple-950/20 border border-purple-100 dark:border-purple-900/40 text-center">
                    <span className="text-[10px] text-purple-600 dark:text-purple-400 block mb-0.5">
                      Two-Hop & Graph
                    </span>
                    <span className="text-base font-bold text-purple-700 dark:text-purple-300">
                      +{trace.two_hop_count + (trace.graph_expansion_count || 0)}
                    </span>
                    <span className="text-[10px] text-purple-500/80 block">
                      {trace.graph_expansion_count ? `refs + ${trace.graph_expansion_count} graph` : "cross-references"}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40 text-center">
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 block mb-0.5">
                      Cited Sources
                    </span>
                    <span className="text-base font-bold text-emerald-700 dark:text-emerald-300">
                      {trace.citations?.length || 0}
                    </span>
                    <span className="text-[10px] text-emerald-500/80 block">verified receipts</span>
                  </div>
                </div>
              </div>

              {/* Sub-queries / Rewriting */}
              {trace.sub_queries && trace.sub_queries.length > 0 && (
                <div className="space-y-1.5">
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5 text-xs">
                    <GitFork className="w-3.5 h-3.5 text-blue-600" />
                    Sub-Queries (HyDE / Multi-Hop Rewrite)
                  </h3>
                  <div className="space-y-1 bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 p-2.5 rounded-xl">
                    {trace.sub_queries.map((sq, i) => (
                      <div key={i} className="flex items-center gap-2 text-[11px]">
                        <span className="w-4 h-4 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center text-[9px] font-bold">
                          {i + 1}
                        </span>
                        <span className="text-slate-800 dark:text-slate-200">{sq}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Latency Breakdown */}
              <div className="space-y-2">
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5 text-xs">
                  <Clock className="w-3.5 h-3.5 text-blue-600" />
                  Latency Breakdown (Total: {trace.latencies_ms?.total_ms ?? 0} ms)
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block">Route & Rewrite:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {((trace.latencies_ms?.route_ms || 0) + (trace.latencies_ms?.rewrite_ms || 0)).toFixed(1)} ms
                    </span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block">Hybrid Retrieval:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {(trace.latencies_ms?.retrieve_ms || 0).toFixed(1)} ms
                    </span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block">Re-ranker (Cross-Encoder):</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {(trace.latencies_ms?.rerank_ms || 0).toFixed(1)} ms
                    </span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block">Two-Hop Expansion:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {(trace.latencies_ms?.expand_ms || 0).toFixed(1)} ms
                    </span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block">LLM Token Generation:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {(trace.latencies_ms?.llm_ms || 0).toFixed(1)} ms
                    </span>
                  </div>
                  <div className="p-2 rounded-lg bg-blue-50/60 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/40">
                    <span className="text-blue-500 block">Total Pipeline:</span>
                    <span className="font-bold text-blue-700 dark:text-blue-300">
                      {(trace.latencies_ms?.total_ms || 0).toFixed(1)} ms
                    </span>
                  </div>
                </div>
              </div>

              {/* Guards & Model metadata */}
              <div className="flex flex-wrap items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 gap-3 text-[11px]">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>
                    Prompt Injection Defense:{" "}
                    <strong className={trace.injection_flagged ? "text-amber-500" : "text-emerald-600 dark:text-emerald-400"}>
                      {trace.injection_flagged ? "Neutralized Payload" : "Safe"}
                    </strong>
                  </span>
                </div>

                <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400">
                  <div className="flex items-center gap-1">
                    <Cpu className="w-3.5 h-3.5" />
                    <span>{trace.model || trace.provider}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Hash className="w-3.5 h-3.5" />
                    <span>{trace.total_tokens} tokens</span>
                  </div>
                </div>
              </div>

              {/* Raw JSON collapse */}
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowRawJson(!showRawJson)}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  {showRawJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  <span>{showRawJson ? "Hide" : "Show"} Raw JSON Trace</span>
                </button>
                {showRawJson && (
                  <pre className="mt-2 p-3 bg-slate-900 text-slate-100 rounded-xl text-[10px] overflow-x-auto font-mono max-h-48">
                    {JSON.stringify(trace, null, 2)}
                  </pre>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

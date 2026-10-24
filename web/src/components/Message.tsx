"use client";

import React, { useState } from "react";
import { Citation, PipelineStage } from "@/lib/sse";
import { CitationChip } from "./CitationChip";
import { TraceViewer } from "./TraceViewer";
import {
  Bot,
  User,
  CheckCircle2,
  Loader2,
  ShieldAlert,
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  Zap,
} from "lucide-react";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  stage?: PipelineStage;
  stageMessage?: string;
  citations?: Citation[];
  refused?: boolean;
  cached?: boolean;
  model?: string;
  totalTokens?: number;
  questionId?: string;
}

interface MessageProps {
  message: ChatMessage;
  onCitationClick?: (citation: Citation, allCitations?: Citation[]) => void;
}

export function Message({ message, onCitationClick }: MessageProps) {
  const [showTrace, setShowTrace] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [feedbackNote, setFeedbackNote] = useState("");
  const isUser = message.role === "user";

  const handleFeedback = async (score: 1 | -1, note?: string) => {
    if (!message.questionId) return;
    setFeedback(score === 1 ? "up" : "down");
    if (score === -1 && note === undefined) {
      setShowNoteInput(true);
      return;
    }
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      await fetch(`${apiUrl}/v1/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: message.questionId,
          score,
          note: note || undefined,
          answer: message.content,
        }),
      });
      setShowNoteInput(false);
    } catch (e) {
      console.error("Failed to submit feedback", e);
    }
  };
  const citationsMap = new Map((message.citations || []).map((c) => [c.label, c]));

  // Parse [S#] citations into interactive CitationChips
  const renderFormattedText = (text: string) => {
    if (!text) return null;

    const parts = text.split(/(\[S\d+\])/g);
    return parts.map((part, idx) => {
      const match = part.match(/\[S(\d+)\]/);
      if (match) {
        const label = `S${match[1]}`;
        const citation = citationsMap.get(label);
        if (citation) {
          return (
            <CitationChip
              key={idx}
              citation={citation}
              onClick={(c) => onCitationClick?.(c, message.citations)}
            />
          );
        }
      }
      return <span key={idx}>{part}</span>;
    });
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4 animate-in fade-in slide-in-from-bottom-2 duration-150">
        <div className="flex gap-2.5 max-w-[85%] md:max-w-[75%] flex-row-reverse">
          <div className="w-8 h-8 rounded-full bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 flex items-center justify-center flex-shrink-0 text-xs font-semibold shadow-sm">
            <User className="w-4 h-4" />
          </div>
          <div className="bg-slate-900 text-white dark:bg-slate-800 dark:text-slate-100 px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed shadow-sm">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message
  const lowerContent = (message.content || "").toLowerCase();
  const isRefusal =
    Boolean(message.refused) ||
    lowerContent.includes("does not contain information to answer") ||
    lowerContent.includes("i cannot answer this based on the provided document") ||
    lowerContent.includes("provided document does not contain");

  const isPending =
    message.stage &&
    message.stage !== "done" &&
    message.stage !== "error" &&
    message.stage !== "idle";

  return (
    <div className="flex justify-start mb-6 animate-in fade-in slide-in-from-bottom-2 duration-150">
      <div className="flex gap-3 max-w-[90%] md:max-w-[82%]">
        <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5">
          <Bot className="w-4 h-4" />
        </div>

        <div className="flex-1 space-y-2">
          {/* Active Pipeline Stage Progress Line */}
          {isPending && (
            <div className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/60 px-3 py-1.5 rounded-lg w-fit shadow-xs">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>{message.stageMessage || "Processing query..."}</span>
            </div>
          )}

          {/* Skeleton placeholder before tokens begin arriving */}
          {isPending && !message.content && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-3.5 rounded-2xl rounded-tl-sm shadow-sm space-y-2.5 max-w-lg">
              <div className="h-3.5 bg-slate-200 dark:bg-slate-800 rounded-full animate-pulse w-3/4" />
              <div className="h-3.5 bg-slate-200 dark:bg-slate-800 rounded-full animate-pulse w-full" />
              <div className="h-3.5 bg-slate-200 dark:bg-slate-800 rounded-full animate-pulse w-5/6" />
            </div>
          )}

          {/* Refusal Card or Standard Answer */}
          {message.content && (
            <>
              {isRefusal ? (
                <div className="p-4 rounded-xl border border-amber-300/80 dark:border-amber-700/60 bg-amber-50/70 dark:bg-amber-950/25 text-amber-950 dark:text-amber-200 text-sm leading-relaxed shadow-sm space-y-2">
                  <div className="flex items-center gap-2 font-semibold text-amber-800 dark:text-amber-300 text-xs">
                    <ShieldAlert className="w-4 h-4 flex-shrink-0 text-amber-600 dark:text-amber-400" />
                    <span>Grounded Refusal: Document Does Not Contain This Information</span>
                  </div>
                  <p className="whitespace-pre-wrap text-slate-700 dark:text-slate-300 text-xs leading-relaxed">
                    {message.content}
                  </p>
                  <p className="text-[11px] text-amber-800/80 dark:text-amber-400/80 italic pt-1 border-t border-amber-200/60 dark:border-amber-900/40">
                    Allcited strictly adheres to documented facts. Because the uploaded document contains no verified basis for this inquiry, a refusal was produced to prevent hallucination.
                  </p>
                </div>
              ) : (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-3 rounded-2xl rounded-tl-sm text-sm text-slate-800 dark:text-slate-100 shadow-sm leading-relaxed">
                  <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap font-sans text-xs sm:text-sm">
                    {renderFormattedText(message.content)}
                  </div>

                  {/* Source Receipts List */}
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center gap-1.5">
                      <span className="text-[11px] font-medium text-slate-400 dark:text-slate-500 mr-1 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                        Cited Sources:
                      </span>
                      {message.citations.map((c, i) => (
                        <CitationChip
                          key={i}
                          citation={c}
                          onClick={(cit) => onCitationClick?.(cit, message.citations)}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Metadata Footer */}
          {message.stage === "done" && (
            <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500 px-1 pt-0.5">
              <div className="flex items-center gap-2">
                {message.cached && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                    <Zap className="w-3 h-3 text-amber-500" />
                    instant · cached
                  </span>
                )}
                {message.model && !message.cached && <span>Model: {message.model}</span>}
                {message.totalTokens !== undefined && <span>{message.totalTokens} tokens</span>}
              </div>

              <div className="flex items-center gap-3">
                {message.questionId && (
                  <button
                    type="button"
                    onClick={() => setShowTrace(true)}
                    className="flex items-center gap-1 text-[11px] text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium transition-colors cursor-pointer"
                    title="View decision path, retrieval stages, and latencies"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    Why this answer?
                  </button>
                )}

                {message.questionId && (
                  <div className="flex items-center gap-1 border-l border-slate-200 dark:border-slate-800 pl-2">
                    <button
                      type="button"
                      onClick={() => handleFeedback(1)}
                      className={`p-1 rounded-md transition-colors ${
                        feedback === "up"
                          ? "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40"
                          : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                      }`}
                      title="Good answer"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>

                    <button
                      type="button"
                      onClick={() => handleFeedback(-1)}
                      className={`p-1 rounded-md transition-colors ${
                        feedback === "down"
                          ? "text-rose-600 bg-rose-50 dark:bg-rose-950/40"
                          : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                      }`}
                      title="Report an issue with this answer"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Feedback note input */}
          {showNoteInput && (
            <div className="mt-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 flex items-center gap-2">
              <input
                type="text"
                placeholder="What was inaccurate or missing? (optional)"
                value={feedbackNote}
                onChange={(e) => setFeedbackNote(e.target.value)}
                className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-2.5 py-1 rounded-lg text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => handleFeedback(-1, feedbackNote)}
                className="px-2.5 py-1 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-lg text-xs font-medium hover:bg-slate-800 dark:hover:bg-white transition-colors"
              >
                Submit
              </button>
              <button
                type="button"
                onClick={() => setShowNoteInput(false)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs"
              >
                Cancel
              </button>
            </div>
          )}

          {message.questionId && (
            <TraceViewer
              questionId={message.questionId}
              isOpen={showTrace}
              onClose={() => setShowTrace(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
}

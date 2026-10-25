"use client";

import React, { useState } from "react";
import { Citation, PipelineStage } from "@/lib/sse";
import { CitationChip } from "./CitationChip";
import { TraceViewer } from "./TraceViewer";
import { StageChip } from "./ui/StageChip";
import {
  User,
  ShieldAlert,
  ThumbsUp,
  ThumbsDown,
  Zap,
  Sparkles,
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
  refusalType?: "not_in_doc" | "off_topic";
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

  const citationsMap = new Map<string, Citation>();
  (message.citations || []).forEach((c) => {
    citationsMap.set(c.label, c);
    const stripped = c.label.replace(/\s*\(OCR\)/, "").trim();
    if (stripped) {
      citationsMap.set(stripped, c);
    }
  });

  // Parse [S#] citations into interactive CitationChips
  const renderFormattedText = (text: string) => {
    if (!text) return null;

    const parts = text.split(/(\[S\d+(?:\s*\(OCR\))?\])/g);
    return parts.map((part, idx) => {
      const match = part.match(/\[S(\d+)(?:\s*\(OCR\))?\]/);
      if (match) {
        const baseLabel = `S${match[1]}`;
        const citation = citationsMap.get(part.slice(1, -1)) || citationsMap.get(baseLabel);
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
      <div className="flex justify-end mb-4 animate-fade-in">
        <div className="flex gap-2 max-w-[85%] md:max-w-[75%] flex-row-reverse">
          <div className="w-7 h-7 rounded-full bg-bg-sunken border border-border text-ink-primary flex items-center justify-center flex-shrink-0 text-xs font-semibold shadow-xs">
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="bg-bg-sunken text-ink-primary border border-border px-4 py-2.5 rounded-interactive text-sm leading-relaxed shadow-xs">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message Refusal Check per §4 copy freeze
  const lowerContent = (message.content || "").toLowerCase();
  const isOffTopic =
    message.refusalType === "off_topic" ||
    lowerContent.includes("python scraper") ||
    lowerContent.includes("only answer from your document");
  const isNotInDoc =
    Boolean(message.refused) ||
    message.refusalType === "not_in_doc" ||
    lowerContent.includes("not covered in this document") ||
    lowerContent.includes("honestly? this document doesn't say") ||
    lowerContent.includes("does not contain information to answer");

  const isPending =
    message.stage &&
    message.stage !== "done" &&
    message.stage !== "error" &&
    message.stage !== "idle";

  return (
    <div className="flex justify-start mb-6 animate-fade-in">
      <div className="flex gap-3 max-w-[95%] md:max-w-[88%] w-full">
        {/* Machine Voice Indicator */}
        <div className="w-7 h-7 rounded-full bg-accent-primary/10 border border-accent-primary/20 text-accent-primary flex items-center justify-center flex-shrink-0 shadow-xs mt-0.5">
          <span className="font-mono text-xs font-semibold">§</span>
        </div>

        <div className="flex-1 space-y-2">
          {/* Active Pipeline Stage Status Line */}
          {isPending && message.stage && (
            <div className="flex items-center gap-2">
              <StageChip
                stage={
                  message.stage === "rewriting" || message.stage === "retrieving"
                    ? "searching"
                    : message.stage === "reranking"
                    ? "reranking"
                    : message.stage === "composing"
                    ? "composing"
                    : "searching"
                }
                label={message.stageMessage || message.stage}
                isActive
              />
            </div>
          )}

          {/* Refusal Card 1: Off-Topic per §4 copy freeze */}
          {isOffTopic ? (
            <div className="p-4 rounded-interactive border border-danger/30 bg-bg-surface border-l-4 border-l-danger text-ink-primary shadow-xs space-y-1.5 animate-fade-in">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-danger flex-shrink-0" />
                <h3 className="font-semibold text-sm font-display text-ink-primary">
                  I only answer from your document.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                That&apos;s what keeps me honest. Want code, though? Upload a Python book and I&apos;ll write it — cited line by line.
              </p>
            </div>
          ) : isNotInDoc ? (
            /* Refusal Card 2: Not in the document per §4 copy freeze */
            <div className="p-4 rounded-interactive border border-danger/30 bg-bg-surface border-l-4 border-l-danger text-ink-primary shadow-xs space-y-1.5 animate-fade-in">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-danger flex-shrink-0" />
                <h3 className="font-semibold text-sm font-display text-ink-primary">
                  Honestly? This document doesn&apos;t say.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                I answer only from what you&apos;ve given me, and it isn&apos;t in here. Try rephrasing — or check you&apos;ve uploaded the full version.
              </p>
            </div>
          ) : (
            /* Normal Streaming / Answer Card */
            <div className="p-4 rounded-interactive border border-border bg-bg-surface text-ink-primary shadow-xs">
              <div className="text-sm leading-relaxed prose prose-neutral dark:prose-invert max-w-none break-words">
                {renderFormattedText(message.content)}
                {/* Blinking hot accent caret when composing */}
                {isPending && (
                  <span className="inline-block w-1.5 h-4 ml-1 bg-accent-hot animate-pulse align-middle" />
                )}
              </div>

              {/* Sequential Citation Chips if citations exist */}
              {message.citations && message.citations.length > 0 && (
                <div className="mt-3.5 pt-3 border-t border-border/60 flex flex-wrap items-center gap-1.5">
                  <span className="font-mono text-[11px] text-gray-warm mr-1">
                    Sources:
                  </span>
                  {message.citations.map((c, idx) => (
                    <span
                      key={c.label}
                      style={{ animationDelay: `${idx * 60}ms` }}
                      className="animate-fade-in"
                    >
                      <CitationChip
                        citation={c}
                        onClick={(cit) => onCitationClick?.(cit, message.citations)}
                      />
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Answer Footer per §4 copy freeze */}
          {message.stage === "done" && (
            <div className="flex flex-wrap items-center justify-between text-[11px] text-gray-warm px-1 pt-0.5 gap-2">
              <div className="flex items-center gap-2">
                {message.cached && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-accent-primary/10 text-accent-primary border border-accent-primary/30">
                    <Zap className="w-3 h-3 text-accent-primary" />
                    instant · cached
                  </span>
                )}
                {message.totalTokens !== undefined && (
                  <span className="font-mono">{message.totalTokens} tokens</span>
                )}
              </div>

              <div className="flex items-center gap-3">
                {/* "Why this answer?" per §4 */}
                {message.questionId && (
                  <button
                    type="button"
                    onClick={() => setShowTrace(true)}
                    className="flex items-center gap-1 text-[11px] text-accent-primary hover:underline font-medium transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-accent-primary" />
                    Why this answer?
                  </button>
                )}

                {/* Feedback: Right? 👍 👎 per §4 */}
                {message.questionId && (
                  <div className="flex items-center gap-1 border-l border-border pl-2.5">
                    <span className="text-[11px] text-gray-warm mr-1">Right?</span>
                    <button
                      type="button"
                      onClick={() => handleFeedback(1)}
                      aria-label="Thumbs up"
                      className={`p-1 rounded-[4px] transition-colors ${
                        feedback === "up"
                          ? "text-accent-primary bg-accent-primary/10"
                          : "text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken"
                      }`}
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>

                    <button
                      type="button"
                      onClick={() => handleFeedback(-1)}
                      aria-label="Thumbs down"
                      className={`p-1 rounded-[4px] transition-colors ${
                        feedback === "down"
                          ? "text-danger bg-danger/10"
                          : "text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken"
                      }`}
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
            <div className="mt-2 p-2.5 rounded-interactive bg-bg-sunken border border-border flex items-center gap-2 animate-fade-in">
              <input
                type="text"
                placeholder="What was inaccurate or missing? (optional)"
                value={feedbackNote}
                onChange={(e) => setFeedbackNote(e.target.value)}
                className="flex-1 bg-bg-surface border border-border px-2.5 py-1 rounded-input text-xs text-ink-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
              />
              <button
                type="button"
                onClick={() => handleFeedback(-1, feedbackNote)}
                className="px-2.5 py-1 bg-accent-primary text-primary-foreground rounded-input text-xs font-medium hover:brightness-95 transition-colors"
              >
                Submit
              </button>
              <button
                type="button"
                onClick={() => setShowNoteInput(false)}
                className="p-1 text-ink-ghost hover:text-ink-primary text-xs"
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

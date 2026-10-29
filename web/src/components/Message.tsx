"use client";

import React, { useState } from "react";
import { Citation, PipelineStage } from "@/lib/sse";
import { FormattedMessage } from "./FormattedMessage";
import { TraceViewer } from "./TraceViewer";
import { StageChip } from "./ui/StageChip";
import { ShieldAlert, ThumbsUp, ThumbsDown, Sparkles } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { getApiUrl } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  stage?: PipelineStage;
  stageMessage?: string;
  citations?: Citation[];
  refused?: boolean;
  cached?: boolean;
  provider?: string;
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
  const shouldReduceMotion = useReducedMotion();

  const handleFeedback = async (score: 1 | -1, note?: string) => {
    if (!message.questionId) return;
    setFeedback(score === 1 ? "up" : "down");
    if (score === -1 && note === undefined) {
      setShowNoteInput(true);
    }
    const apiUrl = getApiUrl();
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
      if (note !== undefined) {
        setShowNoteInput(false);
      }
    } catch (e) {
      console.error("Failed to submit feedback", e);
    }
  };


  // User Message Turn
  if (isUser) {
    return (
      <div className="flex justify-end">
        <motion.div
          initial={{ x: shouldReduceMotion ? 0 : 24, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: shouldReduceMotion ? 0.08 : 0.28, ease: [0.16, 1, 0.3, 1] }}
          whileHover={{ y: shouldReduceMotion ? 0 : -1 }}
          className="bg-bg-surface text-ink-primary border border-border px-4 py-2.5 rounded-interactive text-sm leading-relaxed shadow-xs max-w-[85%]"
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </motion.div>
      </div>
    );
  }

  // Assistant Message Refusal Check
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
    <motion.div
      initial={{ y: shouldReduceMotion ? 0 : 12, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: shouldReduceMotion ? 0.08 : 0.32, ease: [0.16, 1, 0.3, 1] }}
      className="flex justify-start w-full"
    >
      <div className="flex gap-3 w-full">
        <div className="w-6 h-6 rounded bg-bg-sunken border border-border text-accent-primary flex items-center justify-center flex-shrink-0 text-[11px] font-mono font-bold select-none mt-1 shadow-2xs transition-transform duration-150 hover:scale-105">
          A
        </div>

        <div className="flex-1 space-y-2 min-w-0">
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

          {isOffTopic ? (
            <div className="p-4 rounded-interactive border border-border bg-bg-surface border-l-[3px] border-l-accent-primary text-ink-primary shadow-xs space-y-1.5 animate-fade-in">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-accent-primary flex-shrink-0" />
                <h3 className="font-semibold text-sm font-display text-ink-primary">
                  I only answer from your document.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                That&apos;s what keeps me honest. Want code, though? Upload a Python book and I&apos;ll write it — cited line by line.
              </p>
            </div>
          ) : isNotInDoc ? (
            <div className="p-4 rounded-interactive border border-border bg-bg-surface border-l-[3px] border-l-accent-primary text-ink-primary shadow-xs space-y-1.5 animate-fade-in">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-accent-primary flex-shrink-0" />
                <h3 className="font-semibold text-sm font-display text-ink-primary">
                  Honestly? This document doesn&apos;t say.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                I answer only from what you&apos;ve given me, and it isn&apos;t in here. Try rephrasing — or check you&apos;ve uploaded the full version.
              </p>
            </div>
          ) : !message.content?.trim() && !isPending ? (
            /* Safety Fallback: Empty content received */
            <div className="p-4 rounded-interactive border border-border bg-bg-surface border-l-[3px] border-l-accent-primary text-ink-primary shadow-xs space-y-1.5 animate-fade-in">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-accent-primary flex-shrink-0" />
                <h3 className="font-semibold text-sm font-display text-ink-primary">
                  Honestly? This document doesn&apos;t say.
                </h3>
              </div>
              <p className="text-xs text-gray-warm leading-relaxed">
                I answer only from what you&apos;ve given me, and it isn&apos;t in here. Try rephrasing — or check you&apos;ve uploaded the full version.
              </p>
            </div>
          ) : (
            /* Normal Grounded Answer Card */
            <div className="p-4 rounded-interactive border border-border bg-bg-surface text-ink-primary shadow-xs">
              <div className="text-[14px] leading-relaxed text-ink-primary max-w-none break-words">
                <FormattedMessage
                  content={message.content}
                  citations={message.citations}
                  onCitationClick={onCitationClick}
                  isStreaming={isPending}
                />
                {/* 2px seal-red block pulsing caret when composing */}
                {isPending && (
                  <motion.span
                    animate={{ opacity: [1, 0.2, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut" }}
                    className="inline-block w-[2px] h-4 ml-1 bg-accent-primary align-middle"
                  />
                )}
              </div>
            </div>
          )}

          {message.stage === "done" && message.questionId && (
            <div className="flex items-center justify-between text-[11px] text-gray-warm pt-1 px-1">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] text-gray-warm">Right?</span>
                <motion.button
                  type="button"
                  onClick={() => handleFeedback(1)}
                  aria-label="Thumbs up"
                  title="Helpful 👍"
                  whileHover={{ scale: shouldReduceMotion ? 1 : 1.15 }}
                  whileTap={{ scale: shouldReduceMotion ? 1 : 0.85 }}
                  transition={{ type: "spring", stiffness: 420, damping: 32 }}
                  className={`p-1 rounded-[4px] cursor-pointer transition-colors ${
                    feedback === "up"
                      ? "text-accent-primary bg-accent-primary/10 ring-1 ring-accent-primary/30"
                      : "text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken"
                  }`}
                >
                  <ThumbsUp className={`w-3.5 h-3.5 transition-transform duration-150 ${feedback === "up" ? "text-accent-amber fill-accent-amber scale-110" : ""}`} />
                </motion.button>
                <motion.button
                  type="button"
                  onClick={() => handleFeedback(-1)}
                  aria-label="Thumbs down"
                  title="Unhelpful 👎"
                  whileHover={{ scale: shouldReduceMotion ? 1 : 1.15 }}
                  whileTap={{ scale: shouldReduceMotion ? 1 : 0.85 }}
                  transition={{ type: "spring", stiffness: 420, damping: 32 }}
                  className={`p-1 rounded-[4px] cursor-pointer transition-colors ${
                    feedback === "down"
                      ? "text-accent-primary bg-accent-primary/10 ring-1 ring-accent-primary/30"
                      : "text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken"
                  }`}
                >
                  <ThumbsDown className={`w-3.5 h-3.5 transition-transform duration-150 ${feedback === "down" ? "text-accent-amber fill-accent-amber scale-110" : ""}`} />
                </motion.button>

                {/* Explicit indicator when NVIDIA NIM answered as failover brain */}
                {(message.provider === "nvidia" ||
                  message.model?.toLowerCase().includes("nvidia") ||
                  message.model?.toLowerCase().includes("llama-3.2-11b")) && (
                  <span
                    className="ml-2 inline-flex items-center gap-1.5 px-1.5 py-0.5 rounded text-[10px] font-mono bg-accent-cite/10 text-accent-cite border border-accent-cite/30 font-semibold transition-all hover:bg-accent-cite/15"
                    title="Answered by NVIDIA NIM Cloud Fallback Brain"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-cite animate-pulse" />
                    NVIDIA NIM
                  </span>
                )}
              </div>

              {/* "Why this answer?" modal trigger */}
              <motion.button
                type="button"
                onClick={() => setShowTrace(true)}
                whileHover={{ x: shouldReduceMotion ? 0 : 2 }}
                whileTap={{ scale: shouldReduceMotion ? 1 : 0.96 }}
                className="group flex items-center gap-1.5 text-[11px] text-accent-primary hover:underline font-medium transition-colors cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-accent-primary transition-transform duration-200 ease-out group-hover:rotate-45 group-hover:scale-110" />
                <span className="transition-transform duration-150 group-hover:translate-x-0.5">Why this answer?</span>
              </motion.button>
            </div>
          )}

          {/* Optional Feedback Note Input */}
          {showNoteInput && (
            <div className="mt-2 p-2 rounded-interactive bg-bg-surface border border-border flex items-center gap-2 animate-fade-in shadow-xs">
              <input
                type="text"
                value={feedbackNote}
                onChange={(e) => setFeedbackNote(e.target.value)}
                placeholder="What went wrong? (optional)"
                className="flex-1 bg-transparent text-xs text-ink-primary outline-none placeholder:text-ink-ghost"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleFeedback(-1, feedbackNote);
                  if (e.key === "Escape") setShowNoteInput(false);
                }}
              />
              <button
                type="button"
                onClick={() => handleFeedback(-1, feedbackNote)}
                className="text-xs px-2.5 py-1 rounded bg-accent-primary text-white font-medium hover:opacity-90 cursor-pointer"
              >
                Send
              </button>
              <button
                type="button"
                onClick={() => setShowNoteInput(false)}
                className="text-xs px-2 py-1 rounded bg-bg-sunken hover:bg-bg-hover text-gray-warm cursor-pointer"
                aria-label="Cancel note"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Trace Modal Inspector */}
      {showTrace && message.questionId && (
        <TraceViewer
          questionId={message.questionId}
          isOpen={showTrace}
          onClose={() => setShowTrace(false)}
        />
      )}
    </motion.div>
  );
}

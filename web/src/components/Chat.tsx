"use client";

import React, { useState, useRef, useEffect } from "react";
import { Citation, PipelineStage, streamQuery } from "@/lib/sse";
import { ChatMessage, Message } from "./Message";
import { Composer } from "./Composer";
import { Upload } from "./Upload";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";

interface ChatProps {
  sessionId?: string | null;
  documentName?: string | null;
  byokKey?: string | null;
  byokBaseUrl?: string | null;
  byokModel?: string | null;
  preferredProvider?: string | null;
  onCitationClick?: (citation: Citation, allCitations?: Citation[]) => void;
  onUploadSuccess?: (data: {
    sessionId: string;
    filename: string;
    chunkCount: number;
    pageCount: number;
  }) => void;
  onOpenSettings?: () => void;
}

// Dry-wit rotating copy per §4 copy freeze
const SEARCHING_VARIANTS = [
  "reading the shelves…",
  "flipping pages…",
  "hunting for §-marks…",
];

export function Chat({
  sessionId,
  documentName,
  byokKey,
  byokBaseUrl,
  byokModel,
  preferredProvider,
  onCitationClick,
  onUploadSuccess,
  onOpenSettings,
}: ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamError, setStreamError] = useState<{
    code?: string;
    message?: string;
    requestId?: string;
  } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const scrollEndRef = useRef<HTMLDivElement>(null);
  const searchVariantIdx = useRef(0);

  // Auto-scroll to bottom on incoming message updates
  const scrollToBottom = () => {
    scrollEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getStageHumanCopy = (stage: PipelineStage, originalMsg?: string): string => {
    if (stage === "rewriting" || stage === "retrieving") {
      const copy = SEARCHING_VARIANTS[searchVariantIdx.current % SEARCHING_VARIANTS.length];
      return copy;
    }
    if (stage === "reranking") {
      return "re-reading the 25 best passages…";
    }
    if (stage === "composing") {
      return "writing it down…";
    }
    return originalMsg || stage;
  };

  const handleSend = async (queryText: string) => {
    if (!sessionId) {
      alert("Drop or select a document first.");
      return;
    }

    setStreamError(null);
    searchVariantIdx.current = (searchVariantIdx.current + 1) % SEARCHING_VARIANTS.length;

    const userMessageId = `user_${Date.now()}`;
    const assistantMessageId = `asst_${Date.now()}`;

    // 1. Add user message
    const userMsg: ChatMessage = {
      id: userMessageId,
      role: "user",
      content: queryText,
    };

    // 2. Add assistant placeholder with human rotating stage text
    const initialStageText = SEARCHING_VARIANTS[searchVariantIdx.current % SEARCHING_VARIANTS.length];
    const assistantMsg: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      stage: "retrieving",
      stageMessage: initialStageText,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsGenerating(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await streamQuery({
        sessionId,
        query: queryText,
        byokKey,
        byokBaseUrl,
        byokModel,
        preferredProvider,
        signal: controller.signal,
        onStageChange: (stage: PipelineStage, message: string) => {
          const humanStageText = getStageHumanCopy(stage, message);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, stage, stageMessage: humanStageText }
                : msg
            )
          );
        },
        onToken: (delta: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + delta }
                : msg
            )
          );
        },
        onCitations: (citations: Citation[]) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, citations }
                : msg
            )
          );
        },
        onDone: (doneData) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: doneData.answer || msg.content,
                    stage: "done",
                    refused: doneData.refused,
                    cached: doneData.cached,
                    model: doneData.model,
                    totalTokens: doneData.total_tokens,
                    questionId: doneData.question_id,
                  }
                : msg
            )
          );
          setIsGenerating(false);
        },
        onError: (err: Error) => {
          // Parse potential error codes
          let code = "generic";
          const errStr = err.message.toLowerCase();
          if (errStr.includes("swamped") || errStr.includes("rate limit") || errStr.includes("429")) {
            code = "free_tier_busy";
          } else if (errStr.includes("expired") || errStr.includes("404")) {
            code = "session_expired";
          }

          setStreamError({
            code,
            message: err.message,
            requestId: `req_${Math.random().toString(36).slice(2, 10)}`,
          });

          // Remove the empty assistant placeholder if failed early
          setMessages((prev) =>
            prev.filter((m) => m.id !== assistantMessageId || m.content.trim().length > 0)
          );
          setIsGenerating(false);
        },
      });
    } catch {
      setIsGenerating(false);
    }
  };

  const handleAbort = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
  };

  return (
    <div className="flex flex-col h-full bg-bg-base">
      {/* Messages Viewport */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <div className="my-auto">
              {!sessionId && onUploadSuccess && (
                <div className="max-w-xl mx-auto mb-6">
                  <Upload onUploadSuccess={onUploadSuccess} />
                </div>
              )}
              {/* Empty state per §4 copy freeze */}
              <EmptyState onSelectSampleQuestion={(q) => handleSend(q)} />
            </div>
          ) : (
            <>
              {documentName && (
                <div className="mb-6 flex items-center justify-between pb-3 border-b border-border/60 text-xs text-gray-warm">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-accent-primary" />
                    <span className="font-medium text-ink-primary truncate max-w-sm">
                      {documentName}
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-ink-ghost">
                    grounded Q&A session
                  </span>
                </div>
              )}

              {messages.map((msg) => (
                <Message
                  key={msg.id}
                  message={msg}
                  onCitationClick={onCitationClick}
                />
              ))}

              {streamError && (
                <ErrorState
                  code={streamError.code}
                  message={streamError.message}
                  requestId={streamError.requestId}
                  onRetry={() => {
                    const lastUser = [...messages].reverse().find((m) => m.role === "user");
                    if (lastUser) handleSend(lastUser.content);
                  }}
                  onOpenSettings={onOpenSettings}
                />
              )}
            </>
          )}
          <div ref={scrollEndRef} />
        </div>
      </div>

      {/* Composer Dock */}
      <div className="p-4 bg-bg-surface/80 backdrop-blur-md border-t border-border">
        <div className="max-w-3xl mx-auto">
          <Composer
            onSend={handleSend}
            onAbort={handleAbort}
            isGenerating={isGenerating}
            disabled={!sessionId}
          />
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { Citation, PipelineStage, streamQuery } from "@/lib/sse";
import { ChatMessage, Message } from "./Message";
import { Composer } from "./Composer";
import { Upload } from "./Upload";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { checkRateLimit, recordFreeQuery, RateLimitState } from "@/lib/rateLimit";
import { RateLimitBanner } from "./RateLimitBanner";

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
  isGuest?: boolean;
}

// Rotating status indicators
const SEARCHING_VARIANTS = [
  "reading the shelves…",
  "flipping pages…",
  "hunting for citations…",
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
  isGuest,
}: ChatProps) {
  const { getToken } = useAuth();
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

  // Rate Limiter: Free tier is limited to 10 queries / hour (BYOK users are exempt)
  const isByokActive = Boolean(byokKey || preferredProvider === "ollama");
  const [rateLimitState, setRateLimitState] = useState<RateLimitState>(() =>
    checkRateLimit(isByokActive)
  );

  useEffect(() => {
    setRateLimitState(checkRateLimit(isByokActive));
  }, [isByokActive]);

  // Synchronize rate limit status across multiple browser tabs
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === "allcited_free_queries") {
        setRateLimitState(checkRateLimit(isByokActive));
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [isByokActive]);

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

    // Check rate limit for free tier
    if (!isByokActive) {
      const current = checkRateLimit(false);
      if (current.isRateLimited) {
        setRateLimitState(current);
        return;
      }
    }

    setStreamError(null);
    searchVariantIdx.current = (searchVariantIdx.current + 1) % SEARCHING_VARIANTS.length;

    // Record question in free tier history
    if (!isByokActive) {
      const updated = recordFreeQuery(false);
      setRateLimitState(updated);
    }

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
      const authToken = await getToken().catch(() => null);
      await streamQuery({
        sessionId,
        query: queryText,
        authToken,
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
                    provider: doneData.provider,
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
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setStreamError({
        code: "generic",
        message: msg || "Failed to start question stream",
        requestId: `req_${Math.random().toString(36).slice(2, 10)}`,
      });
      setMessages((prev) =>
        prev.filter((m) => m.id !== assistantMessageId || m.content.trim().length > 0)
      );
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
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-[640px] w-full mx-auto">
          {messages.length === 0 ? (
            <div className="my-auto">
              {!sessionId && onUploadSuccess && (
                <div className="max-w-[640px] w-full mx-auto mb-6">
                  <Upload onUploadSuccess={onUploadSuccess} />
                </div>
              )}
              <EmptyState
                onSelectSampleQuestion={(q) => handleSend(q)}
                isGuest={isGuest}
              />
            </div>
          ) : (
            <div className="space-y-6">
              {documentName && (
                <div className="flex items-center justify-between pb-3 border-b border-border/60 text-xs text-gray-warm">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-2 h-2 rounded-full bg-accent-primary flex-shrink-0" />
                    <span className="font-medium text-ink-primary truncate max-w-sm">
                      {documentName}
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-ink-ghost flex-shrink-0">
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
            </div>
          )}
          <div ref={scrollEndRef} />
        </div>
      </div>

      {/* Composer Dock */}
      <div className="p-4 bg-bg-surface/90 backdrop-blur-md border-t border-border">
        <div className="max-w-[640px] w-full mx-auto">
          {rateLimitState.isRateLimited && rateLimitState.resetAt && (
            <RateLimitBanner
              resetAt={rateLimitState.resetAt}
              onReset={() => setRateLimitState(checkRateLimit(isByokActive))}
              onOpenSettings={onOpenSettings}
            />
          )}
          <Composer
            onSend={handleSend}
            onAbort={handleAbort}
            isGenerating={isGenerating}
            disabled={!sessionId || rateLimitState.isRateLimited}
            placeholder={
              rateLimitState.isRateLimited
                ? "Free tier limit reached (10 questions / hour). Resets soon or use BYOK."
                : undefined
            }
          />
        </div>
      </div>
    </div>
  );
}

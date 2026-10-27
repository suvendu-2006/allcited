"use client";

import React, { useState, useRef, useEffect } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { Citation, PipelineStage, streamQuery } from "@/lib/sse";
import { ChatMessage, Message } from "./Message";
import { Composer } from "./Composer";
import { Upload } from "./Upload";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { checkRateLimit, recordFreeQuery, RateLimitState } from "@/lib/rateLimit";
import { RateLimitBanner } from "./RateLimitBanner";
import { motion, useReducedMotion } from "framer-motion";

interface ChatProps {
  sessionId?: string | null;
  documentName?: string | null;
  byokKey?: string | null;
  byokBaseUrl?: string | null;
  byokModel?: string | null;
  preferredProvider?: string | null;
  isPro?: boolean;
  onCitationClick?: (citation: Citation, allCitations?: Citation[]) => void;
  onUploadSuccess?: (data: {
    sessionId: string;
    filename: string;
    chunkCount: number;
    pageCount: number;
  }) => void;
  onOpenSettings?: () => void;
  isGuest?: boolean;
  isShelfMode?: boolean;
  initialShelfQuery?: string | null;
  onClearInitialShelfQuery?: () => void;
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
  isPro,
  onCitationClick,
  onUploadSuccess,
  onOpenSettings,
  isGuest,
  isShelfMode = false,
  initialShelfQuery,
  onClearInitialShelfQuery,
}: ChatProps) {
  const { getToken, isSignedIn } = useAuth();
  const { user } = useUser();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPrecisionMode, setIsPrecisionMode] = useState(false);
  const [isProUser, setIsProUser] = useState<boolean>(Boolean(isPro));
  const [streamError, setStreamError] = useState<{
    code?: string;
    message?: string;
    requestId?: string;
  } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const scrollEndRef = useRef<HTMLDivElement>(null);
  const messagesViewportRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);
  const searchVariantIdx = useRef(0);
  const shouldReduceMotion = useReducedMotion();

  // Pro status detection (via prop, Clerk metadata, or Stripe subscription endpoint)
  useEffect(() => {
    if (isPro) {
      setIsProUser(true);
      return;
    }
    const metaPlan = (user?.publicMetadata?.plan as string) || (user?.unsafeMetadata?.plan as string);
    if (metaPlan === "pro") {
      setIsProUser(true);
      return;
    }
    if (isSignedIn) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      getToken()
        .then((token) => {
          if (!token) return;
          return fetch(`${apiUrl.replace(/\/$/, "")}/v1/stripe/subscription`, {
            headers: { Authorization: `Bearer ${token}` },
          });
        })
        .then((res) => (res && res.ok ? res.json() : null))
        .then((data) => {
          if (data?.plan === "pro") {
            setIsProUser(true);
          }
        })
        .catch(() => {});
    }
  }, [isPro, user, isSignedIn, getToken]);

  // Rate Limiter: Free tier is limited to 10 queries / hour (BYOK and paying Pro users are exempt)
  const isRateLimitExempt = Boolean(byokKey || preferredProvider === "ollama" || isProUser);
  const [rateLimitState, setRateLimitState] = useState<RateLimitState>(() =>
    checkRateLimit(isRateLimitExempt)
  );

  useEffect(() => {
    setRateLimitState(checkRateLimit(isRateLimitExempt));
  }, [isRateLimitExempt]);

  // Synchronize rate limit status across multiple browser tabs
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === "allcited_free_queries") {
        setRateLimitState(checkRateLimit(isRateLimitExempt));
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [isRateLimitExempt]);

  // Handle initial shelf query passed from /?shelf_query=...
  useEffect(() => {
    if (initialShelfQuery && initialShelfQuery.trim()) {
      handleSend(initialShelfQuery.trim());
      onClearInitialShelfQuery?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialShelfQuery]);

  const handleScroll = () => {
    const el = messagesViewportRef.current;
    if (!el) return;
    const threshold = 120;
    const isBottom = el.scrollHeight - el.scrollTop - el.clientHeight <= threshold;
    isNearBottomRef.current = isBottom;
  };

  // Auto-scroll to bottom on incoming message updates: smooth only when user is already at bottom
  const scrollToBottom = () => {
    if (isNearBottomRef.current) {
      scrollEndRef.current?.scrollIntoView({ behavior: shouldReduceMotion ? "auto" : "smooth" });
    }
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
    if (!sessionId && !isShelfMode) {
      alert("Drop or select a document first.");
      return;
    }

    // Check rate limit for free tier (exempt for BYOK, local Ollama, and Pro subscribers)
    if (!isRateLimitExempt) {
      const current = checkRateLimit(false);
      if (current.isRateLimited) {
        setRateLimitState(current);
        return;
      }
    }

    setStreamError(null);
    searchVariantIdx.current = (searchVariantIdx.current + 1) % SEARCHING_VARIANTS.length;

    // Record question in free tier history if not exempt
    if (!isRateLimitExempt) {
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
    const initialStageText = isShelfMode
      ? "searching across your shelf…"
      : SEARCHING_VARIANTS[searchVariantIdx.current % SEARCHING_VARIANTS.length];
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

    // 3. Handle Shelf Query mode (POST /v1/library/query across all saved docs)
    if (isShelfMode) {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        let authToken: string | null = null;
        try {
          authToken = await getToken();
        } catch {}
        if (!authToken && typeof window !== "undefined") {
          authToken = localStorage.getItem("allcited_auth_token");
        }

        if (!authToken) {
          setStreamError({
            code: "unauthorized",
            message: "Please sign in to search across your shelf documents.",
          });
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, stage: "error", stageMessage: "Sign-in required" }
                : msg
            )
          );
          setIsGenerating(false);
          return;
        }

        const res = await fetch(`${apiUrl.replace(/\/$/, "")}/v1/library/query`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({
            query: queryText,
            top_k: 5,
            provider: preferredProvider || undefined,
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => null);
          const errMsg =
            errData?.detail?.error?.message ||
            errData?.error?.message ||
            `Shelf query failed (${res.status})`;
          throw new Error(errMsg);
        }

        const data = await res.json();
        const answer = data.answer || "No relevant documents found in your library.";
        const citations: Citation[] = data.citations || [];

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: answer,
                  citations,
                  stage: "done",
                  stageMessage: undefined,
                }
              : msg
          )
        );
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") return;
        const msg = err instanceof Error ? err.message : String(err);
        setStreamError({
          code: "shelf_query_error",
          message: msg || "Failed to search shelf.",
          requestId: `req_${Math.random().toString(36).slice(2, 10)}`,
        });
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, stage: "error", stageMessage: "Search failed" }
              : msg
          )
        );
      } finally {
        setIsGenerating(false);
      }
      return;
    }

    if (!sessionId) {
      alert("Drop or select a document first.");
      setIsGenerating(false);
      return;
    }

    try {
      const authToken = await getToken().catch(() => null);
      await streamQuery({
        sessionId,
        query: queryText,
        mode: isPrecisionMode ? "precision" : undefined,
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
          } else if (
            errStr.includes("pro feature") ||
            errStr.includes("precision mode") ||
            errStr.includes("plan_limit") ||
            errStr.includes("402")
          ) {
            code = "plan_limit_reached";
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
      let code = "generic";
      const errStr = msg.toLowerCase();
      if (errStr.includes("swamped") || errStr.includes("rate limit") || errStr.includes("429")) {
        code = "free_tier_busy";
      } else if (errStr.includes("expired") || errStr.includes("404")) {
        code = "session_expired";
      } else if (
        errStr.includes("pro feature") ||
        errStr.includes("precision mode") ||
        errStr.includes("plan_limit") ||
        errStr.includes("402")
      ) {
        code = "plan_limit_reached";
      }
      setStreamError({
        code,
        message: msg || "Failed to start question stream",
        requestId: `req_${Math.random().toString(36).slice(2, 10)}`,
      });
      setMessages((prev) =>
        prev.filter((m) => m.id !== assistantMessageId || m.content.trim().length > 0)
      );
      setIsGenerating(false);
    }
  };

  const handleTogglePrecision = (enabled: boolean) => {
    if (enabled && !isProUser && !byokKey) {
      setStreamError({
        code: "plan_limit_reached",
        message: "Precision mode is a Pro feature providing deep iterative agentic retrieval and cross-encoder re-ranking. Upgrade to Pro to enable, or bring your own API key.",
      });
      return;
    }
    setStreamError(null);
    setIsPrecisionMode(enabled);
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
      <div
        ref={messagesViewportRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        <div className="max-w-[640px] w-full mx-auto">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: shouldReduceMotion ? 0.08 : 0.24 }}
              className="my-auto"
            >
              {!sessionId && !isShelfMode && onUploadSuccess && (
                <div className="max-w-[640px] w-full mx-auto mb-6">
                  <Upload onUploadSuccess={onUploadSuccess} />
                </div>
              )}
              <EmptyState
                onSelectSampleQuestion={(q) => handleSend(q)}
                isGuest={isGuest}
              />
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: shouldReduceMotion ? 0.08 : 0.2 }}
              className="space-y-6"
            >
              {documentName && (
                <div className="flex items-center justify-between pb-3 border-b border-border/60 text-xs text-gray-warm">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-2 h-2 rounded-full bg-accent-primary flex-shrink-0" />
                    <span className="font-medium text-ink-primary truncate max-w-sm">
                      {documentName}
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-ink-ghost flex-shrink-0">
                    {isShelfMode ? "multi-document synthesis" : "grounded Q&A session"}
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
                  onOpenUpgrade={() => {
                    window.location.href = "/pricing";
                  }}
                />
              )}
            </motion.div>
          )}
          <div ref={scrollEndRef} />
        </div>
      </div>

      {/* Composer Dock */}
      <div className="p-4 bg-bg-surface/90 backdrop-blur-md border-t border-border">
        <div className="max-w-[640px] w-full mx-auto">
          {!isRateLimitExempt && rateLimitState.isRateLimited && rateLimitState.resetAt && (
            <RateLimitBanner
              resetAt={rateLimitState.resetAt}
              onReset={() => setRateLimitState(checkRateLimit(isRateLimitExempt))}
              onOpenSettings={onOpenSettings}
            />
          )}
          <Composer
            onSend={handleSend}
            onAbort={handleAbort}
            isGenerating={isGenerating}
            isPrecisionMode={isPrecisionMode}
            onTogglePrecision={handleTogglePrecision}
            isPro={isProUser || Boolean(byokKey)}
            disabled={(!sessionId && !isShelfMode) || (!isRateLimitExempt && rateLimitState.isRateLimited)}
            placeholder={
              !isRateLimitExempt && rateLimitState.isRateLimited
                ? "Free tier limit reached (10 questions / hour). Resets soon or use BYOK."
                : isShelfMode
                ? "Ask across everything on your shelf…"
                : undefined
            }
          />
        </div>
      </div>
    </div>
  );
}

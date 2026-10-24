"use client";

import React, { useState, useRef, useEffect } from "react";
import { Citation, PipelineStage, streamQuery } from "@/lib/sse";
import { ChatMessage, Message } from "./Message";
import { Composer } from "./Composer";
import { Upload } from "./Upload";
import { BookOpen, Sparkles, ShieldCheck } from "lucide-react";

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
}

export function Chat({
  sessionId,
  documentName,
  byokKey,
  byokBaseUrl,
  byokModel,
  preferredProvider,
  onCitationClick,
  onUploadSuccess,
}: ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const scrollEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on incoming message updates
  const scrollToBottom = () => {
    scrollEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (queryText: string) => {
    if (!sessionId) {
      alert("Please upload or select an active document session first.");
      return;
    }

    const userMessageId = `user_${Date.now()}`;
    const assistantMessageId = `asst_${Date.now()}`;

    // 1. Add user message
    const userMsg: ChatMessage = {
      id: userMessageId,
      role: "user",
      content: queryText,
    };

    // 2. Add assistant placeholder
    const assistantMsg: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      stage: "routing",
      stageMessage: "Analyzing query...",
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
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, stage, stageMessage: message }
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
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: `Error generating response: ${err.message}`,
                    stage: "error",
                  }
                : msg
            )
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
    <div className="flex flex-col h-full bg-slate-50/50 dark:bg-slate-950">
      {/* Messages Viewport */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <div className="text-center py-16 px-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-950/70 text-blue-600 dark:text-blue-400 mx-auto flex items-center justify-center mb-4 shadow-sm">
                <BookOpen className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-1">
                {documentName ? `Ask about "${documentName}"` : "Welcome to Allcited"}
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-6">
                {documentName
                  ? "Every answer is strictly grounded in your uploaded document with verifiable source citations."
                  : "Upload a document to ask questions with receipt citations, cross-reference expansion, and zero hallucination."}
              </p>

              {!sessionId && onUploadSuccess && (
                <div className="max-w-md mx-auto mb-8">
                  <Upload onUploadSuccess={onUploadSuccess} />
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-left max-w-2xl mx-auto">
                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
                  <div className="flex items-center gap-2 text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    Strict Grounding
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    Answers cite verified sources [S#]. External speculation is refused.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
                  <div className="flex items-center gap-2 text-xs font-semibold text-purple-600 dark:text-purple-400 mb-1">
                    <BookOpen className="w-3.5 h-3.5" />
                    Two-Hop Expansion
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    Cross-referenced rules, clauses, and standards are dynamically resolved.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
                  <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 mb-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Privacy First
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    No code execution. BYOK keys stay in browser localStorage.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <Message
                key={msg.id}
                message={msg}
                onCitationClick={onCitationClick}
              />
            ))
          )}
          <div ref={scrollEndRef} />
        </div>
      </div>

      {/* Composer Dock */}
      <div className="p-4 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-t border-slate-200 dark:border-slate-800">
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

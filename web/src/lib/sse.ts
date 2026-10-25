export interface Citation {
  label: string;
  chunk_id: string;
  page?: number | null;
  page_number?: number | null;
  section_path?: string[];
  text_preview: string;
  is_two_hop?: boolean;
  added_reason?: string | null;
  is_ocr?: boolean;
  doc_name?: string | null;
  document_id?: string | null;
  score?: number | null;
}

export type PipelineStage =
  | "idle"
  | "routing"
  | "rewriting"
  | "retrieving"
  | "reranking"
  | "expanding"
  | "composing"
  | "done"
  | "error";

export interface StreamQueryOptions {
  apiUrl?: string;
  sessionId: string;
  query: string;
  byokKey?: string | null;
  byokBaseUrl?: string | null;
  byokModel?: string | null;
  preferredProvider?: string | null;
  signal?: AbortSignal;
  onStageChange?: (stage: PipelineStage, message: string) => void;
  onToken?: (delta: string) => void;
  onCitations?: (citations: Citation[]) => void;
  onDone?: (data: {
    answer: string;
    question_id: string;
    model?: string;
    refused?: boolean;
    cached?: boolean;
    total_tokens?: number;
  }) => void;
  onError?: (error: Error) => void;
}

const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function streamQuery(options: StreamQueryOptions): Promise<void> {
  const {
    apiUrl = DEFAULT_API_URL,
    sessionId,
    query,
    byokKey,
    byokBaseUrl,
    byokModel,
    preferredProvider,
    signal,
    onStageChange,
    onToken,
    onCitations,
    onDone,
    onError,
  } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  // BYOK headers are passed directly to API per hard constraints
  if (byokKey) {
    headers["X-BYOK-Key"] = byokKey;
  }
  if (byokBaseUrl) {
    headers["X-BYOK-Base-URL"] = byokBaseUrl;
  }
  if (byokModel) {
    headers["X-BYOK-Model"] = byokModel;
  }

  if (preferredProvider) {
    headers["X-Provider"] = preferredProvider;
  }

  const payload: Record<string, string | null> = {
    session_id: sessionId,
    query: query.trim(),
    provider: preferredProvider || null,
    preferred_provider: preferredProvider || null,
  };

  try {
    onStageChange?.("routing", "Analyzing question intent...");

    const response = await fetch(`${apiUrl.replace(/\/$/, "")}/v1/query`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorJson;
      try {
        errorJson = JSON.parse(errorText);
      } catch {
        errorJson = null;
      }
      const msg = errorJson?.detail?.error?.message || errorJson?.detail || errorText || `HTTP ${response.status}`;
      throw new Error(msg);
    }

    if (!response.body) {
      throw new Error("No response stream returned from API");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const eventBlock of events) {
        if (!eventBlock.trim()) continue;

        let eventType = "message";
        let dataStr = "";

        const lines = eventBlock.split("\n");
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            dataStr = line.slice(6).trim();
          }
        }

        if (!dataStr) continue;

        let parsedData: Record<string, unknown> = {};
        try {
          parsedData = JSON.parse(dataStr) as Record<string, unknown>;
        } catch {
          parsedData = { raw: dataStr };
        }

        switch (eventType) {
          case "route": {
            const routeName = typeof parsedData.route === "string" ? parsedData.route.toUpperCase() : "LOOKUP";
            onStageChange?.("routing", `Routed as ${routeName}`);
            break;
          }
          case "rewrite": {
            const subs = Array.isArray(parsedData.sub_queries) ? parsedData.sub_queries : [];
            if (subs.length > 1) {
              onStageChange?.("rewriting", `Refining query into ${subs.length} search angles...`);
            }
            break;
          }
          case "retrieve": {
            const count = typeof parsedData.candidate_count === "number" ? parsedData.candidate_count : 0;
            onStageChange?.("retrieving", `Searching index (found ${count} candidates)...`);
            break;
          }
          case "rerank": {
            const topScore = typeof parsedData.top_score === "number" ? parsedData.top_score : 0;
            onStageChange?.("reranking", `Neural re-ranking candidates (top relevance: ${topScore})...`);
            break;
          }
          case "expand": {
            const twoHopCount = typeof parsedData.two_hop_count === "number" ? parsedData.two_hop_count : 0;
            if (twoHopCount > 0) {
              onStageChange?.("expanding", `Resolved ${twoHopCount} cross-reference definitions...`);
            }
            break;
          }
          case "token": {
            onStageChange?.("composing", "Composing verified answer...");
            if (typeof parsedData.delta === "string") {
              onToken?.(parsedData.delta);
            }
            break;
          }
          case "citations": {
            if (Array.isArray(parsedData.citations)) {
              onCitations?.(parsedData.citations as Citation[]);
            }
            break;
          }
          case "done": {
            onStageChange?.("done", "Answer complete");
            onDone?.({
              answer: typeof parsedData.answer === "string" ? parsedData.answer : "",
              question_id: typeof parsedData.question_id === "string" ? parsedData.question_id : "",
              model: typeof parsedData.model === "string" ? parsedData.model : undefined,
              refused: typeof parsedData.refused === "boolean" ? parsedData.refused : undefined,
              cached: typeof parsedData.cached === "boolean" ? parsedData.cached : undefined,
              total_tokens: typeof parsedData.total_tokens === "number" ? parsedData.total_tokens : undefined,
            });
            break;
          }
          case "error": {
            const errorMsg =
              typeof parsedData.detail === "string"
                ? parsedData.detail
                : typeof parsedData.error === "string"
                ? parsedData.error
                : "Stream error";
            const err = new Error(errorMsg);
            onStageChange?.("error", err.message);
            onError?.(err);
            return;
          }
        }
      }
    }
  } catch (error: unknown) {
    if (signal?.aborted) {
      onStageChange?.("idle", "Cancelled");
      return;
    }
    const err = error instanceof Error ? error : new Error(String(error));
    onStageChange?.("error", err.message);
    onError?.(err);
  }
}

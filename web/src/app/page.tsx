"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { useAuth, useClerk } from "@clerk/nextjs";
import { Chat } from "@/components/Chat";
import { SourcePanel } from "@/components/SourcePanel";
import { ModelSettings, ProviderConfig } from "@/components/ModelSettings";
import { Citation } from "@/lib/sse";
import { Navbar } from "@/components/Navbar";
import { AuthScreen } from "@/components/AuthScreen";
import { DeepSeaAurora } from "@/components/DeepSeaAurora";
import { MagneticButton } from "@/components/MagneticButton";
import { LiveMiniDemo } from "@/components/LiveMiniDemo";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { motion } from "framer-motion";
import { Star, Settings } from "lucide-react";

const PROOF_TICKER_ITEMS = [
  { text: "Every claim, cited", isStamp: false },
  { text: "[S1] 2.1 Leave Policy · p.23", isStamp: true },
  { text: "87% passage accuracy — measured, public", isStamp: false },
  { text: "[S2] Rule 63.7.4 · p.45", isStamp: true },
  { text: "46-question exam on every release", isStamp: false },
  { text: "7-stage pipeline, fully inspectable", isStamp: false },
  { text: "Refuses when the answer isn't in your document", isStamp: false },
  { text: "BM25 + FAISS + cross-encoder re-ranking", isStamp: false },
  { text: "Nothing saved without your say-so", isStamp: false },
  { text: "We read PDF · Word · PowerPoint · Excel · Markdown · web links", isStamp: false },
];

export default function Home() {
  const { isSignedIn, getToken } = useAuth();
  const clerk = useClerk();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [documentName, setDocumentName] = useState<string | null>(null);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [selectedCitationLabel, setSelectedCitationLabel] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [inWorkspace, setInWorkspace] = useState<boolean>(false);
  const [isGuest, setIsGuest] = useState<boolean>(false);
  const [isSaved, setIsSaved] = useState<boolean>(false);
  const [saveToast, setSaveToast] = useState<string | null>(null);

  // Provider configuration state (loaded from localStorage browser-only)
  const [providerConfig, setProviderConfig] = useState<ProviderConfig>({
    mode: "groq",
    byokKey: "",
    byokBaseUrl: "",
    byokModel: "gpt-4o-mini",
    ollamaBaseUrl: "http://localhost:11434",
    ollamaModel: "llama3.2",
  });
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const workspaceRef = useRef<HTMLDivElement>(null);

  // Check health and load saved localStorage configs on mount
  useEffect(() => {
    async function checkHealthAndInit() {
      try {
        const res = await fetch(`${apiUrl}/v1/health`);
        if (res.ok) {
          setApiConnected(true);
        }
      } catch {
        setApiConnected(false);
      }
    }
    checkHealthAndInit();

    if (typeof window !== "undefined") {
      const savedMode =
        (localStorage.getItem("allcited_provider_mode") as "groq" | "byok" | "ollama") ||
        "groq";
      const savedKey = localStorage.getItem("allcited_byok_key") || "";
      const savedBaseUrl = localStorage.getItem("allcited_byok_base_url") || "";
      const savedModel = localStorage.getItem("allcited_byok_model") || "gpt-4o-mini";
      const savedOllamaUrl =
        localStorage.getItem("allcited_ollama_base_url") || "http://localhost:11434";
      const savedOllamaModel =
        localStorage.getItem("allcited_ollama_model") || "llama3.2";

      setProviderConfig({
        mode: savedMode,
        byokKey: savedKey,
        byokBaseUrl: savedBaseUrl,
        byokModel: savedModel,
        ollamaBaseUrl: savedOllamaUrl,
        ollamaModel: savedOllamaModel,
      });

      const savedGuest = sessionStorage.getItem("allcited_is_guest") === "true";
      if (savedGuest) {
        setIsGuest(true);
      }
    }
  }, [apiUrl]);

  // Sync workspace state from URL query parameters (supports back/forward & client navigation)
  useEffect(() => {
    const syncFromUrl = () => {
      if (typeof window === "undefined") return;
      const params = new URLSearchParams(window.location.search);
      const urlSessionId = params.get("session_id");
      const urlFilename = params.get("filename");
      const urlWorkspace = params.get("workspace");

      if (urlSessionId) {
        setSessionId(urlSessionId);
        if (urlFilename) setDocumentName(decodeURIComponent(urlFilename));
        setInWorkspace(true);
      } else if (urlWorkspace === "true") {
        setInWorkspace(true);
      }
    };

    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const handleSaveToShelf = useCallback(async () => {
    if (!sessionId) return;

    if (!isSignedIn) {
      if (typeof window !== "undefined") {
        sessionStorage.setItem("allcited_pending_save_session", sessionId);
        sessionStorage.setItem("allcited_pending_save_doc", documentName || "");
      }
      clerk.openSignIn();
      return;
    }

    try {
      const token = await getToken();
      const res = await fetch(`${apiUrl}/v1/library/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      if (res.ok) {
        setIsSaved(true);
        setSaveToast("Document saved to your shelf!");
        setTimeout(() => setSaveToast(null), 3500);
      } else {
        const err = await res.json();
        setSaveToast(err?.detail?.error?.message || "Failed to save to shelf");
        setTimeout(() => setSaveToast(null), 3500);
      }
    } catch {
      setSaveToast("Could not connect to shelf service");
      setTimeout(() => setSaveToast(null), 3500);
    }
  }, [sessionId, isSignedIn, documentName, clerk, getToken, apiUrl]);

  // Carry across active document when upgrading from guest to signed-in
  useEffect(() => {
    if (isSignedIn && typeof window !== "undefined" && sessionId) {
      const pendingSession = sessionStorage.getItem("allcited_pending_save_session");
      if (pendingSession && pendingSession === sessionId) {
        sessionStorage.removeItem("allcited_pending_save_session");
        sessionStorage.removeItem("allcited_pending_save_doc");
        handleSaveToShelf();
      }
    }
  }, [isSignedIn, sessionId, handleSaveToShelf]);

  const handleUploadSuccess = (data: {
    sessionId: string;
    filename: string;
    chunkCount: number;
    pageCount: number;
  }) => {
    setSessionId(data.sessionId);
    setDocumentName(data.filename);
    setIsSaved(false);
    setInWorkspace(true);
  };

  // Headline wordmark letters for staggered animation
  const headlineWords = ["Answers,", "with", "receipts."];

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-ink-primary font-sans">
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-y-auto">
        {/* Navigation Bar */}
        <Navbar
          apiConnected={apiConnected}
          isInApp={inWorkspace}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onOpenWorkspace={() => setInWorkspace(true)}
          onGoHome={() => {
            setInWorkspace(false);
            if (typeof window !== "undefined") {
              const url = new URL(window.location.href);
              url.searchParams.delete("workspace");
              url.searchParams.delete("session_id");
              url.searchParams.delete("filename");
              window.history.pushState({}, "", url.pathname);
            }
          }}
        />

        {/* Dynamic View: Workspace Mode vs Full Award Landing Page */}
        {inWorkspace ? (
          !isSignedIn && !isGuest ? (
            <AuthScreen
              onContinueAsGuest={() => {
                setIsGuest(true);
                if (typeof window !== "undefined") {
                  sessionStorage.setItem("allcited_is_guest", "true");
                }
              }}
              onBackToHome={() => setInWorkspace(false)}
            />
          ) : (
            <div className="flex-1 min-h-0 relative flex flex-col" ref={workspaceRef}>
              <div className="px-4 h-10 border-b border-border bg-bg-surface flex items-center justify-between text-xs flex-shrink-0">
                <div className="flex items-center gap-2 min-w-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setInWorkspace(false)}
                    className="text-xs h-7 gap-1"
                  >
                    ← Back
                  </Button>
                  {documentName && (
                    <span className="font-mono text-[11px] text-gray-warm border-l border-border pl-2 truncate max-w-xs sm:max-w-md">
                      {documentName}
                    </span>
                  )}
                  {!isSignedIn && isGuest && (
                    <span className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-bg-sunken border border-border text-ink-ghost">
                      Guest mode
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {sessionId && (
                    <button
                      type="button"
                      onClick={handleSaveToShelf}
                      className={`font-mono text-[11px] flex items-center gap-1 px-2.5 py-1 rounded border transition-all duration-150 ease-out cursor-pointer hover:-translate-y-[0.5px] hover:shadow-2xs active:translate-y-0 active:scale-95 ${
                        isSaved
                          ? "border-accent-primary/40 bg-accent-primary/10 text-accent-primary font-semibold"
                          : "border-border/80 hover:border-accent-primary hover:bg-bg-sunken text-ink-primary"
                      }`}
                    >
                      <span>{isSaved ? "Saved to shelf ·" : "Save to shelf"}</span>
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => setIsSettingsOpen(true)}
                    className="group/engine font-mono text-[11px] text-gray-warm hover:text-ink-primary flex items-center gap-1.5 px-2 py-1 rounded border border-border/60 hover:border-ink-primary/30 hover:bg-bg-sunken hover:-translate-y-[0.5px] active:translate-y-0 active:scale-95 transition-all duration-150 ease-out cursor-pointer"
                  >
                    <span>Engine: {providerConfig.mode}</span>
                    <Settings className="w-3.5 h-3.5 text-accent-primary transition-transform duration-200 ease-out group-hover/engine:rotate-45" />
                  </button>
                </div>
              </div>

              {saveToast && (
                <div className="absolute top-12 right-4 z-50 bg-bg-surface border border-accent-primary/50 text-ink-primary text-xs font-mono px-3 py-1.5 rounded shadow-md animate-fade-in">
                  {saveToast}
                </div>
              )}

              <Chat
                sessionId={sessionId}
                documentName={documentName}
                isGuest={!isSignedIn}
                byokKey={providerConfig.mode === "byok" ? providerConfig.byokKey : null}
                byokBaseUrl={
                  providerConfig.mode === "byok"
                    ? providerConfig.byokBaseUrl
                    : providerConfig.mode === "ollama"
                    ? providerConfig.ollamaBaseUrl
                    : null
                }
                byokModel={
                  providerConfig.mode === "byok"
                    ? providerConfig.byokModel
                    : providerConfig.mode === "ollama"
                    ? providerConfig.ollamaModel
                    : null
                }
                preferredProvider={
                  providerConfig.mode === "ollama"
                    ? "ollama"
                    : providerConfig.mode === "byok"
                    ? "byok"
                    : "groq"
                }
                onCitationClick={(cit, allCits) => {
                  setActiveCitations(allCits && allCits.length > 0 ? allCits : [cit]);
                  setSelectedCitationLabel(cit.label);
                  setIsDrawerOpen(true);
                }}
                onUploadSuccess={handleUploadSuccess}
                onOpenSettings={() => setIsSettingsOpen(true)}
              />
            </div>
          )
        ) : (
          <div className="flex-1 overflow-y-auto">
            {/* Hero Section: Fills 100% of Viewport under Navbar */}
            <section className="relative min-h-[calc(100vh-4rem)] flex flex-col items-center justify-between text-center px-4 sm:px-6 pt-16 sm:pt-20 pb-8 overflow-hidden">
              {/* Layer 1-4 Aurora Background with Visible Dot-Grid Pattern */}
              <DeepSeaAurora />

              <div className="relative z-10 max-w-4xl mx-auto space-y-6 my-auto">
                <h1 className="font-display text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-ink-primary drop-shadow-xs">
                  {headlineWords.map((word, idx) => (
                    <motion.span
                      key={word}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{
                        duration: 0.42,
                        delay: idx * 0.04,
                        ease: [0.22, 1, 0.36, 1],
                      }}
                      className="inline-block mr-3"
                    >
                      {word}
                    </motion.span>
                  ))}
                </h1>

                <motion.p
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.42, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}
                  className="text-base sm:text-lg text-gray-warm max-w-xl mx-auto leading-relaxed font-sans"
                >
                  Upload a document. Ask any question. Every answer shows where it came from.
                </motion.p>

                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.42, delay: 0.24, ease: [0.22, 1, 0.36, 1] }}
                  className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2"
                >
                  <MagneticButton>
                    <Button
                      variant="primary"
                      size="lg"
                      onClick={() => setInWorkspace(true)}
                      className="w-full sm:w-auto text-sm shadow-md"
                    >
                      Try it free
                    </Button>
                  </MagneticButton>

                  <Link href="/how-it-works">
                    <Button variant="ghost" size="lg" className="w-full sm:w-auto text-sm border border-border">
                      See how it works
                    </Button>
                  </Link>

                  {/* GitHub Star Button with Constant Stable Rotating Star Animation */}
                  <MagneticButton>
                    <a
                      href="https://github.com/suvendu-2006/allcited"
                      target="_blank"
                      rel="noopener noreferrer"
                      data-tracking-id="home_hero_github_star"
                      className="group relative flex h-11 w-full sm:w-auto items-center justify-center gap-2.5 overflow-hidden whitespace-nowrap rounded-interactive border border-border bg-bg-surface px-5 font-mono text-xs font-semibold text-ink-primary shadow-xs transition-all duration-200 hover:border-ink-primary hover:shadow-sm hover:-translate-y-0.5 active:translate-y-0"
                    >
                      <svg
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="shrink-0 transition-transform duration-300 group-hover:scale-110"
                      >
                        <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
                        <path d="M9 18c-4.51 2-5-2-7-2" />
                      </svg>
                      <span>Star us on GitHub</span>
                      <div className="inline-flex shrink-0 items-center justify-center text-amber-500 transition-transform duration-300 group-hover:scale-110">
                        <Star className="h-4 w-4 fill-amber-500 drop-shadow-sm group-hover:animate-[spin_1.2s_linear_infinite] motion-reduce:group-hover:animate-none" />
                      </div>
                    </a>
                  </MagneticButton>
                </motion.div>

                <p className="font-sans text-xs text-ink-ghost tracking-wide pt-2">
                  Sign in or continue as guest · Nothing is saved unless you keep it · We publish our test scores
                </p>
              </div>
            </section>

            <motion.div
              id="stats-band"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-20px" }}
              transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
              className="border-y border-border bg-bg-surface py-2.5 overflow-hidden"
            >
              <div className="whitespace-nowrap font-mono text-xs text-gray-warm flex items-center justify-center gap-2">
                <span>React · Next.js · TypeScript · FastAPI · RAG pipeline: BM25 + FAISS + cross-encoder re-ranking · Llama on Groq</span>
              </div>
            </motion.div>

            <section className="py-16 px-4 sm:px-6 max-w-4xl mx-auto space-y-4 text-center sm:text-left border-b border-border">
              <h2 className="text-2xl sm:text-3xl font-semibold text-ink-primary font-display">
                How is this different from ChatGPT?
              </h2>
              <div className="text-sm sm:text-base text-gray-warm space-y-3 leading-relaxed">
                <p>
                  Allcited is a <strong className="text-ink-primary font-semibold">RAG system — Retrieval-Augmented Generation</strong>. When you ask a question, a real retrieval pipeline runs first: <strong className="text-ink-primary font-semibold">BM25</strong> (keyword search) and <strong className="text-ink-primary font-semibold">FAISS</strong> (semantic vector search) find candidate passages, and a <strong className="text-ink-primary font-semibold">cross-encoder re-ranker</strong> picks the best ones. Then the LLM writes its answer using <em>only those passages</em>.
                </p>
                <p>
                  Chatbots answer from memory and sometimes invent facts. Allcited answers from retrieved text — and cites it.
                </p>
              </div>
            </section>

            <motion.section
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-30px" }}
              transition={{ duration: 0.5, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
              className="border-b border-border bg-bg-surface/50 py-12 px-4 sm:px-6"
            >
              <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-8 text-center sm:text-left">
                <div className="space-y-1">
                  <div className="font-mono text-4xl sm:text-5xl font-bold text-ink-primary">
                    87%
                  </div>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    we find the right passage for 87 of every 100 test questions
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 justify-center sm:justify-start">
                    <span className="font-mono text-4xl sm:text-5xl font-bold text-ink-primary">
                      46
                    </span>
                    <Link
                      href="/exam"
                      className="font-mono text-[10px] px-2.5 py-1 rounded bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 border border-accent-primary/30 inline-flex items-center"
                    >
                      View scorecard →
                    </Link>
                  </div>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    test questions we run on every release
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="font-mono text-4xl sm:text-5xl font-bold text-ink-primary">
                    6
                  </div>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    file types we read: PDF, Word, PowerPoint, Excel, Markdown, web pages
                  </p>
                </div>
              </div>
            </motion.section>

            <section className="py-16 px-4 sm:px-6 max-w-4xl mx-auto space-y-6">
              <div className="text-center space-y-2">
                <span className="font-mono text-xs uppercase tracking-wider text-accent-primary font-semibold">
                  TRY IT
                </span>
                <h2 className="text-2xl sm:text-3xl font-semibold text-ink-primary font-display">
                  Try it right here.
                </h2>
                <p className="font-sans text-xs text-accent-primary font-medium max-w-md mx-auto">
                  Guest mode available — continue without login.
                </p>
                <p className="text-xs sm:text-sm text-gray-warm max-w-md mx-auto">
                  This is a real answer from a sample handbook. Click any citation. See the exact lines it came from.
                </p>
              </div>

              <LiveMiniDemo />
            </section>

            <section className="py-4 border-y border-border bg-bg-surface/40 overflow-hidden relative select-none group">
              <div className="animate-proof-ticker items-center gap-6 whitespace-nowrap will-change-transform">
                {[...PROOF_TICKER_ITEMS, ...PROOF_TICKER_ITEMS].map((item, idx) => (
                  <span key={idx} className="inline-flex items-center gap-6">
                    {item.isStamp ? (
                      <span className="font-mono text-xs text-ink-primary font-semibold px-2 py-0.5 rounded bg-bg-sunken border border-border/70">
                        {item.text}
                      </span>
                    ) : (
                      <span className="text-ink-primary font-medium text-xs tracking-wide">
                        {item.text}
                      </span>
                    )}
                    <span className="text-accent-primary text-xs select-none font-bold">◆</span>
                  </span>
                ))}
              </div>
            </section>

            <Footer />
          </div>
        )}
      </div>

      <SourcePanel
        citations={activeCitations}
        documentName={documentName}
        activeLabel={selectedCitationLabel}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onSelectCitation={(label) => setSelectedCitationLabel(label)}
      />

      {/* Model & BYOK Settings Modal */}
      <ModelSettings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        config={providerConfig}
        onSave={(updated) => setProviderConfig(updated)}
        apiUrl={apiUrl}
      />
    </div>
  );
}

"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { Chat } from "@/components/Chat";
import { SourcePanel } from "@/components/SourcePanel";
import { ModelSettings, ProviderConfig } from "@/components/ModelSettings";
import { Citation } from "@/lib/sse";
import { Navbar } from "@/components/Navbar";
import { DeepSeaAurora } from "@/components/DeepSeaAurora";
import { MagneticButton } from "@/components/MagneticButton";
import { LiveMiniDemo } from "@/components/LiveMiniDemo";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { Star } from "lucide-react";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [documentName, setDocumentName] = useState<string | null>(null);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [selectedCitationLabel, setSelectedCitationLabel] = useState<string | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [inWorkspace, setInWorkspace] = useState<boolean>(false);

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

  // GitHub Star rotation physics (smooth GPU-accelerated spring motion on hover & cursor movement)
  const starRotate = useMotionValue(0);
  const starScale = useMotionValue(1);
  const smoothStarRotate = useSpring(starRotate, { damping: 24, stiffness: 180, mass: 0.5 });
  const smoothStarScale = useSpring(starScale, { damping: 20, stiffness: 220 });

  const handleStarMouseEnter = () => {
    starScale.set(1.25);
    starRotate.set(starRotate.get() + 360);
  };

  const handleStarMouseMove = (e: React.MouseEvent<HTMLAnchorElement>) => {
    const delta = (Math.abs(e.movementX) + Math.abs(e.movementY)) || 1;
    starRotate.set(starRotate.get() + delta * 4);
  };

  const handleStarMouseLeave = () => {
    starScale.set(1);
    starRotate.set(0);
  };

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

      // Check URL query parameters
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
    }
  }, [apiUrl]);

  const handleUploadSuccess = (data: {
    sessionId: string;
    filename: string;
    chunkCount: number;
    pageCount: number;
  }) => {
    setSessionId(data.sessionId);
    setDocumentName(data.filename);
    setInWorkspace(true);
  };

  // Headline wordmark letters for staggered animation per §6.4
  const headlineWords = ["Answers,", "with", "receipts."];

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-ink-primary font-sans">
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-y-auto">
        {/* Navigation Bar */}
        <Navbar
          apiConnected={apiConnected}
          isInApp={inWorkspace}
          onOpenSettings={() => setIsSettingsOpen(true)}
        />

        {/* Dynamic View: Workspace Mode vs Full Award Landing Page */}
        {inWorkspace ? (
          <div className="flex-1 min-h-0 relative flex flex-col" ref={workspaceRef}>
            {/* Top Workspace Bar */}
            <div className="px-4 py-2 border-b border-border bg-bg-surface flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setInWorkspace(false)}
                  className="text-xs h-7 gap-1"
                >
                  ← Back to Overview
                </Button>
                {documentName && (
                  <span className="font-mono text-[11px] text-gray-warm border-l border-border pl-2">
                    {documentName}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsSettingsOpen(true)}
                  className="font-mono text-[11px] text-gray-warm hover:text-ink-primary flex items-center gap-1.5 px-2 py-1 rounded border border-border/60 hover:bg-bg-sunken"
                >
                  <span>Engine: {providerConfig.mode}</span>
                  <span className="text-accent-primary">⚙</span>
                </button>
              </div>
            </div>

            <Chat
              sessionId={sessionId}
              documentName={documentName}
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
              }}
              onUploadSuccess={handleUploadSuccess}
              onOpenSettings={() => setIsSettingsOpen(true)}
            />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            {/* Hero Section: Fills 100% of Viewport under Navbar */}
            <section className="relative min-h-[calc(100vh-4rem)] flex flex-col items-center justify-between text-center px-4 sm:px-6 pt-16 sm:pt-20 pb-8 overflow-hidden">
              {/* Layer 1-4 Aurora Background with Visible Dot-Grid Pattern */}
              <DeepSeaAurora />

              <div className="relative z-10 max-w-4xl mx-auto space-y-6 my-auto">
                {/* Hero Headline with Staggered Entrance per §6.4 */}
                <h1 className="font-editorial text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-ink-primary drop-shadow-xs">
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

                {/* Subtext per text.md verbatim */}
                <motion.p
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.42, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}
                  className="text-base sm:text-lg text-gray-warm max-w-xl mx-auto leading-relaxed font-sans"
                >
                  Upload a document. Ask any question. Every answer shows where it came from.
                </motion.p>

                {/* CTAs per text.md verbatim: Try it free (primary) · See how it works (ghost) */}
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

                  {/* GitHub Star Button with Interactive Rotating Star Animation (exactly same as multi-agent) */}
                  <MagneticButton>
                    <a
                      href="https://github.com/suvendu-2006/allcited"
                      target="_blank"
                      rel="noopener noreferrer"
                      data-tracking-id="home_hero_github_star"
                      onMouseEnter={handleStarMouseEnter}
                      onMouseMove={handleStarMouseMove}
                      onMouseLeave={handleStarMouseLeave}
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
                      <motion.div
                        style={{ rotate: smoothStarRotate, scale: smoothStarScale }}
                        className="inline-flex shrink-0 items-center justify-center text-amber-500 transform-gpu will-change-transform"
                      >
                        <Star className="h-4 w-4 fill-amber-500 drop-shadow-sm" />
                      </motion.div>
                    </a>
                  </MagneticButton>
                </motion.div>

                {/* Small line (mono) per text.md verbatim */}
                <p className="font-mono text-xs text-ink-ghost tracking-wide pt-2">
                  No account needed · Nothing is saved · We publish our test scores
                </p>
              </div>

              {/* Scroll Down Cue to reveal tech strip & stats on scroll */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.5 }}
                className="relative z-10 flex flex-col items-center gap-1 text-gray-warm/70 hover:text-ink-primary transition-colors cursor-pointer pt-6 pb-2 select-none"
                onClick={() => {
                  document.getElementById("stats-band")?.scrollIntoView({ behavior: "smooth" });
                }}
              >
                <span className="font-mono text-[9px] uppercase tracking-[0.2em] font-medium">
                  Scroll to explore
                </span>
                <motion.span
                  animate={{ y: [0, 4, 0] }}
                  transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }}
                  className="text-xs font-mono"
                >
                  ↓
                </motion.span>
              </motion.div>
            </section>

            {/* Tech Strip under Hero per text.md verbatim */}
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

            {/* Section: RAG explainer per text.md verbatim */}
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

            {/* Section: Stats per text.md verbatim */}
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

            {/* Section: Live demo per text.md verbatim */}
            <section className="py-16 px-4 sm:px-6 max-w-4xl mx-auto space-y-6">
              <div className="text-center space-y-2">
                <span className="font-mono text-xs uppercase tracking-wider text-accent-primary font-semibold">
                  TRY IT
                </span>
                <h2 className="text-2xl sm:text-3xl font-semibold text-ink-primary font-display">
                  Try it right here. No signup.
                </h2>
                <p className="text-xs sm:text-sm text-gray-warm max-w-md mx-auto">
                  This is a real answer from a sample handbook. Click any citation. See the exact lines it came from.
                </p>
              </div>

              <LiveMiniDemo />
            </section>

            {/* Section: Formats (marquee) per text.md verbatim */}
            <section className="py-5 border-y border-border bg-bg-surface/30 overflow-hidden relative select-none">
              <motion.div
                className="flex items-center gap-8 whitespace-nowrap font-mono text-xs text-gray-warm tracking-wider hover:[animation-play-state:paused]"
                animate={{ x: ["0%", "-50%"] }}
                transition={{
                  repeat: Infinity,
                  repeatType: "loop",
                  duration: 36,
                  ease: "linear",
                }}
              >
                {[...Array(4)].map((_, i) => (
                  <span key={i} className="inline-flex items-center gap-6">
                    <span className="text-ink-primary font-medium">We read PDF · Word · PowerPoint · Excel · Markdown · web links</span>
                    <span className="text-accent-primary">◆</span>
                  </span>
                ))}
              </motion.div>
            </section>

            {/* Shared Footer per text.md */}
            <Footer />
          </div>
        )}
      </div>

      {/* Side Source Detail Panel */}
      {activeCitations.length > 0 && (
        <SourcePanel
          citations={activeCitations}
          activeLabel={selectedCitationLabel}
          onClose={() => {
            setActiveCitations([]);
            setSelectedCitationLabel(null);
          }}
          onSelectCitation={(label) => setSelectedCitationLabel(label)}
        />
      )}

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

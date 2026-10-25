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
import { motion } from "framer-motion";

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

  // Rolling counter stats per §4 (900ms count-up)
  const [statRecall, setStatRecall] = useState(0);
  const [statQuestions, setStatQuestions] = useState(0);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const workspaceRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let start = 0;
    const timer = setInterval(() => {
      start += 3;
      if (start >= 87) {
        setStatRecall(87);
        clearInterval(timer);
      } else {
        setStatRecall(start);
      }
    }, 30);

    let startQ = 0;
    const timerQ = setInterval(() => {
      startQ += 2;
      if (startQ >= 46) {
        setStatQuestions(46);
        clearInterval(timerQ);
      } else {
        setStatQuestions(startQ);
      }
    }, 38);

    return () => {
      clearInterval(timer);
      clearInterval(timerQ);
    };
  }, []);

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

  // Load sample handbook fixture for instant testing
  const loadHandbookFixture = async () => {
    try {
      const sampleText = `# Allcited Corporate Employee Handbook
1. General Employment Framework
Welcome to Allcited. This employee handbook sets out the official terms, rules, and conditions governing all personnel. Compliance with company directives is mandatory.
1.2 Code of Business Conduct
Every team member must act with absolute integrity. Conflicts of interest must be formally declared to the ethics committee under procedure EC-101.

2. Leave and Time-Off Entitlements
2.1 Annual Paid Leave
Full-time employees accrue 24 days of paid annual leave per calendar year (2.0 working days per month). A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year. Any surplus beyond 8 days will automatically lapse on March 31.
2.2 Sick and Medical Leave
Staff members are eligible for 12 days of paid sick leave annually. Absences exceeding two consecutive working days require a medical practitioner certificate submitted via Form HR-702.

3. Separation, Resignation and Exit Terms
3.1 Voluntary Resignation and Notice Period
Permanent employees who wish to terminate their employment agreement must tender formal written notice at least 60 calendar days in advance to their designated reporting officer.
3.2 Leave Settlement on Departure
All accrued but unutilized annual leave will be settled in the final paycheck as per rule 63.7.4. Employees under active notice may not take paid leave without the written authorization of the Vice President of HR.

4. Information Technology and Security
Clause 4.2 Security Credential Protocols
Multi-factor authentication (MFA) is strictly mandatory on all internal systems. Passwords must be at least 16 characters in length and refreshed every 90 days as mandated by standard ISO-27001.
Clause 5.1 Remote Work Policy
Employees authorized for remote work must maintain a private secure workspace; public unsecured Wi-Fi connections without VPN encapsulation are strictly prohibited.

5. Statutory Schedules and Specialized Rules
Rule 63.7.4 Leave Encashment on Resignation
Upon voluntary resignation or formal separation, accrued annual leave encashment is strictly capped at a monetary reimbursement equivalent to 15 gross working days at current basic wage rate.`;

      const blob = new Blob([sampleText], { type: "text/markdown" });
      const formData = new FormData();
      formData.append("file", blob, "employee_handbook.md");

      const res = await fetch(`${apiUrl}/v1/ingest`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        setDocumentName("employee_handbook.md");
        setInWorkspace(true);
      }
    } catch {
      setSessionId("sess_demo_handbook");
      setDocumentName("employee_handbook.md");
      setInWorkspace(true);
    }
  };

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

                {/* Subtext per §6.3 v2.1 stripped copy */}
                <motion.p
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.42, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}
                  className="text-base sm:text-lg text-gray-warm max-w-xl mx-auto leading-relaxed font-sans"
                >
                  Drop in any document. Ask anything. Every answer shows its source.
                </motion.p>

                {/* Magnetic CTAs per §6.4 */}
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
                      Open Allcited
                    </Button>
                  </MagneticButton>

                  <Link href="/how-it-works">
                    <Button variant="ferrari" className="py-2.5">
                      SEE HOW IT WORKS
                    </Button>
                  </Link>

                  <Button
                    variant="outline"
                    size="lg"
                    onClick={loadHandbookFixture}
                    className="w-full sm:w-auto text-xs h-11"
                  >
                    Load Sample Handbook
                  </Button>
                </motion.div>

                {/* Trust Line (mono, ghost) per §4 */}
                <p className="font-mono text-xs text-ink-ghost tracking-wide pt-2">
                  No account needed · Sessions vanish when you leave · We publish our own test scores
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

            {/* Tech Strip under Hero — revealed on scroll */}
            <motion.div
              id="stats-band"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-20px" }}
              transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
              className="border-y border-border bg-bg-surface py-2.5 overflow-hidden"
            >
              <div className="whitespace-nowrap font-mono text-xs text-gray-warm flex items-center justify-center gap-2">
                <span>React · Next.js · TypeScript · FastAPI · FAISS — open source, top to bottom.</span>
              </div>
            </motion.div>

            {/* Stats Band with Rolling Counters & Scorecard Chip — revealed on scroll */}
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
                    {statRecall}%
                  </div>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    questions where we find the exact right passage. Measured by us, against us, every release.
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 justify-center sm:justify-start">
                    <span className="font-mono text-4xl sm:text-5xl font-bold text-ink-primary">
                      {statQuestions}
                    </span>
                    <Link
                      href="/exam"
                      className="font-mono text-[10px] px-2.5 py-1 rounded bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 border border-accent-primary/30 inline-flex items-center"
                    >
                      View Scorecard →
                    </Link>
                  </div>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    questions in the exam we run on ourselves before every deploy.
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="font-mono text-4xl sm:text-5xl font-bold text-ink-primary">
                    6
                  </div>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    file formats we read. PDF, Word, PowerPoint, Excel, Markdown, any URL.
                  </p>
                </div>
              </div>
            </motion.section>

            {/* Trust Layer: Live Inline Cited-Answer Mini-Demo per §6.6 */}
            <section className="py-16 px-4 sm:px-6 max-w-4xl mx-auto space-y-6">
              <div className="text-center space-y-2">
                <span className="font-mono text-xs uppercase tracking-wider text-accent-primary">
                  Interactive Preview
                </span>
                <h2 className="text-2xl sm:text-3xl font-semibold text-ink-primary font-display">
                  Experience Grounded Receipts Live
                </h2>
                <p className="text-xs sm:text-sm text-gray-warm max-w-md mx-auto">
                  Click any citation stamp below to inspect the verbatim source receipt in real time.
                </p>
              </div>

              <LiveMiniDemo />
            </section>

            {/* Formats Marquee per §6.3 v2.1 & §6.4 */}
            <section className="py-5 border-y border-border bg-bg-surface/30 overflow-hidden relative select-none">
              <motion.div
                className="flex items-center gap-8 whitespace-nowrap font-mono text-xs text-gray-warm tracking-wider hover:[animation-play-state:paused]"
                animate={{ x: ["0%", "-50%"] }}
                transition={{
                  repeat: Infinity,
                  repeatType: "loop",
                  duration: 40,
                  ease: "linear",
                }}
              >
                {[...Array(4)].map((_, i) => (
                  <span key={i} className="inline-flex items-center gap-6">
                    <span className="text-ink-primary font-medium">PDF · DOCX · PPTX · XLSX · MD · TXT · any URL.</span>
                    <span className="text-accent-primary">◆</span>
                  </span>
                ))}
              </motion.div>
            </section>

            {/* Footer v2 (3 columns + open source pledge) per §6.3 */}
            <footer className="border-t border-border bg-bg-surface/80 py-12 px-4 sm:px-6 text-xs text-gray-warm">
              <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-8 mb-8">
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm text-ink-primary font-display">Product</h4>
                  <ul className="space-y-1.5 font-mono text-xs">
                    <li><Link href="/product" className="hover:text-ink-primary">Architecture</Link></li>
                    <li><Link href="/how-it-works" className="hover:text-ink-primary">How It Works</Link></li>
                    <li><Link href="/pricing" className="hover:text-ink-primary">Pricing (₹0 / ₹299)</Link></li>
                    <li><Link href="/library" className="hover:text-ink-primary">Shelf (Library)</Link></li>
                  </ul>
                </div>

                <div className="space-y-2">
                  <h4 className="font-semibold text-sm text-ink-primary font-display">Evidence</h4>
                  <ul className="space-y-1.5 font-mono text-xs">
                    <li><Link href="/exam" className="hover:text-ink-primary">46-Question Exam Suite</Link></li>
                    <li><Link href="/dev" className="hover:text-ink-primary">/dev Component Gallery</Link></li>
                    <li><Link href="/exam" className="hover:text-ink-primary">Release Scorecard History</Link></li>
                  </ul>
                </div>

                <div className="space-y-2">
                  <h4 className="font-semibold text-sm text-ink-primary font-display">Company</h4>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    Allcited is built in the open. Every claim has a receipt; every deploy runs the exam.
                  </p>
                  <p className="font-mono text-[11px] text-accent-primary">
                    Zero telemetry · Ephemeral RAM only
                  </p>
                </div>
              </div>

              <div className="pt-6 border-t border-border/60 text-center font-mono text-[11px] text-gray-warm">
                Built with React, in the open. 46-question exam on every release. © 2026 Allcited.
              </div>
            </footer>
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

"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { Chat } from "@/components/Chat";
import { SourcePanel } from "@/components/SourcePanel";
import { ModelSettings, ProviderConfig } from "@/components/ModelSettings";
import { Citation } from "@/lib/sse";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Settings,
  Cloud,
  Key,
  Server,
} from "lucide-react";

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

  // Rolling counter stats per §4
  const [statRecall, setStatRecall] = useState(0);
  const [statQuestions, setStatQuestions] = useState(0);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const workspaceRef = useRef<HTMLDivElement>(null);

  // Animate stats band on mount per §4.1 (900ms count-up)
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

    // Browser only storage check
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
      if (urlSessionId) {
        setSessionId(urlSessionId);
        if (urlFilename) setDocumentName(decodeURIComponent(urlFilename));
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
      // Mock session fallback if backend is unreachable
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

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-ink-primary font-sans">
      {/* Main Workspace / Content Area */}
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-y-auto">
        {/* Sticky Glass Header per §7 */}
        <header className="sticky top-0 z-40 w-full border-b border-border bg-bg-surface/85 backdrop-blur-md px-4 sm:px-6 h-14 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setInWorkspace(false)}
              className="flex items-center gap-2 hover:opacity-85 transition-opacity text-left"
            >
              <span className="font-display text-lg font-bold tracking-tight text-ink-primary">
                Allcited
              </span>
              <span className="font-mono text-[10px] uppercase tracking-wider px-1.5 py-0.2 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
                v1.0
              </span>
            </button>

            {/* Nav links per §4 Landing */}
            <nav className="hidden md:flex items-center gap-4 ml-4 text-xs font-medium text-gray-warm">
              <button
                type="button"
                onClick={() => {
                  setInWorkspace(false);
                  setTimeout(() => scrollToSection("problem"), 100);
                }}
                className="hover:text-ink-primary transition-colors"
              >
                Product
              </button>
              <button
                type="button"
                onClick={() => {
                  setInWorkspace(false);
                  setTimeout(() => scrollToSection("how-it-works"), 100);
                }}
                className="hover:text-ink-primary transition-colors"
              >
                How it works
              </button>
              <button
                type="button"
                onClick={() => {
                  setInWorkspace(false);
                  setTimeout(() => scrollToSection("the-exam"), 100);
                }}
                className="hover:text-ink-primary transition-colors"
              >
                The exam
              </button>
              <Link href="/pricing" className="hover:text-ink-primary transition-colors">
                Pricing
              </Link>
              <Link href="/library" className="hover:text-ink-primary transition-colors">
                Shelf
              </Link>
              <Link href="/dev" className="hover:text-ink-primary transition-colors font-mono">
                /dev
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Quick Demo Handbook */}
            {!sessionId && (
              <Button
                variant="outline"
                size="sm"
                onClick={loadHandbookFixture}
                className="text-xs h-8 gap-1 hidden sm:inline-flex"
              >
                <FileText className="w-3.5 h-3.5 text-accent-primary" />
                <span>Try Demo Handbook</span>
              </Button>
            )}

            {/* Model / Engine Config Trigger */}
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              title="Who does the thinking?"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-medium rounded-interactive border border-border bg-bg-surface hover:bg-bg-sunken text-ink-primary transition-colors"
            >
              {providerConfig.mode === "byok" ? (
                <>
                  <Key className="w-3.5 h-3.5 text-accent-hot" />
                  <span className="hidden sm:inline">BYOK</span>
                </>
              ) : providerConfig.mode === "ollama" ? (
                <>
                  <Server className="w-3.5 h-3.5 text-accent-primary" />
                  <span className="hidden sm:inline">Ollama</span>
                </>
              ) : (
                <>
                  <Cloud className="w-3.5 h-3.5 text-accent-primary" />
                  <span className="hidden sm:inline">Free Tier</span>
                </>
              )}
              <Settings className="w-3 h-3 text-ink-ghost ml-0.5" />
            </button>

            {/* Theme Toggle with Wave Transition per §5 */}
            <ThemeToggle />

            {/* Workspace Toggle or CTA */}
            {!inWorkspace ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setInWorkspace(true)}
                className="text-xs h-8"
              >
                Try it — no signup
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInWorkspace(false)}
                className="text-xs h-8"
              >
                Overview
              </Button>
            )}

            {/* Connection status indicator */}
            <div className="flex items-center gap-1.5 pl-1" title={apiConnected ? "Backend online" : "Backend offline"}>
              <span
                className={`w-2 h-2 rounded-full ${
                  apiConnected ? "bg-[#28C840] dark:bg-[#5AD46F] animate-pulse" : "bg-danger"
                }`}
              />
            </div>
          </div>
        </header>

        {/* Dynamic Content: Interactive Chat Workspace or Full Landing Page */}
        {inWorkspace ? (
          <div className="flex-1 min-h-0 relative flex flex-col" ref={workspaceRef}>
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
          /* Full Landing Page per §4 */
          <div className="flex-1 overflow-y-auto">
            {/* Hero Section per §4 */}
            <section className="dot-grid py-16 sm:py-24 px-4 sm:px-6 max-w-5xl mx-auto text-center relative">
              <h1 className="font-editorial text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-ink-primary mb-6">
                Answers, with receipts.
              </h1>
              <p className="text-base sm:text-lg text-gray-warm max-w-2xl mx-auto mb-8 leading-relaxed font-sans">
                Drop in a PDF, Word file, deck, spreadsheet, or a link. Ask real questions. Every claim comes stamped with the exact section it came from.
              </p>

              {/* CTAs per §4 */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 mb-8">
                <Button
                  variant="primary"
                  size="lg"
                  onClick={() => setInWorkspace(true)}
                  className="w-full sm:w-auto text-sm"
                >
                  Open Allcited
                </Button>
                <Button
                  variant="ferrari"
                  onClick={() => scrollToSection("how-it-works")}
                  className="py-2.5"
                >
                  SEE HOW IT WORKS
                </Button>
              </div>

              {/* Trust Line (mono, ghost) per §4 */}
              <p className="font-mono text-xs text-ink-ghost tracking-wide">
                No account needed · Sessions vanish when you leave · We publish our own test scores
              </p>
            </section>

            {/* Stats Band (rolling counters) per §4 */}
            <section className="border-y border-border bg-bg-surface/50 py-10 px-4 sm:px-6">
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
                  <div className="font-mono text-4xl sm:text-5xl font-bold text-ink-primary">
                    {statQuestions}
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
            </section>

            {/* Problem Section per §4 */}
            <section id="problem" className="py-16 sm:py-20 px-4 sm:px-6 max-w-4xl mx-auto">
              <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-ink-primary font-display mb-4">
                Documents are where knowledge goes to hide.
              </h2>
              <p className="text-sm sm:text-base text-gray-warm leading-relaxed">
                An 80-page handbook. You search &quot;leave&quot; and get 200 hits. The answer is in there — on page 23, third paragraph — and you&apos;ll never find it. So you ask a colleague, who guesses. Allcited is the colleague that doesn&apos;t guess.
              </p>
            </section>

            {/* How It Works (3 steps) per §4 */}
            <section id="how-it-works" className="py-16 px-4 sm:px-6 border-t border-border bg-bg-surface/30">
              <div className="max-w-5xl mx-auto">
                <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-ink-primary font-display mb-8 text-center sm:text-left">
                  How it works
                </h2>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                    <span className="font-mono text-xs font-semibold text-accent-primary">01</span>
                    <h3 className="font-semibold text-sm text-ink-primary font-display">
                      Drop it in.
                    </h3>
                    <p className="text-xs text-gray-warm leading-relaxed">
                      Drag any document. We cut it into chunks, map its cross-references, and index every word and meaning.
                    </p>
                  </div>

                  <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                    <span className="font-mono text-xs font-semibold text-accent-primary">02</span>
                    <h3 className="font-semibold text-sm text-ink-primary font-display">
                      Ask like a human.
                    </h3>
                    <p className="text-xs text-gray-warm leading-relaxed">
                      &quot;Can I carry my leaves forward?&quot; works better here than robot keywords. Vague is fine — we&apos;ll rephrase it for you.
                    </p>
                  </div>

                  <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                    <span className="font-mono text-xs font-semibold text-accent-primary">03</span>
                    <h3 className="font-semibold text-sm text-ink-primary font-display">
                      Follow the trail.
                    </h3>
                    <p className="text-xs text-gray-warm leading-relaxed">
                      Every claim carries a stamp like <code className="font-mono text-[11px] text-accent-cite">[S1] §4.2, p.23</code>. Click it. Read the original yourself. That&apos;s the whole point.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Features Grid (6 cards) per §4 */}
            <section className="py-16 sm:py-20 px-4 sm:px-6 max-w-5xl mx-auto">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                  <h3 className="font-semibold text-sm text-ink-primary font-display">
                    Receipts on everything
                  </h3>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    No answer without its source. If the document doesn&apos;t say it, we say so.
                  </p>
                </div>

                <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                  <h3 className="font-semibold text-sm text-ink-primary font-display">
                    Words <em>and</em> meaning
                  </h3>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    Two search engines run on every question: one matches your words, one matches your intent. Together they miss almost nothing.
                  </p>
                </div>

                <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                  <h3 className="font-semibold text-sm text-ink-primary font-display">
                    It reads the fine print
                  </h3>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    When an answer says &quot;as per rule 63.7.4,&quot; we go find rule 63.7.4. Automatically.
                  </p>
                </div>

                <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                  <h3 className="font-semibold text-sm text-ink-primary font-display">
                    It shows its work
                  </h3>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    Every answer has a trace: what we searched, what we nearly picked, why we picked what we did.
                  </p>
                </div>

                <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                  <h3 className="font-semibold text-sm text-ink-primary font-display">
                    Your key, your business
                  </h3>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    Bring your own AI key, or run everything on your own machine. Your call, your control.
                  </p>
                </div>

                <div className="p-5 rounded-interactive border border-border bg-bg-surface space-y-2">
                  <h3 className="font-semibold text-sm text-ink-primary font-display">
                    It forgets on purpose
                  </h3>
                  <p className="text-xs text-gray-warm leading-relaxed">
                    Sessions aren&apos;t stored. Close the tab, and it&apos;s gone. (Want to keep a document? That&apos;s the shelf — and that part&apos;s yours alone.)
                  </p>
                </div>
              </div>
            </section>

            {/* The Exam Section per §4 */}
            <section id="the-exam" className="py-16 px-4 sm:px-6 border-t border-border bg-bg-surface/50">
              <div className="max-w-4xl mx-auto space-y-4">
                <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-ink-primary font-display">
                  We grade ourselves in public.
                </h2>
                <p className="text-sm text-gray-warm leading-relaxed">
                  Most AI demos show you three questions that worked. We run a 46-question exam on every release — including questions designed to break us: answers split across pages, cross-references, trick phrasings, and things the document simply doesn&apos;t say. The scorecard is in the README. If we miss, it&apos;s written down.
                </p>
                <div className="pt-2">
                  <Link href="/dev">
                    <Button variant="ferrari">READ THE SCORECARD</Button>
                  </Link>
                </div>
              </div>
            </section>

            {/* Pricing Preview per §4 */}
            <section className="py-16 px-4 sm:px-6 max-w-4xl mx-auto text-center space-y-4">
              <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-ink-primary font-display">
                Free to ask. Paid to go deep.
              </h2>
              <p className="text-sm text-gray-warm max-w-xl mx-auto leading-relaxed">
                Asking questions is free, forever. Pro is for the heavy stuff — giant documents, precision mode, a shelf that keeps everything.
              </p>
              <div className="pt-2">
                <Link href="/pricing">
                  <Button variant="primary" size="default">
                    See pricing
                  </Button>
                </Link>
              </div>
            </section>

            {/* FAQ per §4 */}
            <section className="py-16 px-4 sm:px-6 border-t border-border max-w-4xl mx-auto">
              <h2 className="text-xl sm:text-2xl font-semibold tracking-tight text-ink-primary font-display mb-6">
                Frequently asked questions
              </h2>

              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-interactive border border-border bg-bg-surface space-y-1">
                  <h4 className="font-semibold text-sm text-ink-primary font-display">
                    Where do my documents go?
                  </h4>
                  <p className="text-gray-warm leading-relaxed">
                    Into memory for your session, then gone. Nothing hits a database unless you personally save it to your shelf.
                  </p>
                </div>

                <div className="p-4 rounded-interactive border border-border bg-bg-surface space-y-1">
                  <h4 className="font-semibold text-sm text-ink-primary font-display">
                    How is this different from just using ChatGPT?
                  </h4>
                  <p className="text-gray-warm leading-relaxed">
                    ChatGPT answers from what it already knows — and invents the rest. Allcited answers only from your document, or says it can&apos;t. You can check every claim in one click.
                  </p>
                </div>

                <div className="p-4 rounded-interactive border border-border bg-bg-surface space-y-1">
                  <h4 className="font-semibold text-sm text-ink-primary font-display">
                    Does it work in Hindi?
                  </h4>
                  <p className="text-gray-warm leading-relaxed">
                    Ask in Hindi, Hinglish, or any mix. The document can be in any language we can read.
                  </p>
                </div>

                <div className="p-4 rounded-interactive border border-border bg-bg-surface space-y-1">
                  <h4 className="font-semibold text-sm text-ink-primary font-display">
                    Scanned PDFs?
                  </h4>
                  <p className="text-gray-warm leading-relaxed">
                    Yes, with OCR. Citations from scans are marked &quot;(OCR)&quot; so you know to double-check them.
                  </p>
                </div>

                <div className="p-4 rounded-interactive border border-border bg-bg-surface space-y-1">
                  <h4 className="font-semibold text-sm text-ink-primary font-display">
                    What does it cost?
                  </h4>
                  <p className="text-gray-warm leading-relaxed">
                    Asking: free. Pro: ₹299/month. That&apos;s it. No per-question nonsense.
                  </p>
                </div>
              </div>
            </section>

            {/* Mono Footer per §4 */}
            <footer className="py-8 border-t border-border text-center font-mono text-[11px] text-gray-warm">
              Built in the open · 46-question exam on every release · © 2026 Allcited
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

"use client";

import { useEffect, useState } from "react";
import { Chat } from "@/components/Chat";
import { SourcePanel } from "@/components/SourcePanel";
import { Citation } from "@/lib/sse";
import { BookOpen, FileText } from "lucide-react";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [documentName, setDocumentName] = useState<string | null>(null);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [selectedCitationLabel, setSelectedCitationLabel] = useState<string | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean>(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Check health and initialize a demo session if none exists
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
  }, [apiUrl]);

  // Quick action to load fixture session for immediate testing
  const loadHandbookFixture = async () => {
    try {
      // Ingest the sample handbook fixture text
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
Upon voluntary resignation or formal separation, accrued annual leave days up to a cap of 30 working days shall be encashed at the employee base daily rate, computed as monthly basic pay divided by 22 working days. Sick leave, compassionate leave, and floating holidays are strictly non-encashable and non-transferable.`;

      const blob = new Blob([sampleText], { type: "text/markdown" });
      const formData = new FormData();
      formData.append("file", blob, "handbook.md");

      const res = await fetch(`${apiUrl}/v1/ingest`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Ingest failed: ${res.statusText}`);
      }

      const data = await res.json();
      setSessionId(data.session_id);
      setDocumentName(data.filename || "handbook.md");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      alert(`Failed to load handbook session: ${message}`);
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
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans">
      {/* Main Content Area */}
      <div className="flex flex-col flex-1 h-full min-w-0">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-sm">
              AC
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                  Allcited
                </span>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900">
                  v1.0
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {sessionId ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                  <FileText className="w-3.5 h-3.5 text-blue-500" />
                  <span className="max-w-[140px] truncate">{documentName}</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSessionId(null);
                    setDocumentName(null);
                  }}
                  className="px-2 py-1 text-xs rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Change
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={loadHandbookFixture}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors cursor-pointer"
              >
                <BookOpen className="w-3.5 h-3.5" />
                Load Demo Handbook
              </button>
            )}

            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
              <span
                className={`w-2 h-2 rounded-full ${
                  apiConnected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
                }`}
              />
              <span className="hidden sm:inline">{apiConnected ? "API Connected" : "Connecting..."}</span>
            </div>
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 min-h-0 relative">
          <Chat
            sessionId={sessionId}
            documentName={documentName}
            onCitationClick={(cit, allCits) => {
              setActiveCitations(allCits && allCits.length > 0 ? allCits : [cit]);
              setSelectedCitationLabel(cit.label);
            }}
            onUploadSuccess={handleUploadSuccess}
          />
        </div>
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
    </div>
  );
}

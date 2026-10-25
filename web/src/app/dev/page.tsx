"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastItem } from "@/components/ui/Toast";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/Table";
import { Skeleton } from "@/components/ui/Skeleton";
import { Tabs } from "@/components/ui/Tabs";
import { Tooltip } from "@/components/ui/Tooltip";
import { CitationChip } from "@/components/CitationChip";
import { StageChip } from "@/components/ui/StageChip";
import { Spinner } from "@/components/ui/Spinner";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";

export default function DevGalleryPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const [toast, setToast] = useState<ToastItem | null>(null);

  const triggerToast = (type: "success" | "error" | "info") => {
    setToast({
      id: String(Date.now()),
      type,
      message:
        type === "error"
          ? "Couldn't read that file — corrupt or password-protected. Nothing was saved."
          : "214 chunks ready — ask away.",
      requestId: "req_88f2a1b9",
    });
    setTimeout(() => setToast(null), 4000);
  };

  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b border-border bg-bg-surface/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center text-xs font-medium text-gray-warm hover:text-ink-primary transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
            Back to App
          </Link>
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-bg-sunken border border-border">
              /dev component gallery
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-6xl w-full mx-auto px-4 py-8 space-y-12">
        <div>
          <h1 className="text-3xl font-bold font-display text-ink-primary">
            Design System & Component Inventory
          </h1>
          <p className="text-xs text-gray-warm mt-1">
            Verification testbed for ALLCITED.md §3 tokens, §5 wave transition, and §6 components.
          </p>
        </div>

        {/* Section 1: Color Tokens */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold font-display border-b border-border pb-2">
            1. Color Tokens (§3.1 & §3.2)
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-interactive border border-border bg-bg-base text-ink-primary text-xs">
              <span className="font-mono block text-[10px] text-gray-warm">bg/base</span>
              <span className="font-semibold">Paper / Teal-Ink</span>
            </div>
            <div className="p-3 rounded-interactive border border-border bg-bg-surface text-ink-primary text-xs shadow-xs">
              <span className="font-mono block text-[10px] text-gray-warm">bg/surface</span>
              <span className="font-semibold">Surface Card</span>
            </div>
            <div className="p-3 rounded-interactive border border-border bg-bg-sunken text-ink-primary text-xs">
              <span className="font-mono block text-[10px] text-gray-warm">bg/sunken</span>
              <span className="font-semibold">Sunken Bars</span>
            </div>
            <div className="p-3 rounded-interactive bg-accent-primary text-primary-foreground text-xs shadow-xs">
              <span className="font-mono block text-[10px] opacity-80">accent/primary</span>
              <span className="font-semibold">Wispr Teal</span>
            </div>
            <div className="p-3 rounded-interactive bg-accent-cite text-white text-xs shadow-xs">
              <span className="font-mono block text-[10px] opacity-80">accent/cite</span>
              <span className="font-semibold">Seal Red</span>
            </div>
            <div className="p-3 rounded-interactive bg-danger text-white text-xs shadow-xs">
              <span className="font-mono block text-[10px] opacity-80">danger</span>
              <span className="font-semibold">Maroon</span>
            </div>
          </div>
        </section>

        {/* Section 2: Typography & Voices */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold font-display border-b border-border pb-2">
            2. Typography & The Two Voices (§3.3)
          </h2>
          <div className="space-y-3 p-4 rounded-interactive border border-border bg-bg-surface">
            <div>
              <span className="text-[10px] font-mono text-gray-warm block mb-1">Display (Bricolage Grotesque)</span>
              <p className="font-display text-2xl font-bold tracking-tight">
                Answers, with receipts.
              </p>
            </div>
            <div>
              <span className="text-[10px] font-mono text-gray-warm block mb-1">UI & Body (Inter)</span>
              <p className="font-sans text-sm leading-relaxed text-ink-primary">
                An 80-page handbook. You search &quot;leave&quot; and get 200 hits. The answer is in there — on page 23, third paragraph — and you&apos;ll never find it.
              </p>
            </div>
            <div>
              <span className="text-[10px] font-mono text-gray-warm block mb-1">Machine Voice (JetBrains Mono)</span>
              <p className="font-mono text-xs text-accent-primary">
                route: lookup · retrieve: 25 candidates · rerank: kept 4, dropped 21 · compose: 3.1s
              </p>
            </div>
            <div>
              <span className="text-[10px] font-mono text-gray-warm block mb-1">Personality Accent (Caveat)</span>
              <p className="font-handwriting text-lg text-accent-primary">
                found on p.23 — 2nd hop via rule 63.7.4
              </p>
            </div>
          </div>
        </section>

        {/* Section 3: Buttons */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold font-display border-b border-border pb-2">
            3. Buttons (§6 & §4.2)
          </h2>
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="primary">Primary Teal</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            {/* Ferrari-style tracked uppercase with sliding arrow */}
            <Button variant="ferrari">SEE HOW IT WORKS</Button>
          </div>
        </section>

        {/* Section 4: Stage & Citation Chips */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold font-display border-b border-border pb-2">
            4. Chips (§6, §4.2)
          </h2>
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-gray-warm mr-2">Stage Chips:</span>
              <StageChip stage="searching" label="reading the shelves…" isActive />
              <StageChip stage="reranking" label="re-reading 25 passages…" isActive />
              <StageChip stage="twohop" label="two-hop definition resolved" isActive />
              <StageChip stage="caching" label="Instant — cached" isActive />
              <StageChip stage="composing" label="writing it down…" isActive />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-gray-warm mr-2">Citation Chips:</span>
              <CitationChip
                citation={{
                  label: "S1",
                  chunk_id: "c1",
                  text_preview: "Leave carry forward is capped at 8 days.",
                  page: 23,
                  section_path: ["Leave Policy"],
                }}
              />
              <CitationChip
                citation={{
                  label: "S2",
                  chunk_id: "c2",
                  text_preview: "Rule 63.7.4 defines final paycheck settlement.",
                  is_two_hop: true,
                  section_path: ["Rule 63.7.4"],
                }}
              />
              <CitationChip
                citation={{
                  label: "S3 (OCR)",
                  chunk_id: "c3",
                  text_preview: "Scanned document text verified by OCR.",
                  is_ocr: true,
                  page: 14,
                }}
              />
            </div>
          </div>
        </section>

        {/* Section 5: Inputs, Tabs, Tooltip, Table */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold font-display border-b border-border pb-2">
            5. Form Controls & Chrome (§6)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3 p-4 rounded-interactive border border-border bg-bg-surface">
              <Input placeholder="Input (4px radius, focus teal glow)" />
              <Select defaultValue="gpt-4o-mini">
                <option value="gpt-4o-mini">gpt-4o-mini (default)</option>
                <option value="llama-3.3-70b">llama-3.3-70b</option>
                <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
              </Select>
              <div className="flex items-center gap-4">
                <Tabs
                  tabs={[
                    { id: "all", label: "All Sources", count: 4 },
                    { id: "twohop", label: "Two-Hop", count: 1 },
                  ]}
                  activeTab={activeTab}
                  onChange={setActiveTab}
                />
                <Tooltip content="Tooltip showing verified receipt details">
                  <span className="text-xs text-accent-primary underline cursor-pointer">
                    Hover for tooltip
                  </span>
                </Tooltip>
                <Spinner size="md" />
              </div>
            </div>

            <div className="p-4 rounded-interactive border border-border bg-bg-surface space-y-3">
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={() => setIsModalOpen(true)}>
                  Open Modal
                </Button>
                <Button size="sm" variant="outline" onClick={() => triggerToast("success")}>
                  Trigger Success Toast
                </Button>
                <Button size="sm" variant="outline" onClick={() => triggerToast("error")}>
                  Trigger Error Toast
                </Button>
              </div>

              <Skeleton className="h-6 w-full" />
              <Skeleton className="h-6 w-3/4" />
            </div>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Metric</TableHead>
                <TableHead>Allcited Baseline</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-mono">Recall@5</TableCell>
                <TableCell className="font-mono">87%</TableCell>
                <TableCell className="text-accent-primary">Verified</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-mono">Exam Questions</TableCell>
                <TableCell className="font-mono">46</TableCell>
                <TableCell className="text-accent-primary">Passing</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </section>

        {/* Section 6: Empty & Error States */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold font-display border-b border-border pb-2">
            6. Workspace States (§7)
          </h2>
          <EmptyState onSelectSampleQuestion={() => {}} />
          <ErrorState
            code="free_tier_busy"
            requestId="req_88f2a1b9"
            onRetry={() => {}}
            onOpenSettings={() => {}}
          />
        </section>
      </main>

      {/* Modal Demo */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Sample Modal Dialog"
        description="With focus trap, escape listener, and backdrop blur."
      >
        <p className="text-xs text-ink-primary leading-relaxed my-4">
          Every dialogue in Allcited adheres to the 10px interactive radius and warm neutral palettes.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => setIsModalOpen(false)}>
            Dismiss
          </Button>
          <Button variant="primary" size="sm" onClick={() => setIsModalOpen(false)}>
            Confirm
          </Button>
        </div>
      </Modal>

      {/* Toast Render */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}

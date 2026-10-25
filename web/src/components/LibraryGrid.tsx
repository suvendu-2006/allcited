"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { LibraryDocCard, LibraryDocument } from "./LibraryDocCard";
import { Skeleton } from "./ui/Skeleton";
import { Button } from "./ui/button";
import { BookOpen, AlertTriangle, ArrowRight, Search } from "lucide-react";

interface LibraryGridProps {
  apiUrl?: string;
  onSelectDocForChat?: (doc: LibraryDocument) => void;
  onAskAcrossShelf?: (query: string) => void;
}

export function LibraryGrid({
  apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  onSelectDocForChat,
  onAskAcrossShelf,
}: LibraryGridProps) {
  const [docs, setDocs] = useState<LibraryDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDegraded, setIsDegraded] = useState(false);
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [shelfQuery, setShelfQuery] = useState("");

  useEffect(() => {
    // Check if user is authenticated via local token or mock session
    const token = typeof window !== "undefined" ? localStorage.getItem("allcited_auth_token") : null;
    if (!token) {
      setIsSignedIn(false);
      setLoading(false);
      return;
    }

    setIsSignedIn(true);
    setLoading(true);
    setIsDegraded(false);

    fetch(`${apiUrl}/v1/library`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) {
          if (res.status === 503 || res.status === 500) {
            setIsDegraded(true);
            return [];
          }
          throw new Error("Failed to load shelf");
        }
        return res.json();
      })
      .then((data) => {
        setDocs(data?.documents || []);
        setLoading(false);
      })
      .catch(() => {
        setIsDegraded(true);
        setLoading(false);
      });
  }, [apiUrl]);

  const handleRemove = async (doc: LibraryDocument) => {
    setRemovingId(doc.id);
    const token = localStorage.getItem("allcited_auth_token") || "mock_clerk_token";
    try {
      const res = await fetch(`${apiUrl}/v1/library/${doc.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setDocs((prev) => prev.filter((d) => d.id !== doc.id));
      }
    } catch {
      // Fallback
    } finally {
      setRemovingId(null);
    }
  };

  const handleSignInMock = () => {
    localStorage.setItem("allcited_auth_token", "mock_clerk_token_active");
    setIsSignedIn(true);
    setLoading(true);
    // Refresh with demo mock documents
    setTimeout(() => {
      setDocs([
        {
          id: "doc_handbook_01",
          filename: "Acme_Employee_Handbook_2026.pdf",
          chunk_count: 214,
          created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        },
        {
          id: "doc_policy_02",
          filename: "Travel_and_Expense_Policy_v3.docx",
          chunk_count: 86,
          created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
        },
      ]);
      setLoading(false);
    }, 500);
  };

  // State 1: Degradation Notice per §4 copy freeze
  if (isDegraded) {
    return (
      <div className="space-y-6">
        <div className="p-4 rounded-interactive border border-amber-300 dark:border-amber-700 bg-amber-50/50 dark:bg-amber-950/20 text-ink-primary flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm">Shelf temporarily unavailable</h4>
            <p className="text-xs text-gray-warm mt-0.5">
              The shelf is briefly unreachable — but chat still works fine. We&apos;re on it.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // State 2: Loading Skeletons per §7
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    );
  }

  // State 3: Empty (signed out) per §4 copy freeze
  if (!isSignedIn) {
    return (
      <div className="dot-grid rounded-interactive border border-border p-8 sm:p-12 text-center bg-bg-surface/40">
        <div className="w-12 h-12 rounded-full bg-bg-sunken border border-border text-accent-primary mx-auto flex items-center justify-center mb-4">
          <BookOpen className="w-6 h-6" />
        </div>

        <h3 className="text-xl sm:text-2xl font-semibold text-ink-primary font-display mb-2">
          Your shelf is empty.
        </h3>
        <p className="text-xs sm:text-sm text-gray-warm max-w-md mx-auto mb-6 leading-relaxed">
          Asking is free and needs no account. But if you want documents that stay — your handbook, your contracts, your manuals — that&apos;s the shelf.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button variant="primary" onClick={handleSignInMock} className="text-xs h-9">
            Sign in to start your shelf
          </Button>
          <Link href="/">
            <Button variant="ghost" className="text-xs h-9">
              Keep asking without one
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // State 4: Signed in with Documents & Ask-My-Library Composer
  return (
    <div className="space-y-6">
      {/* Ask across everything on your shelf per §4 */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (shelfQuery.trim()) onAskAcrossShelf?.(shelfQuery);
        }}
        className="flex items-center gap-2 p-2 rounded-interactive border border-border bg-bg-surface shadow-xs"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-ghost" />
          <input
            type="text"
            value={shelfQuery}
            onChange={(e) => setShelfQuery(e.target.value)}
            placeholder="Ask across everything on your shelf…"
            className="w-full pl-9 pr-3 py-2 text-xs rounded-input bg-bg-sunken border border-border text-ink-primary placeholder:text-ink-ghost focus:outline-none focus:ring-1 focus:ring-accent-primary"
          />
        </div>
        <Button type="submit" size="sm" disabled={!shelfQuery.trim()} className="text-xs h-8 px-3">
          <span>Search shelf</span>
          <ArrowRight className="w-3.5 h-3.5 ml-1" />
        </Button>
      </form>

      {/* Grid of Documents */}
      {docs.length === 0 ? (
        <div className="text-center py-12 text-gray-warm text-xs">
          No documents saved to your shelf yet. Upload a document in chat and click save.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {docs.map((doc) => (
            <LibraryDocCard
              key={doc.id}
              doc={doc}
              onAsk={(d) => onSelectDocForChat?.(d)}
              onRemove={handleRemove}
              isRemoving={removingId === doc.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}

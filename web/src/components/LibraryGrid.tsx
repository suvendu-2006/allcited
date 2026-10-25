"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth, SignInButton } from "@clerk/nextjs";
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
  const { isLoaded, isSignedIn: clerkSignedIn, getToken } = useAuth();
  const [docs, setDocs] = useState<LibraryDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDegraded, setIsDegraded] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [shelfQuery, setShelfQuery] = useState("");

  const hasLocalMockToken =
    typeof window !== "undefined" && Boolean(localStorage.getItem("allcited_auth_token"));
  const isSignedIn = Boolean(clerkSignedIn || hasLocalMockToken);

  useEffect(() => {
    if (!isLoaded) return;

    if (!isSignedIn) {
      setLoading(false);
      return;
    }

    const fetchDocs = async () => {
      setLoading(true);
      setIsDegraded(false);
      try {
        let token: string | null = null;
        if (clerkSignedIn) {
          token = await getToken();
        } else if (typeof window !== "undefined") {
          token = localStorage.getItem("allcited_auth_token");
        }

        if (!token) {
          setLoading(false);
          return;
        }

        const res = await fetch(`${apiUrl}/v1/library`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) {
          if (res.status === 503 || res.status === 500) {
            setIsDegraded(true);
            return;
          }
          throw new Error("Failed to load shelf");
        }

        const data = await res.json();
        setDocs(data?.documents || []);
      } catch {
        setIsDegraded(true);
      } finally {
        setLoading(false);
      }
    };

    fetchDocs();
  }, [apiUrl, isLoaded, isSignedIn, clerkSignedIn, getToken]);

  const handleRemove = async (doc: LibraryDocument) => {
    setRemovingId(doc.id);
    try {
      let token: string | null = null;
      if (clerkSignedIn) {
        token = await getToken();
      } else if (typeof window !== "undefined") {
        token = localStorage.getItem("allcited_auth_token");
      }
      if (!token) token = "mock_clerk_token";

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

  // State 1: Degradation Notice per text.md
  if (isDegraded) {
    return (
      <div className="space-y-6">
        <div className="p-4 rounded-interactive border border-amber-300 dark:border-amber-700 bg-amber-50/50 dark:bg-amber-950/20 text-ink-primary flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-ink-secondary">
              The shelf is briefly unreachable. Chat still works fine. We&apos;re on it.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // State 2: Loading Skeletons
  if (!isLoaded || loading) {
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

  // State 3: Empty (signed out) per text.md
  if (!isSignedIn) {
    return (
      <div className="dot-grid rounded-interactive border border-border p-8 sm:p-12 text-center bg-bg-surface/40">
        <div className="w-12 h-12 rounded-full bg-bg-sunken border border-border text-accent-primary mx-auto flex items-center justify-center mb-4">
          <BookOpen className="w-6 h-6" />
        </div>

        <p className="text-sm text-ink-secondary max-w-md mx-auto mb-6 leading-relaxed">
          Continue as guest to ask right away — or sign in to keep documents between visits.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <SignInButton mode="modal">
            <Button variant="primary" className="text-xs h-9">
              Sign in to start your shelf
            </Button>
          </SignInButton>
          <Link href="/?workspace=true">
            <Button variant="ghost" className="text-xs h-9">
              Continue as guest
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

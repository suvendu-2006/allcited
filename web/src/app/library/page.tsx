"use client";

import React from "react";
import { BookOpen } from "lucide-react";
import { LibraryGrid } from "@/components/LibraryGrid";
import { Navbar } from "@/components/Navbar";
import { useRouter } from "next/navigation";

export default function LibraryPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col">
      <Navbar />

      {/* Main Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8 sm:py-10">
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-border">
          <div>
            <h1 className="text-2xl font-semibold text-ink-primary font-display flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-accent-primary" />
              Your shelf
            </h1>
            <p className="text-xs text-gray-warm mt-1">
              Persistent, cross-session documents saved to your personal library.
            </p>
          </div>
        </div>

        <LibraryGrid
          onSelectDocForChat={(doc) => {
            // Store selected doc and navigate to main workspace
            if (typeof window !== "undefined") {
              sessionStorage.setItem("allcited_active_doc", JSON.stringify(doc));
            }
            router.push(`/?session_id=${doc.id}&filename=${encodeURIComponent(doc.filename)}`);
          }}
          onAskAcrossShelf={(query) => {
            router.push(`/?shelf_query=${encodeURIComponent(query)}`);
          }}
        />
      </main>
    </div>
  );
}

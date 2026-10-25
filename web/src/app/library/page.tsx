"use client";

import React from "react";
import { LibraryGrid } from "@/components/LibraryGrid";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { useRouter } from "next/navigation";

export default function LibraryPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col">
      <Navbar />

      {/* Main Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8 sm:py-12">
        <div className="mb-8 pb-4 border-b border-border">
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-ink-primary font-display">
            Your shelf
          </h1>
          <p className="text-sm text-ink-muted mt-2">
            Keep your documents here. Ask questions across all of them, anytime. Private to your account.
          </p>
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

      <Footer />
    </div>
  );
}

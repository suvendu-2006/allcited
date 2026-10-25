"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col items-center justify-center p-4 dot-grid">
      <div className="max-w-md w-full text-center space-y-4 p-8 rounded-interactive border border-border bg-bg-surface shadow-md animate-fade-in">
        <span className="font-mono text-3xl font-bold text-accent-primary">
          404
        </span>
        {/* Copy per §4 copy freeze */}
        <h2 className="text-xl font-semibold text-ink-primary font-display">
          This page isn&apos;t in the index.
        </h2>
        <p className="text-xs text-gray-warm leading-relaxed">
          The requested document or path could not be found in our citation index.
        </p>
        <div className="pt-2">
          <Link href="/">
            <Button variant="ghost" className="text-xs text-accent-primary hover:underline">
              Take me home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

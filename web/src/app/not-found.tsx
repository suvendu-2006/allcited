"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-bg-base text-ink-primary flex flex-col items-center justify-center p-4 dot-grid">
      <div className="max-w-md w-full text-center space-y-4 p-8 rounded-interactive border border-border bg-bg-surface shadow-md">
        <span className="font-mono text-3xl font-bold text-accent-primary">
          404
        </span>
        <h1 className="text-xl font-semibold text-ink-primary font-display">
          This page isn&apos;t in the index.
        </h1>
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

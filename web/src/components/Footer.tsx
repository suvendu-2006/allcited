"use client";

import React from "react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border bg-bg-surface/60 backdrop-blur-sm py-12 px-4 sm:px-8 text-xs select-none">
      <div className="max-w-6xl mx-auto space-y-8">
        <p className="font-editorial text-base sm:text-lg text-ink-primary font-medium">
          Allcited is built in the open. Every claim has a receipt. Every release runs the exam.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-8 pt-2 text-xs">
          {/* Column 1: Product */}
          <div className="space-y-3">
            <span className="font-mono text-[10px] uppercase tracking-wider text-gray-warm block">
              Product
            </span>
            <ul className="space-y-2">
              <li>
                <Link href="/product" className="text-gray-warm hover:text-ink-primary transition-colors">
                  Product
                </Link>
              </li>
              <li>
                <Link href="/how-it-works" className="text-gray-warm hover:text-ink-primary transition-colors">
                  How it works
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="text-gray-warm hover:text-ink-primary transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="/library" className="text-gray-warm hover:text-ink-primary transition-colors">
                  Shelf
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 2: Scores */}
          <div className="space-y-3">
            <span className="font-mono text-[10px] uppercase tracking-wider text-gray-warm block">
              Scores
            </span>
            <ul className="space-y-2">
              <li>
                <Link href="/exam" className="text-gray-warm hover:text-ink-primary transition-colors">
                  The exam
                </Link>
              </li>
              <li>
                <Link href="/exam#history" className="text-gray-warm hover:text-ink-primary transition-colors">
                  Release history
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Company */}
          <div className="space-y-3 col-span-2 sm:col-span-1">
            <span className="font-mono text-[10px] uppercase tracking-wider text-gray-warm block">
              Company
            </span>
            <ul className="space-y-2">
              <li>
                <a
                  href="https://github.com/suvendu-2006/allcited"
                  target="_blank"
                  rel="noreferrer"
                  className="text-gray-warm hover:text-ink-primary transition-colors"
                >
                  GitHub
                </a>
              </li>
              <li>
                <Link href="/dev" className="text-gray-warm hover:text-ink-primary transition-colors">
                  Component gallery (/dev)
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-border/60 text-center sm:text-left">
          <p className="font-sans text-[11px] text-gray-warm">
            Built with React, in the open. 46-question exam on every release. © 2026 Allcited.
          </p>
        </div>
      </div>
    </footer>
  );
}

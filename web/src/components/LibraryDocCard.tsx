"use client";

import React from "react";
import { FileText, Trash2, ArrowRight } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { Button } from "./ui/button";

export interface LibraryDocument {
  id: string;
  filename: string;
  chunk_count: number;
  created_at: string;
  size_bytes?: number;
}

interface LibraryDocCardProps {
  doc: LibraryDocument;
  onAsk: (doc: LibraryDocument) => void;
  onRemove: (doc: LibraryDocument) => void;
  isRemoving?: boolean;
}

export function LibraryDocCard({
  doc,
  onAsk,
  onRemove,
  isRemoving = false,
}: LibraryDocCardProps) {
  const shouldReduceMotion = useReducedMotion();

  // Format date: e.g. "Oct 24"
  const formattedDate = new Date(doc.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });

  return (
    <motion.div
      layout
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={
        shouldReduceMotion
          ? { opacity: 0 }
          : { opacity: 0, scale: 0.96, height: 0, overflow: "hidden", marginTop: 0, marginBottom: 0, paddingTop: 0, paddingBottom: 0 }
      }
      whileHover={shouldReduceMotion ? undefined : { y: -4, boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.08)" }}
      whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
      transition={{ duration: 0.24, ease: [0.16, 1, 0.3, 1] }}
      className="p-4 rounded-interactive border border-border bg-bg-surface flex flex-col justify-between shadow-xs group"
    >
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-[6px] bg-bg-sunken border border-border flex items-center justify-center text-accent-primary transition-all duration-200 group-hover:scale-105 group-hover:border-accent-primary/40">
              <FileText className="w-4 h-4 transition-transform duration-200 group-hover:scale-105" />
            </div>
            <h4 className="font-semibold text-sm text-ink-primary font-display truncate max-w-[200px]" title={doc.filename}>
              {doc.filename}
            </h4>
          </div>
          <motion.button
            type="button"
            onClick={() => onRemove(doc)}
            disabled={isRemoving}
            title="Remove document"
            whileHover={shouldReduceMotion ? undefined : { scale: 1.15 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.9 }}
            className="text-ink-ghost hover:text-danger p-1 rounded transition-colors disabled:opacity-40 cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </motion.button>
        </div>

        <p className="font-mono text-xs text-gray-warm">
          {doc.chunk_count} chunks · added {formattedDate}
        </p>
      </div>

      <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onAsk(doc)}
          className="text-xs h-7 gap-1 hover:border-accent-primary"
        >
          <span>Ask about this</span>
          <ArrowRight className="w-3 h-3 text-accent-primary transition-transform duration-150 group-hover:translate-x-1" />
        </Button>
      </div>
    </motion.div>
  );
}

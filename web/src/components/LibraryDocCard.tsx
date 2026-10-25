"use client";

import React from "react";
import { FileText, Trash2, ArrowRight } from "lucide-react";
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
  // Format date: e.g. "Oct 24"
  const formattedDate = new Date(doc.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });

  return (
    <div className="p-4 rounded-interactive border border-border bg-bg-surface hover:bg-bg-sunken/30 transition-all duration-120 flex flex-col justify-between shadow-xs group">
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-[6px] bg-bg-sunken border border-border flex items-center justify-center text-accent-primary">
              <FileText className="w-4 h-4" />
            </div>
            <h4 className="font-semibold text-sm text-ink-primary font-display truncate max-w-[200px]" title={doc.filename}>
              {doc.filename}
            </h4>
          </div>
          <button
            type="button"
            onClick={() => onRemove(doc)}
            disabled={isRemoving}
            title="Remove document"
            className="text-ink-ghost hover:text-danger p-1 rounded transition-colors disabled:opacity-40"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Mono meta string per §4: 214 chunks · added Oct 24 */}
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
          <ArrowRight className="w-3 h-3 text-accent-primary" />
        </Button>
      </div>
    </div>
  );
}

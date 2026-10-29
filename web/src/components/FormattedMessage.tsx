"use client";

import React, { useMemo } from "react";
import { CitationChip } from "@/components/CitationChip";
import { Citation } from "@/lib/sse";
import {
  MarkdownBlock,
  InlineToken,
  parseMarkdownBlocks,
  tokenizeInline,
} from "@/lib/markdown";

interface FormattedMessageProps {
  content: string;
  citations?: Citation[];
  onCitationClick?: (citation: Citation, allCitations?: Citation[]) => void;
  isStreaming?: boolean;
}

export const FormattedMessage = React.memo(function FormattedMessage({
  content,
  citations = [],
  onCitationClick,
  isStreaming = false,
}: FormattedMessageProps) {
  // Index citations by label, related label, and stripped label for O(1) lookup
  const citationsMap = useMemo(() => {
    const map = new Map<string, Citation>();
    citations.forEach((c) => {
      map.set(c.label, c);
      const stripped = c.label.replace(/\s*\(OCR\)/gi, "").trim();
      if (stripped) {
        map.set(stripped, c);
      }
    });
    return map;
  }, [citations]);

  // Parse raw text into structured blocks
  const blocks = useMemo(
    () => parseMarkdownBlocks(content, isStreaming),
    [content, isStreaming]
  );

  // Render inline tokens safely into React element trees
  const renderInline = (text: string): React.ReactNode => {
    if (!text) return null;
    const tokens = tokenizeInline(text);

    return tokens.map((token: InlineToken, idx: number) => {
      switch (token.type) {
        case "citation": {
          const baseLabel = token.label.replace(/\s*\(OCR\)/gi, "").trim();
          const relatedLabel = `related: ${baseLabel}`;
          const citation =
            citationsMap.get(token.label) ||
            citationsMap.get(baseLabel) ||
            citationsMap.get(relatedLabel);

          if (citation) {
            return (
              <CitationChip
                key={idx}
                citation={citation}
                onClick={(c) => onCitationClick?.(c, citations)}
              />
            );
          }

          // Fallback for non-indexed bracketed badges (e.g. [Chunks 1-10])
          return (
            <span
              key={idx}
              className="inline-flex items-center font-mono text-[11px] px-1.5 py-0.5 rounded bg-bg-sunken border border-border/80 text-ink-secondary font-medium select-none align-baseline my-0.5 mx-0.5"
              title={token.raw}
            >
              {token.raw}
            </span>
          );
        }
        case "br":
          return <br key={idx} />;
        case "bold":
          return (
            <strong key={idx} className="font-semibold text-ink-primary">
              {token.value}
            </strong>
          );
        case "italic":
          return (
            <em key={idx} className="italic text-ink-secondary">
              {token.value}
            </em>
          );
        case "code":
          return (
            <code
              key={idx}
              className="px-1.5 py-0.5 rounded bg-bg-sunken border border-border font-mono text-[12px] text-accent-primary"
            >
              {token.value}
            </code>
          );
        case "link":
          return (
            <a
              key={idx}
              href={token.url}
              target="_blank"
              rel="noopener noreferrer"
              className="underline decoration-accent-primary/50 hover:decoration-accent-primary text-accent-primary transition-colors"
            >
              {token.text}
            </a>
          );
        case "text":
        default:
          return <React.Fragment key={idx}>{token.value}</React.Fragment>;
      }
    });
  };

  return (
    <div className="space-y-2.5">
      {blocks.map((block: MarkdownBlock, blockIdx: number) => {
        switch (block.type) {
          case "heading": {
            if (block.level === 2) {
              return (
                <h2
                  key={blockIdx}
                  className="text-base font-semibold font-display text-ink-primary mt-4 mb-2 first:mt-0 tracking-tight"
                >
                  {renderInline(block.text)}
                </h2>
              );
            }
            if (block.level === 3) {
              return (
                <h3
                  key={blockIdx}
                  className="text-sm font-semibold font-display text-ink-primary mt-3 mb-1.5 first:mt-0"
                >
                  {renderInline(block.text)}
                </h3>
              );
            }
            return (
              <h4
                key={blockIdx}
                className="text-xs font-semibold font-display text-ink-primary mt-2 mb-1 first:mt-0 uppercase tracking-wider"
              >
                {renderInline(block.text)}
              </h4>
            );
          }
          case "divider":
            return <hr key={blockIdx} className="my-3 border-t border-border/70" />;
          case "table":
            return (
              <div
                key={blockIdx}
                className="my-3 overflow-x-auto rounded-lg border border-border bg-bg-surface/50 shadow-2xs table-scrollbar-touch"
              >
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-bg-sunken/80 border-b border-border text-ink-primary font-medium">
                    <tr>
                      {block.headers.map((h, cIdx) => {
                        const align = block.alignments[cIdx] || "left";
                        const alignClass =
                          align === "center"
                            ? "text-center"
                            : align === "right"
                            ? "text-right"
                            : "text-left";
                        return (
                          <th
                            key={cIdx}
                            className={`px-3 py-2 font-mono text-[11px] font-semibold uppercase tracking-wider ${alignClass}`}
                          >
                            {renderInline(h)}
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {block.rows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-bg-sunken/30 transition-colors">
                        {row.map((cell, cIdx) => {
                          const align = block.alignments[cIdx] || "left";
                          const alignClass =
                            align === "center"
                              ? "text-center"
                              : align === "right"
                              ? "text-right"
                              : "text-left";
                          return (
                            <td
                              key={cIdx}
                              className={`px-3 py-2 align-top leading-relaxed text-ink-primary ${alignClass}`}
                            >
                              {renderInline(cell)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          case "list": {
            if (block.ordered) {
              return (
                <ol
                  key={blockIdx}
                  className="my-2 space-y-1.5 pl-4 list-decimal marker:text-accent-primary/70 text-ink-primary text-sm leading-relaxed"
                >
                  {block.items.map((item, iIdx) => (
                    <li key={iIdx}>{renderInline(item)}</li>
                  ))}
                </ol>
              );
            }
            return (
              <ul
                key={blockIdx}
                className="my-2 space-y-1.5 pl-4 list-disc marker:text-accent-primary/70 text-ink-primary text-sm leading-relaxed"
              >
                {block.items.map((item, iIdx) => (
                  <li key={iIdx}>{renderInline(item)}</li>
                ))}
              </ul>
            );
          }
          case "code":
            return (
              <div
                key={blockIdx}
                className="my-2.5 rounded-lg border border-border bg-bg-sunken/90 overflow-hidden font-mono text-xs shadow-2xs"
              >
                {block.language && (
                  <div className="px-3 py-1 bg-bg-surface/80 border-b border-border/60 text-[10px] text-ink-muted uppercase tracking-wider select-none">
                    {block.language}
                  </div>
                )}
                <pre className="p-3 overflow-x-auto text-ink-primary leading-relaxed">
                  <code>{block.code}</code>
                  {!block.isClosed && (
                    <span className="inline-block w-[2px] h-3.5 ml-1 bg-accent-primary animate-pulse align-middle" />
                  )}
                </pre>
              </div>
            );
          case "paragraph":
          default:
            return (
              <p
                key={blockIdx}
                className="my-2 leading-relaxed text-ink-primary text-[14px] first:mt-0 last:mb-0"
              >
                {renderInline(block.text)}
              </p>
            );
        }
      })}
    </div>
  );
});

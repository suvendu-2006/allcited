/**
 * Zero-dependency streaming-resilient Markdown parser and tokenizer.
 * Converts markdown text into structured block models and safe inline tokens
 * without using dangerouslySetInnerHTML, protecting against XSS by design.
 */

export type TableAlignment = "left" | "center" | "right";

export type MarkdownBlock =
  | { type: "code"; language: string; code: string; isClosed: boolean }
  | { type: "table"; headers: string[]; alignments: TableAlignment[]; rows: string[][] }
  | { type: "heading"; level: 2 | 3 | 4; text: string }
  | { type: "divider" }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "paragraph"; text: string };

export type InlineToken =
  | { type: "text"; value: string }
  | { type: "bold"; value: string }
  | { type: "italic"; value: string }
  | { type: "code"; value: string }
  | { type: "br" }
  | { type: "link"; text: string; url: string }
  | { type: "citation"; raw: string; label: string; isRelated: boolean };

/**
 * Consolidates citations to appear once at the end of each sentence in prose paragraphs.
 * Strictly operates on plain prose text blocks so table rows and code fences are never broken.
 */
export function consolidateSentenceCitations(srcText: string): string {
  if (!srcText) return "";
  const citPattern = /(\[\s*(?:related:\s*)?(?:S\d+|Chunks?\s+[^\]]+)(?:\s*\(OCR\))?\s*\]|\(\s*related:\s*\[?(?:S\d+|Chunks?\s+[^\]]+)\]?\s*\))/gi;
  const paragraphs = srcText.split("\n");
  const cleanedParagraphs: string[] = [];

  for (const para of paragraphs) {
    if (!para.trim()) {
      cleanedParagraphs.push(para);
      continue;
    }

    const sentenceParts = para.split(/([.!?]+(?:\s+|$))/);
    const newParaParts: string[] = [];

    for (let i = 0; i < sentenceParts.length; i += 2) {
      const sent = sentenceParts[i];
      const delim = sentenceParts[i + 1] || "";

      const cits = sent.match(citPattern);
      if (!cits || cits.length === 0) {
        newParaParts.push(sent + delim);
        continue;
      }

      const uniqueCits: string[] = [];
      const seen = new Set<string>();
      for (const c of cits) {
        const norm = c.replace(/\s+/g, "").toUpperCase();
        if (!seen.has(norm)) {
          seen.add(norm);
          uniqueCits.push(c.trim());
        }
      }

      const sentClean = sent.replace(citPattern, "").replace(/[ \t]+/g, " ").trim();
      const citsStr = " " + uniqueCits.join(" ");

      if (sentClean) {
        newParaParts.push(sentClean + citsStr + delim);
      } else {
        newParaParts.push(citsStr.trim() + delim);
      }
    }

    cleanedParagraphs.push(newParaParts.join(""));
  }

  return cleanedParagraphs.join("\n");
}

function parseTableCells(rowStr: string): string[] {
  let cleaned = rowStr.trim();
  if (cleaned.startsWith("|")) {
    cleaned = cleaned.slice(1);
  }
  if (cleaned.endsWith("|")) {
    cleaned = cleaned.slice(0, -1);
  }
  return cleaned.split("|").map((cell) => cell.trim());
}

function isSeparatorRow(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed.includes("-") || !trimmed.includes("|")) return false;
  const cells = parseTableCells(trimmed);
  if (cells.length === 0) return false;
  return cells.every((c) => /^:?-+:?$/.test(c.trim()));
}

function parseAlignments(sepLine: string): TableAlignment[] {
  const cells = parseTableCells(sepLine);
  return cells.map((cell) => {
    const c = cell.trim();
    if (c.startsWith(":") && c.endsWith(":")) return "center";
    if (c.endsWith(":")) return "right";
    return "left";
  });
}

/**
 * Parses raw text into discrete Markdown block structures.
 * Resilient to streaming tokens and handles unclosed fences or partial tables cleanly.
 */
export function parseMarkdownBlocks(rawText: string, isStreaming: boolean = false): MarkdownBlock[] {
  if (!rawText) return [];

  const lines = rawText.replace(/\r\n/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 1. Code Block Fence (```)
    if (trimmed.startsWith("```")) {
      const language = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      let isClosed = false;
      i++;
      while (i < lines.length) {
        if (lines[i].trim().startsWith("```")) {
          isClosed = true;
          i++;
          break;
        }
        codeLines.push(lines[i]);
        i++;
      }
      blocks.push({
        type: "code",
        language,
        code: codeLines.join("\n"),
        isClosed: isClosed || !isStreaming,
      });
      continue;
    }

    // 2. Markdown Table Detection
    // Table requires a header row with pipes, followed by a separator row with dashes
    if (trimmed.startsWith("|") || (trimmed.endsWith("|") && trimmed.includes("|"))) {
      if (i + 1 < lines.length && isSeparatorRow(lines[i + 1])) {
        const headerRow = trimmed;
        const separatorRow = lines[i + 1].trim();
        const headers = parseTableCells(headerRow);
        const alignments = parseAlignments(separatorRow);
        const rows: string[][] = [];

        i += 2;
        while (i < lines.length) {
          const tableLine = lines[i].trim();
          if (!tableLine || (!tableLine.startsWith("|") && !tableLine.includes("|"))) {
            break;
          }
          rows.push(parseTableCells(tableLine));
          i++;
        }

        blocks.push({
          type: "table",
          headers,
          alignments,
          rows,
        });
        continue;
      }
    }

    // 3. Headings (#, ##, ###, ####)
    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const hashes = headingMatch[1].length;
      const level = (hashes === 1 ? 2 : hashes) as 2 | 3 | 4;
      blocks.push({
        type: "heading",
        level,
        text: headingMatch[2].trim(),
      });
      i++;
      continue;
    }

    // 4. Horizontal Rule (---, ***, ___)
    if (/^(?:---+|\*\*\*+|___+)\s*$/.test(trimmed)) {
      blocks.push({ type: "divider" });
      i++;
      continue;
    }

    // 5. Unordered List Items (- , * , • )
    const bulletMatch = line.match(/^(\s*)(?:[-*•])\s+(.+)$/);
    if (bulletMatch) {
      const items: string[] = [];
      while (i < lines.length) {
        const itemMatch = lines[i].match(/^(\s*)(?:[-*•])\s+(.+)$/);
        if (!itemMatch) break;
        items.push(itemMatch[2].trim());
        i++;
      }
      blocks.push({
        type: "list",
        ordered: false,
        items,
      });
      continue;
    }

    // 6. Ordered List Items (1. , 2. )
    const orderedMatch = line.match(/^(\s*)\d+\.\s+(.+)$/);
    if (orderedMatch) {
      const items: string[] = [];
      while (i < lines.length) {
        const itemMatch = lines[i].match(/^(\s*)\d+\.\s+(.+)$/);
        if (!itemMatch) break;
        items.push(itemMatch[2].trim());
        i++;
      }
      blocks.push({
        type: "list",
        ordered: true,
        items,
      });
      continue;
    }

    // 7. Empty line - skip
    if (!trimmed) {
      i++;
      continue;
    }

    // 8. Plain Prose Paragraph
    // Group consecutive prose lines into one paragraph block
    const paraLines: string[] = [];
    while (i < lines.length) {
      const curLine = lines[i];
      const curTrimmed = curLine.trim();
      if (!curTrimmed) break;
      // If next line starts a new block type, break paragraph
      if (
        curTrimmed.startsWith("```") ||
        /^(#{1,4})\s+/.test(curLine) ||
        /^(?:---+|\*\*\*+|___+)\s*$/.test(curTrimmed) ||
        /^(\s*)(?:[-*•]|\d+\.)\s+/.test(curLine) ||
        (curTrimmed.startsWith("|") && i + 1 < lines.length && isSeparatorRow(lines[i + 1]))
      ) {
        break;
      }
      paraLines.push(curLine);
      i++;
    }

    if (paraLines.length > 0) {
      const rawPara = paraLines.join("\n");
      const processedPara = consolidateSentenceCitations(rawPara);
      blocks.push({
        type: "paragraph",
        text: processedPara,
      });
    }
  }

  return blocks;
}

/**
 * Tokenizes inline text into safe, strongly-typed tokens.
 * Automatically handles bold, italic, inline code, line breaks, citations, and links.
 */
export function tokenizeInline(text: string): InlineToken[] {
  if (!text) return [];

  // Normalize fullwidth brackets if any
  const normalized = text.replace(/【/g, "[").replace(/】/g, "]");
  const tokens: InlineToken[] = [];

  // Comprehensive tokenizer regex:
  // 1: Citations [S1], [related: S1], [Chunks 1-10]
  // 2: <br> or <br/> or <br />
  // 3: Inline code `...`
  // 4: Bold **...** or __...__
  // 5: Italic *...* or _..._
  // 6: Markdown link [text](url)
  const pattern =
    /(\[(?:related:\s*)?(?:S\d+|Chunks?\s+[^\]]+)(?:\s*\(OCR\))?\])|(<br\s*\/?>)|(`[^`]+`)|(\*\*[^*]+\*\*|__[^_]+__)|(\*[^*]+\*|_[^_]+_)|(\[[^\]]+\]\((?:https?:\/\/[^\s)]+|[^\s)]+)\))/gi;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(normalized)) !== null) {
    if (match.index > lastIndex) {
      tokens.push({
        type: "text",
        value: normalized.slice(lastIndex, match.index),
      });
    }

    const matchedStr = match[0];

    // Citation Token
    if (match[1]) {
      const isRelated = /^\[\s*related:/i.test(matchedStr);
      let label = matchedStr.slice(1, -1).trim();
      if (isRelated) {
        label = label.replace(/^related:\s*/i, "").trim();
      }
      tokens.push({
        type: "citation",
        raw: matchedStr,
        label,
        isRelated,
      });
    }
    // Line Break Token (<br>)
    else if (match[2]) {
      tokens.push({ type: "br" });
    }
    // Inline Code (`...`)
    else if (match[3]) {
      tokens.push({
        type: "code",
        value: matchedStr.slice(1, -1),
      });
    }
    // Bold (**...**)
    else if (match[4]) {
      tokens.push({
        type: "bold",
        value: matchedStr.slice(2, -2),
      });
    }
    // Italic (*...*)
    else if (match[5]) {
      tokens.push({
        type: "italic",
        value: matchedStr.slice(1, -1),
      });
    }
    // Link ([text](url))
    else if (match[6]) {
      const linkMatch = matchedStr.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (linkMatch) {
        const linkText = linkMatch[1];
        const rawUrl = linkMatch[2].trim();
        // Strict OWASP URL sanitization: only allow http, https, or relative paths
        const isSafe = /^https?:\/\//i.test(rawUrl) || rawUrl.startsWith("/");
        if (isSafe) {
          tokens.push({
            type: "link",
            text: linkText,
            url: rawUrl,
          });
        } else {
          // Neutralize dangerous protocols (e.g. javascript:, data:) by rendering as plain text
          tokens.push({
            type: "text",
            value: linkText,
          });
        }
      } else {
        tokens.push({ type: "text", value: matchedStr });
      }
    }

    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < normalized.length) {
    tokens.push({
      type: "text",
      value: normalized.slice(lastIndex),
    });
  }

  return tokens;
}

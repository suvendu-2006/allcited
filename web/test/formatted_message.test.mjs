import { test, describe } from "node:test";
import assert from "node:assert";

describe("Structured Markdown Parser & Tokenizer (§FormattedMessage)", () => {
  test("1. Parses Markdown table with headers, alignments, and multi-line rows", async () => {
    const { parseMarkdownBlocks, tokenizeInline } = await import("../src/lib/markdown.ts");

    const sampleTable = `
| Module | Hours | Core Topics | Textbook |
|:-------|:-----:|------------:|----------|
| **1. Laplace** | 8 | • Linearity<br>• Transform pairs | *Kreyszig* |
| **2. Fourier** | 8 | • Euler's formula<br>• Wave equation | *Kreyszig* |
`.trim();

    const blocks = parseMarkdownBlocks(sampleTable);
    assert.strictEqual(blocks.length, 1);
    assert.strictEqual(blocks[0].type, "table");

    const table = blocks[0];
    assert.deepStrictEqual(table.headers, ["Module", "Hours", "Core Topics", "Textbook"]);
    assert.deepStrictEqual(table.alignments, ["left", "center", "right", "left"]);
    assert.strictEqual(table.rows.length, 2);
    assert.strictEqual(table.rows[0][0], "**1. Laplace**");
    assert.strictEqual(table.rows[0][1], "8");

    // Tokenize cell with <br> and bold
    const cellTokens = tokenizeInline(table.rows[0][2]);
    const brTokens = cellTokens.filter((t) => t.type === "br");
    assert.strictEqual(brTokens.length, 1);
  });

  test("2. Table rows containing decimal numbers or abbreviations are NOT broken by citation consolidation", async () => {
    const { parseMarkdownBlocks } = await import("../src/lib/markdown.ts");

    const textWithTableAndParagraph = `
## Course Overview [S1]

| Code | Version | Credits | Description |
|---|---|---|---|
| CS101 | v1.0.4 | 4.0 | Intro to C.S. with lab experiments. |
| MATH201 | v2.5 | 3.5 | Linear algebra and multivariable calc. |

Here is a paragraph discussing policy POL-1. It has multiple sentences. [S2]
`.trim();

    const blocks = parseMarkdownBlocks(textWithTableAndParagraph);
    assert.strictEqual(blocks.length, 3);
    assert.strictEqual(blocks[0].type, "heading");
    assert.strictEqual(blocks[1].type, "table");
    assert.strictEqual(blocks[2].type, "paragraph");

    const table = blocks[1];
    assert.strictEqual(table.rows.length, 2);
    assert.strictEqual(table.rows[0][0], "CS101");
    assert.strictEqual(table.rows[0][1], "v1.0.4");
    assert.strictEqual(table.rows[1][0], "MATH201");
  });

  test("3. Streaming resilience: unclosed code block renders without throwing", async () => {
    const { parseMarkdownBlocks } = await import("../src/lib/markdown.ts");

    const incompleteCode = `
\`\`\`python
def calculate_grade(score):
    return score * 1.5
`.trim();

    const blocks = parseMarkdownBlocks(incompleteCode, true);
    assert.strictEqual(blocks.length, 1);
    assert.strictEqual(blocks[0].type, "code");
    assert.strictEqual(blocks[0].language, "python");
    assert.strictEqual(blocks[0].isClosed, false);
    assert.ok(blocks[0].code.includes("calculate_grade"));
  });

  test("4. Tokenizes citation markers ([S1], [related: S2], [Chunks 1-10])", async () => {
    const { tokenizeInline } = await import("../src/lib/markdown.ts");

    const sample = "Notice period is 60 days [S1]. Additional provisions [related: S3] in [Chunks 1-10].";
    const tokens = tokenizeInline(sample);

    const citations = tokens.filter((t) => t.type === "citation");
    assert.strictEqual(citations.length, 3);

    assert.strictEqual(citations[0].label, "S1");
    assert.strictEqual(citations[0].isRelated, false);

    assert.strictEqual(citations[1].label, "S3");
    assert.strictEqual(citations[1].isRelated, true);

    assert.strictEqual(citations[2].label, "Chunks 1-10");
  });

  test("5. XSS Hardening: script tags and javascript: URIs are rendered safely as text", async () => {
    const { tokenizeInline } = await import("../src/lib/markdown.ts");

    const malicious = '<script>alert("xss")</script> and [clickme](javascript:alert(1))';
    const tokens = tokenizeInline(malicious);

    // script tag is treated as plain text string, never HTML
    const scriptToken = tokens.find((t) => t.value && t.value.includes("<script>"));
    assert.ok(scriptToken, "Script tag should remain a plain string token");

    // javascript: link is neutralized into plain text token
    const dangerousLink = tokens.find((t) => t.type === "link" && t.url.includes("javascript:"));
    assert.strictEqual(dangerousLink, undefined, "javascript: link must be rejected");

    const textFallback = tokens.find((t) => t.type === "text" && t.value === "clickme");
    assert.ok(textFallback, "Neutralized link should fallback to plain text");
  });

  test("6. External safe links (https://) are properly parsed", async () => {
    const { tokenizeInline } = await import("../src/lib/markdown.ts");

    const sample = "Check official syllabus at [Syllabus Portal](https://example.edu/syllabus).";
    const tokens = tokenizeInline(sample);

    const link = tokens.find((t) => t.type === "link");
    assert.ok(link);
    assert.strictEqual(link.text, "Syllabus Portal");
    assert.strictEqual(link.url, "https://example.edu/syllabus");
  });
});

import { test, describe } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe("Footer 'Receipt Underline' §4.2 Addendum Assertions", () => {
  const footerPath = path.join(__dirname, "../src/components/Footer.tsx");
  const globalsPath = path.join(__dirname, "../src/app/globals.css");

  const footerCode = fs.readFileSync(footerPath, "utf-8");
  const globalsCss = fs.readFileSync(globalsPath, "utf-8");

  test("All 8 footer links carry .footer-link class and match specified text", () => {
    const expectedLinks = [
      "Product",
      "How it works",
      "Pricing",
      "Shelf",
      "The exam",
      "Release history",
      "GitHub",
      "Component gallery",
    ];

    // Find all elements with className containing footer-link
    const footerLinkMatches = [...footerCode.matchAll(/className="[^"]*footer-link[^"]*"/g)];
    assert.strictEqual(
      footerLinkMatches.length,
      8,
      `Expected exactly 8 footer links with .footer-link class, found ${footerLinkMatches.length}`
    );

    // Verify each expected link text appears in Footer.tsx
    for (const linkText of expectedLinks) {
      assert.ok(
        footerCode.includes(linkText),
        `Footer.tsx should include link text: "${linkText}"`
      );
    }
  });

  test("Column headers and bottom mono line stay static (never animate)", () => {
    // Check that column headers (Product, Scores, Company) do not have footer-link
    const headerSection = footerCode.slice(
      footerCode.indexOf("<span className=\"font-mono text-[10px]"),
      footerCode.indexOf("<ul")
    );
    assert.ok(!headerSection.includes("footer-link"), "Column header must not have footer-link class");

    // Check bottom line
    const bottomSection = footerCode.slice(footerCode.indexOf("Built with React, in the open"));
    assert.ok(!bottomSection.includes("footer-link"), "Bottom copyright line must not have footer-link class");
  });

  test("Pure CSS origin-swap scaleX draw & exit rules exist in globals.css", () => {
    // ScaleX origin-swap: enter draws left->right (left center, 160ms), exit draws right->left (right center, 200ms)
    assert.ok(
      globalsCss.includes("transform-origin: right center;"),
      "Exit state must have transform-origin: right center for origin-swap"
    );
    assert.ok(
      globalsCss.includes("transform-origin: left center;"),
      "Hover/focus state must have transform-origin: left center"
    );
    assert.ok(
      globalsCss.includes("scaleX(0)"),
      "Underline resting state must scaleX(0)"
    );
    assert.ok(
      globalsCss.includes("scaleX(1)"),
      "Underline hover/focus state must scaleX(1)"
    );
    assert.ok(
      globalsCss.includes("160ms"),
      "Hover draw duration must be 160ms"
    );
    assert.ok(
      globalsCss.includes("200ms"),
      "Exit draw duration must be 200ms"
    );
  });

  test("2px seal-red underline, 1px lift (120ms ease/exit), and focus-visible parity", () => {
    // 2px seal-red underline
    assert.ok(
      globalsCss.includes("height: 2px;"),
      "Underline height must be 2px"
    );
    assert.ok(
      globalsCss.includes("background-color: var(--accent-primary);"),
      "Underline color must be seal-red var(--accent-primary)"
    );

    // 1px lift with 120ms ease/exit
    assert.ok(
      globalsCss.includes("translateY(-1px)"),
      "Hover/focus state must have 1px lift (translateY(-1px))"
    );
    assert.ok(
      globalsCss.includes("120ms cubic-bezier(0.22, 1, 0.36, 1)"),
      "Lift duration and ease/exit must match 120ms cubic-bezier(0.22, 1, 0.36, 1)"
    );

    // Focus-visible parity
    assert.ok(
      globalsCss.includes(".footer-link:focus-visible"),
      "Must have :focus-visible parity rule"
    );
    assert.ok(
      globalsCss.includes(".footer-link:focus-visible::after"),
      "Must have :focus-visible::after parity rule"
    );
  });

  test("Reduced-motion fallback disables transforms and underline animation", () => {
    assert.ok(
      globalsCss.includes("@media (prefers-reduced-motion: reduce)"),
      "Must include @media (prefers-reduced-motion: reduce) block"
    );
    const reducedMotionBlock = globalsCss.slice(
      globalsCss.indexOf("@media (prefers-reduced-motion: reduce)")
    );
    assert.ok(
      reducedMotionBlock.includes(".footer-link"),
      "Reduced motion block must target .footer-link"
    );
    assert.ok(
      reducedMotionBlock.includes("transform: none"),
      "Reduced motion block must set transform: none"
    );
  });
});

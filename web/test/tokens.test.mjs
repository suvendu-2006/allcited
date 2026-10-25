import { test, describe } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Relative luminance formula per WCAG 2.1
function getLuminance(hex) {
  const cleanHex = hex.replace("#", "");
  const r = parseInt(cleanHex.substring(0, 2), 16) / 255;
  const g = parseInt(cleanHex.substring(2, 4), 16) / 255;
  const b = parseInt(cleanHex.substring(4, 6), 16) / 255;

  const toLinear = (c) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

function getContrastRatio(hex1, hex2) {
  const lum1 = getLuminance(hex1);
  const lum2 = getLuminance(hex2);
  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);
  return (lighter + 0.05) / (darker + 0.05);
}

describe("Design System Tokens Contrast Assertion (§6.1 v2.1 Ink & Ember)", () => {
  test("Light 'Paper' Theme contrast meets WCAG standards", () => {
    const bgBase = "#F5F2EA";
    const inkPrimary = "#1A1918";
    const accentPrimary = "#A6362F";
    const accentCite = "#9A5B00";

    const textRatio = getContrastRatio(inkPrimary, bgBase);
    const primaryRatio = getContrastRatio(accentPrimary, bgBase);
    const citeRatio = getContrastRatio(accentCite, bgBase);

    // Assert contrast levels per §6.1
    assert.ok(textRatio >= 14.0, `Text contrast should be >= 14:1, got ${textRatio.toFixed(2)}`);
    assert.ok(primaryRatio >= 4.5, `Primary seal-red contrast should be >= 4.5:1, got ${primaryRatio.toFixed(2)}`);
    assert.ok(citeRatio >= 4.5, `Citation amber contrast should be >= 4.5:1 (WCAG AA), got ${citeRatio.toFixed(2)}`);
  });

  test("Dark 'Warm Ink' Theme contrast meets WCAG standards", () => {
    const bgBase = "#0D0C0B";
    const inkPrimary = "#EFEAD9";
    const accentPrimary = "#E8765A";
    const accentCite = "#E8B04B";

    const textRatio = getContrastRatio(inkPrimary, bgBase);
    const primaryRatio = getContrastRatio(accentPrimary, bgBase);
    const citeRatio = getContrastRatio(accentCite, bgBase);

    // Assert contrast levels per §6.1
    assert.ok(textRatio >= 14.0, `Dark text contrast should be >= 14:1, got ${textRatio.toFixed(2)}`);
    assert.ok(primaryRatio >= 4.5, `Dark primary lifted-seal contrast should be >= 4.5:1, got ${primaryRatio.toFixed(2)}`);
    assert.ok(citeRatio >= 7.0, `Dark citation amber contrast should be >= 7:1, got ${citeRatio.toFixed(2)}`);
  });

  test("Zero green in base theme tokens (globals.css gate)", () => {
    const cssPath = path.resolve(__dirname, "../src/app/globals.css");
    const css = fs.readFileSync(cssPath, "utf-8");

    // Extract :root and .dark blocks
    const rootBlock = css.match(/:root\s*\{([^}]+)\}/)?.[1] || "";
    const darkBlock = css.match(/\.dark\s*\{([^}]+)\}/)?.[1] || "";
    const baseTokens = rootBlock + "\n" + darkBlock;

    // Disallowed teal/green palette hexes
    const forbiddenGreens = ["#06211D", "#034F46", "#31C7A5", "#041A16", "#0B2A24", "#10352E"];
    for (const green of forbiddenGreens) {
      assert.ok(
        !baseTokens.toLowerCase().includes(green.toLowerCase()),
        `Forbidden green/teal token ${green} found in base theme tokens`
      );
    }
  });
});

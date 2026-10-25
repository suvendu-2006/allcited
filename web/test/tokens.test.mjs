import { test, describe } from "node:test";
import assert from "node:assert";

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

describe("Design System Tokens Contrast Assertion (§3.1 & §3.2)", () => {
  test("Light 'Paper' Theme contrast meets WCAG AA standards", () => {
    const bgBase = "#FAF8ED";
    const inkPrimary = "#16161A";
    const accentPrimary = "#034F46";
    const accentCite = "#A6362F";

    const textRatio = getContrastRatio(inkPrimary, bgBase);
    const primaryRatio = getContrastRatio(accentPrimary, bgBase);
    const citeRatio = getContrastRatio(accentCite, bgBase);

    // Assert contrast levels per §3.1
    assert.ok(textRatio >= 14.0, `Text contrast should be >= 14:1, got ${textRatio.toFixed(2)}`);
    assert.ok(primaryRatio >= 7.0, `Primary teal contrast should be >= 7:1, got ${primaryRatio.toFixed(2)}`);
    assert.ok(citeRatio >= 4.5, `Citation red contrast should be >= 4.5:1 (WCAG AA), got ${citeRatio.toFixed(2)}`);
  });

  test("Dark 'Teal-Ink Night' Theme contrast meets WCAG AA standards", () => {
    const bgBase = "#06211D";
    const inkPrimary = "#F2EFE0";
    const accentPrimary = "#31C7A5";
    const accentCite = "#F08A75";

    const textRatio = getContrastRatio(inkPrimary, bgBase);
    const primaryRatio = getContrastRatio(accentPrimary, bgBase);
    const citeRatio = getContrastRatio(accentCite, bgBase);

    // Assert contrast levels per §3.2
    assert.ok(textRatio >= 13.0, `Dark text contrast should be >= 13:1, got ${textRatio.toFixed(2)}`);
    assert.ok(primaryRatio >= 7.0, `Dark primary teal contrast should be >= 7:1, got ${primaryRatio.toFixed(2)}`);
    assert.ok(citeRatio >= 4.5, `Dark citation red contrast should be >= 4.5:1 (WCAG AA), got ${citeRatio.toFixed(2)}`);
  });
});

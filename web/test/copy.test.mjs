import { test, describe } from "node:test";
import assert from "node:assert";

describe("Frontend Copy Freeze Assertions (§4)", () => {
  test("Exact error strings match §9 error table verbatim", async () => {
    // Dynamic import to verify actual source file export
    const { ERROR_MESSAGES, PRICING_COPY, SAMPLE_QUESTIONS } = await import("../src/lib/copy.ts");

    assert.strictEqual(
      ERROR_MESSAGES.doc_unreadable,
      "Couldn't read that file — corrupt or password-protected. Nothing was saved."
    );
    assert.strictEqual(
      ERROR_MESSAGES.doc_too_large,
      "That's past the size limit for your plan. (Free: 10 MB · Pro: 100 MB.)"
    );
    assert.strictEqual(
      ERROR_MESSAGES.free_tier_busy,
      "Our free brain is swamped right now. Try again in a minute — or plug in your own key in Settings and skip the line."
    );
    assert.strictEqual(
      ERROR_MESSAGES.ollama_unreachable,
      "Can't reach your local Ollama. Is it running? (ollama serve)"
    );
    assert.strictEqual(
      ERROR_MESSAGES.url_blocked,
      "That link points somewhere private — we don't fetch those. Safety thing."
    );
    assert.strictEqual(
      ERROR_MESSAGES.injection_flagged,
      "Heads up: this document contains text trying to give me instructions. I've treated it as data. The answer stands."
    );
    assert.strictEqual(
      ERROR_MESSAGES.plan_limit_reached,
      "That's a Pro move. Upgrade to keep going."
    );
    assert.strictEqual(
      ERROR_MESSAGES.session_expired,
      "This conversation's gone cold. Re-upload the document and we're back."
    );
    assert.strictEqual(
      ERROR_MESSAGES.offline,
      "You're offline. Your last conversation is still here — ask away when you're back."
    );
  });
});

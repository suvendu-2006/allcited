import { test, describe, beforeEach } from "node:test";
import assert from "node:assert";

// Mock localStorage for node environment
const storage = new Map();
globalThis.localStorage = {
  getItem: (key) => storage.get(key) || null,
  setItem: (key, val) => storage.set(key, String(val)),
  removeItem: (key) => storage.delete(key),
  clear: () => storage.clear(),
};
globalThis.window = globalThis;

describe("Free Tier Rate Limiter (10 queries / hour)", async () => {
  const { checkRateLimit, recordFreeQuery, FREE_LIMIT } = await import(
    "../src/lib/rateLimit.ts"
  );

  beforeEach(() => {
    storage.clear();
  });

  test("Initial state allows up to 10 queries", () => {
    const state = checkRateLimit(false);
    assert.strictEqual(state.isRateLimited, false);
    assert.strictEqual(state.remainingQueries, FREE_LIMIT);
    assert.strictEqual(state.resetAt, null);
  });

  test("BYOK users are exempt from rate limiting", () => {
    // Fill storage with 15 queries
    const past = Array.from({ length: 15 }, () => Date.now());
    storage.set("allcited_free_queries", JSON.stringify(past));

    const state = checkRateLimit(true);
    assert.strictEqual(state.isRateLimited, false);
    assert.strictEqual(state.remainingQueries, Infinity);
    assert.strictEqual(state.resetAt, null);
  });

  test("Rate limits exactly after 10 queries in 1 hour", () => {
    for (let i = 0; i < 9; i++) {
      recordFreeQuery(false);
    }
    let state = checkRateLimit(false);
    assert.strictEqual(state.isRateLimited, false);
    assert.strictEqual(state.remainingQueries, 1);

    // 10th query
    recordFreeQuery(false);
    state = checkRateLimit(false);
    assert.strictEqual(state.isRateLimited, true);
    assert.strictEqual(state.remainingQueries, 0);
    assert.ok(state.resetAt && state.resetAt > Date.now());
  });

  test("Expired queries outside 1 hour window are pruned", () => {
    // 10 queries from 2 hours ago
    const twoHoursAgo = Date.now() - 2 * 60 * 60 * 1000;
    const oldQueries = Array.from({ length: 10 }, () => twoHoursAgo);
    storage.set("allcited_free_queries", JSON.stringify(oldQueries));

    const state = checkRateLimit(false);
    assert.strictEqual(state.isRateLimited, false);
    assert.strictEqual(state.remainingQueries, FREE_LIMIT);
  });
});

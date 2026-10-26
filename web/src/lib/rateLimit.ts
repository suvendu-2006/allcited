/**
 * Free Tier Rate Limiter
 * 10 questions per 1-hour sliding window.
 * Excludes BYOK users.
 * Synchronizes across tabs via localStorage.
 */

const STORAGE_KEY = "allcited_free_queries";
const WINDOW_MS = 60 * 60 * 1000; // 1 hour
export const FREE_LIMIT = 10;

export interface RateLimitState {
  isRateLimited: boolean;
  remainingQueries: number;
  oldestQueryTimestamp: number | null;
  resetAt: number | null;
}

export function getFreeQueryTimestamps(): number[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    const now = Date.now();
    return parsed.filter((t): t is number => typeof t === "number" && now - t < WINDOW_MS);
  } catch {
    return [];
  }
}

export function checkRateLimit(isByokActive: boolean): RateLimitState {
  if (isByokActive) {
    return {
      isRateLimited: false,
      remainingQueries: Infinity,
      oldestQueryTimestamp: null,
      resetAt: null,
    };
  }

  const valid = getFreeQueryTimestamps();
  if (valid.length >= FREE_LIMIT) {
    const oldest = Math.min(...valid);
    return {
      isRateLimited: true,
      remainingQueries: 0,
      oldestQueryTimestamp: oldest,
      resetAt: oldest + WINDOW_MS,
    };
  }

  return {
    isRateLimited: false,
    remainingQueries: Math.max(0, FREE_LIMIT - valid.length),
    oldestQueryTimestamp: valid.length > 0 ? Math.min(...valid) : null,
    resetAt: null,
  };
}

export function recordFreeQuery(isByokActive: boolean): RateLimitState {
  if (isByokActive || typeof window === "undefined") {
    return {
      isRateLimited: false,
      remainingQueries: Infinity,
      oldestQueryTimestamp: null,
      resetAt: null,
    };
  }

  const valid = getFreeQueryTimestamps();
  valid.push(Date.now());
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(valid));
  } catch {
    // Ignore storage quota
  }

  return checkRateLimit(false);
}

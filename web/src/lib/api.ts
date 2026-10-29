/**
 * Canonical backend API URL resolver and connection utilities.
 *
 * Guarantees that neither local development nor production deployments
 * will fail by attempting to connect to a non-existent localhost server.
 */

export const PROD_API_URL = "https://subh-007-allcited-api.hf.space";

/**
 * Resolves the active backend API URL:
 * 1. Explicit NEXT_PUBLIC_API_URL environment variable if set.
 * 2. If running in a browser on Vercel / non-localhost domain, always PROD_API_URL.
 * 3. Default fallback is always the hosted Hugging Face backend (PROD_API_URL).
 */
export function getApiUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  // If in browser on production / cloud domain, NEVER use localhost
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    const isLocal = host === "localhost" || host === "127.0.0.1" || host === "0.0.0.0";
    if (!isLocal) {
      if (envUrl && !envUrl.includes("localhost") && !envUrl.includes("127.0.0.1")) {
        return envUrl.replace(/\/$/, "");
      }
      return PROD_API_URL;
    }
  }

  // If explicit environment variable is set (e.g. developer running local backend)
  if (envUrl && envUrl.length > 0) {
    return envUrl.replace(/\/$/, "");
  }

  return PROD_API_URL;
}

/**
 * Asynchronously checks backend health with retry backoff to handle cold starts.
 */
export async function checkBackendHealth(
  apiUrl: string = getApiUrl(),
  retries: number = 3,
  delayMs: number = 2500
): Promise<boolean> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${apiUrl.replace(/\/$/, "")}/v1/health`, {
        cache: "no-store",
      });
      if (res.ok) {
        return true;
      }
    } catch {
      // Failed to reach backend, wait and retry if attempts remain
    }
    if (attempt < retries) {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  return false;
}

import { test, describe, beforeEach } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webSrc = path.resolve(__dirname, "../src");
const pagePath = path.join(webSrc, "app/page.tsx");

describe("Guest Upgrade Flow & Pending Document Preservation (§6)", () => {
  const pageContent = fs.readFileSync(pagePath, "utf-8");

  test("Page logic contains pending save sessionStorage keys and openSignIn trigger", () => {
    // sessionStorage keys
    assert.match(
      pageContent,
      /sessionStorage\.setItem\("allcited_pending_save_session",\s*sessionId\)/,
      "Must record pending session id into sessionStorage"
    );
    assert.match(
      pageContent,
      /sessionStorage\.setItem\("allcited_pending_save_doc",\s*documentName\s*\|\|\s*""\)/,
      "Must record pending document name into sessionStorage"
    );
    // Clerk openSignIn call
    assert.match(
      pageContent,
      /clerk\.openSignIn\(\)/,
      "Must trigger clerk.openSignIn() when unauthenticated user saves to shelf"
    );
  });

  test("Page logic carries pending document across sign-in and purges sessionStorage", () => {
    // Auto-save effect
    assert.match(
      pageContent,
      /sessionStorage\.getItem\("allcited_pending_save_session"\)/,
      "Must check for pending session in auto-save effect"
    );
    assert.match(
      pageContent,
      /sessionStorage\.removeItem\("allcited_pending_save_session"\)/,
      "Must purge pending session from sessionStorage after consuming"
    );
    assert.match(
      pageContent,
      /sessionStorage\.removeItem\("allcited_pending_save_doc"\)/,
      "Must purge pending doc name from sessionStorage after consuming"
    );
    assert.match(
      pageContent,
      /handleSaveToShelf\(\)/,
      "Must invoke handleSaveToShelf() automatically upon sign-in"
    );
  });

  test("Library save API call posts to /v1/library/save with session_id payload and auth header", () => {
    assert.match(
      pageContent,
      /fetch\(`\${apiUrl}\/v1\/library\/save`,\s*\{/,
      "Must call POST /v1/library/save"
    );
    assert.match(
      pageContent,
      /method:\s*"POST"/,
      "HTTP method must be POST"
    );
    assert.match(
      pageContent,
      /body:\s*JSON\.stringify\(\{\s*session_id:\s*sessionId\s*\}\)/,
      "Request body must contain session_id: sessionId"
    );
    assert.match(
      pageContent,
      /Authorization:\s*`Bearer \${token}`/,
      "Must pass Bearer token in headers"
    );
  });

  test("Button text and styles transition to 'Saved to shelf ·' on success", () => {
    assert.match(
      pageContent,
      /<span>\{isSaved \? "Saved to shelf ·" : "Save to shelf"\}<\/span>/,
      "Button label must switch to 'Saved to shelf ·' when isSaved is true"
    );
    assert.match(
      pageContent,
      /isSaved\s*\?\s*"border-accent-primary\/40 bg-accent-primary\/10 text-accent-primary font-semibold"/,
      "Button must show saved style badge on success"
    );
  });

  describe("State Transition Simulation", () => {
    // Mock environment setup
    let storage;
    let clerkSignInCalls;
    let fetchCalls;
    let state;

    beforeEach(() => {
      storage = new Map();
      clerkSignInCalls = 0;
      fetchCalls = [];

      state = {
        sessionId: null,
        documentName: null,
        isSignedIn: false,
        isSaved: false,
        saveToast: null,
        inWorkspace: false,
      };
    });

    const mockStorage = {
      getItem: (k) => storage.get(k) || null,
      setItem: (k, v) => storage.set(k, String(v)),
      removeItem: (k) => storage.delete(k),
    };

    const mockClerk = {
      openSignIn: () => {
        clerkSignInCalls++;
      },
    };

    const mockGetToken = async () => "mock_clerk_jwt_token_12345";

    const mockFetch = async (url, options) => {
      fetchCalls.push({ url, options });
      if (url.endsWith("/v1/library/save")) {
        const body = JSON.parse(options.body);
        if (body.session_id) {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              status: "saved",
              document: { id: body.session_id, filename: "test.pdf" },
            }),
          };
        }
      }
      return { ok: false, status: 400, json: async () => ({ error: "Bad request" }) };
    };

    // Simulated handleSaveToShelf implementation from page.tsx
    const handleSaveToShelf = async () => {
      if (!state.sessionId) return;

      if (!state.isSignedIn) {
        mockStorage.setItem("allcited_pending_save_session", state.sessionId);
        mockStorage.setItem("allcited_pending_save_doc", state.documentName || "");
        mockClerk.openSignIn();
        return;
      }

      try {
        const token = await mockGetToken();
        const res = await mockFetch("http://localhost:8000/v1/library/save", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ session_id: state.sessionId }),
        });

        if (res.ok) {
          state.isSaved = true;
          state.saveToast = "Document saved to your shelf!";
        } else {
          state.saveToast = "Failed to save to shelf";
        }
      } catch {
        state.saveToast = "Could not connect to shelf service";
      }
    };

    // Simulated auto-save useEffect from page.tsx
    const runAutoSaveEffect = async () => {
      if (state.isSignedIn) {
        const pendingSession = mockStorage.getItem("allcited_pending_save_session");
        const pendingDoc = mockStorage.getItem("allcited_pending_save_doc");
        if (pendingSession) {
          if (!state.sessionId) {
            state.sessionId = pendingSession;
            if (pendingDoc) state.documentName = pendingDoc;
            state.inWorkspace = true;
          } else if (pendingSession === state.sessionId) {
            mockStorage.removeItem("allcited_pending_save_session");
            mockStorage.removeItem("allcited_pending_save_doc");
            await handleSaveToShelf();
          }
        }
      }
    };

    test("Guest uploads doc -> clicks 'Save to shelf' -> triggers openSignIn and sets sessionStorage", async () => {
      // 1. Unauthenticated guest uploads doc
      state.sessionId = "session_guest_001";
      state.documentName = "corporate_contract.pdf";
      state.isSignedIn = false;
      state.isSaved = false;

      // 2. User clicks "Save to shelf"
      await handleSaveToShelf();

      // Assertions:
      assert.strictEqual(clerkSignInCalls, 1, "Clerk openSignIn must be called once");
      assert.strictEqual(
        mockStorage.getItem("allcited_pending_save_session"),
        "session_guest_001",
        "Session ID must be preserved in sessionStorage"
      );
      assert.strictEqual(
        mockStorage.getItem("allcited_pending_save_doc"),
        "corporate_contract.pdf",
        "Document name must be preserved in sessionStorage"
      );
      assert.strictEqual(fetchCalls.length, 0, "No network request should occur before authentication");
      assert.strictEqual(state.isSaved, false, "Document must not be marked saved yet");
    });

    test("Guest completes sign-in -> auto-save effect executes POST /v1/library/save and purges storage", async () => {
      // Setup state from previous step
      state.sessionId = "session_guest_001";
      state.documentName = "corporate_contract.pdf";
      state.isSignedIn = false;
      mockStorage.setItem("allcited_pending_save_session", "session_guest_001");
      mockStorage.setItem("allcited_pending_save_doc", "corporate_contract.pdf");

      // 3. User completes Clerk sign-in
      state.isSignedIn = true;

      // 4. Auto-save effect fires
      await runAutoSaveEffect();

      // Assertions:
      assert.strictEqual(fetchCalls.length, 1, "Exactly one save request should be dispatched");
      assert.strictEqual(fetchCalls[0].url, "http://localhost:8000/v1/library/save");
      assert.strictEqual(fetchCalls[0].options.method, "POST");
      assert.strictEqual(
        fetchCalls[0].options.headers["Authorization"],
        "Bearer mock_clerk_jwt_token_12345"
      );
      assert.deepStrictEqual(JSON.parse(fetchCalls[0].options.body), {
        session_id: "session_guest_001",
      });

      // Storage purged
      assert.strictEqual(
        mockStorage.getItem("allcited_pending_save_session"),
        null,
        "allcited_pending_save_session must be purged"
      );
      assert.strictEqual(
        mockStorage.getItem("allcited_pending_save_doc"),
        null,
        "allcited_pending_save_doc must be purged"
      );

      // State updated
      assert.strictEqual(state.isSaved, true, "isSaved must be true");
      assert.strictEqual(state.saveToast, "Document saved to your shelf!");
    });

    test("Redirect recovery flow: preserves session and doc when returning from redirect auth", async () => {
      // Simulate page reload/redirect: in-memory state starts empty, but sessionStorage has pending items
      state.sessionId = null;
      state.documentName = null;
      state.isSignedIn = true;
      mockStorage.setItem("allcited_pending_save_session", "session_redirect_777");
      mockStorage.setItem("allcited_pending_save_doc", "quarterly_earnings.xlsx");

      // First effect run: restores session and doc into component state
      await runAutoSaveEffect();
      assert.strictEqual(state.sessionId, "session_redirect_777");
      assert.strictEqual(state.documentName, "quarterly_earnings.xlsx");
      assert.strictEqual(state.inWorkspace, true);

      // Second effect run: consumes pending session and calls handleSaveToShelf
      await runAutoSaveEffect();

      assert.strictEqual(fetchCalls.length, 1);
      assert.deepStrictEqual(JSON.parse(fetchCalls[0].options.body), {
        session_id: "session_redirect_777",
      });
      assert.strictEqual(mockStorage.getItem("allcited_pending_save_session"), null);
      assert.strictEqual(mockStorage.getItem("allcited_pending_save_doc"), null);
      assert.strictEqual(state.isSaved, true);
    });

    test("Mismatched session safety: does not save if pendingSession does not match active sessionId", async () => {
      state.sessionId = "session_active_current";
      state.documentName = "current.pdf";
      state.isSignedIn = true;
      mockStorage.setItem("allcited_pending_save_session", "session_different_old");
      mockStorage.setItem("allcited_pending_save_doc", "old.pdf");

      await runAutoSaveEffect();

      assert.strictEqual(fetchCalls.length, 0, "Must not auto-save a mismatched session");
      assert.strictEqual(state.isSaved, false);
      // Pending session remains untouched for safety
      assert.strictEqual(
        mockStorage.getItem("allcited_pending_save_session"),
        "session_different_old"
      );
    });

    test("Already signed-in user saves directly without touching openSignIn or sessionStorage", async () => {
      state.sessionId = "session_auth_456";
      state.documentName = "manual.pdf";
      state.isSignedIn = true;

      await handleSaveToShelf();

      assert.strictEqual(clerkSignInCalls, 0, "openSignIn must not be called");
      assert.strictEqual(mockStorage.getItem("allcited_pending_save_session"), null);
      assert.strictEqual(mockStorage.getItem("allcited_pending_save_doc"), null);
      assert.strictEqual(fetchCalls.length, 1);
      assert.deepStrictEqual(JSON.parse(fetchCalls[0].options.body), {
        session_id: "session_auth_456",
      });
      assert.strictEqual(state.isSaved, true);
    });
  });
});

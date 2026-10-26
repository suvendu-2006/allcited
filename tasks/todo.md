# Master Implementation Plan: Audit Remediation, Hardening & Supabase Persistence

## Phase 1: Critical Security & Authentication Hardening
- [x] Task 1.1: Eliminate Clerk Authentication Bypass (`SEC-01`) in `api/app/auth.py`
- [x] Task 1.2: Defeat SSRF DNS Rebinding & Stream Payloads (`SEC-02`, `SEC-03`) in `api/app/security/ssrf.py`
- [x] Task 1.3: Eliminate Hardcoded Stripe Fallback Secret (`SEC-05`) in `api/app/payments.py`
- [x] Checkpoint: Run Phase 1 security unit tests

## Phase 2: Ingestion & Pipeline Defense
- [x] Task 2.1: Prompt Injection Delimiter Neutralization (`SEC-04`) in `api/app/security/guards.py`
- [x] Task 2.2: Unicode Multilingual Tokenizer for BM25 (`QUAL-01`) in `api/app/pipeline/indexes.py`
- [x] Task 2.3: Chunker Sentence Hard-Splitting & Deduplication (`LOGIC-01`) in `api/app/pipeline/chunker.py`
- [x] Checkpoint: Run Phase 2 retrieval and chunking tests

## Phase 3: File Ingestion, Size Caps & Server Stability
- [x] Task 3.1: Enable 100 MB Uploads for Pro Users (`FUNC-01`, `Item 10`) in `api/app/sessions.py`, `api/app/main.py`, `web/src/components/Upload.tsx`
- [x] Task 3.2: Graceful Error Handling for Corrupt PDF Uploads (`FUNC-02`) in `api/app/sessions.py`
- [x] Checkpoint: Run Phase 3 file upload & plan tests

## Phase 4: Concurrency, Async Architecture & Supabase Persistence
- [x] Task 4.1: Thread-Safe Semantic Cache (`PERF-02`) in `api/app/cache.py`
- [x] Task 4.2: Asynchronous Supabase Synchronization (`PERF-01`) in `api/app/library.py`
- [x] Task 4.3: Non-Blocking Telegram Webhook Handler (`INT-01`) in `api/app/telegram.py`
- [x] Task 4.4: Bounded Trace Record Store (`Item 18`) in `api/app/trace.py`
- [x] Task 4.5: Supabase Persistence for Subscriptions & Sessions (`DATA-01`) in `api/app/payments.py`, `api/app/sessions.py`
- [x] Checkpoint: Run Phase 4 concurrency, cache, and payment tests

## Phase 5: Client Contracts & Frontend Hardening
- [x] Task 5.1: Pass Bearer Auth Tokens in Frontend SSE Queries (`FUNC-03`) in `web/src/lib/sse.ts`, `web/src/components/Chat.tsx`
- [x] Task 5.2: Normalize MapReduce Event Schema Contract (`FUNC-04`) in `api/app/pipeline/mapreduce.py`, `web/src/lib/sse.ts`
- [x] Task 5.3: Prune Spurious Frontend Dependencies (`DEP-01`) in `web/package.json`
- [x] Task 5.4: Robust JSON Array Parsing for CORS Configuration (`Item 1`) in `api/app/config.py`
- [x] Final Checkpoint: Full end-to-end test suite (`pytest` + `npm test` + `npm run build`)

## Phase 6: CI Hardening & Remote Test Parity
- [x] Task 6.1: Hermetic NVIDIA fallback in `api/tests/test_llm.py`
- [x] Task 6.2: Mocked candidate directory resolution in `api/tests/test_ocr.py`
- [x] Task 6.3: Fallback mock test environment variables and `npm test` step in `.github/workflows/ci.yml`
- [x] Checkpoint: Zero failures across isolated envs and full suites

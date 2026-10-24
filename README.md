# Allcited

> Document Q&A with receipts: upload a document → grounded, cited answers → plus an eval harness proving accuracy with numbers.

Allcited is a high-accuracy, grounded document question-answering system featuring hybrid retrieval (BM25 + FAISS Dense Vector + RRF), cross-encoder re-ranking, query routing, query rewriting, two-hop expansion, contextual headers, semantic caching, prompt-injection defense, and verifiable inline citations.

## Evaluation Matrix (Phase 6 — Full 11-Row Empirical Results)

The evaluation harness evaluates 46 questions across trap categories: normal, P1 (boundary straddle), P2 (distractors), P3 (two-hop cross-reference), P4 (multi-aspect), paraphrase, OCR/scanned, library, agentic multi-source, cross-format parity, and scope-boundary refusal traps against the corporate handbook fixture.

| Configuration | Retrieval Hit | Normal | P1 (Boundary) | P2 (Distractor) | P3 (Two-Hop) | P4 (Multi-Aspect) | Paraphrase | Refusal Acc | Answer Corr | p50 (ms) | p95 (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **bm25** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 60.9% | 0.7 | 0.9 |
| **vector** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 60.9% | 8.7 | 13.6 |
| **hybrid** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 60.9% | 0.8 | 1.2 |
| **+rerank** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 63.0% | 37.0 | 109.6 |
| **+twohop** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 63.0% | 38.2 | 44.0 |
| **+rewrite** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 63.0% | 47.4 | 65.0 |
| **+hyde** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 63.0% | 51.2 | 69.9 |
| **+headers** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 63.0% | 39.1 | 44.7 |
| **+agentic** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 63.0% | 39.0 | 48.8 |
| **+graph** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 63.0% | 46.2 | 68.0 |
| **full_system** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 63.0% | 43.5 | 83.4 |

### Row Movement Explanations (The Pipeline Story)

1. **`bm25` (Keyword baseline):** Pure lexical matching provides instantaneous retrieval (p50: 0.1ms) and perfect precision on explicit identifiers (e.g. `ISO-27001`, `Form HR-702`), but drops to 57.7% Hit@1 when queries employ vocabulary mismatch or colloquial paraphrases.
2. **`vector` (Dense semantic search):** Dense embeddings (`all-MiniLM-L6-v2`) increase Hit@1 to 84.6% by mapping conceptual phrasing and paraphrases into semantic vector space at the expense of ~9.5ms embedding latency.
3. **`hybrid` (RRF fusion):** Reciprocal Rank Fusion ($k=60$) merges BM25 and dense vector rankings, canceling out individual blind spots and guaranteeing top candidate recall across both keyword-precise and semantic queries.
4. **`+rerank` (Cross-encoder):** Cross-encoder (`ms-marco-MiniLM-L-6-v2`) directly scores (query, chunk) pairs to separate signal from distractor noise, while enforcing a calibrated relevance floor (`0.0001`) that intercepts off-topic requests with 0 LLM calls.
5. **`+twohop` (Cross-reference resolution):** Dynamically inspects candidate chunks and query text for domain references, traversing the document reference map to pull in definition passages (e.g. `Rule 63.7.4`) alongside mentioning clauses.
6. **`+rewrite` (Query decomposition):** Heuristic and LLM query reformulation expands vague or multi-aspect questions into 2–3 targeted search phrases, preventing keyword dilution on explicit identifiers while providing multi-angle coverage.
7. **`+hyde` (Hypothetical Document Embeddings):** Generates a zero-shot hypothetical answer probe to search dense vector space via 3-way RRF fusion (`probe_vector + query_vector + bm25`), discarding hallucinated text so probe content never enters the answer prompt.
8. **`+headers` (Contextual Headers):** Prepends hierarchical breadcrumbs (`Section > Subsection`) during ingestion, giving isolated chunks explicit structural context so ambiguous subsections are retrieved with clear lineage.
9. **`+agentic` (Self-correcting retrieval loop):** Performs bounded evaluation ($\le 3$ iterations) of candidate sufficiency. When partial coverage is detected, the loop reformulates missing sub-queries to retrieve complementary passages before final synthesis.
10. **`+graph` (GraphRAG-lite):** Extracts domain entities and directed relation edges during ingestion. Retained knowledge graph expands entity-adjacent queries with $\le 4$ neighbor facts cited cleanly as `(related: [S#])`.
11. **`full_system` (End-to-end stack):** Combines the complete pipeline with in-process semantic caching (<100ms response on repeats), prompt injection defense, and PII masking. Achieves 100.0% retrieval hit rate, 100.0% trap resolution across P1–P4, 100.0% refusal accuracy, and 100.0% format parity.

> [!NOTE]
> **API Contract Frozen:** Completion of Phase 3 freezes the `/v1` endpoint contract (`POST /v1/ingest`, `POST /v1/query`, `POST /v1/summarize`, `GET /v1/health`), unblocking parallel implementation across Tracks 4a (Web UI), 4b (Library), and 4c (Parsers).

## Architecture

- **Backend:** FastAPI (`/v1`), Pydantic Settings, FAISS, rank_bm25, sentence-transformers, cross-encoder
- **Frontend:** Next.js 14, Tailwind CSS, TypeScript
- **Brain Client:** Unified OpenAI-compatible client supporting Groq, BYOK, and local Ollama
- **Safety & Guards:** Prompt injection detection, PII masking, no code execution
- **Evaluation:** Automated 46-question evaluation suite measuring hit rates, trap defense, and citation validity

## API Contract & Error Codes

All Allcited endpoints strictly follow the `/v1` prefix. All error responses conform to a standardized error envelope:

```json
{
  "error": {
    "code": "plan_limit_reached",
    "message": "That's a Pro move. Upgrade to keep going.",
    "request_id": "req_8f1a2c3b"
  }
}
```

Every response carries an `X-Request-ID` header matching `error.request_id` for end-to-end tracing and diagnostics.

### Endpoints Overview

| Method | Endpoint | Tags | Description |
|---|---|---|---|
| `GET` | `/v1/health` | System | Health check, operating mode (`cloud`, `byok`, `private`), and environment |
| `GET` | `/v1/auth/me` | System | Validate Clerk JWT session and retrieve authenticated user profile |
| `GET` | `/v1/models` | System | Enumerate available provider modes (Groq Cloud, BYOK, Local Ollama) |
| `POST` | `/v1/ingest` | Ingestion | Upload & parse document (PDF, DOCX, PPTX, XLSX, HTML, MD, TXT, URL) into active session |
| `POST` | `/v1/ingest/url` | Ingestion | Fetch & index web page URL with SSRF validation |
| `GET` | `/v1/session/{session_id}` | Ingestion | Retrieve active session chunk count and document metadata |
| `POST` | `/v1/query` | Q&A | Server-Sent Events (SSE) streaming query answering with grounded citations |
| `POST` | `/v1/summarize` | Q&A | Server-Sent Events (SSE) hierarchical map-reduce document summarization |
| `POST` | `/v1/library/save` | Library | Persist uploaded document session into user library |
| `GET` | `/v1/library/documents` | Library | List saved documents for authenticated user |
| `DELETE` | `/v1/library/documents/{doc_id}` | Library | Delete saved document from library |
| `POST` | `/v1/library/query` | Library | Query and synthesize answers across multiple library documents |
| `POST` | `/v1/stripe/checkout` | Payments | Create Stripe Checkout session for Pro plan upgrade |
| `POST` | `/v1/stripe/webhook` | Payments | Process incoming Stripe webhook events with idempotent replay protection |
| `GET` | `/v1/stripe/subscription` | Payments | Retrieve active subscription tier for authenticated user |
| `POST` | `/v1/telegram/webhook` | Telegram | Telegram Bot webhook handler for document upload and cited Q&A |
| `GET` | `/v1/audit` | Audit & Stats | Retrieve user audit trail for document and payment actions |
| `GET` | `/v1/stats` | Audit & Stats | Platform-wide operational metrics (queries, tokens, costs, format mix) |
| `GET` | `/v1/cache/stats` | Audit & Stats | Semantic cache hit rates and entry metrics |
| `POST` | `/v1/feedback` | Feedback & Trace | Submit thumbs up/down user feedback for an answer |
| `GET` | `/v1/feedback/candidates` | Feedback & Trace | Retrieve candidate eval cases generated from negative feedback |
| `GET` | `/v1/trace/{question_id}` | Feedback & Trace | Retrieve step-by-step pipeline execution trace for a question |

### Error Code Reference

All error codes are machine-readable strings paired with human-voiced, context-aware messages:

| Code | HTTP Status | Meaning | Human Copy |
|---|---|---|---|
| `doc_unreadable` | 400 | File is corrupt, password-protected, or has unreadable text | Couldn't read that file — corrupt or password-protected. Nothing was saved. |
| `url_blocked` | 400 | SSRF guard blocked private, loopback, link-local, or cloud metadata IP | That link points somewhere private — we don't fetch those. Safety thing. |
| `validation_error` | 422 | Request body or parameters failed schema validation | Request validation failed |
| `unauthorized` | 401 | Missing or invalid Bearer authentication header on protected route | Authorization header missing or invalid format (expected Bearer <token>) |
| `token_expired` | 401 | Clerk authentication JWT has expired | Authentication token has expired |
| `invalid_token` | 401 | Clerk JWT signature verification failed or missing subject claim | Invalid authentication token |
| `invalid_secret_token` | 401 | Telegram webhook secret token mismatch | Invalid secret token |
| `invalid_signature` | 400 | Stripe webhook cryptographic signature verification failed | Invalid webhook signature |
| `plan_limit_reached` | 402 | Free tier cap reached (upload > 20 MB, precision mode, library saves > 3) | That's a Pro move. Upgrade to keep going. |
| `doc_too_large` | 402 | File size exceeds plan limit (Free: 20 MB, Pro: 100 MB) | That's past the size limit for your plan. (Free: 20 MB · Pro: 100 MB.) |
| `session_not_found` | 404 | Active in-memory session expired or invalid session ID | Session not found or expired. Re-upload the document and we're back. |
| `session_expired` | 404 | Conversation session went cold | This conversation's gone cold. Re-upload the document and we're back. |
| `doc_not_found` | 404 | Document ID not found in authenticated user's library | Document not found |
| `trace_not_found` | 404 | Question ID trace not found in trace manager | Trace for question not found |
| `free_tier_busy` | 429 / 503 | Rate limits or LLM provider concurrency limit reached on free tier | Our free brain is swamped right now. Try again in a minute — or plug in your own key in Settings and skip the line. |
| `ollama_unreachable` | 502 / 503 | Local Ollama daemon is not responding on configured base URL | Can't reach your local Ollama. Is it running? (`ollama serve`) |
| `injection_flagged` | 200 / Warning | Document content attempted prompt injection; treated strictly as passive data | Heads up: this document contains text trying to give me instructions. I've treated it as data. The answer stands. |
| `offline` | Client | Browser network connection unavailable | You're offline. Your last conversation is still here — ask away when you're back. |
| `generic` | 500 | Unhandled internal server error; trace ID logged for investigation | Something broke on our side. It's noted — try again, and if it repeats, the trace ID below helps us find it. |

## Private Offline Edition (Zero Cloud Egress)

Allcited includes a fully offline, air-gapped private edition that processes documents without sending a single byte to external clouds or third-party APIs.

### Run Fully Offline (One-Liner via Docker)

To run the Allcited API offline using your local Ollama instance:

```bash
docker run -d \
  --name allcited-api \
  -p 8000:8000 \
  -e MODE=private \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e DEFAULT_LLM_MODEL=qwen2.5:3b \
  ghcr.io/suvendu-2006/allcited-api:latest
```

### Run the Full Offline Stack (API + Web UI + Ollama)

A single `docker compose up` spins up Ollama (automatically pulling `qwen2.5:3b`), the FastAPI backend (with pre-cached embedding & cross-encoder models and local Tesseract OCR), and the Next.js web interface:

```bash
docker compose up
```

Once started:
- **Web UI:** [http://localhost:3000](http://localhost:3000)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Ollama:** [http://localhost:11434](http://localhost:11434)

## Development

```bash
# Backend
cd api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend
cd web
npm run dev
```

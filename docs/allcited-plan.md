# Allcited — Complete Build Plan, FULL SCOPE + MNC-PARITY (Plan Only, No Code)

> Document Q&A with receipts: upload a document → grounded, cited answers → **plus an eval harness that proves accuracy with numbers.**
> **Scope:** all features committed (no v1/future split), **plus an audit against enterprise RAG checklists (§12)** that adopted 10 more capabilities. **33 features · dependency-ordered build (agent-assisted) · ₹0 throughout.**

---

## 0. Decisions log

| ID | Decision |
|----|----------|
| D-01..D-12 | session-only anonymous mode + FAISS in RAM; hybrid BM25+vector RRF; small reranker `ms-marco-MiniLM-L-6-v2`; router; map-reduce; one OpenAI-compatible brain client (Groq default / BYOK / Ollama); BYOK keys browser-only; Ollama = local mode; Clerk gates saving not chatting; Next.js on Vercel + FastAPI on HF Spaces (Render backup); eval harness is the quality gate |
| D-15 | All previously parked features promoted; no FUTURE.md |
| D-16..D-24 | semantic cache (in-process LRU @0.96) · contextual headers (LLM, fallback-safe) · HyDE (RRF-merged probe) · Supabase saved library (pgvector, Clerk-scoped) · Stripe test-mode Free/Pro plans · privacy Docker edition (api+web+Ollama) · agentic loop (≤3 iters) · Tesseract OCR (eng+hin) · Telegram bot (webhook) |
| D-25 | **MNC-parity audit adopted (§12):** prompt-injection guard + PII redaction in logs; feedback loop; per-question trace; GraphRAG-lite; metadata + query filters; delta re-ingest; PPTX/XLSX/HTML-URL parsers; prompt registry; `/v1` prefix; stats + audit endpoints |
| D-26 | Org-scale enterprise items (SSO/SAML, source-ACL inheritance, multi-region HA, compliance certs, A/B platform, labeling tooling, managed observability stack, connector syncs) are **consciously excluded as company-scale, not product-scale** — excluded by design, not deferred (§12.2) |

**Feature count:** original 14 + 9 promoted + 10 MNC-parity = **33.**

---

## 1. Architecture (full scope)

```
Clients:  Web (Next.js/Vercel) · Telegram bot (webhook) · local Docker edition
              │ REST /v1 + SSE                     │ webhook
FastAPI /v1 — HF Spaces (2 vCPU/16 GB)  [Render 512 MB backup]
  ├── parsers: PDF(+OCR) · DOCX · PPTX · XLSX · MD/TXT · HTML/URL(SSRF-guarded)
  ├── pipeline: chunk(+contextual headers) → refmap → entities(GraphRAG-lite)
  │            → embed → index (FAISS+BM25 session / pgvector library)
  │            query: router → cache? → rewrite+HyDE → hybrid+agentic(+graph
  │            expansion) → rerank → two-hop → grounded answer / map-reduce
  ├── guards: injection-defence on chunk text · PII-masked logs · per-question trace
  ├── semantic cache (in-process LRU @0.96) · feedback · stats · audit
  ├── Stripe webhooks → plan middleware (Free/Pro gates server-side)
  └── brain: Groq free │ BYOK │ Ollama (local/Docker edition)
Storage: Supabase (library, subscriptions, feedback, audit, graph) · prompts/ registry
```

**What leaves the server, honestly:** retrieved chunk texts + question travel to the brain provider per uncached answer (logs are PII-masked). Local/Docker edition with Ollama: nothing leaves. Stated verbatim in README.

---

## 2. Repository layout

```
papertrail/
├── api/app/
│   ├── main.py config.py sessions.py          # /v1 router, CORS(Vercel), limits
│   ├── pipeline/
│   │   ├── parsers/ pdf.py(+ocr) docx.py pptx.py xlsx.py html.py md_txt.py
│   │   ├── chunker.py(+header gen) refmap.py graph.py embed.py indexes.py
│   │   ├── router.py rewrite.py hyde.py retrieve.py rerank.py twohop.py
│   │   ├── answer.py mapreduce.py agentic.py
│   ├── cache.py trace.py                      # semantic LRU · per-question JSONL trace
│   ├── guards.py                              # injection defence · PII masking
│   ├── library/ payments.py telegram.py stats.py audit.py
│   ├── llm/ (client.py provider.py)  security/ (headers.py limits.py ssrf.py)
│   └── prompts/                               # versioned prompt registry (hash logged)
├── web/ (Next.js: chat, source panel, library, pricing, settings, feedback UI, trace viewer)
├── docker/ (privacy edition compose + Dockerfile with tesseract + models)
├── eval/ (questions.json 44 questions · fixtures: handbook PDF + DOCX twin + PPTX + scanned PDF · results/)
└── .github/workflows/ci.yml
```

---

## 3. Module specs

### 3.0 Document format layer

| Format | Parser | Notes |
|---|---|---|
| PDF | PyMuPDF + Tesseract OCR fallback (eng+hin) | page markers; font/heading heuristics; OCR cited as "(OCR)" |
| DOCX | python-docx | exact heading-style section tree (stronger than PDF heuristics); tables → markdown rows; citations = heading path |
| PPTX | python-pptx | slide = chunk basis; slide titles = parents; speaker notes included |
| XLSX | openpyxl | sheet → header + row-window chunks (25 rows); numeric cells preserved; formulas as text |
| MD / TXT | built-in | `#` headings = section tree |
| HTML / URL | httpx + readability, **SSRF guard** (block private IPs, re-validate redirects, 2 MB cap) | readable-text extraction; URL is a first-class upload type |

Shared contract: `[{text, section_path[], page?, source}]`; chunker is format-agnostic. Limits stated: DOCX images/footnotes not parsed; PDFs with images-as-text need OCR path. Corrupt/password files → `doc_unreadable`.

### 3.1 The 9 promoted features
As previously specified: semantic cache (@0.96, per-doc invalidation, "instant · cached" badge) · contextual headers (batched LLM, fallback-safe) · HyDE (probe RRF-merged) · Supabase library (`saved_documents`, `saved_chunks vector(384)` HNSW, `subscriptions`; Clerk JWT verified server-side) · Stripe test-mode plans (Pro = precision mode, 100 MB docs, unlimited saves; webhook idempotent) · privacy Docker edition (`MODE=private`, Ollama pulls `qwen2.5:3b`) · agentic loop (judge sufficiency, ≤3 iters, "best available sources" note) · OCR · Telegram bot (message-edit streaming, 4096-char chunking, webhook secret).

### 3.2 The 10 MNC-parity additions (from §12 audit)

1. **Prompt-injection guard (`guards.py`)** — retrieved chunk text enters prompts inside delimited blocks labeled data-not-instructions; instruction-looking sentences in sources are neutralized + flagged in trace. MNCs never skip this; neither do we.
2. **PII masking in logs** — emails/phones/IDs matched and masked before any log line; stored answers untouched.
3. **Feedback loop** — `POST /v1/feedback` (👍/👎 + note) → Supabase `feedback`; downvoted questions become eval candidates. Closes the online quality loop the offline eval can't see.
4. **Per-question trace (`trace.py`)** — one JSONL per query: route label, sub-queries, candidate counts per stage, rerank scores, two-hop/graph additions, final citations, latencies, tokens, provider. UI: "Why this answer?" viewer. Our observability without a Grafana cluster.
5. **GraphRAG-lite (`graph.py`)** — entities extracted at ingestion (batched LLM); `graph_nodes/graph_edges` in Supabase; retrieval expands top chunks' entities → ≤4 neighbor facts, cited as "(related: …)". *(Restores a feature dropped in an earlier rewrite — audit catch.)*
6. **Metadata + query filters** — chunks carry `format, section, created, tags`; query API accepts filters; UI chips ("only DOCX", "this section").
7. **Delta re-ingest** — per-chunk content hash; re-upload of same doc upserts changed chunks only (skips re-embedding unchanged).
8. **Prompt registry (`prompts/`)** — versioned files; hash logged per answer; diffs explain behavior changes in evals.
9. **`/v1` API prefix + version header policy** — additive-change discipline from day one.
10. **Stats + audit** — `GET /v1/stats` (questions, cache hit-rate, tokens, est. cost, format mix) and Supabase `audit_log` (saves/deletes/payments/key-adds).

### 3.3 Answer contract & out-of-scope requests

- **Contract (one rule, everywhere):** answer ONLY from labeled sources; every claim carries a `[S#]` marker; not covered ⇒ refusal. This single rule blocks both hallucinated content *and* off-topic generation — the trust boundary that makes the system deployable.
- **Document-grounded codegen is in scope:** "write code implementing §4.2's formula" is normal grounded generation — markdown code blocks allowed, code must follow the cited rules, citation post-pass unchanged.
- **Off-topic requests ("write me a Python scraper" with an HR manual loaded):** low-relevance retrieval ⇒ **friendly refusal**, styled distinctly in the UI: *"I answer only from your uploaded document — ask me about it. (Want code? Upload a Python reference and I'll write code grounded in it.)"* — refusal doubles as a feature redirect.
- **Hard safety line: the system writes code, never executes it.** No code-execution tool exists in Allcited, period.

---

## 4. API surface (`/v1`)

| Route | Method | Auth | Purpose |
|---|---|---|---|
| `/v1/ingest` | POST | – (session) / Clerk (library save) | upload pdf/docx/pptx/xlsx/md/txt/url |
| `/v1/query` · `/v1/summarize` | POST | – | SSE pipeline (events: route→cache→rewrite→retrieve→rerank→expand→tokens→citations→done/error) |
| `/v1/feedback` | POST | – | 👍/👎 + note |
| `/v1/trace/{question_id}` | GET | – | the JSONL trace |
| `/v1/library` `/{id}` `/ask` | GET/POST/DELETE/POST | Clerk | saved docs; pgvector Q&A |
| `/v1/stripe/checkout` `/webhook` | POST | Clerk / signature | plans |
| `/v1/telegram/webhook` | POST | secret token | bot |
| `/v1/me` `/v1/stats` `/v1/models` `/v1/health` `/v1/session` | GET | mixed | profile+plan · counters · modes · liveness · evict |

Error envelope `{error:{code,message,request_id}}`; codes now include `plan_limit_reached`, `doc_unreadable`, `url_blocked` (SSRF), `injection_flagged`.

## 5. Frontend additions
Trace viewer ("Why this answer?") · feedback buttons on every answer · filter chips · PPTX/XLSX/URL in the upload tray · Telegram link card · cached-answer badge.

## 6. Failure-case matrix (delta)
injection-looking source content (neutralized + trace flag, answer continues) · SSRF attempt on URL ingest (`url_blocked`) · XLSX with merged/complex sheets (row-window fallback, noted) · graph expansion pollutes context (≤4 facts cap, cited) · Stripe webhook replay (idempotent) · Telegram flood limits (queue) · trace write failure (answer unaffected, log only) · corrupt files (`doc_unreadable`, nothing half-indexed) · OCR garbage (low-confidence caveat) · header-gen failure (fallback) · Supabase outage (library 503, chat unaffected) · agentic oscillation (≤3 iters) · cache staleness (per-doc invalidation on re-ingest) · off-topic generation request (friendly refusal + redirect — never general-chat mode) · document-grounded codegen (allowed, cited, never executed).

## 7. Eval harness
**46 questions:** 30 original (incl. P1–P4 traps, paraphrase, absent-refusal) + 4 scanned-PDF/OCR + 3 library-scope + 3 agentic-multi-source + **4 cross-format parity** + **2 scope-boundary** (an off-topic generation request must be refused-friendly; a document-grounded codegen request must succeed with citations).
Matrix: BM25 · vector · hybrid · +rerank · +twohop · +rewrite · +HyDE · +headers · +agentic · +graph · **full system** (cache hit-rate reported separately). Gates: full ≥85% retrieval hit-rate, ≥50% per trap category, refusal ≥75%, **cross-format parity ≥90% answer equivalence**.

## 8. Testing (delta)
guards unit (injection fixtures, PII mask fixtures) · parsers per-format fixtures + parity test · SSRF unit (private-IP fixtures) · graph cap test · delta-ingest test (hash upsert) · feedback + trace round-trip · Stripe replay idempotency · Telegram parse/flood · library user-scoping test (B never reads A) · agentic termination ≤3.

## 9. Deployment (₹0)
Web: Vercel · API: HF Spaces (primary) / Render (backup) · Supabase free (DB/JWKS/storage/audit) · Stripe test keys · Telegram token+webhook · GHCR image for Docker edition · keep-alive ping · env adds: `SUPABASE_*`, `STRIPE_*`, `TELEGRAM_*`, `OCR_LANGS`, `CACHE_THRESHOLD`, `GUARDS=on`, `GRAPH_MAX_EXPANSION=4`.

## 10. Build order (dependency-ordered; parallelizable with agents)

| Order | Phase |
|---|---|
| 1 | core retrieval: pdf/md/txt parse → chunk(+overlap+parents) → embed → FAISS+BM25 → hybrid RRF |
| 2 | answering: brain client (3 modes), router, rewrite, rerank, two-hop, grounded answer, citation post-pass, SSE |
| 3 | eval harness v1 + README table — **freezes the API contract for parallel tracks** |
| 4a | web UI (chat, chips, source panel, upload, settings) — *parallel track* |
| 4b | Clerk + Supabase library (save/list/ask-my-library) — *parallel track* |
| 4c | format expansion: docx/pptx/xlsx/html-url + delta ingest — *parallel track* |
| 5 | guards (injection + PII) + trace + feedback |
| 6 | headers · HyDE · cache · agentic · graph-lite → **eval v2, full matrix** |
| 7 | payments + plan gates + pricing page |
| 8 | OCR + Telegram |
| 9 | stats + audit + prompts registry + `/v1` hygiene |
| 10 | privacy Docker edition + deploy all + demo GIF + README |

Agent parallelism rule: tracks 4a/4b/4c may run concurrently **only after** order-3 freezes the API contract; everything from order 5 onward is sequential (it modifies the pipeline all tracks share).

## 11. Definition of done
`/v1` live on free stack answering with citations across all 6 input formats · eval table (11-row matrix) with real numbers in README · BYOK + Ollama + library + plans + Telegram + trace + feedback demonstrable in one session · `docker compose up` runs the private edition · guards on, logs PII-masked, no secrets in repo · every README claim backed by a table row.

---

## 12. MNC-parity audit (the review this plan was re-checked against)

### 12.1 Standard enterprise RAG checklist → our status

| Enterprise capability | MNCs | Allcited |
|---|---|---|
| Multi-format ingestion (pdf/docx/pptx/xlsx/html) | ✅ | ✅ all six + URL |
| OCR for scans | ✅ | ✅ Tesseract |
| Hybrid retrieval (keyword+dense) + re-ranking | ✅ | ✅ BM25+FAISS+cross-encoder |
| Query understanding (rewrite, HyDE, routing) | ✅ | ✅ all three |
| Chunking strategy + parent-child + contextual headers | ✅ | ✅ |
| Semantic cache | ✅ | ✅ @0.96 |
| Agentic/iterative retrieval + knowledge-graph expansion | ✅ | ✅ loop ≤3 + GraphRAG-lite |
| Grounded generation + citation verification + refusal | ✅ | ✅ post-pass |
| Guardrails: prompt-injection defence, PII redaction | ✅ | ✅ **added by this audit** |
| Evaluation harness (retrieval + answer metrics) | ✅ | ✅ 44-question suite (our differentiator) |
| Online feedback capture | ✅ | ✅ **added** |
| Tracing / explainability per request | ✅ | ✅ JSONL trace + viewer **added** |
| Prompt versioning | ✅ | ✅ registry **added** |
| Multi-tenancy / per-user isolation | ✅ | ✅ Clerk-scoped library (+isolation tests) |
| Auth + entitlements/plans | ✅ | ✅ Clerk + Stripe gates |
| Rate limiting + cost metering | ✅ | ✅ per-IP + token/cost logs + stats |
| Incremental ingestion / dedupe | ✅ | ✅ hash dedupe + delta upsert **added** |
| API versioning + typed contracts | ✅ | ✅ `/v1` + OpenAPI |
| Audit logging | ✅ | ✅ audit table **added** |

### 12.2 Consciously excluded (company-scale, not product-scale) — excluded by design, not deferred

| Excluded | Why it doesn't belong here |
|---|---|
| SSO/SAML/SCIM, RBAC hierarchies, admin consoles | org identity infrastructure; Clerk covers real auth needs |
| ACL inheritance from SharePoint/Confluence/Drive connectors | requires being *inside* the company; connector syncs are MNC-scale integrations |
| Multi-region HA / DR runbooks / 99.99% SLAs | single free-tier deployment is the honest architecture at this stage |
| Compliance programs (SOC2, GDPR-DPA processes, data residency) | organizational certifications, not code |
| Online A/B experimentation platform | needs traffic volume our eval-offline approach replaces |
| Human labeling team tooling | needs a team |
| Prometheus/Grafana/OTel stack | replaced by per-question traces + /stats at this scale |
| Managed vector-DB clustering | pgvector + FAISS are the right size; clustering solves problems we don't have |

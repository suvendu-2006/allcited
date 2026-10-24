# Allcited — Build Progress

## Current Status
- **Phase Completed:** PHASE 2 — ANSWERING (THE PIPELINE) [STEPS 11–17]
- **Current Step:** STEP 18 — Question set (Phase 3: EVAL v1)
- **Completed Steps:**
  - [x] STEP 01 — Repo + monorepo skeleton (clean git status, pushed to GitHub)
  - [x] STEP 02 — Python environment + API skeleton (uvicorn serves /v1/health = 200, ruff clean, pytest green)
  - [x] STEP 03 — Config + secrets hygiene (pydantic-settings config, .env.example, gitleaks pre-commit hook active)
  - [x] STEP 04 — Web scaffold + connectivity (Next.js 14, Tailwind CSS, shadcn, Clerk SDK, /v1/health CORS connection verified)
  - [x] STEP 05 — Parsers: PDF + MD/TXT (PyMuPDF heading heuristics, ParsedBlock contract, handbook.pdf fixture)
  - [x] STEP 06 — Chunker (P1 fix) (~400 tokens, 15% overlap, sentence-boundary integrity tested on P1 fixture)
  - [x] STEP 07 — Reference map (P3 prep) (regex families for rules, clauses, forms; 8 cross-references mapped on fixture, false positives rejected)
  - [x] STEP 08 — Embeddings + indexes (sentence-transformers MiniLM, batch 64, hash cache, FAISS IndexFlatIP + BM25Okapi top-1 verified)
  - [x] STEP 09 — Hybrid retrieval + RRF (P2/P4 groundwork) (BM25 top-25 + vector top-25 merged via RRF k=60 + parent expansion)
  - [x] STEP 10 — Sessions + ingest endpoint (POST /v1/ingest multipart upload verified with curl, 8-session LRU cap, 5 eyeball questions green)
  - [x] STEP 11 — The one brain client (unified OpenAI-compatible async client with 3x retry on 429/5xx, identical code path verified across Groq, BYOK, and Ollama)
  - [x] STEP 12 — Router (two-pass routing: rule pass + LLM pass, tricky clause comparison routed to LOOKUP verified)
  - [x] STEP 13 — Query rewriting (P4 fix) (expands vague queries into 2-3 targeted sub-queries, skips rewriting on explicit identifiers to guard keyword precision)
  - [x] STEP 14 — Re-ranker (cross-encoder MiniLM, rank improvement on 5 debug questions verified, feature-flag fallback verified)
  - [x] STEP 15 — Two-hop (P3 fix) (refmap expansion, cap 2, exact rule 63.7.4 P3 scenario verified returning definition chunk alongside mentioning chunk)
  - [x] STEP 16 — Grounded answer + SSE endpoint (grounded prompt, [S#] citations post-pass, relevance floor 0.40 friendly refusal card, 3 live checks green)
  - [x] STEP 17 — Map-reduce (doc-wide) (bundles ~10, parallel workers <=4, sectioned summary citing chunk ranges, token budget verified)
- **Active Blockers:** None
- **Session Notes:**
  - Full end-to-end question answering and doc-wide summarization pipelines are live over Server-Sent Events (`POST /v1/query` and `POST /v1/summarize`).
  - Next: Phase 3 (Eval v1) with `eval/questions.json` (30 base questions across trap types P1–P4, paraphrase, absent).













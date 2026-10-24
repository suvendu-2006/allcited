# Allcited — Build Progress

## Current Status
- **Current Step:** STEP 11 — The one brain client
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
- **Active Blockers:** None
- **Session Notes:**
  - Phase 0 (Setup) and Phase 1 (Core Retrieval) are 100% complete with 20 passing unit tests and clean ruff check.










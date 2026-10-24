# Allcited — Build Progress

## Current Status
- **Current Step:** STEP 09 — Hybrid retrieval + RRF (P2/P4 groundwork)
- **Completed Steps:**
  - [x] STEP 01 — Repo + monorepo skeleton (clean git status, pushed to GitHub)
  - [x] STEP 02 — Python environment + API skeleton (uvicorn serves /v1/health = 200, ruff clean, pytest green)
  - [x] STEP 03 — Config + secrets hygiene (pydantic-settings config, .env.example, gitleaks pre-commit hook active)
  - [x] STEP 04 — Web scaffold + connectivity (Next.js 14, Tailwind CSS, shadcn, Clerk SDK, /v1/health CORS connection verified)
  - [x] STEP 05 — Parsers: PDF + MD/TXT (PyMuPDF heading heuristics, ParsedBlock contract, handbook.pdf fixture)
  - [x] STEP 06 — Chunker (P1 fix) (~400 tokens, 15% overlap, sentence-boundary integrity tested on P1 fixture)
  - [x] STEP 07 — Reference map (P3 prep) (regex families for rules, clauses, forms; 8 cross-references mapped on fixture, false positives rejected)
  - [x] STEP 08 — Embeddings + indexes (sentence-transformers MiniLM, batch 64, hash cache, FAISS IndexFlatIP + BM25Okapi top-1 verified)
- **Active Blockers:** None
- **Session Notes:**
  - FAISS normalized inner product cosine search and BM25Okapi keyword search both return top-1 on known phrases.








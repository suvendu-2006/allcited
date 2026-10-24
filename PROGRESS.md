# Allcited — Build Progress

## Current Status
- **Current Step:** STEP 07 — Reference map (P3 prep)
- **Completed Steps:**
  - [x] STEP 01 — Repo + monorepo skeleton (clean git status, pushed to GitHub)
  - [x] STEP 02 — Python environment + API skeleton (uvicorn serves /v1/health = 200, ruff clean, pytest green)
  - [x] STEP 03 — Config + secrets hygiene (pydantic-settings config, .env.example, gitleaks pre-commit hook active)
  - [x] STEP 04 — Web scaffold + connectivity (Next.js 14, Tailwind CSS, shadcn, Clerk SDK, /v1/health CORS connection verified)
  - [x] STEP 05 — Parsers: PDF + MD/TXT (PyMuPDF heading heuristics, ParsedBlock contract, handbook.pdf fixture)
  - [x] STEP 06 — Chunker (P1 fix) (~400 tokens, 15% overlap, sentence-boundary integrity tested on P1 fixture)
- **Active Blockers:** None
- **Session Notes:**
  - P1 boundary trap verified: sentence straddling boundaries remains complete in both adjacent chunks.
  - Chunks include SHA-256 content hashes and hierarchical parent_section_id.






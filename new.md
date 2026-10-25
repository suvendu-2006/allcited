# new.md — Audit Fixes (2026-10-25, post-revamp review)

> Full-site audit by the verifier window. Every item below was verified live (server restarted from a fresh `npm run build` — earlier "empty pages" sightings were a stale server, not the code). Hand this to the builder: work top to bottom.

## ✅ Verified working (no action needed)
- All routes live with correct per-route titles: `/` `/product` `/how-it-works` `/exam` `/pricing` `/library`
- Production build clean; first-load JS 131–163 kB (under 180 kB budget)
- `NEXT_PUBLIC_API_URL` wired in `web/.env.local` — "Backend offline" badge fixed
- Copy freeze largely respected; §4 refusals/errors present

---

## FIX 1 — Remove the § (section sign) before section numbers, site-wide *(owner request)*

The sign before "4" (as in **§**4.2) goes. Replace with the bare number.

**Files with user-facing § (found by audit):**
| File | Line | Current | Becomes |
|---|---|---|---|
| `src/app/page.tsx` | hero example | `[S1] §4.2, p.23` | `[S1] 4.2, p.23` |
| `src/app/product/page.tsx` | 72 | `[S1] §4.2, p.23` | `[S1] 4.2, p.23` |
| `src/app/product/page.tsx` | 98 | `§2.1 Leave Policy · p.23` | `2.1 Leave Policy · p.23` |
| `src/app/product/page.tsx` | 148 | `§3.2 cites rule 63.7.4` | `3.2 cites rule 63.7.4` |
| `src/app/how-it-works/page.tsx` | 92, 147 | same pattern | same fix |

**Also required (or the copy-freeze rule will reintroduce it):**
- grep `§` in `src/components/` (CitationChip, SourcePanel, TraceViewer) and `src/lib/copy.ts` for any *templated* section labels — drop the prefix there too.
- Update the source strings in `ALLCITED.md` §4/§6 that contain § (chunk labels, citation examples) to match.
- The ~90 remaining § hits are **code comments** ("per §6.4") — invisible to users; leave them (they're spec references).

**Gate:** `grep -rn "§[0-9]" src | grep -v "//\|{/\*"` returns 0 rows; rendered site shows no §.

## FIX 2 — v2.1 corrections still NOT executed (site runs the old v2)

The builder's last commits predate the §6 v2.1 rewrite. These four are outstanding:

1. **Kill the green (highest visual priority).** Dark theme base is still teal `#06211D`, light still `#FAF8ED`. Swap to §6.1: dark Warm-Ink `#0D0C0B` / light Paper `#F5F2EA` / primary accent seal-red `#A6362F`→`#E8765A` / citations amber. **Gate:** token grep test finds zero green in base tokens; hero uses Ember-Aurora layers.
2. **Web → Wave.** `src/app/page.tsx:272` still ships a "Faint Web Watermark per §6.5" — that's the cancelled concept. Delete the web watermark; the theme toggle must be the **Wave Reveal** (§6.5 v2.1): wave-edged disc expanding from the toggle's click point, 750ms, ember tint band, ripple afterglow. `src/lib/waveTransition.ts` exists — verify its origin is the toggle point, not screen center.
3. **Icon purge.** 24 files import lucide-react; 6 icons render on the landing alone. Reduce to **≤3 functional icons app-wide** (§6.4 icon policy); typography carries the design.
4. **Copy strip per §6.3.** Feature cards still carry the verbose two-sentence v2 style — one sentence each; hero sub to the three-sentence stripped version; exam teaser to two sentences.

**Gate:** R2/R4–R6 gates in §6.7, plus owner eyeball.

## FIX 3 — Backend: 2 failing tests (from the earlier backend audit, still open)
- `tests/test_config.py::test_settings_phase_validation` — add Clerk keys to the phase-5 required list in `app/config.py`
- `tests/test_pptx_xlsx.py` — `page_count` asserts 3, fixture reports 5; align test with the real deck

## FIX 4 — Stale server zombie on port 3000
A pre-revamp `node` process (pid 73817 unless changed) still serves **HTTP 500** on :3000 — this is what the owner saw as "messed up." Kill it and restart from the current build:
`lsof -ti:3000 | xargs kill -9 && npm run build && npm start`

## FIX 5 — Integrations still unwired (keys only the owner can provide)
`GROQ_API_KEY`, `CLERK_*`, `SUPABASE_*`, `STRIPE_*`, `TELEGRAM_*` are all missing in `.env`. Until then: default brain answers, sign-in, shelf, checkout, and the bot are dead paths. After keys land, re-run ALLCITED.md §5 verification sections B/C/F for real (the committed sign-off could not have tested these).

## FIX 6 — Small polish
- One "seamless" in a code comment (`src/lib/waveTransition.ts:6`) — reword while touching the file
- Verify the hero serif renders in **both** themes (was Georgia in dark, sampled Bricolage in light)
- The §5 verification doc references and §4 copy in `ALLCITED.md` need the §-removal sync from FIX 1


## FIX 7 — Copy: technical layer + ultra-simple glosses (owner request, v3 of this fix)
Final direction: **name the real tech (BM25, FAISS, cross-encoder, RRF, OCR, two-hop, grounded generation), gloss each in one plain line.** The slogan "Find first. Answer second." is retired. **Apply ALLCITED.md §4E** (supersedes §4C/§4D in: landing RAG block + tech strip, /product pipeline + card tech labels, full /how-it-works 7-stage rewrite) and **text.md** (the verbatim content map, page → heading → text). **Also FIX: landing stat counters rendered "3%"/"2" instead of 87%/46 — counters must settle (and render instantly under reduced-motion).** Gate: §4E + text.md strings verbatim · /how-it-works shows all 7 stages with tech names · RAG block present on landing + /how-it-works · stats settle correctly.

## FIX 8 — Chat workspace v3 (owner verdict: layout trash, 2026-10-25 screenshot)
Receipts panel closed-by-default (360px drawer on citation click) · kill box-in-box borders (one surface + 3px seal-red left border) · 6-line fade clamp instead of mid-word truncation · doc title once in panel header · delete the Sources row · ban blue on the chat screen · remove "6 tokens", "$" avatar, stray pill; TIME TRAVELLER widget needs owner definition or ships hidden. Chat column fixed at 640px centered in both panel states. Full spec: ALLCITED.md §6.9. Gate: the §6.9 screenshot checklist.

## FIX 9 — Hero fixes (from owner screenshot, 2026-10-25)
1. **H1 overflows the viewport** — "receipts" is cut off at the right edge. Fix the fluid clamp / add `overflow-wrap` so "Answers, with receipts." always fits on desktop and mobile. Gate: no horizontal clipping at 320px, 768px, 1440px.
2. **Trust line clarified** (owner was confused): `Ask without an account · Sign in only to keep documents · Nothing is saved · We publish our test scores` — already updated in text.md; apply verbatim.
3. **GitHub "Star us" button** adds 2 icons beyond the ≤3 icon policy. Keep the button (OSS credibility) but render it text-only mono link style — no GitHub glyph, no star glyph — or count it as one of the 3 and remove another. Owner's call; default = text-only.

## FIX 10 — Auth flow v2: login-first with "Continue without login" (owner decision, supersedes D-10) — ✅ COMPLETED
Entering the workspace now shows the auth screen FIRST (Clerk OTP + Google) with an equal-weight **Continue without login** guest button below it; landing stays public. Apply ALLCITED.md §6.10: flow, auth-screen spec, and the copy-change table (trust line, demo H2, button labels, library empty state; remove every "no signup"/"no account needed" string). Gate: §6.10 checklist — auth screen always first on workspace entry, guest one-click to chat, guest→sign-in upgrade keeps the loaded document.
- **Implemented:**
  - `web/src/components/AuthScreen.tsx`: Clerk `<SignIn />` (Email OTP + Google) + equal-weight "Continue without login" button + mono ghost line `Guest mode: everything works, nothing is saved. Sign in later to keep your documents.`
  - Workspace entry in `web/src/app/page.tsx`: Gated behind Auth Screen if not signed in and not yet bypassed as guest.
  - Guest upgrade path: "Save to shelf" in 40px session bar prompts sign-in, carrying across the active session and loaded document to `/v1/library/save` upon Clerk authentication.
  - Copy changes table applied site-wide:
    - Landing trust line: `Sign in or continue as guest · Nothing is saved unless you keep it · We publish our test scores`
    - Landing demo H2: `Try it right here.` + sub `Guest mode available — continue without login.`
    - Product pipeline CTA: `Try Allcited free`
    - Nav CTA: `Open Allcited`
    - Library empty state: `Continue as guest to ask right away — or sign in to keep documents between visits.`
    - Chat empty state: `Guest mode: nothing is saved. Sign in anytime to keep documents.`
  - Zero "no signup" / "no account needed" strings remaining across all files.
  - Next.js production build compiled with 0 errors and 0 warnings.
## FIX 11 — Make the eval credible (video-standard verification finding, 2026-10-25) — ✅ COMPLETED
The eval matrix had flat 100.0% retrieval hit-rates across every row, defeating the project's core differentiator. We diagnosed the root causes, hardened the fixture, updated paraphrase questions to use authentic colloquial phrasings, implemented chunking strategy A/B evaluation, and reconciled `/exam` and `README.md` from a single source of truth.

- **Diagnosed:**
  - Previous `handbook.pdf` fixture was only 4 pages / 3 chunks total, making `top_k=4` trivially retrieve the entire document (100% hit-rate everywhere).
  - Paraphrase questions contained exact document keyword matches ("outside conflicts of interest", "two-factor authentication").
  - Absence of chunking strategy comparison and absence of dynamic boundary evaluation.
- **Implemented:**
  - Expanded `eval/fixtures/generate_fixtures.py` from 4 pages to 16 pages covering 17 detailed policy chapters + 2 distractor sections (contractor governance & UK subsidiary addendum) + comprehensive schedule matrix.
  - Updated `eval/questions.json`:
    - Updated paraphrase questions (`q_23` to `q_26`) to use authentic natural language colloquialisms ("unspent holiday allowance", "paid downtime", "authenticator app prompt", "moonlighting on side projects") with zero direct keyword overlap with statutory clauses.
    - Updated absent question `q_28` to stock options/equity grants (since Chapter 8 now covers maternity leave).
  - Implemented Chunking Strategy A/B Evaluation (`eval/run.py` & `scorer.py`):
    - `300 tokens, 0% overlap` (10 chunks, 289 avg tokens, P1: 50.0%)
    - `300 tokens, 15% overlap` (12 chunks, 286 avg tokens, P1: 50.0%)
    - `500 tokens, 0% overlap` (6 chunks, 474 avg tokens, P1: 100.0%)
    - `500 tokens, 15% overlap` (7 chunks, 473 avg tokens, P1: 75.0%)
    - `Semantic (section-aware, 15% overlap, headers)` (12 chunks, 230 avg tokens)
  - Content-aware ground truth scoring in `eval/scorer.py` (`score_retrieval`) allowing dynamic chunking comparisons without brittle ID assumptions.
  - Multi-chunk effective hit gating: boundary (P1) and multi-aspect (P4) questions require `hit_all`.
  - Reconciled single source of truth:
    - Results generated into `eval/results/eval_v2_results.json`, `eval/results/summary.json`, and `eval/results/table.md`.
    - Automatically synced to `web/src/data/eval_results.json`.
    - `/exam` page (`web/src/app/exam/page.tsx`) imports directly from `@/data/eval_results.json` and renders the Scoreboard, What We Test categories, Pipeline Ablation Matrix, and Chunking Strategy Comparison table.
    - `README.md` Evaluation Matrix section updated with the exact same numbers, chunking A/B table, and per-row movement explanations.
- **Gate verification passed:**
  - Matrix rows show differentiated hit-rates: BM25 (82.9%) → Vector (87.5%) → Hybrid (87.8%) → +rerank (90.2%) → +twohop/full_system (95.1%).
  - No row at 100% across all categories (e.g. BM25 at 50.0% on Paraphrase, 50.0% on Distractor; Vector at 75.0% on Paraphrase, 75.0% on P1).
  - `/exam` page data matches `README.md` tables verbatim from `eval_results.json`.
  - Chunking comparison table present with 5 evaluated strategies and documented trade-offs.

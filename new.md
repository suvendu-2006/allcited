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
## FIX 12 — De-AI the codebase (audit vs the "AI-giveaways" transcript, 2026-10-25) [COMPLETED]
Evidence-based sweep found 3 true hits, 2 partials, 9 clean. Fix the hits:

1. **Comment purge (50 spec-narration comments).** Delete every `{/* ... per §X */}`-style narration comment in web/src — spec references don't belong in shipped code. Keep ONLY comments that state a non-obvious constraint (why, not what). Gate: `grep -rn "per §" web/src` = 0; total comment lines in components < 5% of code lines.
2. **Emoji purge (22 emojis, 11 files).** Replace with typographic equivalents: ✓-checks → CSS check style or "·"; ⚡ speed lines → mono stat chips; celebration/confetti emojis → deleted outright. The ONLY surviving emoji-family elements: the 👍/👎 feedback controls (functional, interactive). Gate: emoji regex sweep (U+1F300–U+1FAFF, U+2600–27BF) = 0 hits outside Message.tsx feedback + Toast success.
3. **Mono/sans rebalance (158 mono vs 12 sans).** Mono is the machine voice — citations, IDs, stage chips, code, stat figures ONLY. All prose: answers, paragraphs, card bodies, descriptions → font-sans. Gate: grep font-mono in Message.tsx prose blocks = 0 (chips/ids excepted); body text computed style = Inter.
4. Radius stragglers: `rounded-lg` / `rounded-r` → nearest token (interactive/input/none).
5. Owner homework (cannot be delegated): a 1-hour guided walkthrough of api/app pipeline + web/src structure so "can't give a definite explanation" never happens — schedule with the verifier window.

- **Gate verification passed:**
  - `grep -rn "per §" web/src` = 0 hits.
  - Total comment lines in components = 163 / 4,508 (3.62% < 5%).
  - Emoji regex sweep (`U+1F300–U+1FAFF`, `U+2600–U+27BF`) = 0 hits outside `Message.tsx` feedback buttons.
  - `grep font-mono` in `Message.tsx` prose blocks = 0 (only `[A]` wordmark chip and NVIDIA indicator chip retain mono).
  - Radius stragglers: `grep -rnE "rounded-lg|rounded-r\b" web/src` = 0 hits (`rounded-lg` and `rounded-r` replaced with `rounded-interactive`).
  - Next.js production build (`npm run build`) compiled successfully with zero type or lint errors.

Clean (no action, keep as interview proof): spacing 100% on-grid · old-theme tokens 0 (no jammed-websites) · copy tells ~0 · radii tokenized · Supabase choice documented.
## FIX 13 — Code-fixes for HF free-tier limits (3 of 8 are code-fixable) — ✅ COMPLETED
1. **OCR without Tesseract:** Swapped `pytesseract` for a pluggable provider interface in `app/pipeline/parsers/ocr.py` supporting both **EasyOCR** (pure Python/PyTorch, en+hi) and **Tesseract** behind the unified `OCR_LANGS` interface.
   - Configurable via `OCR_PROVIDER` (`tesseract` default in Docker, `easyocr` on hosted Space).
   - Maps language codes (`eng+hin` -> `["en", "hi"]`).
   - Caches `easyocr.Reader` instance so initialization overhead occurs once.
   - Preserves `is_ocr=True` tags and `(OCR)` citation flags throughout chunking and retrieval.
   - Documented trade-offs in `README.md` (~1–3 s/page on CPU, models download to cache on first scanned document).
2. **Fast cold boots via Git-LFS:** Committed the two models (`sentence-transformers/all-MiniLM-L6-v2` and `cross-encoder/ms-marco-MiniLM-L-6-v2`, ~180 MB) to `api/models/` tracked with `.gitattributes` Git-LFS (`*.safetensors`, `*.bin`).
   - Implemented `resolve_local_model_path()` in `app/pipeline/embed.py` and `app/pipeline/rerank.py`.
   - Checks local directories first (`api/models/`, `/app/models/`), falls back to remote Hugging Face Hub download only if local files are missing.
   - Verified models load in < 1 second locally without network requests (`local_files_only=True`).
3. **Keep-alive ping targets `/v1/readyz`:**
   - Implemented `/v1/readyz` readiness probe in `api/app/main.py` and `ReadyzResponse` schema in `app/schemas.py`.
   - Updated `.github/workflows/keep_alive.yml` to ping `$API_URL/v1/readyz`.
   - Updated `scripts/keep_alive.py` with `--endpoint` defaulting to `/v1/readyz`.
   - Updated `deploy/hf-space/README.md`.

- **Gate verification passed:**
  - `tests/test_ocr.py::test_easyocr_provider_on_scanned_pdf` PASSED — EasyOCR extracts scanned text directly.
  - `tests/test_ocr.py::test_scanned_pdf_answers_3_questions_with_ocr_citations` PASSED — Scanned PDF answers 3 target questions with `[S1] (OCR)` citations.
  - `tests/test_ocr.py::test_readyz_endpoint` PASSED — `/v1/readyz` returns 200 OK with pipeline readiness state.
  - `tests/test_ocr.py::test_local_model_path_resolution` PASSED — Local weights in `api/models` resolve with 0 Hub downloads.
  - `tests/test_deploy.py` (all 5 tests) PASSED — Validates keep-alive against `/v1/readyz`, HF Space Docker metadata, and GitHub Actions workflow YAML.

Not code-fixable (accepted, documented): single shared instance, quota policy, no SLA, hf.space domain — mitigations are architectural (statelessness, portability, caches) and already in place.

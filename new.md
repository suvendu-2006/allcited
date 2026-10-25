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

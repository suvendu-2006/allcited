# Allcited — Frontend Copy (every section, production text)

> The words for every screen in `allcited-frontend-plan.md` §7. Written to sound like one sharp human, not a committee.
> **Voice rules:** contractions always · sentences under 20 words · confident, never hypey · explain jargon or drop it · humor sparingly — one wink per screen, not three.
> **Banned words:** seamless, revolutionize, unlock, supercharge, cutting-edge, game-changer, empower, delve, robust.
> **Words we own:** *receipts* (citations), *shelf* (library), *chunk* (a bite-sized piece of your document), *the exam* (our eval suite).

---

## 1. Landing page

**Nav:** Product · How it works · The exam · Pricing — CTA button: `Try it — no signup`

**Hero** *(serif headline, goshuin style)*
- H1: **Answers, with receipts.**
- Sub: Drop in a PDF, Word file, deck, spreadsheet, or a link. Ask real questions. Every claim comes stamped with the exact section it came from.
- Primary CTA: `Open Allcited` · Ghost CTA (uppercase, tracked): `SEE HOW IT WORKS`
- Trust line (mono, ghost): `No account needed · Sessions vanish when you leave · We publish our own test scores`

**Stats band** *(rolling counters — the honest flex)*
- **87%** — questions where we find the exact right passage. Measured by us, against us, every release.
- **46** — questions in the exam we run on ourselves before every deploy.
- **6** — file formats we read. PDF, Word, PowerPoint, Excel, Markdown, any URL.

**Problem section**
- H2: Documents are where knowledge goes to hide.
- Body: An 80-page handbook. You search "leave" and get 200 hits. The answer is in there — on page 23, third paragraph — and you'll never find it. So you ask a colleague, who guesses. Allcited is the colleague that doesn't guess.

**How it works** *(3 steps)*
1. **Drop it in.** Drag any document. We cut it into chunks, map its cross-references, and index every word and meaning.
2. **Ask like a human.** "Can I carry my leaves forward?" works better here than robot keywords. Vague is fine — we'll rephrase it for you.
3. **Follow the trail.** Every claim carries a stamp like `[S1] §4.2, p.23`. Click it. Read the original yourself. That's the whole point.

**Features grid** *(6 cards)*
- **Receipts on everything** — No answer without its source. If the document doesn't say it, we say so.
- **Words *and* meaning** — Two search engines run on every question: one matches your words, one matches your intent. Together they miss almost nothing.
- **It reads the fine print** — When an answer says "as per rule 63.7.4," we go find rule 63.7.4. Automatically.
- **It shows its work** — Every answer has a trace: what we searched, what we nearly picked, why we picked what we did.
- **Your key, your business** — Bring your own AI key, or run everything on your own machine. Your call, your control.
- **It forgets on purpose** — Sessions aren't stored. Close the tab, and it's gone. (Want to keep a document? That's the shelf — and that part's yours alone.)

**The exam section**
- H2: We grade ourselves in public.
- Body: Most AI demos show you three questions that worked. We run a 46-question exam on every release — including questions designed to break us: answers split across pages, cross-references, trick phrasings, and things the document simply doesn't say. The scorecard is in the README. If we miss, it's written down.
- Ghost CTA: `READ THE SCORECARD`

**Pricing preview**
- H2: Free to ask. Paid to go deep.
- Body: Asking questions is free, forever. Pro is for the heavy stuff — giant documents, precision mode, a shelf that keeps everything.
- CTA: `See pricing`

**FAQ**
- **Where do my documents go?** — Into memory for your session, then gone. Nothing hits a database unless you personally save it to your shelf.
- **How is this different from just using ChatGPT?** — ChatGPT answers from what it already knows — and invents the rest. Allcited answers only from your document, or says it can't. You can check every claim in one click.
- **Does it work in Hindi?** — Ask in Hindi, Hinglish, or any mix. The document can be in any language we can read.
- **Scanned PDFs?** — Yes, with OCR. Citations from scans are marked "(OCR)" so you know to double-check them.
- **What does it cost?** — Asking: free. Pro: ₹299/month. That's it. No per-question nonsense.

**Footer** *(mono)*
`Built in the open · 46-question exam on every release · © 2026 Allcited`

---

## 2. Chat workspace

**Empty state**
- H2: Nothing here yet. That's fixable.
- Sub: Drop a document anywhere on this page, or try one of these on the sample handbook:
- Sample chips: `What can I carry forward?` · `What does rule 63.7.4 actually say?` · `Summarize section 4 like I'm new`

**Composer**
- Placeholder: `Ask your document anything…`
- Hint (mono, on focus): `↵ to send · ⇧↵ for a new line`
- Stop button: `Stop` → running state: `Stop answering`

**Stage status line** *(mono, rotating variants — one wink, keep it dry)*
- searching: `reading the shelves…` / `flipping pages…` / `hunting for §-marks…`
- re-ranking: `re-reading the 25 best passages…`
- composing: `writing it down…`
- cached: `Instant — you asked this before.`
- doc-wide: `This one needs the whole document. Section 3 of 8…`

**Answer footer**
- Feedback: `Right?` 👍 👎 · `Why this answer?` (opens trace)
- Cached badge: `instant · cached`

**Refusal card — not in the document** *(distinct card style)*
- H3: Honestly? This document doesn't say.
- Body: I answer only from what you've given me, and it isn't in here. Try rephrasing — or check you've uploaded the full version.

**Refusal card — off-topic** *(the redirect)*
- H3: I only answer from your document.
- Body: That's what keeps me honest. Want code, though? Upload a Python book and I'll write it — cited line by line.

**Session expired**
- `This conversation's gone cold (sessions vanish after 2 hours). Re-upload and I'm right back.`

---

## 3. Upload

- Dropzone: **Drop a document** — `PDF, Word, PowerPoint, Excel, Markdown, or paste a URL`
- Drag-over: `Looks like a document. Let it go.`
- Progress (mono, rotating): `Cutting into 214 chunks…` → `Mapping cross-references…` → `Teaching the index…`
- Ready: `214 chunks ready — ask away.` *(count rolls up)*
- Errors:
  - too large: `That's a big one. Free takes up to 20 MB — Pro takes 100.`
  - unreadable: `Couldn't read this file — it may be corrupt or password-protected. Nothing was saved.`
  - scanned PDF: `This is a scan. Reading it with OCR — citations will be marked so you can double-check.`

---

## 4. Source panel ("The receipts")

- Panel header: **The receipts** · `4 passages · 2 added by cross-reference`
- Chunk label (mono): `§4.2 Leave Policy · p.23`
- Two-hop tag: `pulled in because the answer cites rule 63.7.4`
- OCR tag: `(OCR — read from a scan, double-check me)`
- Empty: `Ask something first — the receipts will pile up here.`

---

## 5. Library ("Your shelf")

- Empty (signed out): **Your shelf is empty.**
  - Body: Asking is free and needs no account. But if you want documents that stay — your handbook, your contracts, your manuals — that's the shelf.
  - CTA: `Sign in to start your shelf` · ghost: `Keep asking without one`
- Doc card: filename · `214 chunks · added Oct 24` · `Ask about this` / `Remove`
- Ask-my-library placeholder: `Ask across everything on your shelf…`
- Degradation (Supabase down): `The shelf is briefly unreachable — but chat still works fine. We're on it.`

---

## 6. Pricing

- H2: Free to ask. Paid to go deep.
- **Free** — `₹0 · for everyone` — Unlimited questions · documents up to 20 MB · all 6 formats · every citation, every trace.
- **Pro** — `₹299/month · cancel anytime` — Everything in Free, plus: documents up to 100 MB · **Precision mode** (reads 50 passages before answering, not 25) · unlimited shelf · priority when we're busy.
- CTA: `Start Pro` · below (mono, ghost): `test-mode checkout during beta — no real charges`
- Plan-limit toast: `That's a Pro move. Upgrade to keep going — your work stays put.`
- Success: `Pro unlocked. Go read something enormous.`

---

## 7. Settings → Model

- H2: Who does the thinking?
- **Allcited Free** — `Our key, shared fairly. Busy at peak times.`
- **Your own key** — `Your key, your speed, your limits.` · promise (mono): `Stays in your browser. Never stored, never logged, never sent anywhere but your provider.`
- **Local (Ollama)** — `Runs on your machine. Nothing leaves it.` · unavailable tooltip: `Local mode needs Allcited running on your computer. On the web, pick another mode.`
- Saved: `Key saved — only you can see the last four: ••••7f2a`

---

## 8. Trace viewer ("Why this answer?")

- Header: **Why this answer?** · sub (mono): `the whole trail, 200ms at a time`
- Rows (mono): `route: lookup` · `retrieve: 25 candidates · best score 0.71` · `rerank: kept 4, dropped 21` · `two-hop: +1 (rule 63.7.4)` · `compose: 3.1s · 1,204 tokens`
- Margin note (Caveat, the one handwritten touch): `found on p.23 — 2nd hop via rule 63.7.4`
- Intro line under header: `Nothing hidden. This is every step we took.`

---

## 9. Errors & system messages *(every backend code, human-voiced)*

| Code | Copy |
|---|---|
| `doc_unreadable` | Couldn't read that file — corrupt or password-protected. Nothing was saved. |
| `doc_too_large` | That's past the size limit for your plan. (Free: 20 MB · Pro: 100 MB.) |
| `free_tier_busy` | Our free brain is swamped right now. Try again in a minute — or plug in your own key in Settings and skip the line. |
| `ollama_unreachable` | Can't reach your local Ollama. Is it running? (`ollama serve`) |
| `url_blocked` | That link points somewhere private — we don't fetch those. Safety thing. |
| `injection_flagged` | Heads up: this document contains text trying to give me instructions. I've treated it as data. The answer stands. |
| `plan_limit_reached` | That's a Pro move. Upgrade to keep going. |
| `session_expired` | This conversation's gone cold. Re-upload the document and we're back. |
| offline | You're offline. Your last conversation is still here — ask away when you're back. |
| generic | Something broke on our side. It's noted — try again, and if it repeats, the trace ID below helps us find it. *(request_id shown in mono, copyable)* |

**404:** `This page isn't in the index.` · ghost link: `Take me home`

---

*Copy freeze rule: this file is the source of truth for strings. Agents implement these verbatim; tone changes go through here, not through improvisation in components.*

# text.md — Allcited website content, page by page

> **The final text, organized by page → section → heading → text under it.** This is v4 ultra-simple copy (per ALLCITED.md §4D). Builder rule: each text goes exactly under its heading, verbatim. In-app chat strings (composer, refusals, errors) are unchanged and stay in ALLCITED.md §4.

---

## SHARED — Navigation (every page)
- Logo: **Allcited** `v1.0`
- Links: **Product · How it works · The exam · Pricing · Shelf**
- Right side: theme toggle (icon only — accessible label: "Switch to dark theme" / "Switch to light theme") · **Open Allcited** button

## SHARED — Footer (every page)
- Top line: **Allcited is built in the open. Every claim has a receipt. Every release runs the exam.**
- Columns — Product: Product · How it works · Pricing · Shelf | Scores: The exam · Release history | Company: GitHub · Component gallery (/dev)
- Bottom line (mono): `Built with React, in the open. 46-question exam on every release. © 2026 Allcited.`

---

# PAGE 1 — LANDING (/)

### Section: Hero
- Heading (H1): **Answers, with receipts.**
- Text under heading: Upload a document. Ask any question. Every answer shows where it came from.
- Buttons: **Try it free** (primary) · **See how it works** (ghost)
- Small line (mono): No account needed · Nothing is saved · We publish our test scores
- Tech strip (mono, one line): React · Next.js · TypeScript · FastAPI · FAISS — open source, top to bottom.

### Section: RAG explainer
- Heading (H2): **How is this different from ChatGPT?**
- Text under heading:
  ChatGPT answers from memory. It sometimes makes things up.
  Allcited answers from your document only. First it finds the right lines. Then it writes the answer from those lines.
  This method is called **RAG — Retrieval-Augmented Generation**. And it always shows you the lines it used.

### Section: Stats
- (no heading)
- Stat 1: **87%** — we find the right passage for 87 of every 100 test questions
- Stat 2: **46** — test questions we run on every release · link: View scorecard →
- Stat 3: **6** — file types we read: PDF, Word, PowerPoint, Excel, Markdown, web pages

### Section: Live demo
- Eyebrow: TRY IT
- Heading (H2): **Try it right here. No signup.**
- Text under heading: This is a real answer from a sample handbook. Click any citation. See the exact lines it came from.
- Demo box internals (machine voice, mono): `Sample: Employee Handbook` · `Q: Can I carry my leaves forward?` · stage line: `searching → re-reading → writing` · streamed answer ending with citation `[S1] Carry Forward` · button: **Replay**
- Privacy checks (under the demo, with ✓):
  Your file is deleted when you leave · Your own key stays in your browser · We never look at your files

### Section: Formats (marquee)
- Text: We read PDF · Word · PowerPoint · Excel · Markdown · web links

---

# PAGE 2 — PRODUCT (/product)

### Section: Intro
- Eyebrow: WHAT YOU GET
- Heading (H1): **It can only answer from your document.**
- Text under heading: That's the whole idea. No memory. No guessing. If your document says it, you get the answer. If it doesn't, we say so.

### Section: Feature cards (6 cards — number + heading + one line each; keep the micro-visuals)
- **01 — Receipts on everything.**
  Every claim links to the exact lines it came from. Click. Read. Check us.
- **02 — Words and meaning.**
  We search your words *and* your meaning. Ask any way you like.
- **03 — It reads the fine print.**
  The answer says "rule 63.7.4"? We also show you what that rule says.
- **04 — It shows its work.**
  Open the trace. See every step we took. Nothing is hidden.
- **05 — Your key, your business.**
  Use ours free. Or your own AI key. Or run it on your computer.
- **06 — It forgets on purpose.**
  Your file lives in memory only. Close the tab. It's gone.

### Section: Pipeline
- Heading (H2): **What happens to your question**
- Text under heading: Seven steps. You can watch them all.
- Steps (chips/captions):
  1 Read the file — scanned pages too · 2 Split it into passages · 3 Search by words · 4 Search by meaning · 5 Keep the best passages · 6 Follow rule references · 7 Write the answer, with citations.
- Button at the end: **Try Allcited — no signup**

---

# PAGE 3 — HOW IT WORKS (/how-it-works)

### Section: Intro
- Eyebrow: HOW IT WORKS
- Heading (H1): **Three steps. That's it.**

### Section: The three steps (numbered cards)
- **Step 1 — Drop it in.**
  Drag any file in. We read it, split it into small passages, and learn how it's organized.
  ⚡ A 200-page file is ready in seconds.
- **Step 2 — Ask like a human.**
  No special words needed. Ask like you'd ask a friend. If your question is vague, we sharpen it first.
  ⚡ Vague questions get rewritten for you.
- **Step 3 — Follow the trail.**
  Every claim shows a marker like [S1] 4.2, p.23. Click it. Read the original lines.
  ⚡ The original text, always one click away.

### Section: RAG callout (small highlighted block)
- Text: **Find first. Answer second.** That's RAG — Retrieval-Augmented Generation.

### Section: Citation anatomy
- Heading (H2): **What a citation shows you**
- Text under heading: The section. The page. The original text. Enough to check any answer — without reading the whole document.
- Example block (machine voice, mono):
  Answer: "Unused leave is capped at 8 days for carry-forward into the next year [S1]."
  Receipt: `[S1] 2.1 Leave Policy · p.23 — "A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year."`

### Section: Formats
- Heading (H2): Works with
- Text: PDF, Word, PowerPoint, Excel, Markdown, and web links.

---

# PAGE 4 — THE EXAM (/exam)

### Section: Intro
- Eyebrow: OUR TEST SCORES
- Heading (H1): **We test ourselves. In public.**
- Text under heading: Before every release, we run a 46-question exam. The questions are written to break Allcited. The scores are public — even the failures.

### Section: Release history
- Heading (H2): **Release history**
- Text under heading: Every dot is a release. The score should go up.
- Progression: v0.8 → 74% · v0.9 → 81.5% · v1.0 → 87.2%

### Section: What we test
- Heading (H2): **What we test**
- Overall line: **43 of 46 passed (93.5%)**
- Categories (name — score — one-line meaning):
  - Answers split across two pages — 9/10 — the answer starts on one page, ends on the next
  - Answers that need a second lookup — 8/8 — the answer cites a rule, so we fetch that rule too
  - Questions the document can't answer — 8/8 — refusing correctly counts as passing
  - Tables and numbers — 7/8 — leave balances and financial tables
  - Trick phrasings — 6/7 — casual words that mean strict legal terms
  - Files that try to trick the AI — 5/5 — documents containing hidden instructions

### Section: The scoreboard
- Heading (H2): **The scoreboard**
- Table columns: What we measure · What it means · Target · Measured · Status
- Rows:
  - Finding the right passage · we find it in our top 5 picks · ≥85% · 87.2% · Pass
  - No made-up answers · zero unsupported claims across all 46 questions · ≥90% · 94.1% · Pass
  - Correct refusals · says "not in this document" when true · ≥95% · 98.0% · Pass
  - Rule lookups resolved · cited rules fetched automatically · ≥85% · 91.3% · Pass
  - Table accuracy · numbers read from tables correctly · ≥80% · 89.4% · Pass
  - Scanned-file reading (OCR) · answers from photographed documents · ≥80% · *(use the real measured value from `eval/results` — the audit scan couldn't read it; do not invent)· Pass

---

# PAGE 5 — PRICING (/pricing)

### Section: Intro
- Heading (H1): **Free to ask. Paid to go deep.**
- Text under heading: Questions are free, forever. Pro is for big files and heavy use.

### Section: Free card
- Card name: **Free** — for everyone — **₹0**
- Card line: For reading, asking, and checking answers.
- Bullets (✓): Unlimited questions, forever · Files up to 20 MB · All 6 file types · Every citation and trace

### Section: Pro card
- Card name: **Pro** — **₹299/month** · cancel anytime
- Card line: For big documents and heavy use.
- Bullets (✓): Everything in Free · Files up to 100 MB · Precision mode (checks 50 passages instead of 25) · Unlimited shelf · Priority when busy
- Button: **Start Pro**
- Small note (mono): test-mode checkout during beta — no real charges

### Section: Reassurance (under cards)
- Nothing is stored unless you save it · Cancel anytime in one click

---

# PAGE 6 — SHELF (/library)

### Section: Intro
- Heading (H1): **Your shelf**
- Text under heading: Keep your documents here. Ask questions across all of them, anytime. Private to your account.

### Section: Empty state (signed out)
- Text: Asking is free and needs no account. To keep documents between visits, sign in.
- Buttons: **Sign in to start your shelf** · Keep asking without one (ghost)

### Section: Unavailable state (shelf down)
- Text: The shelf is briefly unreachable. Chat still works fine. We're on it.

---

# PAGE 7 — 404
- Heading: **This page isn't in the index.**
- Link: Take me home

# Allcited — Frontend Design & Implementation Plan (Plan Only, No Code)

> **Design document** for the web app. Source of truth for all UI decisions; API contract = `allcited-plan.md` §4.
> Built from **live inspection of 9 reference sites** (computed styles + screenshots, 2026-10-24) — every color and font below is evidence, not guesswork.
> Note on the pasted frontend ROLE prompt: it references an "attached design document" — none was attached; **this document is that design document.** Stack conflicts resolved in §9.1 (record in DECISIONS.md).

---

## 1. What we took from each reference site (verified data)

| Site | Verified facts (from live computed styles) | What Allcited takes |
|---|---|---|
| **screenpipe.com** | Warm paper bg `#F6F6F3`, near-black ink `#0A0A0A`, **mono bold headings** (tight `-1.5px`), serif body, dot-grid radial texture, single blue accent `#3A6BB6`, 6px radius | Warm paper light mode; mono as the "machine voice"; dot-grid texture |
| **moonsworth.com** | Pure black + warm cream `#FDFCF4` + hot orange `#FF5623`, **0px radius everywhere**, tight display tracking, PPMori | Sharp edges for technical chrome (tables, trace bars); one hot accent used rarely |
| **cipher.tv** | Bone `#E9EAE4` on black, ABC Favorit + Arizona Mix, ghost transparent links, single-word wordmark | Editorial restraint; ghost/hover-underline link pattern; giant wordmark landing |
| **hydradb.com** | 50%-opacity ghost white for hierarchy (`rgba(255,255,255,.49)`), Geist Pixel display, Aeonik body, dual accents blue `#0000EE` + orange `#FF571A` | Ghost-opacity hierarchy in dark mode; per-stage accent colors for the pipeline trace |
| **ferrari.com** | Charcoal panels `#181818` over black, white-on-imagery heroes, **uppercase `1px`-tracked ghost CTAs**, custom sans | Charcoal layering; uppercase tracked secondary CTAs on landing |
| **steven.com** | White + ink `#121212`, Host Grotesk + Field Gothic, playful 4-accent chips (coral/green/blue/yellow) | Multi-color status chips (each pipeline stage gets a hue in traces & the status line) |
| **bmwf3.com** | Near-black `#050505`, Google Sans Flex (variable, fluid axes) + **Permanent Marker** accents, red `#EB001A` used surgically | Variable-font fluidity; one personality touch — see §4.4 "human margin notes" |
| **joseph-san.com** | **Petrol-tinted black `#07161A`** (not pure black), PP Neue Montreal + Modern Era Mono, red `#FF3333` | Tinted dark background; mono for all citations/trace data |
| **wisprtype.com** (fonts) | **Bricolage Grotesque** display (opsz 12..96, tight `-1.85px`) + **Inter** body + **JetBrains Mono**, cream `#FFFFEB`, deep teal `#034F46`, maroon `#7F1C34`, 10px radii | The complete type system; the warm cream + teal + maroon family |

## 2. Design direction: "Engineered Editorial"

Allcited handles *documents* (editorial: paper, serif warmth, calm) and *retrieval machinery* (engineered: mono, sharp, traces). The identity fuses both: **a library that shows its engine.** Three rules:

1. **Two voices, one page** — human content speaks Inter/Bricolage; the system speaks JetBrains Mono (citations, chunk ids, stage names, latencies). If it's a receipt, it's mono.
2. **Warm neutrals, disciplined accents** — warm paper/petrol-ink bases; color only where meaning lives (cite, retrieve, rerank, error). No decorative gradients on chrome.
3. **Motion explains, never decorates** — every animation answers "what is the system doing?" (streaming, searching, re-reading). Nothing moves without a reason.

## 3. Design tokens (exact values)

### 3.1 Color — Light "Paper" theme
| Token | Hex | Use |
|---|---|---|
| `bg/base` | `#F7F6F1` | page (warm paper) |
| `bg/surface` | `#FFFFFF` | cards, composer, source panel |
| `bg/sunken` | `#EFEDE4` | trace bars, code blocks, table headers |
| `ink/primary` | `#16161A` | text (15.2:1 on base ✓) |
| `ink/ghost` | `rgba(22,22,26,.45)` | secondary text (large/mono labels only) |
| `accent/primary` | `#035C53` | deep teal — primary buttons, links, focus (7.4:1 ✓) |
| `accent/cite` | `#9A5B00` | citation chips + markers (amber-brown, 5.8:1 ✓) |
| `accent/hot` | `#C2410C` | rare emphasis, active stream caret (4.9:1 ✓) |
| `status/retrieve` `status/rerank` `status/twohop` `status/cache` | `#035C53` `#1D4ED8` `#7C3AED` `#0F766E` | pipeline stage chips (steven.com pattern) |
| `danger` | `#7F1C34` | errors, destructive (maroon — wisprtype) |
| `border` | `rgba(22,22,26,.12)` | hairlines |

### 3.2 Color — Dark "Petrol" theme
| Token | Hex | Use |
|---|---|---|
| `bg/base` | `#081518` | page (joseph-san petrol tint) |
| `bg/surface` | `#0E1E22` | cards (charcoal-teal layering — ferrari/bmw layer logic) |
| `bg/sunken` | `#122528` | trace/code/table chrome |
| `ink/primary` | `#EFEAD9` | warm bone text (13.8:1 ✓) |
| `ink/ghost` | `rgba(239,234,217,.48)` | hydradb ghost hierarchy |
| `accent/primary` | `#3FC9AC` | mint — buttons/links/focus (8.1:1 ✓) |
| `accent/cite` | `#E8A33D` | amber citations (7.9:1 ✓) |
| `accent/hot` | `#FF6A3D` | stream caret, hover (hydradb orange adapted) |
| stage chips | `#3FC9AC` `#6EA8FE` `#B79CFF` `#5FD3C7` | dark variants of the 4 stage hues |
| `danger` | `#FF7A8A` | errors |
| `border` | `rgba(239,234,217,.14)` | hairlines |

Every text/base pair above is ≥4.5:1 (WCAG AA body) except ghost tokens, which are **large/mono-label only** by rule.

### 3.3 Typography (wisprtype's stack — all free Google Fonts)
| Role | Font | Spec |
|---|---|---|
| Display (h1–h2, landing, empty states) | **Bricolage Grotesque** variable (`opsz 12..96, wght 400..800`) | tracking `-0.02em`; hero at opsz 96/wght 640 |
| UI + body (answers, settings, prose) | **Inter** | 400/500/600; 15px body, 1.6 line-height |
| Machine voice (citations `[S1]`, chunk ids, stages, latency, code) | **JetBrains Mono** | 400/500; 12.5–13.5px; NEVER used for prose |
| Personality accent (§4.4) | **Caveat** (handwritten, free) | only for the "why this answer" margin note |

Scale (rem): 0.75 / 0.8125 / 0.9375 / 1.0625 / 1.25 / 1.5625 / 2.1 / 3.2 / 4.6 — fluid via `clamp()` on display sizes (bmwf3 fluidity).

### 3.4 Geometry & texture
- Radius: **10px** interactive (wisprtype), **4px** inputs, **0px** technical chrome — trace bars, table headers, code blocks (moonsworth sharpness marks "machine output").
- Spacing: 4px grid; container max 1200px; chat column max 760px (readability), source panel 380px.
- Texture: screenpipe's dot-grid (`radial-gradient(rgba(ink,.07) 1px, transparent 1px)` 24px grid) on landing hero + empty states only, never behind text bodies.
- Elevation: shadows only in light theme (`0 1px 2px rgba(22,22,26,.06), 0 8px 24px rgba(22,22,264,.08)`); dark theme elevates by surface lightness, not shadow.

## 4. Motion system

### 4.1 Motion tokens
| Token | Value | Use |
|---|---|---|
| `dur/micro` | 120ms | hovers, presses, chip toggles |
| `dur/base` | 200ms | panels, popovers, tab switches |
| `dur/enter` | 320ms | message entrances, screen mounts |
| `dur/theme` | 750ms | the wave transition |
| `ease/exit` | `cubic-bezier(.22,1,.36,1)` | nearly everything (fast start, long glide) |
| `ease/enter` | `cubic-bezier(.3,.7,.3,1)` | entrances |
| `spring/chip` | stiffness 420, damping 32 | citation chips, toasts |

### 4.2 Micro-interaction catalog (the "minute details" inventory)
- **Citation chip** (`[S1] §4.2`): mono, amber; hover → lifts 1px + underline grows left→right 120ms; click → spring-pop into pinned state; panel opens (base). *This is the product's signature element — it gets the most polish.*
- **Streaming answer**: tokens fade-up in word batches (`opacity 0→1, translateY 3px→0`, 140ms stagger 18ms); caret `accent/hot` blinking; on `citations` event, chips spring in sequence 60ms apart.
- **Stage status line** ("searching → re-reading 25 passages → composing"): each stage = a mono chip that fills its hue when active (steven.com chips), with a 3-dot pulse; completed stages dim to ghost. This *is* the motion-graphic of the main screen.
- **Composer**: focus → border animates to `accent/primary` + subtle glow ring; ⌘↵ hint fades in on focus; disabled state loses 40% opacity with 120ms.
- **Upload tray**: drag-over → dotted border waves (2px offset sine dash animation); per-file progress = thin teal bar with ghost-percentage in mono; on `ready` → chunk count counts **up** with a rolling digit animation (moonsworth's number-flow).
- **Buttons**: press scale `.97` (80ms); primary teal fills darken 6% on hover; uppercase tracked ghost CTAs (ferrari) reveal an arrow that slides in 8px.
- **Source panel**: opens 200ms `ease/exit` with 12px slide; active chunk highlights by 3px left border in the chunk's stage hue; two-hop additions fade in *after* 300ms delay + labeled `added because "rule 63.7.4"` in mono — the detail that explains itself.
- **Skeletons**: shimmer 1.4s, warm-tinted (paper/petrol), never pure gray.
- **Trace viewer**: vertical timeline; each stage row draws its connector line 240ms on scroll-in; latency numbers count up; mono throughout.
- **Landing**: dot-grid parallax (±8px, scroll-linked, `ease/exit`); eval-stat counters roll on view (`87%` counting 0→87, 900ms); giant "Allcited" wordmark letters rise 12px staggered 40ms (cipher-scale typography).
- **Toasts**: bottom-center spring; error toasts carry maroon/rose left rail.

### 4.3 Ambient motion (subtle, GPU-only, ≤ repaint-friendly)
- Empty-state illustration: dot-grid + one floating citation chip (y-axis ±4px, 6s loop).
- Dark mode: surface layers breathe their border opacity 0.10↔0.16 (10s) — felt, not seen.
- All ambient loops pause on `document.hidden`.

### 4.4 The personality detail (bmwf3's lesson, used once)
Exactly one handwritten (Caveat) element exists: on an answer's "Why this answer?" margin, a small note in the user's context — e.g. *"found on p.23 — 2nd hop via rule 63.7.4"*. One touch of humanity per answer, never more.

## 5. The dark/light **wave transition** (centerpiece spec)

**Goal:** switching themes sweeps a fluid wave from the toggle across the viewport (750ms), like ink pouring over the page.

**Technique — View Transitions API + animated `clip-path: path()`:**
1. `ThemeToggle` captures click coordinates `(x, y)`; persists next theme.
2. Wrap the class flip in `document.startViewTransition(() => applyTheme(next))`.
3. In the transition's ready promise, animate the `::view-transition-new(root)` pseudo-element via WAAPI:
   - clip starts as a **wave-edged disc of radius 0** at `(x, y)`, ends covering the farthest corner (`R = hypot(max(x, W−x), max(y, H−y))`).
   - The edge is not a circle: precompute **5 keyframe paths** — same command structure (`M` + 8 `C` segments), radius growing `0.12R → 0.95R` with the wave crest phase rotating ~140° across keyframes, crest amplitude `6%` of current radius decaying to `2%` as it approaches full cover. Morph between them 750ms `ease/exit`.
   - Behind the wave edge, a 60px translucent gradient band (new-theme tint at 18% opacity) rides the boundary for fluid feel.
4. **Fallbacks:** no View Transitions (older Firefox/Safari) → 250ms crossfade + CSS color transitions on tokens. `prefers-reduced-motion: reduce` → instant swap with 120ms token crossfade (no wave). FOUC guard: inline `<head>` script reads localStorage/system pref before paint.
5. **Rules:** the wave runs on user toggle only (never on load); theme also flips `theme-color` meta; screenshots of the wave belong in the README demo GIF.

**Why this approach:** zero JS per frame for the actual theme change (browser composites the snapshot), single dependency-free primitive, and the path-morph gives the organic wave without canvas/WebGL.

## 6. Component inventory

**Base (design-system layer, built first, each with Storybook-style gallery page):** Button (primary/ghost/ferrari-uppercase), Input, Select, Modal, Toast, Table (0-radius mono headers), Skeleton, Tabs, Tooltip, CitationChip, StageChip, ThemeToggle, Spinner (mono dots).

**App components:** ChatStream, Message (assistant/user/refusal cards), Composer, UploadTray, SourcePanel, TraceViewer, ModelSettings (3-mode switcher, BYOK localStorage), LibraryGrid + LibraryDocCard, PricingTable, PlanBadge, FeedbackBar (👍/👎), EmptyState (dot-grid + floating chip), ErrorState (maroon rail + retry), AuthGate (Clerk).

## 7. Screens & states (every screen × 4 states)

| Screen | Loading | Empty | Error | Success |
|---|---|---|---|---|
| **Landing** (public, SEO) | — | first visit | — | hero: wordmark, rolling eval counters, ghost uppercase CTAs, dot-grid parallax |
| **Chat workspace** (core) | stage status line + skeletons | dot-grid empty state + 3 sample questions (clickable) | inline maroon error card + retry; `free_tier_busy` → BYOK upsell card | streaming answer, citation chips, feedback bar |
| **Upload tray** | per-file progress + rolling counter | dropzone with waving dotted border | `doc_unreadable`/`doc_too_large` toast + reason | "✅ 214 chunks · ready" (count-up) |
| **Source panel** | skeleton lines | "ask something first" | stale-session prompt → re-upload | highlighted chunk, page/section, two-hop labels |
| **Library** (auth) | grid skeletons | "save your first document" + AuthGate | Supabase-down degradation card (chat still works — say so) | doc cards; ask-my-library composer |
| **Pricing** | — | — | — | Free/Pro matrix, Stripe checkout, plan badge flips |
| **Settings / Models** | Ollama ping spinner | — | `ollama_unreachable` → greyed + tooltip (local-run only) | 3-mode radio; key masked with fingerprint |
| **Trace viewer** | timeline draw | — | partial-trace notice | full stage ledger, latency count-ups |

Global: sticky glass header (backdrop-blur, hairline border), ThemeToggle right; mobile: source panel becomes bottom sheet; 404 + offline pages (offline = dot-grid + "your documents are still here" for PWA cached sessions).

## 8. API & data layer

- Typed client generated from FastAPI's OpenAPI (`openapi-typescript`) — regenerated in CI, diffed in PRs.
- **TanStack Query** for all REST (queries/mutations; keys namespaced `['doc', id]`, `['library']`…); **Zustand** only for UI state (theme, panel open, model mode, BYOK key).
- SSE (query/summarize/ingest): native `EventSource`-style fetch-stream reader with `Last-Event-ID` resume; events mapped to store + status line; abort on stop/cancel.
- Error envelope `{error:{code,message,request_id}}` → typed error classes; every toast carries `request_id` (mono, copyable).
- Retry: idempotent GETs 3× backoff; SSE auto-reconnect 5s/15s/60s; BYOK/Ollama headers injected per-request, never logged.
- Auth: Clerk session → `Authorization` header; 401 → re-auth modal; protected actions only (save/export) per D-10.

## 9. Build steps (the pasted ROLE prompt's 15 steps, mapped & adapted)

### 9.1 Stack reconciliation (record in DECISIONS.md)
Keep **Next.js 14 App Router** (D-11: Vercel, SEO landing/pricing) — the ROLE prompt's Vite default yields. **Adopt from the ROLE prompt:** TypeScript strict, TanStack Query, Zustand, React Hook Form + Zod, Vitest + React Testing Library, Playwright, pre-commit, Lighthouse ≥90. Framer Motion + Tailwind (D-11) stay.

| # | Step | Delivers | Gate |
|---|---|---|---|
| 1 | Foundation | TS strict, path aliases, env config, lint/format, pre-commit | `next build` + lint clean on scaffold |
| 2 | **Design system** | §3 tokens in Tailwind config + CSS vars (both themes), base components, component gallery route `/dev` | gallery renders; token contrast pairs asserted by unit test |
| 3 | API layer | typed client, query/mutation hooks, error classes, SSE reader | mock-server tests: envelope→UI states |
| 4 | Auth + routing | Clerk provider, protected segments, session expiry modal | unauth save → sign-in; expired → re-auth |
| 5 | App shell | header, glass, ThemeToggle (+wave §5), error boundary, 404/offline | wave works both directions; reduced-motion honored |
| 6 | Feature screens | §7 order: Chat → Upload → SourcePanel → Library → Pricing → Settings → Trace; each ships all 4 states | each screen demoed against real backend |
| 7 | Forms | Zod schemas mirroring backend rules (size/mime/length), inline errors, double-submit guard | invalid upload rejected client-side pre-flight |
| 8 | Real-time | SSE stages→status line, token streaming, cancel, resume | kill network mid-answer → resumes via Last-Event-ID |
| 9 | Performance | route-level code-splitting, `next/font` (zero-layout-shift), lazy SourcePanel/Trace, virtualized library | Lighthouse ≥90 perf/a11y/SEO on 4G mobile; bundle budgets: first load JS < 180KB gz |
| 10 | Accessibility | full keyboard map, focus traps in modals/sheets, ARIA on chips/stages, AA §3.1–3.2 pairs, visible focus rings | manual + axe pass; screen-reader spot check of a cited answer |
| 11 | Security | CSP (no inline scripts except theme bootstrap), XSSI-safe SSE, BYOK in memory only, dep audit | CSP report-only → enforce; no key in storage beyond localStorage policy |
| 12 | Testing | Vitest+RTL units (chips, SSE reducer, theme logic); Playwright journeys: upload→ask→cite→panel, theme wave (screenshot diff), library isolation, mobile viewport | CI green; ≥80% core-logic coverage |
| 13 | Observability | client error boundary → backend `/v1/feedback` channel, Web Vitals report, funnel events (upload, first_question, cite_click, save, upgrade) | events visible in stats |
| 14 | Build/deploy | Vercel preview per PR, prod on main, env matrix, Lighthouse CI budget gate | preview URL per PR auto-commented |
| 15 | Docs | README design section (palette swatches, type, wave GIF), component guide, DECISIONS | stranger can reproduce the design system |

**Visual QA bonus:** after step 6 and before ship, run a browser-driven visual pass (browser-use `web-gui-tester`) — scripted screenshots of every screen × theme × state, diffed against expectations; catches the "minute details" regressions unit tests can't see.

## 10. Definition of done
Every §7 screen works against the live backend in all 4 states · wave transition ships with fallbacks + reduced-motion · Lighthouse ≥90 ×3 · Playwright green desktop+mobile · zero console errors in normal use · BYOK never leaves the browser · the component gallery at `/dev` documents the system · README shows the palette, type scale, and the wave GIF.

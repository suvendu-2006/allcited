# Allcited — Frontend Web Application

> Interactive, grounded document intelligence workspace built with Next.js 14, TypeScript, Tailwind CSS, and Framer Motion. Every claim stamped with verifiable receipts.

[![Next.js 14](https://img.shields.io/badge/NEXT.JS-14-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript 5](https://img.shields.io/badge/TYPESCRIPT-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS 3](https://img.shields.io/badge/TAILWIND-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/LICENSE-MIT-yellow?style=for-the-badge)](../LICENSE)

---

## Overview

The Allcited web interface is designed around radical transparency and verifiable provenance. Rather than presenting opaque answers, every response streams with bracketed citation chips (`[S1]`, `[S2]`) that open a dedicated **Receipts Drawer** to inspect the source document down to the exact section, page, and sentence.

---

## Key Features & Micro-Interactions

### 1. Receipts Drawer & Citation Verification
- Real-time Server-Sent Events (SSE) streaming with live token deltas and post-pass citation grounding.
- Clicking any `[S1]` or `[S2]` chip launches the slide-over Receipts Drawer, showing:
  - Exact source sentence highlighted in context.
  - Hierarchical breadcrumbs (`Document > Section > Clause`).
  - Scanned page OCR badges (`[S1] (OCR)`) when text was recovered via Tesseract/EasyOCR.
  - Multi-hop traversal indicators (`[S2 (2nd-hop)]`) for cross-referenced definitions.

### 2. Interactive 24-Hour Orbit Clock (`InteractiveOrbitClock.tsx`)
- Custom theme dial with scrubbable 24-hour angle physics:
  - `0°` (Top) → 12:00 (Noon, Day/Light theme)
  - `90°` (Right) → 18:00 (Sunset, Night/Dark theme)
  - `180°` (Bottom) → 00:00 (Midnight, Night/Dark theme)
  - `270°` (Left) → 06:00 (Sunrise, Day/Light theme)
- Automatic live-time lock with smooth orbital rotation and manual interactive scrub support.

### 3. Equilateral Triangle Theme Transition (`ThemeTransitionOverlay.tsx`)
- Mathematical centroid-centered canvas overlay that smoothly scales corner-to-corner during dark/light toggles without visual distortion.

### 4. Footer 'Receipt Underline' Hover (§4.2 Addendum)
- Pure CSS `scaleX` transform-origin swap across all 8 footer links:
  - **Hover Enter**: Draws 2px seal-red underline from left to right (`160ms`) + 1px lift (`120ms` `ease/exit`).
  - **Hover Exit**: Retracts from right to left (`200ms`) via origin-swap.
  - **`:focus-visible` Parity**: Full keyboard navigation support.
  - **Reduced Motion Fallback**: Disables transforms and line animations, preserving clean text color shift.

### 5. Clerk Authentication Integration
- Styled with dark mode tokens (`var(--bg-surface)` / `#171514`) eliminating unstyled development mode boxes and white containers.
- Original multi-colored Google logo preserved across all themes.
- Monochrome provider icons (GitHub, X) inverted with high contrast in dark mode.

---

## Design System Tokens ("Ink & Ember")

Allcited enforces strict WCAG AA contrast standards and a strict "zero green on chat screen" rule (§6.1):

| Token | Light Theme ("Paper") | Dark Theme ("Warm Ink") | Usage |
| :--- | :--- | :--- | :--- |
| `--bg-base` | `#F5F2EA` | `#0D0C0B` | Viewport backdrop |
| `--bg-surface` | `#FFFFFF` | `#171514` | Cards, modals, drawers |
| `--bg-sunken` | `#ECE8DC` | `#201D1B` | Input fields, code chips |
| `--ink-primary` | `#1A1918` | `#EFEAD9` | Primary typography |
| `--accent-primary` | `#A6362F` (Seal-Red) | `#E8765A` (Ember/Terracotta) | Primary actions, receipt stamps |
| `--accent-cite` | `#9A5B00` (Amber) | `#E8B04B` (Warm Amber) | Citation chips, failover badges |
| `--border` | `#E0DAD0` | `#2C2825` | Structural borders |

---

## Application Routes

- **`/` (Workspace)**: Document ingestion dropzone, SSE query streaming, receipts drawer, and provider settings modal.
- **`/library` (Shelf)**: Authenticated document repository with cross-document search and document deletion.
- **`/exam` (Public Test Scores)**: Self-grading public dashboard rendering the 11-row ablation matrix and 5-row chunking A/B benchmark.
- **`/how-it-works`**: Educational deep-dive into RAG, hybrid search, and citation verification.
- **`/pricing`**: Transparent pricing comparison (Free Guest vs. Pro subscription via Stripe).
- **`/product`**: Product capabilities, air-gapped security model, and format compatibility overview.
- **`/dev`**: Interactive design component gallery for live UI testing.

---

## Getting Started

### Prerequisites
- Node.js 18+ & npm
- Running backend API (local at `http://localhost:8000` or hosted on Hugging Face Spaces)

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Create a `.env.local` file in `web/`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

### 3. Start Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Verification & Testing

The frontend includes a 16-test automated verification suite asserting design token contrast, copy freeze, transition geometry, and hover mechanics:

```bash
# Run unit tests
npm test

# Run production build and type check
npm run build
```

---

## License

Distributed under the [MIT License](../LICENSE). Part of the [Allcited](https://github.com/suvendu-2006/allcited) project.

# Allcited — Frontend Architecture & Design System

> Production frontend architecture for Allcited built with Next.js 14 App Router, TypeScript 5, Tailwind CSS, and Framer Motion. Engineered for radical transparency, verifiable citations, WCAG AA compliance, and precision micro-interactions.

---

## 1. Architectural Foundations

The Allcited web interface is structured around immediate document comprehension without cognitive friction:

- **Framework:** Next.js 14 with React Server Components (RSC) and App Router.
- **Language:** TypeScript 5 in strict mode with full schema parity against backend Pydantic models.
- **Styling:** Tailwind CSS 3.4 driven by the custom **"Ink & Ember"** token architecture.
- **Motion:** Framer Motion 11 for layout animations, slide-over sheets, and canvas transitions.
- **Authentication:** Clerk React SDK customized with surface tokens and dark-mode brand preservation.

---

## 2. "Ink & Ember" Design Token System

Allcited strictly implements the **"Ink & Ember"** editorial design language, enforcing high-contrast paper and ink textures while maintaining strict compliance with WCAG AA accessibility standards.

### 2.1 Color Palette & Tokens

| Token Variable | Light Theme ("Paper") | Dark Theme ("Warm Ink") | Semantic Role |
| :--- | :--- | :--- | :--- |
| `--bg-base` | `#F5F2EA` | `#0D0C0B` | Viewport backdrop |
| `--bg-surface` | `#FFFFFF` | `#171514` | Cards, modals, slide-over drawers |
| `--bg-sunken` | `#ECE8DC` | `#201D1B` | Input fields, code chips, dropzones |
| `--ink-primary` | `#1A1918` | `#EFEAD9` | Primary typography and headings |
| `--ink-secondary` | `#5A554E` | `#A6A095` | Captions, metadata, secondary text |
| `--accent-primary` | `#A6362F` (Seal-Red) | `#E8765A` (Ember) | Primary actions, receipt stamps |
| `--accent-cite` | `#9A5B00` (Amber) | `#E8B04B` (Warm Amber) | Inline citation chips, failover badges |
| `--border` | `#E0DAD0` | `#2C2825` | Structural borders and dividers |

### 2.2 The "Zero Green on Chat Screen" Rule (§6.1)
Under section §6.1, Allcited prohibits green accenting in the active conversation stream. Status indicators, success badges, and NVIDIA NIM failover notifications use the warm amber token (`--accent-cite` / `#E8B04B`) to preserve the editorial paper-and-ink aesthetic.

### 2.3 WCAG AA Accessibility
- Every text-to-background pairing achieves a minimum contrast ratio of **4.5:1** for body text and **3.0:1** for large typography.
- Keyboard navigation is fully supported across all interactive elements with visible focus rings (`:focus-visible`).
- All interactive controls feature semantic ARIA labels (`aria-expanded`, `aria-controls`, `role="region"`).

---

## 3. Application Route Directory

| Route | View Component | Core Purpose |
| :--- | :--- | :--- |
| `/` | `app/page.tsx` | Main workspace: multi-format file ingestion, SSE query streaming, chat feed, and Receipts Drawer. |
| `/library` | `app/library/page.tsx` | Authenticated shelf: saved document management, multi-document synthesis, and document deletion. |
| `/exam` | `app/exam/page.tsx` | Self-grading public dashboard rendering the 11-row ablation matrix and 5-row chunking A/B benchmark. |
| `/how-it-works` | `app/how-it-works/page.tsx` | Interactive educational guide explaining hybrid retrieval, cross-encoders, and citation verification. |
| `/pricing` | `app/pricing/page.tsx` | Transparent plan breakdown (Free Guest vs. Pro tier with Stripe integration). |
| `/product` | `app/product/page.tsx` | Enterprise capabilities, zero cloud egress air-gap mode, and format compatibility matrix. |
| `/dev` | `app/dev/page.tsx` | Interactive component gallery for design system token and animation testing. |

---

## 4. Key Subsystems & Precision Micro-Interactions

### 4.1 The Receipts Slide-Over Drawer (`ReceiptsDrawer.tsx`)
The centerpiece of Allcited's transparency contract. Clicking any inline citation chip (`[S1]`, `[S2]`) in the chat window triggers the slide-over drawer:

```
┌──────────────────────────────────────────────┐
│  Receipts Drawer                      [✕]    │
├──────────────────────────────────────────────┤
│  [S1] Employee_Handbook.pdf • Page 14        │
│  Handbook > Section 4: Benefits > 4.2 Leave  │
├──────────────────────────────────────────────┤
│  "...Employees may carry forward up to 10    │
│  <mark>unspent annual leave days</mark>      │
│  into the subsequent fiscal calendar..."     │
├──────────────────────────────────────────────┤
│  Provenance Badges:                          │
│  • [2nd-hop] Resolved via Rule 63.7.4        │
│  • [OCR] Extracted via Tesseract 5.3         │
└──────────────────────────────────────────────┘
```

- **Exact Highlight:** Contextually marks the target sentence within the full retrieved chunk.
- **Hierarchical Breadcrumbs:** Renders the structural path (`Doc > Section > Clause`).
- **Provenance Badges:**
  - `[S1] (OCR)`: Displayed if text was extracted via Tesseract/EasyOCR fallback.
  - `[S2 (2nd-hop)]`: Displayed if chunk was brought in via graph reference expansion.

---

### 4.2 Interactive 24-Hour Orbit Clock (`InteractiveOrbitClock.tsx`)
A custom circular dial component controlling application theme and demonstrating time-of-day orbital mechanics:

- **Angle Physics & Time Mapping:**
  - `0°` (Top / 12 o'clock) $\to$ **12:00 (Noon)**: Day/Light theme ("Paper").
  - `90°` (Right / 3 o'clock) $\to$ **18:00 (Sunset)**: Evening transition.
  - `180°` (Bottom / 6 o'clock) $\to$ **00:00 (Midnight)**: Night/Dark theme ("Warm Ink").
  - `270°` (Left / 9 o'clock) $\to$ **06:00 (Sunrise)**: Morning transition.
- **Interaction Modes:**
  - **Live Lock:** Automatically locks orbital rotation to the client's actual system clock.
  - **Interactive Scrubbing:** Users can click and drag the celestial sun/moon bead around the dial to manually scrub time and toggle themes dynamically.
  - Utilizes pointer capture (`setPointerCapture`) to prevent mouse slippage during rapid circular drag gestures.

---

### 4.3 Equilateral Triangle Theme Transition Overlay (`ThemeTransitionOverlay.tsx`)
Rather than relying on basic CSS opacity fades or circular radial clips, theme toggles trigger a mathematical equilateral triangle canvas transition:

- **Mathematical Centroid Geometry:**
  - Computes the center of the viewport $(x_c, y_c)$.
  - Projects an expanding equilateral triangle whose vertices scale outward at $120^\circ$ angles until the bounding radius circumscribes the viewport corners:
    $$R_{\text{circum}} = \sqrt{w^2 + h^2}$$
- **Aspect-Ratio Invariance:**
  - Guaranteed zero distortion across mobile vertical displays and ultra-wide desktop monitors.
  - Smooth animation curve (`cubic-bezier(0.16, 1, 0.3, 1)`) completing in 380ms.

---

### 4.4 Footer 'Receipt Underline' Hover (§4.2 Addendum)
All navigation links in `Footer.tsx` feature an editorial pure CSS underline interaction mimicking an authentic ink pen stroke:

- **Hover Enter (160ms):**
  - Sets `transform-origin: left center`.
  - Scales `scaleX(0) -> scaleX(1)` using a 2px seal-red line (`--accent-primary`).
  - Lifts the text 1px vertically (`translateY(-1px)`) over 120ms with ease-out physics.
- **Hover Exit (200ms):**
  - Automatically swaps `transform-origin: right center`.
  - Retracts `scaleX(1) -> scaleX(0)` from left to right, creating a natural pull-away effect.
- **Focus & Reduced Motion Parity:**
  - Fully accessible via `:focus-visible` keyboard rings.
  - Respects `@media (prefers-reduced-motion: reduce)`, instantly falling back to simple color swaps without transform animation.

---

### 4.5 Clerk Authentication Styling
- Form containers, modals, and user profile buttons are styled using dark-mode tokens (`var(--bg-surface)` / `#171514`), eliminating default white containers in dark mode.
- Preserves the official multi-color Google logo across both light and dark themes.
- Dynamically inverts monochrome third-party provider icons (GitHub, X) to maintain high contrast.

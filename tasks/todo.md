# Revised Tasks: UI Polish, Rate Limiting, & Clerk Light Mode Hardening

- [x] Task 1: Verify Sound is 100% removed across the codebase (confirmed 0 Web Audio APIs / audio assets)
- [x] Task 2: Stabilize Hero Buttons by unwrapping `Try it free` and `Star us on GitHub` in page.tsx and removing unused `MagneticButton` import
- [x] Task 3: Fix Ticker Bar by deleting hover pause rule in globals.css and removing `group` from ticker section in page.tsx
- [x] Task 4: Smooth Footer Underline without breaking test suite (preserve required origin-swap strings, add will-change and subpixel rendering)
- [x] Task 5: Implement Free Tier Rate Limiting (10 q/hr) with BYOK exemption, isolated `<RateLimitBanner />`, Date.now() calculation, storage event sync, and Pricing page beta notice
- [x] Task 6: Implement Clerk Light Mode hardening using CSS design tokens (`var(--ink-primary)`, `var(--bg-surface)`, `var(--border)`) without raw hexes, neutralizing dark variables in light mode
- [x] Checkpoint: Run automated tests (`npm test --prefix web`), production build (`npm run build --prefix web`), and verify zero regressions

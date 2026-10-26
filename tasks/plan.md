# Revised Implementation Plan: UI Polish, Rate Limiting, & Clerk Light Mode

## Overview
Address all 6 user requirements incorporating critical architectural fixes identified in the plan review:
1. Sound: Zero audio assets or Web Audio APIs remain.
2. Stable Hero Buttons: Unwrap buttons and remove unused `MagneticButton` import.
3. Continuous Ticker: Remove hover pause and section `group` class.
4. Smooth Footer Link Underline: Retain exact tested origin-swap strings while smoothing hardware-accelerated transitions.
5. Rate Limiting (10 q/hr): Exclude BYOK users, isolate countdown timer component to prevent re-render stutter, use `Date.now()` timestamp diffs, sync across tabs with `storage` events, and update Pricing page beta notices.
6. Clerk Light Mode: Use design tokens (`var(--ink-primary)`, `var(--bg-surface)`, etc.) without hardcoded hexes to override Clerk styles on `:root:not(.dark)`.

## Task List
See [todo.md](file:///Users/suvendu/Downloads/allcited/tasks/todo.md).

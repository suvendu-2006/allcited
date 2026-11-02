## Description

Please include a summary of the change, motivation, and context. List any dependencies that are required for this change.

Closes # (issue)

---

## Type of Change

Please mark the options that are relevant:

- [ ] **Bug fix** (non-breaking change which fixes an issue)
- [ ] **New feature** (non-breaking change which adds functionality)
- [ ] **Breaking change** (fix or feature that would cause existing functionality to not work as expected)
- [ ] **Refactoring / Performance** (code improvement without functional change)
- [ ] **Documentation update** (README, architecture specs, API docs)
- [ ] **CI / Tooling** (GitHub Actions, build scripts, linters)

---

## Pre-Submission Verification & Checklist

Please verify each item before requesting a review:

- [ ] My code adheres to the project's coding standards:
  - Backend: Ruff formatted (100-character line length limit), type annotated
  - Frontend: Next.js ESLint passed, TypeScript strict types, "Ink & Ember" design token compliance
- [ ] I have executed the test suites locally and all tests pass:
  - `cd api && pytest tests/`
  - `cd web && npm test`
- [ ] I have executed linters and static checks:
  - `cd api && ruff check .`
  - `cd web && npm run lint`
- [ ] I have verified the frontend production build passes (`cd web && npm run build`)
- [ ] I have added unit or integration tests that prove my fix is effective or that my feature works
- [ ] I have updated relevant documentation, docstrings, or schemas
- [ ] No API keys, secret credentials, or `.env` files are tracked in this commit

---

## Verification Evidence

Please paste terminal command outputs or test run summaries verifying the change:

```text
# Example:
# cd api && pytest tests/
# cd web && npm test
```

---

## Screenshots or UI Evidence (if applicable)

If this pull request introduces or modifies UI components (Next.js / Tailwind CSS), please attach before/after screenshots or screen recordings showing compliance with "Ink & Ember" design tokens in both light and dark modes.

# Contributing to Allcited

Thank you for your interest in contributing to **Allcited**! We are committed to building an enterprise-grade, privacy-first legal research and statutory citation engine. We welcome contributions from developers, legal technologists, security researchers, and document processing specialists.

This guide outlines our development workflow, coding and architecture standards, testing protocols, and pull request procedures.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Prerequisites & System Dependencies](#prerequisites-system-dependencies)
- [Local Development Setup](#local-development-setup)
  - [Clone the Repository](#clone-the-repository)
  - [Backend Setup (FastAPI & Python 3.12)](#backend-setup-fastapi-python-312)
  - [Frontend Setup (Next.js 14 & Node.js 22 LTS)](#frontend-setup-nextjs-14-nodejs-22-lts)
  - [Environment Configuration](#environment-configuration)
- [Coding Standards & Conventions](#coding-standards-conventions)
  - [Python & Backend Standards](#python-backend-standards)
  - [Frontend & TypeScript Standards](#frontend-typescript-standards)
  - ["Ink & Ember" Design Tokens](#ink-ember-design-tokens)
- [Git Workflow & Conventional Commits](#git-workflow-conventional-commits)
- [Testing & Quality Verification](#testing-quality-verification)
- [Pull Request Checklist](#pull-request-checklist)
- [Reporting Issues & Getting Help](#reporting-issues-getting-help)

---

## Code of Conduct

All contributors and maintainers are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms, fostering an inclusive, welcoming, and harassment-free community.

---

## Prerequisites & System Dependencies

Before setting up Allcited locally, ensure your machine has the following dependencies:

| Dependency | Minimum Version | Notes |
|------------|-----------------|-------|
| **Python** | `3.12+` | Tested on Python 3.12.x; required for FastAPI backend and ingestion pipelines |
| **Node.js** | `22.x LTS` (or `20.x LTS`) | Required for Next.js 14 frontend; includes `npm 10+` |
| **Tesseract OCR** | `5.x` | Required for scanned PDF/document ingestion; must include English and Hindi models |
| **Git** | `2.40+` | Required for version control |
| **Docker** *(Optional)* | `24.x+` | Recommended for running local PostgreSQL / Supabase, Redis, and vector stores |

### Installing Tesseract OCR

- **macOS** (via Homebrew):
  ```bash
  brew install tesseract tesseract-lang
  ```
- **Ubuntu / Debian**:
  ```bash
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
  ```
- **Windows**:
  Download and install the official binary installer from UB-Mannheim, ensuring the English and Hindi language data packages are selected, and add the installation folder to your system `PATH`.

---

## Local Development Setup

### Clone the Repository

```bash
git clone https://github.com/suvendu-2006/allcited.git
cd allcited
```

### Backend Setup (FastAPI & Python 3.12)

We recommend using a dedicated virtual environment:

```bash
cd api
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install ruff pytest
```

Verify your backend environment:
```bash
ruff check .
pytest tests/
```

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup (Next.js 14 & Node.js 22 LTS)

Open a separate terminal for the web workspace:

```bash
cd web
npm install # or npm ci for reproducible lockfile installation
```

Verify the frontend build and test suites:
```bash
npm test
npm run lint
npm run build
```

Start the Next.js development server:
```bash
npm run dev
```

The web application will be accessible at `http://localhost:3000`.

### Environment Configuration

Copy the example environment files and adjust variables for your local services:

```bash
# Root / backend configuration
cp api/.env.example api/.env

# Web configuration (if required)
cp .env.example .env.local
```

Key configuration parameters include:
- `CLERK_SECRET_KEY` & `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: Clerk authentication credentials.
- `DATABASE_URL` / `SUPABASE_URL`: PostgreSQL / Supabase connection strings.
- `NVIDIA_API_KEY` / `OPENAI_API_KEY`: Model provider keys (mockable in local testing).
- `EMBEDDING_PROVIDER`: Vector embedding service selection (`local`, `nvidia`, `openai`).
- `AIR_GAPPED_MODE`: Set to `true` to disable all third-party external model network requests.

---

## Coding Standards & Conventions

### Python & Backend Standards

- **Formatter & Linter:** We strictly use **Ruff**. Configuration is centralized in `pyproject.toml`.
  - **Line Length:** 100 characters (`line-length = 100`).
  - **Lint Rules:** Pyflakes (`F`), pycodestyle (`E`, `W`), isort (`I`). Line length warnings (`E501`) are deferred to the formatter.
- **Type Hints:** All public functions, method signatures, and class variables must include strict Python type hints.
- **Data Validation:** Use Pydantic v2 schemas for all request/response validation, API contracts, and settings models.
- **Security Best Practices:**
  - Never execute arbitrary strings via `eval()`, `exec()`, or unsanitized shell commands.
  - All external URL requests must pass through SSRF filters (`is_safe_url`) that block private CIDRs, link-local metadata endpoints (`169.254.169.254`), and loopback addresses.
  - All LLM prompts must employ delimiter isolation and input sanitization to prevent injection vulnerabilities.
  - Sensitive personal identifying information (PII) must be redacted before model inference.

### Frontend & TypeScript Standards

- **Framework:** Next.js 14 with the App Router architecture.
- **TypeScript:** Strict type checking enabled (`strict: true` in `tsconfig.json`). Avoid `any`; use discriminating unions and precise interfaces.
- **Components:** Functional components with React 18 hooks. Keep business logic and data fetching separated from visual presentation.
- **Styling:** Tailwind CSS combined with `clsx` and `tailwind-merge` (`cn` utility).

### "Ink & Ember" Design Tokens

All UI contributions must respect the **Ink & Ember** design system tokens to ensure high contrast, readability, and WCAG AA/AAA compliance:

| Token | Light Theme ("Paper") | Dark Theme ("Warm Ink") | Semantic Role |
|-------|-----------------------|-------------------------|---------------|
| `bg-base` | `#F5F2EA` | `#0D0C0B` | Primary surface background |
| `ink-primary` | `#1A1918` | `#EFEAD9` | Primary typography (Contrast > 14:1) |
| `accent-primary` | `#A6362F` (Seal Red) | `#E8765A` (Lifted Seal) | Primary action buttons & key highlights (Contrast > 4.5:1) |
| `accent-cite` | `#9A5B00` (Amber) | `#E8B04B` (Amber Glow) | Statutory citations & verification chips |

Contrast ratios are asserted in automated unit tests (`web/test/tokens.test.mjs`). Do not alter colors without running token assertions.

---

## Git Workflow & Conventional Commits

We follow a feature-branch workflow paired with the **Conventional Commits** specification:

### Branch Naming Conventions

- `feat/short-description`: New feature or capability
- `fix/short-description`: Bug fix
- `docs/short-description`: Documentation additions or corrections
- `refactor/short-description`: Code refactoring without behavior change
- `test/short-description`: Adding or refactoring test suites
- `perf/short-description`: Performance improvements
- `ci/short-description`: CI/CD workflow changes

### Conventional Commit Message Format

Commit messages must follow the structure:
```text
<type>(<optional scope>): <imperative subject>

[optional body explaining context and motivation]

[optional footer(s), e.g., Fixes #123]
```

**Common types:**
- `feat`: A new feature (e.g., `feat(retrieval): add cross-encoder statutory reranking`)
- `fix`: A bug fix (e.g., `fix(ocr): handle multi-column scanned PDF alignment`)
- `docs`: Documentation only changes (e.g., `docs: update API authentication guides`)
- `refactor`: Code changes that neither fix a bug nor add a feature (e.g., `refactor(db): streamline async session pool management`)
- `test`: Adding missing tests or correcting existing tests (e.g., `test(auth): add JWT expiration edge case tests`)
- `perf`: Code change that improves performance (e.g., `perf(parser): cache regex patterns for citation lookup`)
- `chore`: Maintenance tasks, dependencies, tooling updates

---

## Testing & Quality Verification

Before committing changes or opening a pull request, run the complete verification suite locally:

### 1. Backend Linting & Tests
```bash
cd api

# Format & Lint
ruff check .
ruff format --check .

# Execute test suite
pytest tests/
```

### 2. Frontend Linting, Tests & Build
```bash
cd web

# Run unit tests
npm test

# Run ESLint
npm run lint

# Verify TypeScript compilation and production build
npm run build
```

---

## Pull Request Checklist

When submitting a Pull Request (PR), verify each item:

- [ ] **Branch updated:** Rebased on or merged with the latest `main` branch.
- [ ] **Conventional commit messages:** All commits follow the conventional format.
- [ ] **Issue linked:** Issue reference included in the PR description (e.g., `Closes #42`).
- [ ] **Backend verification:** `cd api && ruff check . && pytest tests/` passes with 0 failures.
- [ ] **Frontend verification:** `cd web && npm test && npm run lint && npm run build` passes with 0 errors.
- [ ] **Tests included:** Added unit or integration tests demonstrating bug reproduction or feature validation.
- [ ] **Documentation updated:** Relevant documentation, docstrings, or schemas updated.
- [ ] **No secrets:** Verified that no API keys, private credentials, or personal secrets are included in commits.

---

## Reporting Issues & Getting Help

- **Bug Reports:** Open an issue using our [Bug Report Form](https://github.com/suvendu-2006/allcited/issues/new?template=bug_report.yml).
- **Feature Requests:** Suggest improvements via our [Feature Request Form](https://github.com/suvendu-2006/allcited/issues/new?template=feature_request.yml).
- **Security Vulnerabilities:** Do **not** open public issues for security vulnerabilities. Review our [Security Policy](SECURITY.md) and report privately.
- **Discussions & Questions:** Join the community discussion board or reach out via maintainer contact.

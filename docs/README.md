# Allcited — Documentation Hub

Welcome to the centralized documentation directory for **Allcited** — the production-grade, air-gapped document intelligence platform engineered for zero hallucinations and verifiable bracketed receipts down to the exact section, page, and sentence.

---

## Documentation Index

Explore the comprehensive subsystem documentation:

| Document | Scope | Key Focus Areas |
| :--- | :--- | :--- |
| [**Architecture**](architecture.md) | **System Topology & RAG Pipeline** | Hybrid BM25 + FAISS retrieval, Reciprocal Rank Fusion ($k=60$), Cross-Encoder re-ranking (`ms-marco-MiniLM-L-6-v2`), Two-Hop Graph expansion, Brain client failover (Groq → NVIDIA NIM → Ollama), and Architectural Decision Log (D-01 to D-32). |
| [**API Reference**](api.md) | **REST & SSE Endpoint Contracts** | Complete OpenAPI endpoint specifications (`/v1/health`, `/v1/readyz`, `/v1/ingest`, `/v1/ingest/url`, `/v1/query`, `/v1/summarize`, `/v1/library/*`), request/response JSON schemas, SSE streaming protocol events, and error envelope contract. |
| [**Frontend Architecture**](frontend.md) | **Web Workspace & UI System** | Next.js 14 App Router, "Ink & Ember" design token system, Receipts Drawer, WCAG AA accessibility, and micro-interactions (Interactive 24-Hour Orbit Clock dial, equilateral triangle geometry, footer physics). |
| [**Security Model**](security.md) | **Enterprise Hardening & Defense** | Zero cloud egress air-gapped mode, SSRF defense (private IP & `169.254.169.254` blocklist), delimiter-isolated prompt injection neutralization, PII masking, Clerk JWKS auth, PostgREST RLS isolation, and sliding-window rate limiting. |
| [**Deployment Guide**](deployment.md) | **Production Runbooks & Ops** | Runbooks for Hugging Face Spaces (backend container), Vercel (frontend), and air-gapped Docker Compose with local Ollama (`qwen:7b`). Full environment variables reference table and Node.js 22+ (LTS) requirement note. |
| [**Evaluation & Benchmarks**](evaluation.md) | **Empirical Verification** | 46-question evaluation fixture, 11-row ablation matrix, 5-row chunking A/B test, P1–P4 RAG trap taxonomy, and reproducibility commands. |

---

## High-Level System Topology

```
                    ┌───────────────────────────────┐
                    │      Frontend Client (web/)   │
                    │   Next.js 14, TypeScript, CSS │
                    │   Hosted on Vercel Edge Infra │
                    └───────────────┬───────────────┘
                                    │
                       HTTPS / SSE Query Streams
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      Backend Engine (api/)    │
                    │   FastAPI, Python 3.12 Slim   │
                    │   Hugging Face Spaces / Docker│
                    └───────────────┬───────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
  [ Hybrid Retrieval ]      [ Ingestion & OCR ]        [ Multi-Brain Failover ]
  - BM25Okapi Lexical       - PyPDF / python-docx      - Primary: Groq Cloud LLM
  - FAISS Dense Vector      - python-pptx / openpyxl   - Failover: NVIDIA NIM (D-32)
  - Reciprocal Rank Fusion  - Dual OCR: Tesseract /    - Local: Ollama (Air-gapped)
  - Cross-Encoder Rerank      EasyOCR                  - BYOK: Browser-side keys
```

---

## Core Engineering Principles

1. **Radical Grounding & Zero Hallucination:** Every factual claim must be backed by an inline citation chip (`[S1]`, `[S2]`). Any assertion lacking verifiable attribution is stripped during the post-pass audit.
2. **Deterministic Receipts:** Clicking any citation chip opens the slide-over Receipts Drawer displaying the source text highlighted in context, hierarchical breadcrumbs (`Document > Section > Clause`), page numbers, and OCR / 2nd-hop provenance flags.
3. **P1–P4 RAG Trap Elimination:** Engineered to conquer boundary straddles (P1), distractor clauses (P2), two-hop cross references (P3), and multi-aspect composite queries (P4) without relying on heavy or opaque multi-agent frameworks.
4. **Air-Gap Capability:** Full offline functionality with zero external dependencies when running via Docker Compose with local Ollama models.
5. **Radical Transparency:** Evaluation scores and ablation comparisons are graded in public against fixed empirical fixtures.

---

## Quick Navigation Links

- **Main Repository Root:** [`../README.md`](../README.md)
- **Backend Service:** [`../api`](../api)
- **Frontend Workspace:** [`../web`](../web)
- **Deployment Scripts:** [`../deploy`](../deploy)
- **Evaluation Fixtures & Results:** [`../eval`](../eval)

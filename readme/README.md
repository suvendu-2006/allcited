# Allcited Documentation Hub

Welcome to the centralized documentation directory for **Allcited**. All project specifications, subsystem readmes, and deployment guides are indexed here in a clear and structured format.

---

## Documentation Index

| Document | Subsystem / Scope | Focus Areas |
| :--- | :--- | :--- |
| [**`project.md`**](project.md) | **System Architecture & Eval** | Full repository overview, 11-row ablation matrix, P1–P4 RAG trap mitigations, chunking A/B benchmarks, and air-gapped security model. |
| [**`api.md`**](api.md) | **Backend API & RAG Engine** | FastAPI endpoints, hybrid BM25 + FAISS retrieval, Reciprocal Rank Fusion (RRF), cross-encoder re-ranking, and model loading. |
| [**`web.md`**](web.md) | **Frontend Web Application** | Next.js 14, Tailwind CSS ("Ink & Ember" tokens), interactive 24-hour orbit clock, receipts drawer, and Clerk authentication. |
| [**`deploy.md`**](deploy.md) | **Deployment & Infrastructure** | Hugging Face Spaces Docker containerization, Vercel frontend hosting, environment variables, and health check monitoring. |

---

## System Architecture Diagram

```
                    ┌─────────────────────────┐
                    │    Frontend (web/)      │
                    │ Next.js 14, TypeScript  │
                    │ Hosted on Vercel        │
                    └────────────┬────────────┘
                                 │
                   HTTPS / SSE Query Streams
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Backend (api/)      │
                    │ FastAPI, Python 3.12    │
                    │ Hugging Face Spaces     │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
 [ Hybrid Retrieval ]    [ Model Cache ]          [ External Services ]
 - BM25Okapi Lexical     - all-MiniLM-L6-v2       - Groq Cloud LLM
 - FAISS Dense Vector    - ms-marco-MiniLM-L-6-v2 - NVIDIA NIM (Failover)
 - Reciprocal Rank Fusion                         - Clerk Authentication
 - Cross-Encoder Rerank                           - Supabase Database
                                                  - Stripe Billing
```

---

## Quick Links

- **Main Repository Root:** [`../README.md`](../README.md)
- **Frontend Source Code:** [`../web`](../web)
- **Backend Source Code:** [`../api`](../api)
- **Deployment Configurations:** [`../deploy`](../deploy)
- **Evaluation Fixtures & Results:** [`../eval`](../eval)

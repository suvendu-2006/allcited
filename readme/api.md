# Allcited — Backend API & RAG Engine

> High-performance, air-gapped FastAPI backend serving grounded document Q&A with verifiable receipts, cross-encoder re-ranking, and zero cloud egress.

[![Python 3.12](https://img.shields.io/badge/PYTHON-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FASTAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![FAISS](https://img.shields.io/badge/VECTOR%20STORE-FAISS-blue?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/LICENSE-MIT-yellow?style=for-the-badge)](../LICENSE)

---

## Architecture Overview

The Allcited backend is engineered to eliminate the four universal RAG failure modes (P1: boundary straddle, P2: distractors, P3: two-hop references, P4: multi-aspect composite) without depending on opaque multi-agent frameworks.

```
                        [ Ingest / Upload ]
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
   Digital Documents                           Scanned PDFs / Images
(PDF, DOCX, PPTX, XLSX, HTML)                (Tesseract / EasyOCR Dual Engine)
           │                                           │
           └─────────────────────┬─────────────────────┘
                                 ▼
                     Hierarchical Chunking
              (300 tokens + 15% sliding window)
             Prepend breadcrumbs: Doc > Sec > Clause
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
      BM25 Index                                FAISS Dense Index
  (BM25Okapi lexical)                  (all-MiniLM-L6-v2, 384-dim L2)
           │                                           │
           └─────────────────────┬─────────────────────┘
                                 ▼
                    Reciprocal Rank Fusion (RRF)
                                 │
                                 ▼
                     Cross-Encoder Re-Ranking
                  (ms-marco-MiniLM-L-6-v2)
                Score floor filtering (>= 0.05)
                                 │
                                 ▼
                    Two-Hop Cross-Reference Map
              Resolves referenced rules/schedules ([S2])
                                 │
                                 ▼
                   Grounded Generation (Groq LLM)
             (Failover to NVIDIA NIM LLaMA-3.2 Vision)
                                 │
                                 ▼
                    Strict Citation Post-Pass
            Strips any claim lacking verified bracketed receipts
                                 │
                                 ▼
                   Server-Sent Events (SSE) Stream
```

---

## Core Pipeline Features

### 1. Ingestion & Dual OCR Provider
- Multi-format parser: PDF, DOCX, PPTX, XLSX, HTML/URL, Markdown, and TXT.
- Pluggable OCR interface (`OCR_PROVIDER=easyocr` or `OCR_PROVIDER=tesseract`) for scanned documents.
- Structure-preserving tables and section header extraction.

### 2. Hybrid Retrieval with RRF
- Combines sparse BM25 lexical recall with dense FAISS vector semantic search.
- Merges candidate ranks using Reciprocal Rank Fusion ($k=60$):
  $$RRF(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$$

### 3. Cross-Encoder Re-Ranking
- Pre-trained `cross-encoder/ms-marco-MiniLM-L-6-v2` scores full token interactions across query-passage pairs.
- Calibrated score floor filters out irrelevant distractors before prompt assembly.

### 4. Deterministic Citation Grounding
- System prompt enforces inline citation chips `[S1]`, `[S2]`.
- Post-pass citation audit checks every assertion against retrieved context.
- Unattributed claims are automatically stripped before final emission.

### 5. Multi-Hop Graph Traversal
- Identifies cross-referenced clauses (e.g., *"governed by Rule 14.2"*) during ingestion.
- Expands query retrieval to automatically pull referenced target passages stamped as `[S2 (2nd-hop)]`.

### 6. Zero-Token Semantic Cache
- Computes embedding cosine similarity against prior evaluated queries.
- Answers cache hits in **< 100 ms** with zero LLM API cost.

---

## API Endpoints Contract

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/v1/health` | Service liveness probe returning environment status |
| `GET` | `/v1/readyz` | Readiness check (database, models, vector store health) |
| `POST` | `/v1/ingest` | Uploads and indexes documents (`multipart/form-data`) |
| `POST` | `/v1/query` | SSE streaming endpoint delivering token deltas & receipts |
| `GET` | `/v1/trace/{session_id}` | Detailed latency and step execution telemetry |
| `GET` | `/v1/cache/stats` | Semantic cache hit/miss statistics |
| `POST` | `/v1/payments/webhook` | Stripe subscription lifecycle webhook |
| `POST` | `/v1/telegram/webhook` | Telegram bot query integration |

---

## Environment Variables

| Variable | Required | Description |
| :--- | :---: | :--- |
| `GROQ_API_KEY` | Yes | Primary LLM generation key (Llama-3.3-70b-versatile) |
| `NVIDIA_API_KEY` | Optional | NVIDIA NIM API key for cloud brain failover (Decision D-32) |
| `CLERK_SECRET_KEY` | Optional | Auth validation key |
| `SUPABASE_URL` | Optional | Supabase database endpoint |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | Supabase service key for persistent document library |
| `STRIPE_SECRET_KEY` | Optional | Stripe billing integration key |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram Bot Father token |
| `OCR_PROVIDER` | No | `tesseract` (default) or `easyocr` |
| `ENVIRONMENT` | No | `development` or `production` |

---

## Local Development & Testing

### 1. Set Up Python Environment
```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Run the Test Suite
```bash
pytest tests/ -v
```

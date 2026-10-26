# Allcited — Production Deployment Guide

> Step-by-step deployment and operational guide for Allcited, covering the Hugging Face Spaces Docker container backend and the Vercel Next.js 14 frontend.

[![Hugging Face Spaces](https://img.shields.io/badge/DEPLOYMENT-HF%20SPACES-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/spaces)
[![Vercel](https://img.shields.io/badge/HOSTING-VERCEL-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Docker](https://img.shields.io/badge/CONTAINER-DOCKER-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

---

## Architecture Topology

```
   [ Client Browser ]
           │
           ▼
 [ Vercel Production ]
  https://allcited.vercel.app  (Next.js 14 Web Application)
           │
           │ HTTPS / Server-Sent Events (SSE)
           ▼
 [ Hugging Face Spaces ]
  https://subh-007-allcited-api.hf.space  (FastAPI Docker Container, port 8000)
           │
           ├── Embedding: all-MiniLM-L6-v2 (local LFS pre-loaded)
           ├── Re-ranking: ms-marco-MiniLM-L-6-v2 (local LFS pre-loaded)
           ├── Vector Index: FAISS L2 (in-memory per session)
           └── Lexical Index: BM25Okapi
```

---

## 1. Backend Deployment (Hugging Face Spaces)

The backend runs as a containerized FastAPI application on Hugging Face Spaces with Docker SDK.

### Docker Configuration
- **Base image:** Python 3.12 slim
- **Exposed Port:** `8000` (`app_port: 8000`)
- **System packages:** `tesseract-ocr`, `libgl1`, `poppler-utils`
- **Model weights:** Local Git-LFS caching under `api/models/` ensures sub-30s cold boot times without external network downloads.

### Deployment Script
From the project root:
```bash
export SPACE_URL=https://huggingface.co/spaces/<YOUR_HF_USERNAME>/allcited-api
bash deploy/hf-space/deploy.sh
```

### Hugging Face Space Secrets & Variables
Set these via **HF Space Settings → Variables and secrets**:

| Key | Type | Description |
| :--- | :---: | :--- |
| `GROQ_API_KEY` | Secret | Primary generation LLM (Llama-3.3-70b-versatile) |
| `NVIDIA_API_KEY` | Secret | Failover brain API key (Decision D-32) |
| `CLERK_SECRET_KEY` | Secret | Clerk user session validation |
| `CLERK_PUBLISHABLE_KEY` | Variable | Clerk public frontend key |
| `SUPABASE_URL` | Variable | Supabase PostgreSQL project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Secret | Supabase admin key for document storage |
| `STRIPE_SECRET_KEY` | Secret | Stripe API secret for checkout sessions |
| `STRIPE_WEBHOOK_SECRET` | Secret | Stripe webhook signing secret |
| `TELEGRAM_BOT_TOKEN` | Secret | Telegram bot authentication token |
| `CORS_ORIGINS` | Variable | `https://allcited.vercel.app,http://localhost:3000` |
| `ENVIRONMENT` | Variable | `production` |

---

## 2. Frontend Deployment (Vercel)

The frontend is deployed on Vercel with automatic continuous integration on pushes to `main`.

### Root Directory Configuration
In Vercel Project Settings:
- **Root Directory:** `web`
- **Framework Preset:** Next.js
- **Build Command:** `next build`
- **Output Directory:** `.next`

### Vercel Environment Variables
Set these in **Vercel Project Settings → Environment Variables**:

| Variable | Value / Notes |
| :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://subh-007-allcited-api.hf.space` (or your custom API domain) |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_live_...` or `pk_test_...` |
| `CLERK_SECRET_KEY` | `sk_live_...` or `sk_test_...` |

---

## 3. Production Health Monitoring

Allcited provides standard liveness and readiness endpoints:

- **Liveness probe:** `GET /v1/health`
  ```json
  {"status": "ok", "environment": "production"}
  ```
- **Readiness & Keep-Alive:** `GET /v1/readyz`
  ```json
  {"status": "ready", "database": "healthy", "cache": "active"}
  ```
- **Interactive OpenAPI Documentation:** `https://subh-007-allcited-api.hf.space/docs`

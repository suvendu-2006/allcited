---
title: Allcited API
emoji: 📑
colorFrom: red
colorTo: green
sdk: docker
app_port: 8000
pinned: true
---

# Allcited API (Hugging Face Spaces Deployment)

FastAPI production backend serving grounded document Q&A with receipts:
- Hybrid BM25 + FAISS Dense Vector retrieval with RRF fusion
- Cross-encoder re-ranking with calibrated relevance floors
- Verifiable inline citations and multi-hop resolution
- Zero-token semantic caching and PII masking
- Multi-format ingestion: PDF (with Tesseract OCR), DOCX, PPTX, XLSX, HTML/URL, Markdown, and TXT

### Deployment Notes
- Container port: **8000** (`app_port: 8000`; uvicorn binds `0.0.0.0:${PORT:-8000}`)
- Models (`sentence-transformers/all-MiniLM-L6-v2` + `cross-encoder/ms-marco-MiniLM-L-6-v2`, ~180 MB) pre-committed via Git-LFS and loaded via `local_path` fallback — cold boot in ~30s with zero model downloads
- OCR: Dual provider interface supporting `OCR_PROVIDER=easyocr` (pure Python/PyTorch) and `OCR_PROVIDER=tesseract`
- Health: `/v1/health` · Readiness & Keep-Alive: `/v1/readyz`
- Environment variables configured via Space Settings → Variables and secrets (never committed):
  - `GROQ_API_KEY`: Groq Cloud LLM API key
  - `NVIDIA_API_KEY`: Optional NVIDIA NIM API key for cloud brain failover (meta/llama-3.2-11b-vision-instruct, Decision D-32)
  - `CLERK_SECRET_KEY` / `CLERK_PUBLISHABLE_KEY` / `CLERK_JWKS_URL`: Clerk authentication
  - `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`: Supabase library database keys
  - `STRIPE_SECRET_KEY` / `STRIPE_PRICE_ID_PRO` / `STRIPE_WEBHOOK_SECRET`: Stripe payment keys
  - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_WEBHOOK_SECRET`: Telegram bot integration keys
  - `CORS_ORIGINS`: must include `https://allcited.vercel.app`
  - `ENVIRONMENT=production`
- Deploy: `bash deploy.sh` (assembles api/ + this metadata and pushes to the Space repo)

---
title: Allcited API
emoji: 📑
colorFrom: red
colorTo: gray
sdk: docker
app_port: 8000
---

# Allcited API (Hugging Face Spaces Deployment)

FastAPI production backend serving grounded document Q&A with receipts:
- Hybrid BM25 + FAISS Dense Vector retrieval with RRF fusion
- Cross-encoder re-ranking with calibrated relevance floors
- Verifiable inline citations and multi-hop resolution
- Zero-token semantic caching and PII masking
- Multi-format ingestion: PDF (with Tesseract OCR), DOCX, PPTX, XLSX, HTML/URL, Markdown, and TXT

### Deployment Notes
- Container port: 8000 (`app_port: 8000`)
- Environment variables configured via Space Settings:
  - `GROQ_API_KEY`: Groq Cloud LLM API key
  - `CLERK_SECRET_KEY` / `CLERK_PUBLISHABLE_KEY`: Clerk authentication JWT keys
  - `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`: Supabase library database keys
  - `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET`: Stripe payment keys
  - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_WEBHOOK_SECRET`: Telegram bot integration keys

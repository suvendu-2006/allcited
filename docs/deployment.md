# Allcited — Production Deployment & Operations Runbook

> Step-by-step production runbooks for deploying Allcited across Hugging Face Spaces (containerized FastAPI backend), Vercel (Next.js 14 frontend), and fully air-gapped Docker Compose with local Ollama.

---

## 1. Environment & Prerequisites

> [!IMPORTANT]
> **Node.js LTS Requirement:**
> The frontend requires **Node.js 22+ (LTS)** and npm 10+ for building and running. Ensure your environment matches or exceeds Node.js v22.0.0 before initiating frontend builds.

- **Python:** Python 3.12+ (with `uv` or `pip`).
- **Container Runtime:** Docker Engine 24+ & Docker Compose v2.20+ (for local offline mode).
- **OCR Engine (Local/Bare-metal):** Tesseract OCR 5.0+ (`brew install tesseract` on macOS / `apt-get install tesseract-ocr` on Debian/Ubuntu).

---

## 2. Environment Variables Reference

All runtime configuration parameters are declared via environment variables:

| Variable | Scope | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GROQ_API_KEY` | Backend | **Yes** | — | Primary LLM generation key for Groq Cloud (`llama-3.3-70b-versatile`). |
| `NVIDIA_API_KEY` | Backend | Optional | — | Failover LLM key for NVIDIA NIM (`meta/llama-3.2-11b-vision-instruct`, Decision D-32). |
| `CLERK_SECRET_KEY` | Backend / Web | Optional | — | Clerk secret API key used for JWT verification and webhook validation. |
| `CLERK_PUBLISHABLE_KEY` | Backend | Optional | — | Clerk publishable key for tenant verification. |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Frontend | Optional | — | Client-side Clerk publishable key (`pk_live_...` or `pk_test_...`). |
| `NEXT_PUBLIC_API_URL` | Frontend | **Yes** | `http://localhost:8000` | Fully qualified base URL pointing to the active backend API. |
| `SUPABASE_URL` | Backend | Optional | — | Supabase PostgreSQL project URL for persistent document library shelf. |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend | Optional | — | Supabase service-role administrative secret for persistent storage. |
| `STRIPE_SECRET_KEY` | Backend | Optional | — | Stripe secret key for Pro subscription checkout creation. |
| `STRIPE_WEBHOOK_SECRET` | Backend | Optional | — | Webhook signing secret verifying Stripe subscription lifecycle events. |
| `TELEGRAM_BOT_TOKEN` | Backend | Optional | — | Telegram Bot Father token for direct chat and file streaming. |
| `OCR_PROVIDER` | Backend | No | `tesseract` | OCR engine selection: `tesseract` (native binaries) or `easyocr` (PyTorch). |
| `OLLAMA_BASE_URL` | Backend | No | `http://localhost:11434` | Endpoint for local air-gapped Ollama daemon. |
| `DEFAULT_LLM_MODEL` | Backend | No | `llama-3.3-70b-versatile` | Default model tag passed to the active brain client. |
| `RELEVANCE_FLOOR` | Backend | No | `0.0001` | Normalized cross-encoder score floor (Decision D-27). |
| `CORS_ORIGINS` | Backend | No | `*` | Comma-delimited list of permitted CORS web origins. |
| `ENVIRONMENT` | Backend | No | `development` | Runtime environment mode (`development` or `production`). |

---

## 3. Backend Deployment: Hugging Face Spaces

The backend runs as a containerized FastAPI application on Hugging Face Spaces using the Docker SDK.

### 3.1 Container Architecture
- **Base Image:** `python:3.12-slim`
- **Application Port:** `8000` (`app_port: 8000`)
- **System Dependencies:** `tesseract-ocr`, `tesseract-ocr-eng`, `tesseract-ocr-hin`, `libgl1`, `poppler-utils`
- **Pre-Cached Models:** Sentence transformer weights (`all-MiniLM-L6-v2`) and cross-encoder weights (`ms-marco-MiniLM-L-6-v2`) reside in `api/models/` via Git-LFS, ensuring cold boot times under 30 seconds.

### 3.2 Deployment Procedure
From the repository root:

```bash
# 1. Set your target Space git remote
export SPACE_URL="https://huggingface.co/spaces/<YOUR_USERNAME>/allcited-api"

# 2. Run the deployment automation script
bash deploy/hf-space/deploy.sh
```

### 3.3 Configuring Secrets on Hugging Face
In your Space settings (**Settings $\to$ Variables and secrets**), configure:
- `GROQ_API_KEY`: Primary generation key.
- `NVIDIA_API_KEY`: Failover brain key.
- `CLERK_SECRET_KEY`: User authentication key.
- `SUPABASE_URL` & `SUPABASE_SERVICE_ROLE_KEY`: Document persistence credentials.
- `CORS_ORIGINS`: Set to your production frontend URL (e.g., `https://allcited.vercel.app`).

---

## 4. Frontend Deployment: Vercel

The frontend Next.js 14 application is optimized for zero-configuration edge hosting on Vercel.

### 4.1 Project Configuration
In the Vercel dashboard:
- **Framework Preset:** `Next.js`
- **Root Directory:** `web`
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Node.js Version:** `22.x` (Configured under Project Settings $\to$ General $\to$ Node.js Version)

### 4.2 Environment Variables
Add the following in **Vercel Settings $\to$ Environment Variables**:

```env
NEXT_PUBLIC_API_URL=https://<YOUR_HF_SPACE_SUBDOMAIN>.hf.space
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
```

---

## 5. Air-Gapped Offline Deployment: Docker Compose

For secure, private environments requiring zero outbound network traffic, Allcited runs entirely locally with an integrated Ollama container.

### 5.1 One-Command Launch
From the repository root:

```bash
docker compose up -d
```

### 5.2 Pulling the Offline Model
Once the containers are active, pull your desired local model (e.g., `qwen2.5:7b` or `qwen:7b`):

```bash
docker exec -it allcited-ollama ollama pull qwen2.5:7b
```

### 5.3 Service Endpoints

- **Web Workspace:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Ollama Engine:** [http://localhost:11434](http://localhost:11434)

---

## 6. Health Checks & Production Verification

Verify pipeline liveness and model readiness via CLI:

```bash
# 1. Check basic liveness
curl -s -f https://<API_DOMAIN>/v1/health | jq .

# Expected Output:
# {"status": "ok", "environment": "production", "provider": "groq", "version": "1.0.0"}

# 2. Check full system readiness (database, vector store, reranker)
curl -s -f https://<API_DOMAIN>/v1/readyz | jq .

# Expected Output:
# {"status": "ready", "database": "healthy", "cache": "active", "vector_store": "ready", "cross_encoder": "loaded"}
```

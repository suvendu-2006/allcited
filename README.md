<div align="center">

# Allcited

### Document Q&A with Receipts. No Hallucinations.

**Upload any document → get grounded answers with inline citations → verified down to the page, paragraph, and cell.**

[![CI Pipeline](https://github.com/suvendu-2006/allcited/actions/workflows/ci.yml/badge.svg)](https://github.com/suvendu-2006/allcited/actions)
[![Evaluation Hit Rate](https://img.shields.io/badge/EVAL%20RETRIEVAL-95.1%25%20Hit%20Rate-success?style=for-the-badge&logo=target)](eval/results/table.md)
[![Python 3.12](https://img.shields.io/badge/PYTHON-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/NEXT.JS-14-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Zero Cloud Egress](https://img.shields.io/badge/PRIVACY-AIR--GAPPED%20ZERO%20CLOUD%20EGRESS-red?style=for-the-badge&logo=shield)](docker-compose.yml)
[![License](https://img.shields.io/badge/LICENSE-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

[**Live Web App**](https://allcited.vercel.app) • [**API Explorer**](https://subh-007-allcited-api.hf.space/docs) • [**Health Probe**](https://subh-007-allcited-api.hf.space/v1/health) • [**Telegram Bot (@AllcitedBot)**](https://t.me/allcited_test_bot) • [**Docs Hub**](docs/README.md) • [**Docker Quickstart**](#quickstart-air-gapped-docker)

<br/>

<kbd>
  <img src="assets/demo.gif" alt="Allcited Interactive Document Q&A Demo" width="860" style="border-radius: 8px; box-shadow: 0 8px 30px rgba(0,0,0,0.12);" />
</kbd>

<br/><br/>

</div>

---

### Quick Navigation

- [Why Allcited? (The P1–P4 RAG Trap Story)](#why-allcited-the-p1p4-rag-trap-story)
- [Architecture & Data Flow](#architecture--data-flow)
  - [Document Ingestion & Indexing Pipeline](#document-ingestion--indexing-pipeline)
  - [Query Execution & Grounded Generation](#query-execution--grounded-generation)
- [Monorepo Directory Layout](#monorepo-directory-layout)
- [Enterprise Tech Stack Matrix](#enterprise-tech-stack-matrix)
- [Quickstart: Air-Gapped Docker & Local Dev](#quickstart-air-gapped-docker)
  - [Option 1: Instant Air-Gapped Docker Compose](#option-1-instant-air-gapped-docker-compose)
  - [Option 2: Local Development Setup](#option-2-local-development-setup)
- [API Reference & Error Envelope Contract](#api-reference--error-envelope-contract)
- [Empirical Evaluation Benchmark](#empirical-evaluation-benchmark-11-row-matrix)
  - [Chunking Strategy A/B Comparison](#chunking-strategy-ab-comparison)
- [Live Channels & Deployments](#live-channels--deployments)
- [Honest Limitations (What Allcited Does Not Do)](#honest-limitations-what-allcited-does-not-do)
- [Enterprise Quality Gates & Governance](#enterprise-quality-gates--governance)

---

## Why Allcited? (The P1–P4 RAG Trap Story)

Naive vector retrieval scores only **55%–65%** on complex real-world documents. Enterprise contracts, compliance guidelines, financial statements, and technical manuals are adversarial by design: critical caveats condition general terms, definitions live in cross-referenced schedules, and superficial lexical similarities mislead cosine distance.

Allcited was engineered from first principles to defeat the **four universal RAG failure traps**:

<table>
  <thead>
    <tr>
      <th width="18%">Trap Category</th>
      <th width="38%">Why Conventional RAG Fails</th>
      <th width="44%">How Allcited Solves It</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>P1: Boundary Straddle</b></td>
      <td>A critical governing condition (e.g. <i>"except when authorized in writing by the Regional VP"</i>) is sliced across an arbitrary 500-token chunk boundary. Vector retrieval matches only the unqualified blanket rule.</td>
      <td><b>Hierarchical Section Breadcrumbs:</b> Every chunk is prepended with its structural AST breadcrumbs (<code>Doc &gt; Section &gt; Clause</code>) plus a 15% sliding window boundary overlap to guarantee conditional cohesion.</td>
    </tr>
    <tr>
      <td><b>P2: Distractors</b></td>
      <td>High semantic or lexical overlap from superficially similar but legally inapplicable clauses (e.g. domestic vs. overseas contractor travel expense policies) deceives dense cosine similarity.</td>
      <td><b>RRF + Cross-Encoder Re-Ranking:</b> Blends lexical BM25 and dense FAISS candidates via Reciprocal Rank Fusion ($k=60$), followed by deep token cross-attention (<code>ms-marco-MiniLM-L-6-v2</code>) with a calibrated score floor (<code>0.0001</code>).</td>
    </tr>
    <tr>
      <td><b>P3: Two-Hop Cross References</b></td>
      <td>An operative clause states: <i>"Payouts are calculated pursuant to Rule 63.7.4."</i> Without the annex schedule defining Rule 63.7.4, standard LLMs hallucinate numbers or refuse to answer.</td>
      <td><b>Two-Hop Graph RefMap:</b> An AST reference map extractor identifies citations and cross-references at ingestion, resolving graph neighbors during retrieval to inject both clause and definition (<code>[S2 (2nd-hop)]</code>).</td>
    </tr>
    <tr>
      <td><b>P4: Multi-Aspect Composite</b></td>
      <td>Queries demanding synthesis across orthogonal domains (e.g. <i>"Notice period for employees vs. equipment security for contractors"</i>) disperse retrieval embeddings and yield incomplete answers.</td>
      <td><b>Agentic Multi-Document Synthesis:</b> Decomposes multi-faceted questions into orthogonal sub-queries, running parallel targeted retrieval probes through a bounded Sufficiency Loop (&le; 3 passes).</td>
    </tr>
  </tbody>
</table>

> [!NOTE]
> **Deterministic Receipts:** Every claim generated by Allcited contains verifiable bracketed citation chips (`[S1]`, `[S2]`). Clicking any chip opens the interactive **Receipts Drawer**, displaying the exact source sentence, page number, section breadcrumb, and a 1-click verification link directly back to the original document.

---

## Architecture & Data Flow

Allcited decouples ingestion and query execution into two modular, high-reliability pipelines:

### Document Ingestion & Indexing Pipeline

```mermaid
flowchart TD
    subgraph Ingestion ["1. Document Ingestion & Preprocessing"]
        Doc["Document Input<br/>(PDF, DOCX, PPTX, XLSX, HTML, MD, TXT)"] --> SSRF["SSRF Guard & URL/File Validation"]
        SSRF --> CheckOCR{"Needs OCR?<br/>(&lt;50 characters text)"}
        CheckOCR -- Yes --> OCR["Dual OCR Fallback<br/>(Tesseract eng+hin / EasyOCR)"]
        CheckOCR -- No --> StructParse["Structured Document Parser<br/>(Heading-Aware AST)"]
        OCR --> Chunker["Section-Aware Chunker<br/>+ 15% Sliding Window"]
        StructParse --> Chunker
        Chunker --> Breadcrumbs["Contextual Section Breadcrumbs<br/>(Doc &gt; Section &gt; Clause)"]
    end

    subgraph Indexing ["2. Knowledge Graph & Dual Indexing"]
        Breadcrumbs --> RefMap["Reference Map Extractor<br/>(Cross-References &amp; Entities)"]
        RefMap --> Graph["Entity &amp; Cross-Reference Graph"]
        Breadcrumbs --> Dense["Dense Embeddings<br/>(Sentence-Transformers all-MiniLM-L6-v2)"]
        Breadcrumbs --> Sparse["Lexical Indexer<br/>(BM25Okapi Tokenizer)"]
        Dense --> FAISS[("FAISS Vector Index<br/>(In-Memory Cosine L2)")]
        Sparse --> BM25[("BM25 Inverted Index<br/>(Exact Term Matching)")]
    end

    subgraph QueryPipeline ["3. Retrieval & Grounding Synthesis"]
        UserQ["User Query"] --> QueryEngine["Hybrid RRF Fusion + Reranker + Multi-Brain LLM"]
        FAISS -.-> QueryEngine
        BM25 -.-> QueryEngine
        Graph -.-> QueryEngine
        QueryEngine --> VerifiedOut["Grounded Answer with [S1], [S2] Receipts"]
    end
```

### Query Execution & Grounded Generation

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client
    participant Guard as PII Scrub & Guard
    participant Cache as Semantic Cache (@0.96)
    participant Router as Query Router & HyDE Probe
    participant Hybrid as Hybrid Retrieval (FAISS + BM25)
    participant Rerank as Cross-Encoder (ms-marco-MiniLM)
    participant Graph as Two-Hop Graph Expander
    participant Sufficiency as Agentic Sufficiency Judge
    participant LLM as Multi-Brain LLM (Groq / NVIDIA Failover)
    participant Audit as Grounding & Receipts Audit

    User->>Guard: POST /v1/query (Question + Session ID)
    Guard->>Guard: Scrub PII & Sanitize Prompt Injection
    Guard->>Cache: Probe Semantic Cache (Cosine >= 0.96)
    alt Cache Hit
        Cache-->>User: Instant Cached SSE Stream (<100ms)
    else Cache Miss
        Cache->>Router: Forward Sanitized Query
        Router->>Router: Decompose Query & Generate HyDE Hypothetical Passage
        Router->>Hybrid: Parallel Dense FAISS + Sparse BM25 Search
        Hybrid->>Hybrid: Reciprocal Rank Fusion (RRF k=60)
        Hybrid->>Rerank: Top-K Fused Candidates
        Rerank->>Rerank: Cross-Attention Scoring & Filter Floor (>= 0.0001)
        Rerank->>Graph: High-Scoring Core Chunks
        Graph->>Graph: Traverse Reference Map (2-Hop Cross-References <= 4)
        Graph->>Sufficiency: Core Chunks + Cross-Referenced Definitions
        loop Sufficiency Loop (<= 3 Iterations)
            Sufficiency->>Sufficiency: Evaluate Context Completeness
            opt Missing Sub-Aspect
                Sufficiency->>Hybrid: Target Sub-Query Probe
            end
        end
        Sufficiency->>LLM: Synthesize Grounded Prompt with Context Chunks
        LLM->>LLM: Stream Generation (Primary: Groq LLaMA 3.3 70B)
        opt Failover Triggered (Rate Limit / Outage)
            LLM->>LLM: Automatic Failover to NVIDIA NIM LLaMA 3.2 11B
        end
        LLM->>Audit: Raw Token Stream with Citations
        Audit->>Audit: Audit Citations against Retrieved Context
        Audit-->>User: Verified SSE Stream with [S1], [S2] Chips + Receipts Drawer
    end
```

---

## Monorepo Directory Layout

The Allcited repository is organized as a clean, cohesive monorepo spanning the backend engine, web frontend, empirical evaluation suite, documentation hub, and operational tools:

```
allcited/
├── .github/              # CI/CD automation workflows (ci.yml, keep_alive.yml, docker-publish.yml)
├── api/                  # High-performance FastAPI backend service (Python 3.12)
│   ├── app/              # Core application logic, schemas, and RAG pipeline
│   │   ├── pipeline/     # Multi-format parsers, chunking, hybrid retrieval, reranker, graph, LLMs
│   │   ├── security/     # Security guards (SSRF defense, PII scrubber, rate limiters)
│   │   └── main.py       # REST & SSE endpoints (/health, /ingest, /query, /library, /trace)
│   ├── tests/            # Automated test suite (180+ tests verifying ingestion, retrieval, security)
│   ├── Dockerfile        # Production Dockerfile with pre-baked models and local OCR binaries
│   └── requirements.txt  # Pinned backend dependencies
├── web/                  # Production Next.js 14 App Router workspace (TypeScript, Tailwind CSS)
│   ├── src/app/          # Application routes: workspace (/), document exam (/exam), library (/library)
│   ├── src/components/   # Receipts Drawer, Orbit Clock dial, chat streamer, UI design tokens
│   ├── src/data/         # Single-source evaluation benchmarks & results JSON
│   └── public/           # Static web assets, branding icons, and demo files
├── docs/                 # Centralized Documentation Hub
│   ├── README.md         # Documentation index and subsystem navigation
│   ├── architecture.md   # Detailed system architecture, hybrid RRF, brain failover, D-01–D-32 ADRs
│   ├── api.md            # OpenAPI specifications, SSE streaming protocols, and error catalog
│   ├── frontend.md       # "Ink & Ember" design tokens, layout geometry, WCAG AA standards
│   ├── security.md       # Threat model, SSRF defense, prompt injection isolation, Clerk JWKS
│   ├── deployment.md     # Runbooks for Hugging Face Spaces, Vercel, and Docker Compose
│   └── evaluation.md     # Evaluation methodology, 46-question fixtures, ablation results
├── eval/                 # Empirical Evaluation Framework & Benchmarks
│   ├── fixtures/         # Standardized test documents (17 policy chapters, scanned OCR, XLSX)
│   ├── questions.json    # Hardened 46-question empirical benchmark across P1–P4 trap categories
│   ├── run.py            # Automated benchmark runner for 11 ablation modes & chunking A/B tests
│   └── results/          # Machine-readable evaluation outputs and markdown tables
├── deploy/               # Cloud & Container Deployment Configurations
│   ├── hf-space/         # Hugging Face Spaces Docker container manifest & deployment scripts
│   └── hf-gradio/        # Interactive Gradio fallback UI deployment
├── scripts/              # Operational Tooling & Verification Scripts
│   ├── keep_alive.py     # Health monitoring and automated wake-up cron script
│   ├── setup_telegram_webhook.py # Telegram bot webhook registration and configuration
│   └── verify_*.py       # Acceptance criteria, deletion audit, and security verification scripts
├── supabase/             # Relational Persistence & Multi-Tenant Isolation
│   ├── migrations/       # Schema definitions, document metadata, pgvector, and RLS policies
│   └── test_rls_isolation.sql # Deterministic cross-tenant isolation test suite
└── docker-compose.yml    # Self-contained air-gapped stack (API + Web + Local Ollama)
```

---

## Enterprise Tech Stack Matrix

| Architectural Domain | Technology Choice | Enterprise Purpose & Engineering Rationale |
| :--- | :--- | :--- |
| **Hybrid Retrieval** | BM25Okapi + FAISS | Sparse lexical precision for exact alphanumeric codes (`Form EXP-9`, `Rule 63.7.4`) fused with dense MiniLM semantic search via Reciprocal Rank Fusion ($k=60$). |
| **Neural Re-Ranking** | Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) | Full query-passage cross-attention scoring with calibrated score floor (`0.0001`) to drop superficial distractor clauses (P2). |
| **Knowledge Graph** | Two-Hop Graph RefMap | Fast regex & AST reference map extraction identifying cross-references at ingestion, expanding graph neighbors during retrieval up to 4 hops. |
| **Backend Runtime** | FastAPI + Python 3.12 | High-throughput async ASGI server with strict Pydantic v2 schema validation, streaming Server-Sent Events (SSE), and modular pipeline hooks. |
| **Frontend Framework**| Next.js 14 App Router | React 18, TypeScript, Tailwind CSS workspace featuring a slide-over Receipts Drawer, responsive layouts, and WCAG AA accessibility. |
| **Multi-Brain LLM Engine**| Groq &rarr; NVIDIA NIM &rarr; Ollama | Multi-brain resilience: Groq LLaMA 3.3 70B by default with automated zero-touch failover to NVIDIA NIM (D-32) and local Ollama (`qwen2.5:7b`). |
| **Document Ingestion** | PyPDF, python-docx, openpyxl, python-pptx | Multi-format parsing (PDF, DOCX, PPTX, XLSX, HTML, Markdown, TXT) with hierarchical AST and contextual heading breadcrumbs. |
| **OCR Processing** | Tesseract OCR (`eng+hin`) / EasyOCR | Dual-provider optical character recognition for scanned PDFs and low-text raster images without cloud dependencies. |
| **Database & Vector Storage**| PostgreSQL + pgvector (Supabase) | Multi-tenant library persistence protected by strict Row-Level Security (RLS) policies guaranteeing tenant isolation. |
| **Identity & Authentication**| Clerk Auth (JWKS) | Stateless JWT verification with public key rotation and seamless guest anonymous sessions. |
| **Security & Hardening**| SSRF Guard + Delimiter Isolation | Blocks private/link-local/metadata IP ranges; neutralizes prompt injections by treating text as inert passive data. |
| **Observability & Audit**| In-Process JSONL Traces | Deterministic step-by-step pipeline execution ledger (`/v1/trace/{question_id}`) with zero external SaaS overhead. |

---

<a id="quickstart-air-gapped-docker"></a><a id="private-offline-edition-zero-cloud-egress"></a>
## Quickstart: Air-Gapped Docker & Local Dev

Allcited is designed to run anywhere: fully air-gapped on private workstations, or distributed across cloud environments.

### Option 1: Instant Air-Gapped Docker Compose

Deploy the complete self-contained stack with zero external network egress. No data ever leaves your hardware:

```bash
docker compose up
```

This single command provisions:
- **Allcited Web UI:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend & OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Local Ollama Daemon:** [http://localhost:11434](http://localhost:11434) with local `qwen2.5:3b` or `qwen2.5:7b` pre-pulled.

> [!TIP]
> The container images include pre-cached embedding weights (`all-MiniLM-L6-v2`), cross-encoder weights (`ms-marco-MiniLM-L-6-v2`), and local Tesseract OCR binaries. Post-pull execution requires zero external network calls.

#### Standalone Container One-Liner (Existing Ollama Instance)

If you already run Ollama on your host machine, connect Allcited directly:

```bash
docker run -d \
  --name allcited-api \
  -p 8000:8000 \
  -e MODE=private \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e DEFAULT_LLM_MODEL=qwen2.5:3b \
  ghcr.io/suvendu-2006/allcited-api:latest
```

---

### Option 2: Local Development Setup

#### Prerequisites
- **Node.js 22+ (LTS)** & npm
- **Python 3.12**
- **Tesseract OCR** (`brew install tesseract` on macOS / `apt-get install tesseract-ocr` on Ubuntu)

#### 1. Backend Setup

```bash
cd api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup

```bash
cd web
npm install
npm run dev
```

The web workspace will be live at [http://localhost:3000](http://localhost:3000) with hot-reload enabled.

#### 3. Test Suites & Evaluation Benchmark

```bash
# Run all 180+ backend tests
cd api && .venv/bin/pytest tests/ -q

# Run empirical evaluation benchmark matrix
cd eval && python run.py --matrix --chunking-ab
```

---

## API Reference & Error Envelope Contract

All backend routes are version-prefixed with `/v1`. Every request returns an `X-Request-ID` HTTP header matching `error.request_id` for deterministic debugging and audit logs.

For complete schema specifications and event streaming contracts, see the comprehensive [API Reference Documentation (docs/api.md)](docs/api.md).

### Standard Error Envelope

```json
{
  "error": {
    "code": "plan_limit_reached",
    "message": "Free tier limit of 3 saved library documents reached. Upgrade to Pro for unlimited document storage.",
    "request_id": "9d1f3b7c-482a-412e-8e3b-9a4f2c15e8b2"
  }
}
```

### Primary REST & SSE Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/v1/health` | Service health probe, active LLM provider, and environment mode |
| `GET` | `/v1/readyz` | Readiness probe confirming model weights and vector index availability |
| `POST` | `/v1/ingest` | Upload file (PDF, DOCX, PPTX, XLSX, HTML, MD, TXT) and build session index |
| `POST` | `/v1/ingest/url` | Ingest web URL with strict SSRF domain and IP validation |
| `POST` | `/v1/query` | SSE streaming query execution with grounded citations (`[S1]`, `[S2]`) |
| `POST` | `/v1/summarize` | SSE hierarchical map-reduce document summarization citing chunk ranges |
| `POST` | `/v1/library/save` | Persist active document session into user library (Clerk authenticated) |
| `GET` | `/v1/library/documents`| Enumerate saved documents for authenticated user |
| `POST` | `/v1/library/query` | Multi-document cross-synthesis across saved library items |
| `GET` | `/v1/trace/{question_id}` | Retrieve complete step-by-step pipeline execution trace ledger |
| `GET` | `/v1/stats` | Platform operational counters, latency figures, and cost avoided |

<details>
<summary><b>Click to expand full Error Code Catalog</b></summary>
<br/>

| Error Code | HTTP Status | Meaning & Resolution |
| :--- | :---: | :--- |
| `doc_unreadable` | 400 | File is corrupt, password-protected, or contains unreadable binary streams. |
| `url_blocked` | 400 | SSRF guard blocked private, loopback, link-local, or cloud-metadata IP. |
| `validation_error` | 422 | Request payload failed Pydantic schema validation. |
| `unauthorized` | 401 | Missing or invalid Bearer authentication token. |
| `token_expired` | 401 | Clerk JWT token has expired. Re-authenticate client. |
| `invalid_token` | 401 | JWT signature verification failed or subject claim missing. |
| `plan_limit_reached` | 402 | Free tier cap reached (upload > 10 MB, precision mode, library saves > 3). |
| `doc_too_large` | 402 | File size exceeds plan limit (Free: 10 MB, Pro: 100 MB). |
| `session_not_found` | 404 | In-memory session expired or invalid ID. Re-upload document. |
| `free_tier_busy` | 429 / 503 | Rate limits or LLM concurrency ceiling reached on free tier. |
| `ollama_unreachable` | 502 / 503 | Local Ollama daemon unreachable at configured base URL. |
| `injection_flagged` | 200 (Warning) | Document attempted prompt injection; treated strictly as passive data. |

</details>

---

## Empirical Evaluation Benchmark (11-Row Matrix)

Allcited verifies itself in public. Every pipeline change runs against a hardened 46-question empirical evaluation fixture ([eval/questions.json](eval/questions.json)) spanning 17 policy chapters, scanned OCR pages, distractor schedules, and cross-references.

All metrics are reproducible from single-source results ([eval/results/eval_v2_results.json](eval/results/eval_v2_results.json) & [web/src/data/eval_results.json](web/src/data/eval_results.json)):

| Configuration | Retrieval Hit | Normal | P1: Boundary | P2: Distractor | P3: Two-Hop | P4: Multi-Aspect | Paraphrase | Refusal Acc | Answer Corr | p50 (ms) | p95 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **bm25** | `82.9%` | 100.0% | 75.0% | 75.0% | 100.0% | 75.0% | 50.0% | 60.0% | 56.5% | `1.0` | `1.1` |
| **vector** | `87.5%` | 100.0% | 75.0% | 100.0% | 80.0% | 75.0% | 75.0% | 66.7% | 56.5% | `7.6` | `11.6` |
| **hybrid** | `87.8%` | 100.0% | 75.0% | 100.0% | 100.0% | 50.0% | 75.0% | 60.0% | 56.5% | `1.1` | `1.1` |
| **+rerank** | `90.2%` | 100.0% | 75.0% | 100.0% | 100.0% | 75.0% | 50.0% | 80.0% | 58.7% | `101.5` | `112.1` |
| **+twohop** | `95.1%` | 100.0% | 100.0% | 100.0% | 100.0% | 75.0% | 75.0% | 80.0% | 58.7% | `102.3` | `114.1` |
| **+rewrite** | `95.1%` | 100.0% | 100.0% | 100.0% | 100.0% | 75.0% | 75.0% | 80.0% | 58.7% | `106.0` | `113.7` |
| **+hyde** | `95.1%` | 100.0% | 100.0% | 100.0% | 100.0% | 75.0% | 75.0% | 80.0% | 58.7% | `112.7` | `156.3` |
| **+headers** | `95.1%` | 100.0% | 100.0% | 100.0% | 100.0% | 75.0% | 75.0% | 80.0% | 58.7% | `103.1` | `135.2` |
| **+agentic** | `95.1%` | 100.0% | 100.0% | 100.0% | 100.0% | 75.0% | 75.0% | 80.0% | 58.7% | `102.7` | `126.2` |
| **+graph** | `95.1%` | 100.0% | 100.0% | 100.0% | 100.0% | 75.0% | 75.0% | 80.0% | 58.7% | `102.7` | `116.7` |
| **full_system** | **`95.1%`** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **75.0%** | **75.0%** | **80.0%** | **58.7%** | `102.2` | `132.9` |

> **What "Answer Corr" means:** Strict exact-match scoring — an answer passes only if it contains the exact figure and verbatim clause text from the source. The LLM-judged pass rate (semantic correctness) is **93.5% (43/46)** as presented on [/exam](https://allcited.vercel.app/exam). Both are reported; strict is the harder bar.

### Architectural Insights & Ablation Progression

- **BM25 Alone (82.9%):** Blazing fast (1.0ms), but collapses on colloquial paraphrasing (**50.0%**) where questions like *"unspent holiday"* share 0 lexical tokens with *"annual leave carry-forward"*.
- **Vector Search (87.5%):** Dense MiniLM embeddings recover semantic paraphrases (**75.0%**), but falter on alphanumeric policy codes (`Rule 63.7.4`, `Form EXP-9`).
- **Hybrid Fusion (87.8%):** Reciprocal Rank Fusion ($k=60$) balances sparse and dense signals without hyperparameter overfitting.
- **Cross-Encoder Re-Ranking (90.2%):** Filters false-positive distractors, raising refusal accuracy from 60.0% to **80.0%**.
- **Two-Hop Traversal (95.1%):** Traverses cross-references to annexes and definitions, pushing P1 and P3 recall to **100.0%**.

---

### Chunking Strategy A/B Comparison

Chunking strategy directly dictates whether boundary conditions survive ingestion. We evaluated 5 distinct strategies across identical questions:

| Chunking Strategy | Chunks | Avg Tokens | Retrieval Hit | P1 (Boundary) | P4 (Multi-Aspect) | Paraphrase | Answer Corr | Key Engineering Trade-off |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **300 tokens, 0% overlap** | 10 | 289 | 85.4% | 50.0% | 50.0% | 50.0% | 58.7% | High fragmentation; split clauses drop P1 recall to 50% |
| **300 tokens, 15% overlap** | 12 | 286 | 80.5% | 50.0% | 50.0% | 50.0% | 60.9% | 15% window bridges clauses; +18% index size |
| **500 tokens, 0% overlap** | 6 | 474 | 90.2% | 100.0% | 50.0% | 75.0% | 58.7% | Fewer chunks; topic transitions at boundaries still vulnerable |
| **500 tokens, 15% overlap** | 7 | 473 | 87.8% | 75.0% | 50.0% | 50.0% | 54.3% | Strong context retention; slight dilution on pinpoint lookup |
| **Semantic (section-aware, 15% overlap, headers)** | 12 | 230 | 78.0% | 50.0% | 25.0% | 75.0% | 58.7% | Section isolation + contextual headers; zero cross-topic bleeding |

---

## Live Channels & Deployments

| Channel | URL / Handle | Description |
| :--- | :--- | :--- |
| **Web Interface** | [allcited.vercel.app](https://allcited.vercel.app) | Next.js 14 App Router workspace with Receipts Drawer, Wave theme toggle, and Clerk authentication |
| **API Backend** | [subh-007-allcited-api.hf.space/v1/health](https://subh-007-allcited-api.hf.space/v1/health) | FastAPI cloud runner on Hugging Face Spaces with automated provider failover (Groq &rarr; NVIDIA NIM) |
| **Interactive Docs** | [subh-007-allcited-api.hf.space/docs](https://subh-007-allcited-api.hf.space/docs) | Swagger UI & OpenAPI 3.1 schema specification |
| **Telegram Bot** | [@AllcitedBot](https://t.me/allcited_test_bot) | Real-time message streaming, document upload, and cited answers in chat (`@allcited_test_bot`) |
| **Container Registry**| `ghcr.io/suvendu-2006/allcited-api:latest` | Pre-built air-gapped container image with local OCR and embedded vector pipelines |

---

## Honest Limitations (What Allcited Does Not Do)

We believe in radical engineering honesty. Allcited deliberately does not attempt to solve every problem:

1. **OCR Confidence & Provider Trade-offs:** Allcited supports dual OCR providers via `pipeline/parsers/ocr.py` (`OCR_PROVIDER=tesseract` or `OCR_PROVIDER=easyocr`):
   - **Tesseract (Default in Docker / Local):** Native C++ binaries (`eng+hin`), fast (~200–500ms/page), zero model download overhead.
   - **EasyOCR (Hosted Cloud / Hugging Face Spaces):** Pure Python/PyTorch pipeline requiring no system C-binaries. Trade-offs: ~1–3 s/page on CPU, models (~80 MB) download to cache on first scanned document.
   - **OCR Confidence on Low-DPI Documents:** Degraded handwriting, skew > 15°, or heavy watermarking may introduce localized character noise on low-DPI scans (<150 DPI).
2. **DOCX Images & Nested Footnotes:** Embedded drawings, vector shapes, and margin footnotes in DOCX files are bypassed in favor of clean heading-style tree parsing.
3. **Complex Nested XLSX Spreadsheets:** Sheets with irregularly merged header hierarchies are windowed row-wise (25 rows per chunk); formulas are indexed as literal values rather than re-computed dynamically.
4. **Org-Scale Enterprise Baggage (Decision D-26):** Allcited deliberately excludes company-scale enterprise overhead:
   - No SAML/Okta SSO (uses standard Clerk JWT / anonymous sessions)
   - No Active Directory / SharePoint source-ACL inheritance
   - No multi-region geo-replicated HA infrastructure
   - No SOC-2 / HIPAA compliance certifications
   - No heavyweight observability agents (Datadog/Grafana clusters) — uses lightweight in-process JSONL traces
   *These exclusions are by design to ensure ₹0 operating cost and frictionless open-source deployment.*

---

## Enterprise Quality Gates & Governance

Allcited enforces strict production quality gates across all operational and behavioral dimensions:

| Quality Gate | Standard & Threshold | Verification Mechanism |
| :--- | :--- | :--- |
| **Codebase Integrity** | Clean typing, Python 3.12 / TypeScript strict mode, zero lint warnings | Ruff, ESLint, and CI build workflows |
| **Secret Zero-Tolerance** | Zero credentials or private keys in source tree or git history | Automated `gitleaks` scanning on every push |
| **Test Reliability** | 100% pass rate across 180+ backend tests | Automated Pytest suite (`api/tests/`) running in CI |
| **Grounding Verification** | 95.1% retrieval hit rate across P1–P4 RAG failure traps | Reproducible 46-question empirical benchmark fixture |
| **Security Hardening** | SSRF blocked, PII masked, prompt injection neutralized | Automated security spot-check tests |
| **Multi-Environment Support** | Verified on Vercel, Hugging Face Spaces, GHCR, and local Docker | Automated keep-alive and readiness probes |

### Open-Source Community & Contributing

We welcome community contributions, bug reports, and architectural proposals:

- **Contributing Guide:** [CONTRIBUTING.md](CONTRIBUTING.md) — Setup instructions, PR workflows, and coding conventions.
- **Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant v2.1 standards.
- **Security Policy:** [SECURITY.md](SECURITY.md) — Vulnerability reporting, SSRF disclosure, and defense model.
- **License:** [MIT License](LICENSE) — Permissive open-source licensing.

---

<div align="center">

### Built for precision. Grounded in evidence.

Licensed under [MIT](LICENSE). Maintained by [Suvendu](https://github.com/suvendu-2006).

</div>

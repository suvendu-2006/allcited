# Allcited

> Document Q&A with receipts: upload a document → grounded, cited answers → plus an eval harness proving accuracy with numbers.

Allcited is a high-accuracy, grounded document question-answering system featuring hybrid retrieval (BM25 + FAISS Dense Vector + RRF), cross-encoder re-ranking, query routing, query rewriting, two-hop expansion, contextual headers, semantic caching, prompt-injection defense, and verifiable inline citations.

## Evaluation Matrix

*(Evaluations will be recorded here across retrieval modes: BM25, Vector, Hybrid, +Rerank, +Two-hop, +Rewrite, +HyDE, +Headers, +Agentic, +Graph, and Full System)*

| Configuration | Retrieval Hit Rate | Answer Correctness | Refusal Accuracy | p50 Latency | p95 Latency | Notes |
|---|---|---|---|---|---|---|
| BM25 only | TBD | TBD | TBD | TBD | TBD | Baseline keyword search |
| Dense Vector | TBD | TBD | TBD | TBD | TBD | sentence-transformers MiniLM |
| Hybrid (BM25 + Vector RRF) | TBD | TBD | TBD | TBD | TBD | Reciprocal Rank Fusion (k=60) |
| + Re-ranking | TBD | TBD | TBD | TBD | TBD | ms-marco-MiniLM-L-6-v2 |
| + Two-hop expansion | TBD | TBD | TBD | TBD | TBD | Cross-reference graph expansion |
| + Query rewriting | TBD | TBD | TBD | TBD | TBD | Targeted sub-query generation |
| + HyDE | TBD | TBD | TBD | TBD | TBD | Hypothetical document embeddings |
| + Contextual headers | TBD | TBD | TBD | TBD | TBD | Chunk heading preservation |
| + Agentic retrieval | TBD | TBD | TBD | TBD | TBD | Multi-step iterative search |
| + GraphRAG-lite | TBD | TBD | TBD | TBD | TBD | Entity relationship expansion |
| **Full System** | TBD | TBD | TBD | TBD | TBD | End-to-end grounded pipeline |

## Architecture

- **Backend:** FastAPI (`/v1`), Pydantic Settings, FAISS, rank_bm25, sentence-transformers, cross-encoder
- **Frontend:** Next.js 14, Tailwind CSS, TypeScript
- **Brain Client:** Unified OpenAI-compatible client supporting Groq, BYOK, and local Ollama
- **Safety & Guards:** Prompt injection detection, PII masking, no code execution
- **Evaluation:** Automated 46-question evaluation suite measuring hit rates, trap defense, and citation validity

## Development

```bash
# Backend
cd api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend
cd web
npm run dev
```

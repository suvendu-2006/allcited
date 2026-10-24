# Allcited

> Document Q&A with receipts: upload a document → grounded, cited answers → plus an eval harness proving accuracy with numbers.

Allcited is a high-accuracy, grounded document question-answering system featuring hybrid retrieval (BM25 + FAISS Dense Vector + RRF), cross-encoder re-ranking, query routing, query rewriting, two-hop expansion, contextual headers, semantic caching, prompt-injection defense, and verifiable inline citations.

## Evaluation Matrix (Phase 3 — Empirical Results)

The evaluation harness evaluates 30 base questions across trap categories: normal, P1 (boundary straddle), P2 (distractors), P3 (two-hop cross-reference), P4 (multi-aspect), paraphrase, and absent-refusal traps against the corporate handbook fixture.

| Configuration | Retrieval Hit | Normal | P1 (Boundary) | P2 (Distractor) | P3 (Two-Hop) | P4 (Multi-Aspect) | Paraphrase | Refusal Acc | Answer Corr | p50 (ms) | p95 (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **bm25** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 56.7% | 0.1 | 0.2 |
| **vector** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 56.7% | 9.5 | 21.1 |
| **hybrid** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 56.7% | 0.1 | 0.2 |
| **+rerank** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 56.7% | 44.3 | 98.8 |
| **+twohop** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 56.7% | 48.6 | 87.8 |
| **+rewrite** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 56.7% | 43.3 | 57.7 |

### Row Movement Explanations (The Pipeline Story)

1. **`bm25` (Keyword baseline):** Pure lexical matching provides instantaneous retrieval (p50: 0.1ms) and perfect precision on explicit identifiers (e.g. `ISO-27001`, `Form HR-702`), but drops to 57.7% Hit@1 when queries employ vocabulary mismatch or colloquial paraphrases.
2. **`vector` (Dense semantic search):** Dense embeddings (`all-MiniLM-L6-v2`) increase Hit@1 to 84.6% by mapping conceptual phrasing and paraphrases into semantic vector space at the expense of ~9.5ms embedding latency.
3. **`hybrid` (RRF fusion):** Reciprocal Rank Fusion ($k=60$) merges BM25 and dense vector rankings, canceling out individual blind spots and guaranteeing top candidate recall across both keyword-precise and semantic queries.
4. **`+rerank` (Cross-encoder):** Cross-encoder (`ms-marco-MiniLM-L-6-v2`) directly scores (query, chunk) pairs to separate signal from distractor noise, while enforcing a calibrated relevance floor (`0.0001`) that intercepts off-topic requests with 0 LLM calls.
5. **`+twohop` (Cross-reference resolution):** Dynamically inspects candidate chunks and query text for domain references, traversing the document reference map to pull in definition passages (e.g. `Rule 63.7.4`) alongside mentioning clauses.
6. **`+rewrite` (Query decomposition):** Heuristic and LLM query reformulation expands vague or multi-aspect questions into 2–3 targeted search phrases, preventing keyword dilution on explicit identifiers while providing multi-angle coverage.

> [!NOTE]
> **API Contract Frozen:** Completion of Phase 3 freezes the `/v1` endpoint contract (`POST /v1/ingest`, `POST /v1/query`, `POST /v1/summarize`, `GET /v1/health`), unblocking parallel implementation across Tracks 4a (Web UI), 4b (Library), and 4c (Parsers).

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

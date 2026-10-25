# Allcited — Architecture & Decision Log

## 0. Decisions Log (from plan §0)

| ID | Decision |
|----|----------|
| D-01..D-12 | session-only anonymous mode + FAISS in RAM; hybrid BM25+vector RRF; small reranker `ms-marco-MiniLM-L-6-v2`; router; map-reduce; one OpenAI-compatible brain client (Groq default / BYOK / Ollama); BYOK keys browser-only; Ollama = local mode; Clerk gates saving not chatting; Next.js on Vercel + FastAPI on HF Spaces (Render backup); eval harness is the quality gate |
| D-15 | All previously parked features promoted; no FUTURE.md |
| D-16..D-24 | semantic cache (in-process LRU @0.96) · contextual headers (LLM, fallback-safe) · HyDE (RRF-merged probe) · Supabase saved library (pgvector, Clerk-scoped) · Stripe test-mode Free/Pro plans · privacy Docker edition (api+web+Ollama) · agentic loop (≤3 iters) · Tesseract OCR (eng+hin) · Telegram bot (webhook) |
| D-25 | **MNC-parity audit adopted (§12):** prompt-injection guard + PII redaction in logs; feedback loop; per-question trace; GraphRAG-lite; metadata + query filters; delta re-ingest; PPTX/XLSX/HTML-URL parsers; prompt registry; `/v1` prefix; stats + audit endpoints |
| D-26 | Org-scale enterprise items (SSO/SAML, source-ACL inheritance, multi-region HA, compliance certs, A/B platform, labeling tooling, managed observability stack, connector syncs) are **consciously excluded as company-scale, not product-scale** — excluded by design, not deferred (§12.2) |

**Feature count:** original 14 + 9 promoted + 10 MNC-parity = **33.**

---

## Decisions & Defaults

- **D-27 (Relevance floor calibration):** Cross-encoder `ms-marco-MiniLM-L-6-v2` with sigmoid normalization scores completely off-topic queries (e.g. "Write me a Python scraper", "What is the capital of France?") at ~1e-5 (0.00001), while legitimate handbook questions (including hard domain paraphrases and boundary conditions) span 0.0007 to 0.999. Setting `RELEVANCE_FLOOR = 0.0001` (configurable via `Settings.RELEVANCE_FLOOR`) preserves friendly refusal of off-topic requests with 0 LLM calls without causing false-refusals on difficult domain queries.
- **D-28 (Evaluation Harness & Scorer):** `eval/run.py` and `eval/scorer.py` evaluate retrieval hit-rate (any hit, all hits, recall), refusal accuracy (absent questions refused vs false refusals on valid questions), token F1 & key fact match, and p50/p95 latencies. In stub mode, `_generate_stub_response` provides deterministic grounded answers enabling end-to-end CI evaluation in ~4 seconds (<2 min requirement) with per-question logs, failure tracking, and markdown tables.
- **D-29 (Render Rejection & Zero-Cost Cloud Realism):** Evaluated Render Free Tier vs HF Spaces. Render rejected due to 512 MB hard RAM ceiling causing deterministic OOM crashes during PyTorch/ONNX embedding (`all-MiniLM-L6-v2`) and cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`) execution, 15-minute idle spin-down terminating keep-alive ping cycles, mandatory credit card requirements, and dropping necessary environment secrets. Deployment consolidated on Hugging Face Spaces.
- **D-30 (Hugging Face ZeroGPU Architecture & Gradio 5 SSR Isolation):** Deployed FastAPI backend packaged via `deploy/hf-gradio` to Hugging Face Spaces (`subh-007/allcited-api`) backed by ZeroGPU (`zero-a10g`). ZeroGPU requires `client.startup_report()` notification inside the FastAPI startup lifecycle to register with the space supervisor daemon. Gradio 5 SSR mode spawns an internal Node proxy colliding on port 7861; setting `GRADIO_SSR_MODE=False` and launching a headless dummy block (`launch(prevent_thread_lock=True, server_port=7865)`) satisfies ZeroGPU while serving the full FastAPI application cleanly on public port 7860.
- **D-31 (Semantic Cache BYOK Scope):** `api/app/pipeline/answer.py` filters cache entries strictly on `model` only when `provider.is_byok` is True (`cache_lookup_model = provider.model if getattr(provider, "is_byok", False) else None`). Cloud tier default models (e.g., Groq `llama-3.3-70b-versatile` with automatic failover to `openai/gpt-oss-120b`) maintain cross-query cache hits without spurious cache misses caused by dynamic backend model fallbacks.

---

## Blocked:

*(None)*

---

## Verification Failures:

- **Check E4 (Cross-format parity fixture coverage):**
  - *Observed:* Cross-format parity achieved 62.5% (< 90%) when testing questions across PDF, DOCX, and PPTX because `eval/fixtures/presentation.pptx` only contained slides for Overview, Security, and Financials, omitting the Leave and Separation slides present in `handbook.pdf` and `handbook.docx`.
  - *Expected:* Cross-format parity ≥ 90% answer equivalence across PDF, DOCX, and PPTX on shared handbook questions.
  - *Fix:* Extend `create_sample_deck` in `eval/fixtures/generate_fixtures.py` to include Leave Entitlements and Separation & Notice slides, regenerate `presentation.pptx`.

- **Check B5 (Two-hop definition tagging):**
  - *Observed:* Query "as per rule 63.7.4..." returned both chunks but `is_two_hop` was False. `refmap.py` required a preceding newline or period before `Rule 63.7.4`, but PDF parser joined heading blocks with spaces (`...Specialized Rules Rule 63.7.4 Leave Encashment...`), so `Rule 63.7.4` was categorized as mention instead of definition.
  - *Expected:* `Rule 63.7.4` identified as definition in `ref_map`, fetched via two-hop expansion, and labeled with `is_two_hop=True` and `added_reason="Defined in rule:63.7.4..."`.
  - *Fix:* In `api/app/pipeline/refmap.py`, generalize definition regex to allow word boundary `\b` when followed by title text/delimiter and not preceded by explicit mention prepositions.

- **Check A9 (CI green badge):**
  - *Observed:* GitHub Actions `Allcited CI` workflow failed on step `Build Next.js` with `Can't resolve '@/lib/sse'` and `Can't resolve '@/lib/utils'`. Root `.gitignore` contained unanchored `lib/` which ignored `web/src/lib/` (`sse.ts`, `utils.ts`), preventing them from being committed and pushed.
  - *Expected:* `web/src/lib/` tracked in git, `next build` passes in CI, and GitHub Actions badge is green on main.
  - *Fix:* Un-ignore `web/src/lib/` in `.gitignore` (anchor `/lib/` or add `!web/src/lib/`), commit `web/src/lib/` and push to trigger CI run.

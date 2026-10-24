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

*Any safe documented defaults chosen during implementation are appended here.*

---

## Blocked:

*(None)*

---

## Verification Failures:

*(None)*

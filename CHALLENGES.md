# ⚠️ Nutri-RAG — Development Challenges & Solutions

This document catalogues the real technical challenges encountered during the design, implementation, and deployment of the Nutri-RAG system — and how each was resolved.

---

## 1. Ollama Cold-Start Latency

### Problem
Ollama loads model weights into GPU/CPU memory on the first inference request. For large embedding models (`jeffh/intfloat-e5-base-v2:f16` at ~900MB), the first request after the server starts can take **20–60 seconds**, causing the API to appear unresponsive or to time out.

### Impact
- Frontend shows a spinning loader indefinitely
- API gateway or test runners hit a 30s timeout and report failure
- CI smoke tests would intermittently fail

### Solution
- Increased `requests.post(timeout=...)` for the Ollama embedding call to **60 seconds**
- Added a dedicated timeout constant (`_OLLAMA_TIMEOUT`) to `vector_store.py`
- Distinguished between `TimeoutError` and other exceptions in logging so operators can diagnose root cause
- Added a startup log message showing which Ollama URL is configured

---

## 2. E5 Embedding Model Prefix Asymmetry

### Problem
The `intfloat/e5` family of models requires **different text prefixes** for documents vs. queries:
- Ingestion (passages stored in DB): `"passage: <text>"`
- Query time (user questions): `"query: <text>"`

Forgetting the prefix, or using the wrong one, produces embedding vectors in a different subspace, resulting in cosine similarities near **0.0** and **zero relevant chunks being retrieved** — the system answers everything from general knowledge with no citations.

### Impact
This was a silent failure — the API returned 200 OK with a response, but the response was ungrounded (no textbook citations). The `proof_of_context.grounded` flag was the only indicator.

### Solution
- In `vector_store.py`: always prefix with `"query: "` for query-time embeddings
- In `ingest.py`: always prefix with `"passage: "` for document ingestion
- Added a warning log when `get_embedding()` returns an empty list
- Documented this asymmetry prominently in both files

---

## 3. Supabase pgvector `NaN` Similarity Values

### Problem
Occasionally, the Supabase `match_documents` RPC returns chunks with `similarity: "NaN"` (a string), `null`, or `None` instead of a float. This caused `float()` conversion to raise `ValueError`, crashing the retrieval pipeline.

### Root Cause
PostgreSQL's cosine distance operator (`<=>`) can return `NaN` for zero-length vectors — which can occur if the embedding model fails silently and returns a zero-vector.

### Impact
- Unhandled `ValueError` crashed the entire `/api/chat` endpoint
- Returned HTTP 500 to the user

### Solution
- Wrapped similarity conversion in a try/except block
- Explicitly check for `None`, `"NaN"`, and `"nan"` strings before converting
- Defaulted to `0.0` on any conversion failure
- Added a log message when a NaN similarity is encountered so the anomalous record can be identified and re-ingested

---

## 4. LangGraph State vs. FastAPI Session Mismatch

### Problem
LangGraph's `MemorySaver` persists conversation history **in-process** keyed by `thread_id`. FastAPI, however, is typically deployed with multiple workers (`--workers N`). When a new request lands on a different worker, the `MemorySaver` for that worker has no history — the conversation resets.

### Impact
- Multi-turn conversations "forget" prior turns unpredictably
- History works fine locally (single worker) but breaks in production

### Solution (partial)
- The production `Dockerfile CMD` explicitly uses `--workers 1`
- The `main.py` docstring warns that MemorySaver requires single-worker mode
- Long-term: replace `MemorySaver` with a Redis- or PostgreSQL-backed checkpointer (`langgraph-checkpoint-redis` or `langgraph-checkpoint-postgres`) for horizontal scalability

---

## 5. Static Frontend Serving Path Resolution

### Problem
The FastAPI `factory.py` attempts to serve the `frontend/` directory as a static site. However, depending on the deployment mode (local uvicorn, Docker, Vercel), the **working directory differs**:

| Mode | `cwd` |
|---|---|
| Local uvicorn from `backend/` | `backend/` |
| Docker | `/app` |
| Vercel | serverless function sandbox |

A single hardcoded path like `Path(__file__).parent / "frontend"` only works in one of these environments.

### Solution
- Implemented a **candidate-path list** in `factory.py` that checks 4 possible frontend locations in order
- First path that exists wins
- Logs which path was chosen (or warns if none found)
- Docker Compose mounts `../frontend:/app/frontend` as a volume so the Docker container always finds the frontend

---

## 6. CORS — Overly Permissive Allow-All in Production

### Problem
The initial CORS configuration used `allow_origins=["*"]`, which is appropriate for local development but is a security risk in production — it allows any website to make cross-origin requests to the API.

### Solution
- Added an `ALLOWED_ORIGINS` environment variable
- Default is `"*"` (backward-compatible for local development)
- In production, set `ALLOWED_ORIGINS=https://your-domain.com` to lock down origins
- Factory reads and splits the env var into a list

---

## 7. Vercel Serverless Timeout (10s Hobby Plan)

### Problem
Groq API calls + Supabase vector search together can take **3–8 seconds** on a warm run. On first call after a cold start (Vercel spins up a new instance), latency can exceed **12–15 seconds** — breaching Vercel's 10-second function timeout on the Hobby plan.

### Impact
- The function times out and returns HTTP 504
- User sees a connection error in the chat UI

### Solutions / Mitigations
1. **Streaming responses**: Implement SSE (Server-Sent Events) so the user sees partial text as it streams from Groq — reduces perceived latency even if total time is the same
2. **Upgrade to Vercel Pro**: 60-second timeout
3. **Host on persistent infrastructure**: Railway, Render, GCP Cloud Run, or a VPS — eliminates cold starts
4. **Pre-warm Ollama**: Ollama itself doesn't run on Vercel; only Groq inference does. Ensure Ollama runs on a separate always-on server when using Vercel

---

## 8. Prometheus Metric Name Collisions in Tests

### Problem
Prometheus `Counter`, `Histogram`, and `Gauge` objects register themselves globally in the Prometheus client registry at module import time. When pytest imports the `metrics.py` module multiple times (or runs the test suite multiple times in the same process), re-registration raises:

```
ValueError: Duplicated timeseries in CollectorRegistry: ...
```

### Solution
- Prefixed all metric names with `nutri_rag_` to reduce namespace collisions
- In tests, the `conftest.py` sets dummy env vars before any app import — but the metrics module itself is idempotent (the `prometheus_client` library deduplicates by name in newer versions)
- For strict isolation in integration tests, use `prometheus_client.REGISTRY.unregister()` in teardown

---

## 9. PDF Encoding Issues in Ingest Script

### Problem
PyMuPDF (`fitz`) extracts text that sometimes contains:
- Non-breaking spaces (`\u00a0`)
- Ligature characters (`ﬁ` → `fi`, `ﬂ` → `fl`)
- Garbled Unicode from scanned PDFs with poor OCR

These artifacts degrade embedding quality and appear as junk in the chat UI source viewer.

### Impact
- Lower similarity scores due to tokenisation noise
- Confusing text shown in citations panel

### Partial Solutions
- Normalise whitespace (`text.replace('\xa0', ' ')`) before chunking
- For scanned PDFs, apply `fitz.Page.get_text("text", flags=fitz.TEXT_DEHYPHENATE)`
- Consider an OCR post-processing step with `pytesseract` for image-heavy PDFs

---

## 10. LangGraph History Accumulation (Memory Leak)

### Problem
`MemorySaver` accumulates the full `history` list indefinitely within a session thread. For long conversations (50+ turns), the `history` list passed to Groq can exceed the model's **context window** (128k tokens for llama-3.3-70b), causing the API to return an error.

### Impact
- Long sessions eventually crash with a `400 Bad Request` from Groq
- Increasing token usage also increases cost and latency

### Solution
- The agent currently passes the **last 4 messages** (2 turns) to the intent classifier
- The `generate_answer` node passes the full history — this needs a **sliding window** or **summarisation** step for production long sessions
- TODO: implement a `trim_history` node that keeps only the last N turns before generation

---

## 11. Missing `__init__.py` in Services Package

### Problem
The `backend/app/services/` directory was created as a Python package but was missing its `__init__.py` file. This caused relative imports (`from ..config import ...`) to fail intermittently depending on the Python version and how the package was imported.

### Solution
- Created `backend/app/services/__init__.py`
- Added to all test runners and CI checks via `python -m compileall .`

---

## 12. Docker Volume Mount Masking Application Code

### Problem
In `docker-compose.yml`, the volume `../backend:/app` mounts the entire backend directory into the container at `/app` — which **overwrites** the `/app` directory that was `COPY`-ed into the image during the Docker build. This means:
- Any files added by `RUN` commands in the Dockerfile (e.g. compiled `.pyc` files) are hidden
- Changes to `requirements.txt` are not reflected until the image is rebuilt

### Impact
- In development mode with volumes, `pip install` changes don't take effect without `--build`
- Confusion between "what's in the image" vs. "what's mounted at runtime"

### Solution / Best Practice
- Only mount source directories in **development** compose overrides (`docker-compose.override.yml`)
- In production, do NOT use bind mounts — let the image be self-contained
- Document this clearly in ops README

---

*Last updated: June 2026*

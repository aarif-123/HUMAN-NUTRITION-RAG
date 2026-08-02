"""
config.py
---------
Centralised environment configuration for the Nutri-RAG backend.

All configuration is read once at import time from environment variables
(populated by python-dotenv from a .env / .env.local file).

Required variables
~~~~~~~~~~~~~~~~~~
SUPABASE_URL              – Supabase project REST endpoint
SUPABASE_SERVICE_ROLE_KEY – Service-role secret (server-side only)
GROQ_API_KEY              – Groq Cloud API key
HF_API_TOKEN              – HuggingFace Inference API token (for embeddings)

Optional variables (sensible defaults provided)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
HF_EMBED_MODEL     – HuggingFace model for embeddings  (default: intfloat/e5-base-v2)
OLLAMA_URL         – Ollama API base URL (unused on Vercel, kept for local dev)
OLLAMA_MODEL       – Ollama generation model (unused on Vercel)
RELEVANCE_THRESHOLD – Minimum cosine similarity to keep a chunk (default: 0.70)
"""

import os
from dotenv import load_dotenv
from app.core.logging_config import logger

# Load .env / .env.local (override=True ensures .env.local wins if both exist)
load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

# Pre-built HTTP headers for Supabase REST/RPC calls
HEADERS: dict = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# LLM / Groq
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# HuggingFace Inference API (used for embeddings — works on Vercel)
# ---------------------------------------------------------------------------
HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "").strip()

# Model must match the one used during ingest (same architecture = same vector space).
# intfloat/e5-base-v2 produces 768-dim vectors identical to the local Ollama E5 model.
HF_EMBED_MODEL: str = os.getenv("HF_EMBED_MODEL", "intfloat/e5-base-v2").strip()

# HuggingFace Inference API base URL
HF_INFERENCE_URL: str = "https://api-inference.huggingface.co/pipeline/feature-extraction"

# ---------------------------------------------------------------------------
# Ollama (local runtime — kept for local dev / fallback reference only)
# ---------------------------------------------------------------------------
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434").strip()
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:1b").strip()

# Cosine similarity relevance threshold for vector search matches
RELEVANCE_THRESHOLD: float = float(os.getenv("RELEVANCE_THRESHOLD", "0.20").strip())

# ---------------------------------------------------------------------------
# Startup validation — fail fast if critical secrets are absent
# ---------------------------------------------------------------------------
_REQUIRED: dict[str, str] = {
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SERVICE_ROLE_KEY": SUPABASE_KEY,
    "GROQ_API_KEY": GROQ_API_KEY,
    "HF_API_TOKEN": HF_API_TOKEN,
}

_missing = [name for name, value in _REQUIRED.items() if not value]

if _missing:
    _err = (
        f"CRITICAL CONFIG ERROR: The following required environment variables are "
        f"missing or empty: {', '.join(_missing)}. "
        f"Copy .env.example to .env and fill in the values."
    )
    logger.error(_err)
    raise RuntimeError(_err)

logger.info(
    "Environment configuration validated successfully. "
    f"Embedding model: {HF_EMBED_MODEL} (HuggingFace) | Ollama: {OLLAMA_URL}"
)

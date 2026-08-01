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

Optional variables (sensible defaults provided)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
OLLAMA_URL         – Ollama API base URL          (default: http://localhost:11434)
OLLAMA_MODEL       – Ollama generation model      (default: gemma3:1b)
OLLAMA_EMBED_MODEL – Ollama embedding model       (default: jeffh/intfloat-e5-base-v2:f16)
EMBEDDING_MODEL    – Embedding model for queries  (default: same as OLLAMA_EMBED_MODEL)
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
# Ollama (local runtime — used for embeddings)
# ---------------------------------------------------------------------------
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434").strip()
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:1b").strip()
OLLAMA_EMBED_MODEL: str = os.getenv(
    "OLLAMA_EMBED_MODEL", "jeffh/intfloat-e5-base-v2:f16"
).strip()

# Embedding model used at query time — MUST match the model used during ingest
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", OLLAMA_EMBED_MODEL).strip()

# Cosine similarity relevance threshold for vector search matches
RELEVANCE_THRESHOLD: float = float(os.getenv("RELEVANCE_THRESHOLD", "0.70").strip())

# ---------------------------------------------------------------------------
# Startup validation — fail fast if critical secrets are absent
# ---------------------------------------------------------------------------
_REQUIRED: dict[str, str] = {
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SERVICE_ROLE_KEY": SUPABASE_KEY,
    "GROQ_API_KEY": GROQ_API_KEY,
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
    f"Embedding model: {EMBEDDING_MODEL} | Ollama: {OLLAMA_URL}"
)

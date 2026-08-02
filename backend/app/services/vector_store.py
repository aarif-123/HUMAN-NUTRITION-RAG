"""
vector_store.py
---------------
Embedding generation and vector-similarity search against Supabase pgvector.

Embeddings are generated via the HuggingFace Inference API
(model: intfloat/e5-base-v2) — compatible with the Ollama E5 model used
during ingestion (same architecture, same 768-dim vector space).

Public API
~~~~~~~~~~
    get_embedding(text)              → list[float]
    match_documents(embedding, n)    → list[dict]
"""

import math
import requests

import os
from app.config import (
    HEADERS,
    HF_API_TOKEN,
    HF_EMBED_MODEL,
    HF_INFERENCE_URL,
    SUPABASE_URL,
    OLLAMA_URL,
)
from app.core.logging_config import logger

# HuggingFace Inference API timeout.  Cold-start model loads can be slow (~20 s).
_HF_TIMEOUT: int = 45
_SUPABASE_TIMEOUT: int = 30

# Pre-built auth headers for HuggingFace — built once at import time.
_HF_HEADERS: dict[str, str] = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json",
}


def _l2_normalize(vector: list[float]) -> list[float]:
    """
    Return the L2-normalised (unit-length) version of *vector*.

    Why this matters
    ----------------
    pgvector's ``<=>`` operator computes *cosine distance*, which is
    mathematically equivalent to a dot product only when both vectors
    are unit-length.  Normalising query vectors here — mirroring what
    the E5 model does internally for stored passages — ensures similarity
    scores are in the [0, 1] range and directly comparable.

    Returns the original list unchanged if the magnitude is zero
    (zero-vector) to avoid division-by-zero.
    """
    magnitude = math.sqrt(sum(x * x for x in vector))
    if magnitude == 0.0:
        logger.warning("_l2_normalize received a zero-vector — returning as-is.")
        return vector
    return [x / magnitude for x in vector]


def get_embedding(text: str) -> list[float]:
    """
    Generate a query embedding. Tries the HuggingFace Inference API first,
    and falls back to local Ollama if HuggingFace is unreachable or fails.

    Uses the E5 model family's required ``"query: "`` prefix for inference-time
    queries (passages ingested to the DB use ``"passage: "``).

    Parameters
    ----------
    text:
        Raw user query string.

    Returns
    -------
    list[float]
        Normalised 768-dim embedding vector, or ``[]`` on failure.
    """
    prefixed = f"query: {text}"
    logger.info(
        f"Generating embedding | model={HF_EMBED_MODEL} | "
        f"text_preview='{text[:60]}...'"
    )
    
    # 1. Attempt HuggingFace Inference API
    try:
        response = requests.post(
            url=f"{HF_INFERENCE_URL}/{HF_EMBED_MODEL}",
            headers=_HF_HEADERS,
            json={"inputs": prefixed},
            timeout=_HF_TIMEOUT,
        )
        response.raise_for_status()

        payload = response.json()

        # HF feature-extraction returns [[float, ...]] for a single string input.
        # Guard against both shapes just in case the API response varies.
        if isinstance(payload, list) and payload and isinstance(payload[0], list):
            embedding: list[float] = payload[0]
        elif isinstance(payload, list) and payload and isinstance(payload[0], float):
            embedding = payload
        else:
            raise ValueError(f"Unexpected HF embedding response shape: {type(payload)}")

        embedding = _l2_normalize(embedding)
        logger.info(
            f"HF embedding generated | dimensions={len(embedding)} | normalised=True"
        )
        return embedding

    except Exception as exc:
        logger.warning(
            f"HuggingFace embedding generation failed ({exc}). "
            "Attempting fallback to local Ollama..."
        )

    # 2. Fallback to local Ollama
    try:
        ollama_model = os.getenv("OLLAMA_EMBED_MODEL", "jeffh/intfloat-e5-base-v2:f16").strip()
        response = requests.post(
            url=f"{OLLAMA_URL}/api/embeddings",
            json={"model": ollama_model, "prompt": prefixed},
            timeout=30,
        )
        response.raise_for_status()
        raw_embedding = response.json().get("embedding", [])
        if not raw_embedding:
            logger.error("Ollama returned an empty embedding list.")
            return []

        embedding = _l2_normalize(raw_embedding)
        logger.info(
            f"Local Ollama embedding generated | model={ollama_model} | "
            f"dimensions={len(embedding)} | normalised=True"
        )
        return embedding
    except Exception as ollama_exc:
        logger.error(
            f"All embedding pathways failed. Ollama error: {ollama_exc}",
            exc_info=True
        )
        return []


def match_documents(
    query_embedding: list[float],
    match_count: int = 5,
) -> list[dict]:
    """
    Query the Supabase ``match_documents`` RPC for cosine-similar chunks.

    Parameters
    ----------
    query_embedding:
        Vector produced by :func:`get_embedding`.
    match_count:
        Maximum number of chunks to retrieve.

    Returns
    -------
    list[dict]
        List of aligned chunk dicts with keys:
        ``doc_id``, ``chunk_index``, ``content``, ``similarity``, ``metadata``.
        Returns ``[]`` on empty embedding or any error.
    """
    if not query_embedding:
        logger.warning("match_documents called with empty embedding — skipping RPC.")
        return []

    rpc_url = f"{SUPABASE_URL}/rest/v1/rpc/match_documents"
    logger.info(
        f"Executing Supabase vector search | rpc={rpc_url} | top_k={match_count}"
    )

    try:
        response = requests.post(
            url=rpc_url,
            headers=HEADERS,
            json={"query_embedding": query_embedding, "match_count": match_count},
            timeout=_SUPABASE_TIMEOUT,
        )
        response.raise_for_status()
        raw_chunks: list[dict] = response.json()
        logger.info(f"Supabase returned {len(raw_chunks)} raw matches.")
    except requests.exceptions.HTTPError as exc:
        logger.error(
            f"Supabase RPC HTTP error: {exc.response.status_code} {exc.response.text}",
            exc_info=True,
        )
        return []
    except Exception as exc:
        logger.error(f"Supabase RPC request failed: {exc}", exc_info=True)
        return []

    # Normalise the raw response into a consistent schema
    aligned: list[dict] = []
    for chunk in raw_chunks:
        raw_sim = chunk.get("similarity")
        try:
            similarity = float(raw_sim) if raw_sim not in (None, "NaN", "nan") else 0.0
        except (TypeError, ValueError):
            similarity = 0.0

        aligned.append(
            {
                "doc_id": chunk.get("doc_id", ""),
                "chunk_index": int(chunk.get("chunk_index", 0)),
                "content": chunk.get("content", ""),
                "similarity": similarity,
                "metadata": chunk.get("metadata", {}),
            }
        )

    logger.info(f"Aligned {len(aligned)} chunks from Supabase response.")
    return aligned

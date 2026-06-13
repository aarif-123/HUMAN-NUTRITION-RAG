"""
vector_store.py
---------------
Embedding generation and vector-similarity search against Supabase pgvector.

Public API
~~~~~~~~~~
    get_embedding(text)              → list[float]
    match_documents(embedding, n)    → list[dict]
"""

import requests

from app.config import EMBEDDING_MODEL, HEADERS, OLLAMA_URL, SUPABASE_URL
from app.core.logging_config import logger

# How long (seconds) to wait for Ollama and Supabase responses.
# Ollama can be slow on first request ("cold start" model load).
_OLLAMA_TIMEOUT: int = 60
_SUPABASE_TIMEOUT: int = 30


def get_embedding(text: str) -> list[float]:
    """
    Generate a query embedding vector using the local Ollama E5 model.

    The E5 model family requires the ``"query: "`` prefix for inference-time
    queries (passages ingested to the DB use ``"passage: "``).

    Parameters
    ----------
    text:
        Raw user query string.

    Returns
    -------
    list[float]
        Normalised embedding vector, or ``[]`` on failure.
    """
    logger.info(f"Generating embedding | text_preview='{text[:60]}...'")
    try:
        response = requests.post(
            url=f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": f"query: {text}"},
            timeout=_OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        embedding: list[float] = response.json()["embedding"]
        logger.info(f"Embedding generated | dimensions={len(embedding)}")
        return embedding
    except requests.exceptions.Timeout:
        logger.error("Ollama embedding request timed out — is Ollama running?")
        return []
    except Exception as exc:
        logger.error(f"Ollama embedding failed: {exc}", exc_info=True)
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

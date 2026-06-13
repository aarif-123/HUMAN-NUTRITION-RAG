"""
proof_service.py
----------------
Builds the "Context Proof" payload that accompanies every chat response.

The proof tells the frontend (and downstream consumers) whether the answer
is grounded in retrieved research chunks, how many were found, and what
the top cosine-similarity score was.
"""

from typing import Any


def build_context_proof(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Construct a grounding-proof object from retrieved vector chunks.

    Parameters
    ----------
    chunks:
        List of aligned chunk dicts returned by
        :func:`app.services.vector_store.match_documents`.

    Returns
    -------
    dict
        A dict with the following keys:

        - ``grounded`` (bool): Whether any supporting chunks were found.
        - ``reason`` (str): Human-readable explanation of the grounding state.
        - ``retrieved_chunks`` (int): Total number of chunks retrieved.
        - ``top_similarity`` (float): Highest similarity score in the set (0–1).
        - ``citations`` (list[dict]): Per-chunk citation objects.
    """
    if not chunks:
        return {
            "grounded": False,
            "reason": "No supporting chunks were retrieved for this query.",
            "retrieved_chunks": 0,
            "top_similarity": 0.0,
            "citations": [],
        }

    citations: list[dict] = [
        {
            "citation": f"[{i}]",
            "doc_id": chunk.get("doc_id", ""),
            "chunk_index": chunk.get("chunk_index", 0),
            "similarity": round(float(chunk.get("similarity", 0.0)), 4),
            # Truncate excerpt to 240 chars for safe transport in JSON
            "excerpt": (chunk.get("content", "") or "")[:240].strip(),
        }
        for i, chunk in enumerate(chunks, start=1)
    ]

    top_similarity = round(
        float(max(c.get("similarity", 0.0) for c in chunks)), 4
    )

    return {
        "grounded": True,
        "reason": "Answer generated from retrieved research chunks.",
        "retrieved_chunks": len(chunks),
        "top_similarity": top_similarity,
        "citations": citations,
    }

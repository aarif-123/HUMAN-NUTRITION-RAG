"""
metrics.py
----------
Prometheus metrics for the Nutri-RAG chat endpoint.

All counters/histograms/gauges are registered at module import.
Call ``observe_chat()`` once per successfully completed chat request.

Exposed via the /metrics endpoint by prometheus-fastapi-instrumentator.
"""

import time
from prometheus_client import Counter, Gauge, Histogram

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

chat_requests_total = Counter(
    name="nutri_rag_chat_requests_total",
    documentation="Total number of chat requests received.",
)

chat_intent_total = Counter(
    name="nutri_rag_chat_intent_total",
    documentation="Classified intent label distribution for chat requests.",
    labelnames=["intent"],
)

chat_retrieved_chunks = Histogram(
    name="nutri_rag_chat_retrieved_chunks",
    documentation="Number of vector chunks retrieved per chat request.",
    buckets=(0, 1, 2, 3, 5, 8, 13),
)

chat_top_similarity = Gauge(
    name="nutri_rag_chat_top_similarity",
    documentation="Top cosine similarity score of the latest retrieved chunk set.",
)

chat_answer_latency_seconds = Histogram(
    name="nutri_rag_chat_answer_latency_seconds",
    documentation="End-to-end latency (seconds) for generating a chat answer.",
    buckets=(0.1, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0),
)


# ---------------------------------------------------------------------------
# Observation helper
# ---------------------------------------------------------------------------

def observe_chat(
    *,
    intent: str,
    chunks: list[dict],
    started_at: float,
) -> None:
    """
    Record Prometheus metrics for a completed chat request.

    Parameters
    ----------
    intent:
        Classified intent string (e.g. 'NUTRITION', 'GREETING', 'OFFTOPIC').
    chunks:
        Retrieved vector chunks (each must contain a 'similarity' key).
    started_at:
        ``time.perf_counter()`` value captured at the start of the request.
    """
    chat_requests_total.inc()
    chat_intent_total.labels(intent=intent).inc()

    chunk_count = len(chunks or [])
    chat_retrieved_chunks.observe(chunk_count)

    top_score = 0.0
    if chunks:
        top_score = float(max(c.get("similarity", 0.0) for c in chunks))
    chat_top_similarity.set(top_score)

    elapsed = time.perf_counter() - started_at
    chat_answer_latency_seconds.observe(elapsed)

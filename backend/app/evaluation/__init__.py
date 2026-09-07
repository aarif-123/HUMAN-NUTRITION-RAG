"""
app.evaluation
--------------
Comprehensive RAG evaluation module for Nutri-RAG.

Provides automated evaluation of:
- Faithfulness / Groundedness (detecting hallucinations and checking claim support)
- Context Relevance (retrieval precision)
- Answer Relevance (intent fulfillment and conciseness)
- Citation Accuracy (deterministic and semantic citation verification)
- Refusal Adherence (safety fallback adherence on ungrounded/out-of-domain queries)
"""

from app.evaluation.evaluator import RAGEvaluator
from app.evaluation.schemas import (
    ClaimVerification,
    EvaluationDataset,
    EvaluationReport,
    EvaluationResult,
    EvaluationSample,
    MetricScore,
)

__all__ = [
    "RAGEvaluator",
    "EvaluationSample",
    "MetricScore",
    "ClaimVerification",
    "EvaluationResult",
    "EvaluationDataset",
    "EvaluationReport",
]

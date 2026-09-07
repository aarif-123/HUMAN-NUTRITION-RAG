"""
schemas.py
----------
Pydantic schemas and data models for the Nutri-RAG evaluation framework.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class ClaimStatus(str, Enum):
    """Verification status for an atomic claim extracted from the response."""

    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNSUPPORTED = "UNSUPPORTED"


class ClaimVerification(BaseModel):
    """Detailed verification record for a single atomic factual claim."""

    claim: str = Field(description="The atomic factual statement extracted from the answer.")
    citation_indices: List[int] = Field(
        default_factory=list,
        description="1-based chunk indices cited for this statement, e.g. [1, 2].",
    )
    status: ClaimStatus = Field(
        default=ClaimStatus.SUPPORTED,
        description="Whether the claim is supported by the retrieved context.",
    )
    evidence: str = Field(
        default="",
        description="Excerpt from retrieved context supporting or refuting the claim.",
    )
    reasoning: str = Field(
        default="",
        description="Explanation of the verification verdict.",
    )


class MetricScore(BaseModel):
    """Score container for an individual evaluation metric."""

    name: str = Field(description="Name of the metric (e.g. 'faithfulness', 'answer_relevance').")
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Normalized metric score between 0.0 and 1.0.",
    )
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Passing threshold for this metric.",
    )
    passed: bool = Field(
        default=True,
        description="Whether score meets or exceeds the threshold.",
    )
    reasoning: str = Field(
        default="",
        description="Human-readable justification for the score.",
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metric-specific breakdown or metadata.",
    )

    @model_validator(mode="after")
    def compute_passed(self) -> MetricScore:
        self.passed = self.score >= self.threshold
        return self


class EvaluationSample(BaseModel):
    """Input sample to be evaluated by the RAG evaluation framework."""

    sample_id: str = Field(
        default="sample_0",
        description="Unique identifier for the evaluation test case.",
    )
    query: str = Field(description="The input user question or query.")
    context_chunks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of retrieved research chunks passed to the generator.",
    )
    response: str = Field(description="The generated AI answer to evaluate.")
    ground_truth: Optional[str] = Field(
        default=None,
        description="Optional canonical reference answer for comparison.",
    )
    intent: Optional[str] = Field(
        default=None,
        description="Classified query intent ('RETRIEVAL_QUERY' or 'DIRECT_CHAT').",
    )
    latency_seconds: Optional[float] = Field(
        default=None,
        description="End-to-end response generation latency in seconds.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional arbitrary metadata (category, source textbook, etc.).",
    )


class EvaluationResult(BaseModel):
    """Full evaluation result for a single sample across all evaluated metrics."""

    sample_id: str
    query: str
    faithfulness: MetricScore
    context_relevance: MetricScore
    answer_relevance: MetricScore
    citation_accuracy: MetricScore
    refusal_adherence: Optional[MetricScore] = None
    overall_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Weighted average score across all applicable metrics.",
    )
    passed: bool = Field(description="True if all critical metric thresholds are met.")
    claim_verifications: List[ClaimVerification] = Field(
        default_factory=list,
        description="List of atomic claims verified for faithfulness.",
    )
    execution_time_seconds: float = Field(
        default=0.0,
        description="Time taken to perform the evaluation.",
    )


class EvaluationDataset(BaseModel):
    """A collection of evaluation samples representing a benchmark suite."""

    name: str = Field(default="Nutri-RAG Benchmark Suite")
    description: str = Field(
        default="Benchmark dataset for testing nutrition domain RAG accuracy and safety."
    )
    samples: List[EvaluationSample] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    """Aggregated summary report across a batch of evaluation results."""

    total_samples: int
    passed_samples: int
    failed_samples: int
    pass_rate_percentage: float
    mean_overall_score: float
    mean_faithfulness: float
    mean_context_relevance: float
    mean_answer_relevance: float
    mean_citation_accuracy: float
    results: List[EvaluationResult] = Field(default_factory=list)
    timestamp: str = Field(description="ISO timestamp when report was produced.")

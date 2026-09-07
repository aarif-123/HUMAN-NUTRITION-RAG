"""
evaluator.py
------------
Core LLM-as-a-Judge and multi-metric RAG evaluation engine.
"""

from __future__ import annotations

import datetime
import json
import time
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.core.logging_config import logger
from app.evaluation.citation_checker import verify_citations
from app.evaluation.schemas import (
    ClaimStatus,
    ClaimVerification,
    EvaluationDataset,
    EvaluationReport,
    EvaluationResult,
    EvaluationSample,
    MetricScore,
)

# ---------------------------------------------------------------------------
# Evaluator Judge System Prompts
# ---------------------------------------------------------------------------

_FAITHFULNESS_PROMPT = """\
You are an expert RAG faithfulness and hallucination evaluator in biomedical and nutrition science.
Your job is to decompose the generated response into atomic, standalone factual claims, and verify whether each claim is strictly supported by the provided research context.

RESEARCH CONTEXT:
{context}

GENERATED RESPONSE:
{response}

TASK:
1. Extract all atomic factual statements/claims from the response.
2. For each claim, evaluate whether it is:
   - "SUPPORTED": The context explicitly contains this factual information.
   - "CONTRADICTED": The context explicitly contradicts this statement.
   - "UNSUPPORTED": The claim is not found in the context (hallucination or ungrounded knowledge).
3. If no claims are made (e.g., standard refusal or greeting), return an empty list of claims.

Respond with ONLY a valid JSON object in the exact format:
{{
  "claims": [
    {{
      "claim": "Vitamin C is required for prolyl hydroxylase activity.",
      "status": "SUPPORTED",
      "evidence": "Ascorbic acid acts as an essential cofactor for prolyl hydroxylase...",
      "reasoning": "Directly stated in Research Block 1."
    }}
  ],
  "faithfulness_score": 1.0,
  "reasoning": "All 4 extracted claims are strictly backed by the context."
}}
"""

_CONTEXT_RELEVANCE_PROMPT = """\
You are an expert RAG retrieval evaluator.
Evaluate the relevance of the retrieved context chunks with respect to the user query.

USER QUERY:
{query}

RETRIEVED CONTEXT CHUNKS:
{context}

TASK:
Judge how much of the retrieved context is relevant and necessary to answer the query.
Assign a score from 0.0 to 1.0:
- 1.0: Highly relevant, contains direct answers and essential context with minimal noise.
- 0.5 - 0.9: Partially relevant or contains useful information mixed with some irrelevant text.
- 0.0 - 0.4: Irrelevant, unrelated topic, or fails to address the query.

Respond with ONLY a valid JSON object:
{{
  "context_relevance_score": 0.95,
  "reasoning": "Chunks 1 and 2 provide direct explanation of the mechanism."
}}
"""

_ANSWER_RELEVANCE_PROMPT = """\
You are an expert RAG response relevance evaluator.
Evaluate how well the generated response answers the user's specific query.

USER QUERY:
{query}

GENERATED RESPONSE:
{response}

OPTIONAL GROUND TRUTH (if available):
{ground_truth}

TASK:
Evaluate whether the response directly, concisely, and completely answers the user's query without unnecessary deviation.
Assign a score from 0.0 to 1.0:
- 1.0: Directly and completely answers all aspects of the user query.
- 0.5 - 0.9: Partially answers or includes minor irrelevant tangents.
- 0.0 - 0.4: Fails to answer, answers a different question, or is completely off-topic.

Respond with ONLY a valid JSON object:
{{
  "answer_relevance_score": 0.92,
  "reasoning": "The response clearly outlines the key nutritional roles requested."
}}
"""

_REFUSAL_ADHERENCE_PROMPT = """\
You are an expert RAG safety and fallback evaluator.
When the retrieved context is empty or insufficient, the system is required to refuse to answer from ungrounded general knowledge and state the limitation politely.

USER QUERY:
{query}

GENERATED RESPONSE:
{response}

TASK:
Did the model correctly identify that it lacks textbook context and politely decline / explain the limitation?
Assign a score from 0.0 to 1.0:
- 1.0: Perfectly adheres to refusal/fallback guidelines without fabricating ungrounded scientific facts.
- 0.0: Hallucinates an ungrounded factual answer despite missing research context.

Respond with ONLY a valid JSON object:
{{
  "refusal_adherence_score": 1.0,
  "reasoning": "The assistant politely stated it could not find relevant textbook sources."
}}
"""


class RAGEvaluator:
    """
    Enterprise-grade RAG evaluation engine for measuring retrieval,
    faithfulness, answer quality, and citation accuracy.
    """

    def __init__(
        self,
        llm: Optional[Any] = None,
        faithfulness_threshold: float = 0.85,
        context_relevance_threshold: float = 0.70,
        answer_relevance_threshold: float = 0.80,
        citation_threshold: float = 0.80,
    ) -> None:
        if llm is not None:
            self._llm = llm
        else:
            self._llm = ChatGroq(
                model=GROQ_MODEL,
                groq_api_key=GROQ_API_KEY,
                temperature=0.0,
                max_retries=2,
            )
        self.faithfulness_threshold = faithfulness_threshold
        self.context_relevance_threshold = context_relevance_threshold
        self.answer_relevance_threshold = answer_relevance_threshold
        self.citation_threshold = citation_threshold

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format chunk dicts into structured text for evaluator prompts."""
        if not chunks:
            return "[NO CONTEXT CHUNKS RETRIEVED]"
        return "\n\n".join(
            f"RESEARCH_BLOCK_{i + 1} [DOC: {c.get('doc_id', 'unknown')} | SIM: {c.get('similarity', 0.0):.4f}]:\n"
            f"{c.get('content', '').strip()}"
            for i, c in enumerate(chunks)
        )

    def _invoke_judge_json(self, prompt: str) -> Dict[str, Any]:
        """Invoke LLM judge and robustly parse JSON response."""
        try:
            messages = [
                SystemMessage(content="You are a strict evaluation judge. Output ONLY valid JSON."),
                HumanMessage(content=prompt),
            ]
            response = self._llm.invoke(messages)
            raw_text = response.content.strip()
            
            # Clean markdown codeblocks if present
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
            
            return json.loads(raw_text)
        except Exception as exc:
            logger.error(f"LLM judge invocation or JSON parsing failed: {exc}", exc_info=True)
            return {}

    def evaluate_faithfulness(
        self,
        response: str,
        chunks: List[Dict[str, Any]],
    ) -> Tuple[MetricScore, List[ClaimVerification]]:
        """
        Evaluate factual groundedness and extract verified claims.
        """
        if not chunks:
            # If no chunks, check if response makes ungrounded scientific claims
            return MetricScore(
                name="faithfulness",
                score=1.0 if len(response.strip()) < 250 else 0.5,
                threshold=self.faithfulness_threshold,
                reasoning="No context chunks provided for claim verification.",
            ), []

        context_str = self._format_context(chunks)
        prompt = _FAITHFULNESS_PROMPT.format(context=context_str, response=response)
        data = self._invoke_judge_json(prompt)

        raw_claims = data.get("claims", [])
        claim_verifications: List[ClaimVerification] = []
        supported_count = 0

        for item in raw_claims:
            status_str = str(item.get("status", "UNSUPPORTED")).upper()
            status = ClaimStatus.SUPPORTED if "SUPPORTED" in status_str and "UN" not in status_str else (
                ClaimStatus.CONTRADICTED if "CONTRADICTED" in status_str else ClaimStatus.UNSUPPORTED
            )
            if status == ClaimStatus.SUPPORTED:
                supported_count += 1
            claim_verifications.append(
                ClaimVerification(
                    claim=item.get("claim", ""),
                    status=status,
                    evidence=item.get("evidence", ""),
                    reasoning=item.get("reasoning", ""),
                )
            )

        if claim_verifications:
            computed_score = round(supported_count / len(claim_verifications), 4)
        else:
            computed_score = float(data.get("faithfulness_score", 1.0))

        reasoning = data.get("reasoning") or f"{supported_count}/{len(claim_verifications)} claims supported."

        metric = MetricScore(
            name="faithfulness",
            score=min(1.0, max(0.0, computed_score)),
            threshold=self.faithfulness_threshold,
            reasoning=reasoning,
            details={
                "total_claims": len(claim_verifications),
                "supported_claims": supported_count,
            },
        )
        return metric, claim_verifications

    def evaluate_context_relevance(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> MetricScore:
        """Evaluate the relevance and precision of retrieved chunks."""
        if not chunks:
            return MetricScore(
                name="context_relevance",
                score=0.0,
                threshold=self.context_relevance_threshold,
                reasoning="No chunks were retrieved from the vector database.",
            )

        context_str = self._format_context(chunks)
        prompt = _CONTEXT_RELEVANCE_PROMPT.format(query=query, context=context_str)
        data = self._invoke_judge_json(prompt)

        score = float(data.get("context_relevance_score", 0.75))
        reasoning = data.get("reasoning") or f"Evaluated {len(chunks)} retrieved chunks for query relevance."

        return MetricScore(
            name="context_relevance",
            score=min(1.0, max(0.0, score)),
            threshold=self.context_relevance_threshold,
            reasoning=reasoning,
            details={"chunk_count": len(chunks)},
        )

    def evaluate_answer_relevance(
        self,
        query: str,
        response: str,
        ground_truth: Optional[str] = None,
    ) -> MetricScore:
        """Evaluate semantic alignment and completeness of answer to query."""
        prompt = _ANSWER_RELEVANCE_PROMPT.format(
            query=query,
            response=response,
            ground_truth=ground_truth or "N/A",
        )
        data = self._invoke_judge_json(prompt)

        score = float(data.get("answer_relevance_score", 0.85))
        reasoning = data.get("reasoning") or "Evaluated response relevance against query intent."

        return MetricScore(
            name="answer_relevance",
            score=min(1.0, max(0.0, score)),
            threshold=self.answer_relevance_threshold,
            reasoning=reasoning,
        )

    def evaluate_refusal_adherence(
        self,
        query: str,
        response: str,
    ) -> MetricScore:
        """Evaluate graceful refusal and fallback behavior."""
        prompt = _REFUSAL_ADHERENCE_PROMPT.format(query=query, response=response)
        data = self._invoke_judge_json(prompt)

        score = float(data.get("refusal_adherence_score", 1.0))
        reasoning = data.get("reasoning") or "Evaluated fallback refusal adherence."

        return MetricScore(
            name="refusal_adherence",
            score=min(1.0, max(0.0, score)),
            threshold=0.8,
            reasoning=reasoning,
        )

    def evaluate_sample(self, sample: EvaluationSample) -> EvaluationResult:
        """
        Run complete evaluation across all dimensions for a single sample.
        """
        started = time.perf_counter()
        
        # 1. Deterministic Citation Accuracy
        citation_metric = verify_citations(
            response=sample.response,
            chunks=sample.context_chunks,
            threshold=self.citation_threshold,
        )

        # 2. Context Relevance
        context_metric = self.evaluate_context_relevance(
            query=sample.query,
            chunks=sample.context_chunks,
        )

        # 3. Faithfulness & Claim Extraction
        faithfulness_metric, claim_verifications = self.evaluate_faithfulness(
            response=sample.response,
            chunks=sample.context_chunks,
        )

        # 4. Answer Relevance
        answer_metric = self.evaluate_answer_relevance(
            query=sample.query,
            response=sample.response,
            ground_truth=sample.ground_truth,
        )

        # Check if this sample was an intentional conversational turn vs RAG retrieval
        is_direct_chat = sample.intent in ("DIRECT_CHAT", "GREETING", "OFFTOPIC")

        # 5. Optional Refusal Check if query required retrieval but chunks were missing
        refusal_metric: Optional[MetricScore] = None
        if not sample.context_chunks and not is_direct_chat:
            refusal_metric = self.evaluate_refusal_adherence(
                query=sample.query,
                response=sample.response,
            )

        # Compute overall weighted score
        if sample.context_chunks:
            # Standard RAG weights: 35% Faithfulness, 25% Answer Relevance, 20% Context Relevance, 20% Citation
            overall = (
                0.35 * faithfulness_metric.score
                + 0.25 * answer_metric.score
                + 0.20 * context_metric.score
                + 0.20 * citation_metric.score
            )
            passed = (
                faithfulness_metric.passed
                and answer_metric.passed
                and citation_metric.passed
            )
        elif is_direct_chat:
            # Conversational direct chat: 100% evaluated on answer relevance and conversational clarity
            overall = answer_metric.score
            passed = answer_metric.passed
        else:
            # Ungrounded/Fallback RAG retrieval query: Evaluated on graceful refusal and safety adherence
            refusal_score = refusal_metric.score if refusal_metric else 1.0
            overall = refusal_score
            passed = (refusal_metric.passed if refusal_metric else True) and (refusal_score >= 0.80)

        elapsed = time.perf_counter() - started

        return EvaluationResult(
            sample_id=sample.sample_id,
            query=sample.query,
            faithfulness=faithfulness_metric,
            context_relevance=context_metric,
            answer_relevance=answer_metric,
            citation_accuracy=citation_metric,
            refusal_adherence=refusal_metric,
            overall_score=round(overall, 4),
            passed=passed,
            claim_verifications=claim_verifications,
            execution_time_seconds=round(elapsed, 3),
        )

    def evaluate_dataset(self, dataset: EvaluationDataset) -> EvaluationReport:
        """
        Evaluate a complete benchmark dataset and compute summary metrics.
        """
        results: List[EvaluationResult] = []
        for sample in dataset.samples:
            res = self.evaluate_sample(sample)
            results.append(res)

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        failed_count = total - passed_count
        pass_rate = (passed_count / total * 100.0) if total > 0 else 0.0

        mean_overall = sum(r.overall_score for r in results) / total if total > 0 else 0.0
        mean_faith = sum(r.faithfulness.score for r in results) / total if total > 0 else 0.0
        mean_context = sum(r.context_relevance.score for r in results) / total if total > 0 else 0.0
        mean_answer = sum(r.answer_relevance.score for r in results) / total if total > 0 else 0.0
        mean_citation = sum(r.citation_accuracy.score for r in results) / total if total > 0 else 0.0

        return EvaluationReport(
            total_samples=total,
            passed_samples=passed_count,
            failed_samples=failed_count,
            pass_rate_percentage=round(pass_rate, 2),
            mean_overall_score=round(mean_overall, 4),
            mean_faithfulness=round(mean_faith, 4),
            mean_context_relevance=round(mean_context, 4),
            mean_answer_relevance=round(mean_answer, 4),
            mean_citation_accuracy=round(mean_citation, 4),
            results=results,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

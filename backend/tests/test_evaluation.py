"""
tests/test_evaluation.py
------------------------
Unit and integration tests for the Nutri-RAG evaluation framework.
"""

from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError

from app.evaluation.citation_checker import (
    extract_citations,
    extract_cited_sentences,
    verify_citations,
)
from app.evaluation.evaluator import RAGEvaluator
from app.evaluation.schemas import (
    ClaimStatus,
    ClaimVerification,
    EvaluationDataset,
    EvaluationReport,
    EvaluationResult,
    EvaluationSample,
    MetricScore,
)


# ===========================================================================
# 1. Citation Checker Tests
# ===========================================================================

class TestCitationChecker:
    def test_extract_citations_various_formats(self):
        text = "Vitamin C is essential [1]. It prevents scurvy [2, 3] and aids absorption [4][5]."
        cites = extract_citations(text)
        assert cites == [1, 2, 3, 4, 5]

    def test_extract_citations_empty(self):
        text = "Hello! I am a nutrition assistant."
        assert extract_citations(text) == []

    def test_extract_cited_sentences(self):
        text = "- Vitamin C acts as a cofactor [1].\n- It aids iron uptake [2]."
        pairs = extract_cited_sentences(text)
        assert len(pairs) == 2
        assert pairs[0][1] == [1]
        assert pairs[1][1] == [2]

    def test_verify_citations_valid(self):
        chunks = [
            {"doc_id": "doc1.pdf", "chunk_index": 0, "content": "Vitamin C activates prolyl hydroxylase."},
            {"doc_id": "doc2.pdf", "chunk_index": 1, "content": "Scurvy is caused by ascorbic acid deficiency."},
        ]
        response = (
            "- Vitamin C acts on prolyl hydroxylase [1].\n"
            "- Scurvy is prevented by ascorbic acid [2]."
        )
        metric = verify_citations(response, chunks, threshold=0.7)
        assert metric.name == "citation_accuracy"
        assert metric.passed is True
        assert metric.score >= 0.7
        assert metric.details["out_of_bounds_citations"] == []

    def test_verify_citations_out_of_bounds(self):
        chunks = [{"doc_id": "doc1.pdf", "chunk_index": 0, "content": "Iron is absorbed in duodenum."}]
        response = "Iron absorption happens here [1], but also needs copper [5]."
        metric = verify_citations(response, chunks, threshold=0.7)
        assert metric.passed is False
        assert 5 in metric.details["out_of_bounds_citations"]

    def test_verify_citations_no_chunks_no_citations(self):
        metric = verify_citations("I cannot find information on this topic.", chunks=[], threshold=0.8)
        assert metric.score == 1.0
        assert metric.passed is True

    def test_verify_citations_no_chunks_with_hallucinated_citations(self):
        metric = verify_citations("According to textbook research [1], quantum gravity applies.", chunks=[], threshold=0.8)
        assert metric.score == 0.0
        assert metric.passed is False


# ===========================================================================
# 2. Evaluation Schema Tests
# ===========================================================================

class TestEvaluationSchemas:
    def test_metric_score_passed_auto_computation(self):
        m_pass = MetricScore(name="test", score=0.85, threshold=0.70)
        assert m_pass.passed is True

        m_fail = MetricScore(name="test", score=0.65, threshold=0.70)
        assert m_fail.passed is False

    def test_metric_score_bounds_validation(self):
        with pytest.raises(ValidationError):
            MetricScore(name="test", score=1.5)
        with pytest.raises(ValidationError):
            MetricScore(name="test", score=-0.1)

    def test_claim_verification_schema(self):
        cv = ClaimVerification(
            claim="Ascorbic acid prevents scurvy.",
            status=ClaimStatus.SUPPORTED,
            evidence="Ascorbic acid prevents clinical scurvy.",
            reasoning="Direct match.",
        )
        assert cv.status == ClaimStatus.SUPPORTED


# ===========================================================================
# 3. RAGEvaluator Tests (with Mocked LLM)
# ===========================================================================

class TestRAGEvaluator:
    @pytest.fixture
    def mock_llm(self):
        return MagicMock()

    def test_evaluate_faithfulness_with_mock_llm(self, mock_llm):
        mock_response = MagicMock()
        mock_response.content = """
        {
          "claims": [
            {
              "claim": "Vitamin C is a cofactor for prolyl hydroxylase.",
              "status": "SUPPORTED",
              "evidence": "Cofactor for prolyl hydroxylase",
              "reasoning": "Direct match"
            },
            {
              "claim": "Vitamin C gives you night vision.",
              "status": "UNSUPPORTED",
              "evidence": "",
              "reasoning": "Not mentioned in context"
            }
          ],
          "faithfulness_score": 0.5,
          "reasoning": "1 out of 2 claims supported"
        }
        """
        mock_llm.invoke.return_value = mock_response

        evaluator = RAGEvaluator(llm=mock_llm, faithfulness_threshold=0.8)
        chunks = [{"doc_id": "test.pdf", "content": "Vitamin C is a cofactor for prolyl hydroxylase."}]
        response_text = "Vitamin C is a cofactor for prolyl hydroxylase [1]. It also gives you night vision."

        metric, claims = evaluator.evaluate_faithfulness(response_text, chunks)
        assert metric.name == "faithfulness"
        assert metric.score == 0.5
        assert metric.passed is False
        assert len(claims) == 2
        assert claims[0].status == ClaimStatus.SUPPORTED
        assert claims[1].status == ClaimStatus.UNSUPPORTED

    def test_evaluate_context_relevance_with_mock_llm(self, mock_llm):
        mock_response = MagicMock()
        mock_response.content = '{"context_relevance_score": 0.95, "reasoning": "Highly relevant chunks"}'
        mock_llm.invoke.return_value = mock_response

        evaluator = RAGEvaluator(llm=mock_llm)
        chunks = [{"doc_id": "test.pdf", "content": "Collagen synthesis mechanism"}]
        metric = evaluator.evaluate_context_relevance("How is collagen synthesized?", chunks)
        assert metric.score == 0.95
        assert metric.passed is True

    def test_evaluate_sample_complete(self, mock_llm):
        mock_llm.invoke.side_effect = [
            # 1. context relevance
            MagicMock(content='{"context_relevance_score": 0.90, "reasoning": "Relevant context"}'),
            # 2. faithfulness
            MagicMock(content='{"claims": [{"claim": "Fact 1", "status": "SUPPORTED"}], "faithfulness_score": 1.0, "reasoning": "All supported"}'),
            # 3. answer relevance
            MagicMock(content='{"answer_relevance_score": 0.92, "reasoning": "Answers query"}'),
        ]

        evaluator = RAGEvaluator(llm=mock_llm)
        sample = EvaluationSample(
            sample_id="SAMPLE_001",
            query="What is Vitamin C?",
            context_chunks=[{"doc_id": "test.pdf", "content": "Vitamin C is ascorbic acid."}],
            response="Vitamin C is ascorbic acid [1].",
        )

        result = evaluator.evaluate_sample(sample)
        assert result.sample_id == "SAMPLE_001"
        assert result.passed is True
        assert result.faithfulness.score == 1.0
        assert result.overall_score > 0.85

    def test_evaluate_dataset_report(self, mock_llm):
        mock_llm.invoke.return_value = MagicMock(content='{"context_relevance_score": 0.9, "claims": [{"claim": "Fact", "status": "SUPPORTED"}], "faithfulness_score": 1.0, "answer_relevance_score": 0.9}')

        evaluator = RAGEvaluator(llm=mock_llm, citation_threshold=0.7)
        dataset = EvaluationDataset(
            name="Test Suite",
            samples=[
                EvaluationSample(
                    sample_id="S1",
                    query="Q1",
                    context_chunks=[{"doc_id": "d1", "content": "Nutrition fact about Vitamin C"}],
                    response="Nutrition fact about Vitamin C [1].",
                ),
                EvaluationSample(
                    sample_id="S2",
                    query="Q2",
                    context_chunks=[{"doc_id": "d2", "content": "Nutrition fact about Vitamin D"}],
                    response="Nutrition fact about Vitamin D [1].",
                ),
            ],
        )

        report = evaluator.evaluate_dataset(dataset)
        assert report.total_samples == 2
        assert report.passed_samples == 2
        assert report.pass_rate_percentage == 100.0
        assert len(report.results) == 2

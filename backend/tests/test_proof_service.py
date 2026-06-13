"""
tests/test_proof_service.py
---------------------------
Unit tests for app.services.proof_service.build_context_proof.

These tests require no external services (no Supabase, no Ollama, no Groq)
and run in milliseconds — safe to execute in CI without any env vars.
"""

import pytest
from app.services.proof_service import build_context_proof


class TestBuildContextProofEmptyInput:
    """Verify the function handles the "no chunks retrieved" case correctly."""

    def test_returns_not_grounded(self):
        result = build_context_proof([])
        assert result["grounded"] is False

    def test_zero_chunks(self):
        result = build_context_proof([])
        assert result["retrieved_chunks"] == 0

    def test_zero_top_similarity(self):
        result = build_context_proof([])
        assert result["top_similarity"] == 0.0

    def test_empty_citations_list(self):
        result = build_context_proof([])
        assert result["citations"] == []

    def test_reason_is_string(self):
        result = build_context_proof([])
        assert isinstance(result["reason"], str)
        assert len(result["reason"]) > 0


class TestBuildContextProofWithChunks:
    """Verify the function correctly processes retrieved chunks."""

    @pytest.fixture
    def sample_chunks(self):
        return [
            {
                "doc_id": "nutrition_textbook.pdf",
                "chunk_index": 0,
                "content": "Vitamin C is an essential water-soluble vitamin.",
                "similarity": 0.912,
                "metadata": {"page_number": 12},
            },
            {
                "doc_id": "nutrition_textbook.pdf",
                "chunk_index": 1,
                "content": "Iron deficiency is the most common nutritional deficiency worldwide.",
                "similarity": 0.875,
                "metadata": {"page_number": 47},
            },
        ]

    def test_grounded_true(self, sample_chunks):
        result = build_context_proof(sample_chunks)
        assert result["grounded"] is True

    def test_correct_chunk_count(self, sample_chunks):
        result = build_context_proof(sample_chunks)
        assert result["retrieved_chunks"] == 2

    def test_top_similarity_is_max(self, sample_chunks):
        result = build_context_proof(sample_chunks)
        # Should be the highest value (0.912), rounded to 4 decimal places
        assert result["top_similarity"] == pytest.approx(0.912, abs=1e-4)

    def test_citations_length_matches_chunks(self, sample_chunks):
        result = build_context_proof(sample_chunks)
        assert len(result["citations"]) == 2

    def test_citation_labels_are_sequential(self, sample_chunks):
        result = build_context_proof(sample_chunks)
        assert result["citations"][0]["citation"] == "[1]"
        assert result["citations"][1]["citation"] == "[2]"

    def test_citation_contains_doc_id(self, sample_chunks):
        result = build_context_proof(sample_chunks)
        assert result["citations"][0]["doc_id"] == "nutrition_textbook.pdf"

    def test_excerpt_max_length(self, sample_chunks):
        result = build_context_proof(sample_chunks)
        for citation in result["citations"]:
            assert len(citation["excerpt"]) <= 240

    def test_similarity_rounded(self, sample_chunks):
        result = build_context_proof(sample_chunks)
        for citation in result["citations"]:
            # Should be rounded to at most 4 decimal places
            assert citation["similarity"] == round(citation["similarity"], 4)


class TestBuildContextProofEdgeCases:
    """Edge cases: missing fields, NaN similarities, long content."""

    def test_missing_similarity_defaults_to_zero(self):
        chunks = [{"doc_id": "doc.pdf", "chunk_index": 0, "content": "text"}]
        result = build_context_proof(chunks)
        assert result["top_similarity"] == 0.0
        assert result["citations"][0]["similarity"] == 0.0

    def test_long_content_is_truncated(self):
        long_content = "A" * 1000
        chunks = [
            {
                "doc_id": "doc.pdf",
                "chunk_index": 0,
                "content": long_content,
                "similarity": 0.5,
            }
        ]
        result = build_context_proof(chunks)
        assert len(result["citations"][0]["excerpt"]) <= 240

    def test_single_chunk_grounded(self):
        chunks = [
            {
                "doc_id": "doc.pdf",
                "chunk_index": 0,
                "content": "Protein is essential.",
                "similarity": 0.6,
            }
        ]
        result = build_context_proof(chunks)
        assert result["grounded"] is True
        assert result["retrieved_chunks"] == 1

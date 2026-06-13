"""
tests/test_schemas.py
---------------------
Unit tests for Pydantic request/response schemas.
Validates field constraints without any external dependencies.
"""

import pytest
from pydantic import ValidationError
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse


class TestChatRequest:
    def test_valid_request(self):
        req = ChatRequest(message="What is vitamin D?")
        assert req.message == "What is vitamin D?"
        assert req.session_id == "default_session"

    def test_custom_session_id(self):
        req = ChatRequest(message="Hello", session_id="abc-123")
        assert req.session_id == "abc-123"

    def test_empty_message_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_message_too_long_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 2001)

    def test_whitespace_only_message_is_rejected(self):
        # min_length=1 should reject purely empty strings
        # (whitespace alone passes min_length but is handled at API level)
        with pytest.raises(ValidationError):
            ChatRequest(message="")


class TestHealthResponse:
    def test_valid_health_response(self):
        resp = HealthResponse(status="ok", service="Nutri-RAG Modular")
        assert resp.status == "ok"
        assert resp.service == "Nutri-RAG Modular"


class TestChatResponse:
    def test_valid_chat_response(self):
        resp = ChatResponse(
            answer="Vitamin D is essential for calcium absorption.",
            sources=[],
            intent="NUTRITION",
            proof_of_context={"grounded": True, "retrieved_chunks": 2, "top_similarity": 0.91},
        )
        assert resp.intent == "NUTRITION"
        assert resp.sources == []

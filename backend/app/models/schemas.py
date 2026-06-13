"""
schemas.py
----------
Pydantic v2 request/response models for the Nutri-RAG API.
"""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message payload."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's research question.",
        examples=["What are the essential amino acids for humans?"],
    )
    session_id: str = Field(
        default="default_session",
        description=(
            "Unique session identifier used to maintain conversation history. "
            "Generate a UUID on the client and reuse across a conversation."
        ),
    )


class HealthResponse(BaseModel):
    """Health-check response payload."""

    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["Nutri-RAG Modular"])


class ChatResponse(BaseModel):
    """Full chat response payload including citations and grounding proof."""

    answer: str = Field(..., description="Markdown-formatted answer from the AI.")
    sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of retrieved vector chunks used to ground the answer.",
    )
    intent: str = Field(
        ...,
        description="Classified intent: NUTRITION | GREETING | OFFTOPIC",
    )
    proof_of_context: dict[str, Any] = Field(
        ...,
        description=(
            "Grounding proof: whether the answer is grounded, "
            "chunk count, top similarity score, and per-chunk citations."
        ),
    )

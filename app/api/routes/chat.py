"""
chat.py  (API route)
--------------------
Defines the ``/api/chat`` and ``/health`` endpoints.

All business logic lives in the service layer; this module is
intentionally thin — it only handles HTTP concerns (validation,
error mapping, metric observation).
"""

import time

from fastapi import APIRouter, HTTPException, status

from app.core.logging_config import logger
from app.core.metrics import observe_chat
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.langgraph_agent import query_agent
from app.services.proof_service import build_context_proof

router = APIRouter(tags=["Chat"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns 200 OK if the API is alive. Used by load balancers and CI smoke tests.",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="Nutri-RAG Modular")


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Send a research query",
    description=(
        "Submit a user query. The agent classifies intent, optionally retrieves "
        "relevant textbook chunks from Supabase pgvector, and generates a grounded "
        "answer via Groq (llama-3.3-70b-versatile). Returns the answer, source "
        "citations, intent label, and a context-proof object."
    ),
    status_code=status.HTTP_200_OK,
)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    Raises ``HTTP 500`` if the underlying LangGraph agent throws an unhandled
    exception; all other errors are caught and returned gracefully.
    """
    started_at = time.perf_counter()
    logger.info(
        f"Chat request received | session_id={req.session_id} "
        f"| message_len={len(req.message)}"
    )

    try:
        config = {"configurable": {"thread_id": req.session_id}}
        inputs: dict = {
            "query": req.message,
            "history": [],
            "chunks": [],
            "response": "",
        }

        output = query_agent.invoke(inputs, config=config)

        answer: str = output.get("response") or "No response generated."
        chunks: list = output.get("chunks", [])
        intent: str = output.get("intent", "UNKNOWN")

        proof = build_context_proof(chunks)
        observe_chat(intent=intent, chunks=chunks, started_at=started_at)

        logger.info(
            f"Chat response ready | intent={intent} "
            f"| chunks={len(chunks)} | latency={time.perf_counter() - started_at:.2f}s"
        )
        return ChatResponse(
            answer=answer,
            sources=chunks,
            intent=intent,
            proof_of_context=proof,
        )

    except Exception as exc:
        logger.error(f"Unhandled error in /api/chat: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}",
        ) from exc

"""
factory.py
----------
FastAPI application factory for Nutri-RAG.

Usage
~~~~~
    # Development (auto-reload) — run from backend/
    uvicorn main:app --reload

    # Production
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

The factory pattern lets the app be re-instantiated in tests without
global side-effects from module-level code.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes.chat import router as chat_router
from app.core.logging_config import logger, setup_logging

# ---------------------------------------------------------------------------
# Frontend directory — always two levels up from this file:
#   factory.py  →  backend/app/factory.py
#   parents[0]  →  backend/app/
#   parents[1]  →  backend/
#   parents[2]  →  rag-chat/          (project root)
#   / "frontend" → rag-chat/frontend/ ✅
# ---------------------------------------------------------------------------
_FRONTEND_DIR: Path = Path(__file__).resolve().parents[2] / "frontend"


def create_app() -> FastAPI:
    """
    Construct and configure the FastAPI application instance.

    Returns
    -------
    FastAPI
        Fully configured ASGI application ready for uvicorn.
    """
    setup_logging()

    app = FastAPI(
        title="Nutri-RAG API",
        description=(
            "Production-grade Retrieval-Augmented Generation (RAG) API for Human Nutrition Research. "
            "Powered by LangGraph, Groq (llama-3.3-70b-versatile), Supabase pgvector, and Ollama embeddings."
        ),
        version="4.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------
    # CORS — restrict in production by setting ALLOWED_ORIGINS env var
    # ------------------------------------------------------------------
    _origins_env = os.getenv("ALLOWED_ORIGINS", "*")
    _allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # ------------------------------------------------------------------
    # Prometheus metrics
    # ------------------------------------------------------------------
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/metrics", "/health"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # ------------------------------------------------------------------
    # API routes
    # ------------------------------------------------------------------
    app.include_router(chat_router)

    # ------------------------------------------------------------------
    # Static frontend
    # ------------------------------------------------------------------
    if _FRONTEND_DIR.exists() and _FRONTEND_DIR.is_dir():
        logger.info(f"Frontend directory mounted: {_FRONTEND_DIR}")

        # Serve /chat explicitly before the catch-all StaticFiles mount
        @app.get("/chat", response_class=HTMLResponse, include_in_schema=False)
        def serve_chat_ui() -> FileResponse:
            chat_file = _FRONTEND_DIR / "chat.html"
            if chat_file.exists():
                return FileResponse(chat_file)
            return HTMLResponse(content="<h1>404 — chat.html not found</h1>", status_code=404)

        app.mount(
            "/",
            StaticFiles(directory=str(_FRONTEND_DIR), html=True),
            name="static",
        )
    else:
        logger.error(
            f"Frontend directory NOT found at: {_FRONTEND_DIR}\n"
            "Make sure you are running uvicorn from the backend/ directory."
        )

    logger.info("FastAPI application created successfully.")
    return app


# ---------------------------------------------------------------------------
# Module-level app instance — referenced by uvicorn and Vercel
# ---------------------------------------------------------------------------
app = create_app()

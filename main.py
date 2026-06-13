"""
main.py
-------
Uvicorn entry point for the Nutri-RAG FastAPI backend.

Development
~~~~~~~~~~~
    uvicorn main:app --reload --port 8000

Production (Docker)
~~~~~~~~~~~~~~~~~~~
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

Note: LangGraph's MemorySaver is in-process — use ``--workers 1`` to keep
conversation history consistent across requests. For horizontal scaling,
replace MemorySaver with a persistent store (Redis, PostgreSQL).
"""

from app.factory import app  # noqa: F401 — re-exported for uvicorn

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_config=None,  # use our custom structured JSON logger
    )

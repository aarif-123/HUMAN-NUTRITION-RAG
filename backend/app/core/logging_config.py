"""
logging_config.py
-----------------
Structured JSON logging for the Nutri-RAG backend.

Usage
~~~~~
    from app.core.logging_config import logger, setup_logging

    setup_logging()          # called once at app startup
    logger.info("message")   # use anywhere in the codebase
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """Emit log records as newline-delimited JSON for log-aggregation pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(level: str | None = None) -> logging.Logger:
    """
    Configure structured logging for the application.

    Parameters
    ----------
    level:
        Override log level (e.g. 'DEBUG', 'WARNING').
        Falls back to the LOG_LEVEL environment variable, then 'INFO'.
    """
    effective_level = level or os.getenv("LOG_LEVEL", "INFO").upper()

    root = logging.getLogger()

    # Remove any handlers added by previous calls (idempotent)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root.addHandler(handler)
    root.setLevel(effective_level)

    # Silence verbose third-party libraries
    for noisy_lib in ("uvicorn.access", "httpcore", "httpx", "hpack"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)

    app_logger = logging.getLogger("nutri-rag")
    app_logger.info(f"Logging initialised at level={effective_level}")
    return app_logger


# Module-level logger — import this directly in other modules
logger = logging.getLogger("nutri-rag")

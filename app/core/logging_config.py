"""
logging_config.py
-----------------
Production-grade logging configuration for the Nutri-RAG backend.

Supports:
1. Environment-aware formatting (Colored console in local TTY, structured JSON in production).
2. Correlation ID tracking (Request ID) across async tasks using contextvars.
3. ASGI request-response logging middleware.
4. Unification of third-party library loggers.
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

# ContextVar for tracing requests across threads/coroutines
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")

# ANSI colors for local development formatting
_COLORS = {
    logging.DEBUG: "\033[36m",      # Cyan
    logging.INFO: "\033[32m",       # Green
    logging.WARNING: "\033[33m",    # Yellow
    logging.ERROR: "\033[31m",      # Red
    logging.CRITICAL: "\033[1;31m", # Bold Red
}
_RESET = "\033[0m"
_GREY = "\033[90m"

# Standard LogRecord attributes to filter out when exporting custom extra attributes in JSON
_STANDARD_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message"
}


class ColouredFormatter(logging.Formatter):
    """Clean, human-readable console formatter with ANSI colors and Request ID support."""

    def format(self, record: logging.LogRecord) -> str:
        orig_levelname = record.levelname
        color = _COLORS.get(record.levelno, _RESET)
        
        # Colorise severity level name
        record.levelname = f"{color}{orig_levelname:<8}{_RESET}"
        
        req_id = request_id_var.get()
        req_part = f"{_GREY}[req:{req_id[:8]}]{_RESET} " if req_id else ""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        time_part = f"{_GREY}[{timestamp}]{_RESET}"
        
        detail_part = ""
        if record.levelno >= logging.WARNING or record.levelno == logging.DEBUG:
            detail_part = f" {_GREY}({record.filename}:{record.lineno}){_RESET}"
            
        log_line = f"{time_part} {record.levelname} ({record.name}) {req_part}{record.getMessage()}{detail_part}"
        
        # Restore levelname
        record.levelname = orig_levelname
        
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        return log_line


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for production log aggregation services."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_var.get()
        
        log_obj: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "severity": record.levelname,  # GCP standard field
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }
        
        if req_id:
            log_obj["request_id"] = req_id
            
        # Extract custom extra attributes passed via logger.info("msg", extra={"key": "val"})
        for key, val in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                log_obj[key] = val

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


class RequestLoggingMiddleware:
    """ASGI middleware injecting correlation/request IDs and logging HTTP request lifecycles."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers_dict: dict[str, str] = {}
        for k, v in scope.get("headers", []):
            headers_dict[k.decode("utf-8").lower()] = v.decode("utf-8")
            
        request_id = (
            headers_dict.get("x-request-id")
            or headers_dict.get("x-correlation-id")
            or str(uuid.uuid4())
        )
        
        token = request_id_var.set(request_id)
        start_time = time.perf_counter()
        
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "")
        query = scope.get("query_string", b"").decode("utf-8")
        query_part = f"?{query}" if query else ""
        
        client = scope.get("client")
        client_host = client[0] if client else "unknown"
        
        logger.info(
            f"Incoming request: {method} {path}{query_part} from {client_host}",
            extra={
                "http_method": method,
                "http_path": path,
                "client_host": client_host,
                "query_string": query
            }
        )

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = headers
                
                status_code = message.get("status", 200)
                latency = time.perf_counter() - start_time
                logger.info(
                    f"Request completed: {method} {path}{query_part} -> status={status_code} latency={latency:.4f}s",
                    extra={
                        "http_method": method,
                        "http_path": path,
                        "status_code": status_code,
                        "latency": latency,
                    }
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            latency = time.perf_counter() - start_time
            logger.error(
                f"Unhandled exception in request lifecycle: {method} {path}{query_part} -> {exc}",
                exc_info=True,
                extra={
                    "http_method": method,
                    "http_path": path,
                    "latency": latency,
                }
            )
            raise exc
        finally:
            request_id_var.reset(token)


def setup_logging(level: str | None = None) -> logging.Logger:
    """
    Configure root and library loggers to use the colored formatter or structured JSON formatter.
    """
    effective_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    env = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()
    log_format = os.getenv("LOG_FORMAT", "").lower()
    
    is_production = env in ("prod", "production")
    use_json = log_format == "json" or (is_production and not sys.stdout.isatty())
    
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
        
    handler = logging.StreamHandler(sys.stdout)
    if use_json:
        handler.setFormatter(StructuredFormatter())
    else:
        if sys.platform == "win32":
            os.system("")  # Enables ANSI escapes on Windows console
        handler.setFormatter(ColouredFormatter())
        
    root.addHandler(handler)
    root.setLevel(effective_level)
    
    # Hijack and unify third-party loggers
    loggers_to_unify = (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "httpx",
        "httpcore",
        "hpack",
    )
    
    for name in loggers_to_unify:
        lib_logger = logging.getLogger(name)
        for h in list(lib_logger.handlers):
            lib_logger.removeHandler(h)
        lib_logger.propagate = True
        
        if name in ("httpx", "httpcore", "hpack", "uvicorn.access") and effective_level != "DEBUG":
            lib_logger.setLevel(logging.WARNING)
        else:
            lib_logger.setLevel(effective_level)
            
    app_logger = logging.getLogger("nutri-rag")
    app_logger.info(
        f"Logging initialised | level={effective_level} | format={'json' if use_json else 'colored-text'}"
    )
    return app_logger


# Global logger instance for app imports
logger: logging.Logger = logging.getLogger("nutri-rag")

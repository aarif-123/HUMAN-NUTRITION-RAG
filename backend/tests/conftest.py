"""
tests/conftest.py
-----------------
Shared pytest fixtures and configuration for the Nutri-RAG test suite.
"""

import os

import pytest


# ---------------------------------------------------------------------------
# Ensure test env vars are set before any app code imports happen
# (prevents RuntimeError from config.py's startup validation)
# ---------------------------------------------------------------------------
def pytest_configure(config):
    """Set dummy environment variables so config.py validates without real secrets."""
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
    os.environ.setdefault("GROQ_API_KEY", "test-groq-api-key")
    os.environ.setdefault("OLLAMA_URL", "http://localhost:11434")
    os.environ.setdefault("EMBEDDING_MODEL", "jeffh/intfloat-e5-base-v2:f16")

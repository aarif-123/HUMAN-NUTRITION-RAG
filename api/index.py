"""
api/index.py
------------
Vercel serverless function entry point.

Vercel routes all /api/* requests and /health to this file (see vercel.json).
It adds the backend package to sys.path so that ``from app.xxx import yyy``
resolves correctly in the Vercel Python runtime.

This module simply re-exports the FastAPI ``app`` instance created by
:func:`app.factory.create_app`; the ASGI adapter is handled by Vercel
automatically.
"""

from __future__ import annotations

import os
import sys

# Resolve the absolute path to the backend package and add it to sys.path
# so that ``from app.factory import app`` works regardless of the cwd.
_BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "backend")
)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Import the ASGI app — Vercel uses it as the serverless function handler
from app.factory import app  # noqa: E402, F401

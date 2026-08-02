"""
ingest.py
---------
One-shot PDF ingestion script for Nutri-RAG.

What it does
~~~~~~~~~~~~
1. Opens a PDF file using PyMuPDF (fitz).
2. Extracts text page-by-page.
3. Splits each page into ~1000-character chunks.
4. Generates a passage embedding for each chunk via the HuggingFace
   Inference API (model: intfloat/e5-base-v2, 768 dims).
5. Inserts each chunk (content + embedding + metadata) into the Supabase
   ``chunks`` table.

Usage
~~~~~
    # Single file
    python ingest.py path/to/nutrition_textbook.pdf

    # Dry-run (validate PDF without inserting to DB)
    python ingest.py path/to/nutrition_textbook.pdf --dry-run

Prerequisites
~~~~~~~~~~~~~
- HF_API_TOKEN must be set in .env (get one at https://huggingface.co/settings/tokens).
- Supabase ``chunks`` table must exist with pgvector enabled.
  See the Supabase setup instructions in SETUP.md.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from typing import Optional

import fitz  # PyMuPDF
import requests
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
HF_EMBED_MODEL: str = os.getenv("HF_EMBED_MODEL", "intfloat/e5-base-v2")
# HuggingFace Inference API base URL (updated to the new router.huggingface.co domain)
HF_INFERENCE_URL: str = "https://router.huggingface.co/hf-inference/models"
CHUNK_SIZE: int = 1000  # characters per chunk
EMBED_TIMEOUT: int = 45  # seconds — HF cold-start can take ~20 s

_HF_HEADERS: dict[str, str] = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _l2_normalize(vector: list[float]) -> list[float]:
    """
    Return the L2-normalised (unit-length) version of *vector*.

    Both stored passage embeddings (here) and query embeddings (vector_store.py)
    must be normalised so that pgvector's cosine distance operator produces
    scores in [0, 1] that are directly comparable across the two sets.
    """
    magnitude = math.sqrt(sum(x * x for x in vector))
    if magnitude == 0.0:
        print("  ⚠  Zero-vector encountered during normalisation — storing as-is.")
        return vector
    return [x / magnitude for x in vector]


def _get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        sys.exit(
            "ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env"
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_passage_embedding(text: str) -> Optional[list[float]]:
    """
    Generate a passage embedding via the HuggingFace Inference API.

    Uses the ``"passage: "`` prefix required by the E5 model family for
    documents being ingested (query-time uses ``"query: "``).

    The HF feature-extraction endpoint returns ``[[float, ...]]`` for a
    single string input — we unwrap the outer list.

    Returns ``None`` on failure so the caller can decide whether to skip or retry.
    """
    if not HF_API_TOKEN:
        print("  ⚠  HF_API_TOKEN is not set — cannot generate embeddings.")
        return None
    try:
        res = requests.post(
            f"{HF_INFERENCE_URL}/{HF_EMBED_MODEL}/pipeline/feature-extraction",
            headers=_HF_HEADERS,
            json={"inputs": f"passage: {text}"},
            timeout=EMBED_TIMEOUT,
        )
        res.raise_for_status()
        payload = res.json()
        # Unwrap nested list returned by HF feature-extraction pipeline
        if isinstance(payload, list) and payload and isinstance(payload[0], list):
            embedding: list[float] = payload[0]
        elif isinstance(payload, list) and payload and isinstance(payload[0], float):
            embedding = payload
        else:
            print(f"  ⚠  Unexpected HF response shape: {type(payload)}")
            return None
        return _l2_normalize(embedding)
    except requests.exceptions.Timeout:
        print(f"  ⚠  HuggingFace timed out after {EMBED_TIMEOUT}s — skipping chunk.")
        return None
    except requests.exceptions.HTTPError as exc:
        print(f"  ⚠  HuggingFace HTTP {exc.response.status_code}: {exc.response.text}")
        return None
    except Exception as exc:
        print(f"  ⚠  Embedding error: {exc}")
        return None


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split ``text`` into non-overlapping chunks of at most ``size`` characters."""
    return [text[i : i + size] for i in range(0, len(text), size)]


# ---------------------------------------------------------------------------
# Ingestion logic
# ---------------------------------------------------------------------------


def ingest_pdf(file_path: str, *, dry_run: bool = False) -> None:
    """
    Ingest a single PDF file into the Supabase chunks table.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the PDF.
    dry_run:
        If ``True``, parse and embed but do NOT insert into Supabase.
    """
    if not os.path.isfile(file_path):
        sys.exit(f"ERROR: File not found: {file_path}")

    supabase = None if dry_run else _get_supabase_client()

    doc_id = os.path.basename(file_path)
    print(f"\n📄 Ingesting: {doc_id}  (dry_run={dry_run})")

    doc = fitz.open(file_path)
    total_pages = len(doc)
    inserted = 0
    skipped = 0

    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        raw_text = page.get_text().strip()

        if not raw_text:
            print(f"  ⏭  Page {page_num + 1}/{total_pages}: empty — skipped.")
            continue

        chunks = chunk_text(raw_text)
        print(
            f"  📖 Page {page_num + 1}/{total_pages}: "
            f"{len(chunks)} chunk(s) | ~{len(raw_text)} chars"
        )

        for i, chunk in enumerate(chunks):
            embedding = get_passage_embedding(chunk)
            if embedding is None:
                skipped += 1
                continue

            record = {
                "doc_id": doc_id,
                "chunk_index": i,
                "content": chunk,
                "metadata": {
                    "page_number": page_num + 1,
                    "source_file": file_path,
                },
                "embedding": embedding,
            }

            if not dry_run:
                supabase.table("chunks").insert(record).execute()  # type: ignore[union-attr]

            inserted += 1
            time.sleep(0.05)  # gentle rate-limit to avoid hammering Ollama

    doc.close()
    print(
        f"\n✅ Done: {inserted} chunk(s) {'processed' if dry_run else 'inserted'}, "
        f"{skipped} skipped.\n"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest a PDF into the Nutri-RAG Supabase vector store.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("pdf_path", help="Path to the PDF file to ingest.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and embed without writing to Supabase.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    ingest_pdf(args.pdf_path, dry_run=args.dry_run)

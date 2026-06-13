"""
ingest.py
---------
One-shot PDF ingestion script for Nutri-RAG.

What it does
~~~~~~~~~~~~
1. Opens a PDF file using PyMuPDF (fitz).
2. Extracts text page-by-page.
3. Splits each page into ~1000-character chunks.
4. Generates a passage embedding for each chunk using Ollama (E5 model).
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
- Ollama must be running locally with the embedding model pulled:
      ollama pull jeffh/intfloat-e5-base-v2
- Supabase ``chunks`` table must exist with pgvector enabled.
  See the Supabase setup instructions in SETUP.md.
"""

from __future__ import annotations

import argparse
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
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL: str = os.getenv(
    "OLLAMA_EMBED_MODEL", "jeffh/intfloat-e5-base-v2:f16"
)
CHUNK_SIZE: int = 1000  # characters per chunk
EMBED_TIMEOUT: int = 60  # seconds

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        sys.exit(
            "ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env"
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_passage_embedding(text: str) -> Optional[list[float]]:
    """
    Generate a passage embedding via Ollama.

    Uses the ``"passage: "`` prefix required by the E5 model family for
    documents being ingested (queries use ``"query: "``).

    Returns ``None`` on failure so the caller can decide whether to skip or retry.
    """
    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": f"passage: {text}"},
            timeout=EMBED_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()["embedding"]
    except requests.exceptions.Timeout:
        print(f"  ⚠  Ollama timed out after {EMBED_TIMEOUT}s — skipping chunk.")
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

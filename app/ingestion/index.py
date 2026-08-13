"""
Ingestion pipeline entry point.

Usage:
    python -m app.ingestion.index

Loads all documents from company_docs, chunks them, embeds via Ollama,
and stores the vectors in a local Chroma database.
"""

import time

from app.ingestion.loader import load_documents
from app.ingestion.chunker import chunk_documents
from app.ingestion.store import build_vectorstore


def run_ingestion() -> dict:
    """
    Execute the full ingestion pipeline.

    Returns a summary dict with document and chunk counts.
    """
    start = time.time()

    print("=" * 60)
    print("KnowledgeBase AI — Ingestion Pipeline")
    print("=" * 60)

    # Step 1: Load
    print("\n[1/3] Loading documents...")
    documents = load_documents()
    if not documents:
        print("No documents found. Add files to company_docs/ and retry.")
        return {"documents": 0, "chunks": 0, "seconds": 0}

    # Step 2: Chunk
    print("\n[2/3] Chunking documents...")
    chunks = chunk_documents(documents)

    # Step 3: Embed & store
    print("\n[3/3] Embedding and storing in Chroma...")
    build_vectorstore(chunks)

    elapsed = round(time.time() - start, 2)
    print(f"\nDone in {elapsed}s — {len(documents)} doc section(s), {len(chunks)} chunk(s)")
    print("=" * 60)

    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "seconds": elapsed,
    }


if __name__ == "__main__":
    run_ingestion()

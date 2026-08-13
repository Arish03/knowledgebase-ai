"""
Vector store helpers — build a new Chroma store from chunks, or
open the existing persisted store for querying.
"""

import shutil
from pathlib import Path
from typing import List

import chromadb
from langchain_community.vectorstores import Chroma

from app.config import CHROMA_DB_PATH
from app.ingestion.embedder import get_embeddings

COLLECTION_NAME = "knowledgebase"


def build_vectorstore(chunks: List) -> Chroma:
    """
    Create (or replace) the Chroma vector store from a list of chunks.

    This wipes the existing store so the index is always a clean
    reflection of what's currently in company_docs.
    """
    db_path = Path(CHROMA_DB_PATH)

    # Remove old store to avoid stale/duplicate chunks.
    if db_path.exists():
        shutil.rmtree(db_path)
        print(f"Cleared existing vector store at {db_path}")

    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(db_path),
        collection_name=COLLECTION_NAME,
    )
    print(f"Vector store created at {db_path} with {len(chunks)} chunks")
    return vectorstore


def load_vectorstore() -> Chroma:
    """
    Open the persisted Chroma store for similarity search.

    Raises FileNotFoundError if the store hasn't been built yet.
    """
    db_path = Path(CHROMA_DB_PATH)
    if not db_path.exists():
        raise FileNotFoundError(
            f"Vector store not found at {db_path}. "
            "Run the ingestion pipeline first: python -m app.ingestion.index"
        )

    embeddings = get_embeddings()
    return Chroma(
        persist_directory=str(db_path),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )

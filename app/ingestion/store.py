"""
Vector store helpers — build a new Chroma store from chunks, or
open the existing persisted store for querying.
"""

from pathlib import Path
from typing import List

import chromadb
from langchain_community.vectorstores import Chroma

from app.config import CHROMA_DB_PATH
from app.ingestion.embedder import get_embeddings

COLLECTION_NAME = "knowledgebase"


def build_vectorstore(chunks: List) -> Chroma:
    """
    Create (or replace) the Chroma vector store collection from a list of chunks.

    Clears existing items in the collection without deleting mounted directories.
    """
    db_path = Path(CHROMA_DB_PATH)
    embeddings = get_embeddings()

    # Use PersistentClient to manage the collection safely
    client = chromadb.PersistentClient(path=str(db_path))
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Cleared existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass  # Collection didn't exist yet

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=client,
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
    client = chromadb.PersistentClient(path=str(db_path))
    return Chroma(
        client=client,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )

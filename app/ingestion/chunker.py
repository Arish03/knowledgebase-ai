"""
Document chunker — splits loaded documents into smaller chunks
suitable for embedding and retrieval.
"""

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Spec: chunk_size=800, chunk_overlap=100
_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    length_function=len,
    add_start_index=True,   # records character offset in metadata
)


def chunk_documents(documents: List) -> List:
    """
    Split documents into chunks.

    Each chunk inherits the parent document's metadata and gains:
    - ``start_index``: character offset within the original document
    - ``chunk_index``: sequential index across all chunks
    """
    chunks = _SPLITTER.split_documents(documents)

    # Add a sequential chunk index for easy reference.
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = idx

    print(f"Split into {len(chunks)} chunk(s) (size=800, overlap=100)")
    return chunks

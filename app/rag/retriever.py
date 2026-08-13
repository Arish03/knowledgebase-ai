"""
Retriever — opens the persisted Chroma vector store and performs
similarity search against it.
"""

from typing import List

from app.ingestion.store import load_vectorstore


def retrieve(question: str, k: int = 4) -> List:
    """
    Embed *question* and return the top-k most similar document chunks
    from the Chroma vector store.

    Each result is a LangChain Document with:
    - page_content: the chunk text
    - metadata: source file path, chunk_index, page number (if PDF), etc.
    """
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search(question, k=k)
    return results

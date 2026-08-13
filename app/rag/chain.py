"""
RAG chain — the full ask() pipeline: retrieve → build prompt → call LLM.

Returns both the answer and structured source metadata so the API and
UI can display citations.
"""

from typing import List, Dict, Any
from pathlib import Path

from ollama import Client

from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL
from app.rag.retriever import retrieve
from app.rag.prompt import build_messages


def _format_sources(docs: List) -> List[Dict[str, Any]]:
    """Extract citation metadata from retrieved documents."""
    sources = []
    for doc in docs:
        meta = doc.metadata
        source_path = meta.get("source", "unknown")
        sources.append({
            "document": Path(source_path).name,
            "content": doc.page_content[:300],  # preview snippet
            "page": meta.get("page"),
            "chunk_index": meta.get("chunk_index"),
        })
    return sources


def ask(question: str, k: int = 4) -> Dict[str, Any]:
    """
    Answer a question using the RAG pipeline.

    Parameters
    ----------
    question : str
        The user's natural-language question.
    k : int
        Number of context chunks to retrieve (default 4).

    Returns
    -------
    dict
        ``{"answer": str, "sources": [{"document", "content", "page", "chunk_index"}]}``
    """
    # 1. Retrieve relevant chunks
    context_docs = retrieve(question, k=k)

    if not context_docs:
        return {
            "answer": (
                "I don't have enough information in the available documents "
                "to answer that question."
            ),
            "sources": [],
        }

    # 2. Build the constrained prompt
    messages = build_messages(question, context_docs)

    # 3. Call the LLM on the remote Ollama VM
    client = Client(host=OLLAMA_BASE_URL)
    response = client.chat(
        model=OLLAMA_CHAT_MODEL,
        messages=messages,
    )

    answer = response["message"]["content"]

    # 4. Return answer + sources
    return {
        "answer": answer,
        "sources": _format_sources(context_docs),
    }

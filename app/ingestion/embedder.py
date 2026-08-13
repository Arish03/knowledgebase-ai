"""
Embedding helper — creates an OllamaEmbeddings instance connected
to the remote Ollama VM via OLLAMA_BASE_URL.

This module is used by both the ingestion pipeline (to embed chunks)
and the query path (to embed user questions).
"""

from langchain_ollama import OllamaEmbeddings
from app.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL


def get_embeddings() -> OllamaEmbeddings:
    """Return an OllamaEmbeddings instance pointed at the remote VM."""
    return OllamaEmbeddings(
        model=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

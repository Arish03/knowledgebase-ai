"""
Prompt builder — constructs the system and user messages that
constrain the LLM to answer ONLY from the retrieved context.
"""

from typing import List

SYSTEM_PROMPT = (
    "You are KnowledgeBase AI, an internal company assistant. "
    "You answer questions using ONLY the context provided below. "
    "If the context does not contain enough information to answer "
    "the question, say: \"I don't have enough information in the "
    "available documents to answer that question.\" "
    "Do NOT make up facts or use outside knowledge. "
    "Always be concise, accurate, and professional."
)


def build_messages(question: str, context_docs: List) -> List[dict]:
    """
    Build the message list for the Ollama chat API.

    Parameters
    ----------
    question : str
        The user's natural-language question.
    context_docs : list
        LangChain Document objects retrieved from the vector store.

    Returns
    -------
    list[dict]
        Messages in ``[{"role": ..., "content": ...}]`` format.
    """
    # Format each chunk with its source for traceability.
    context_parts = []
    for i, doc in enumerate(context_docs, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page")
        source_label = f"{source}" + (f" (page {page + 1})" if page is not None else "")
        context_parts.append(
            f"[Source {i}: {source_label}]\n{doc.page_content}"
        )

    context_block = "\n\n---\n\n".join(context_parts)

    user_content = (
        f"Context:\n{context_block}\n\n"
        f"Question: {question}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

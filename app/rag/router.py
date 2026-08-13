"""
Router — decides whether a question needs document context (RAG),
structured data (tool call), or both.

This sits ABOVE the existing Phase 1 chain and delegates to it
for document-only questions. Phase 1 logic is completely untouched.

Flow:
1. Send the question to Ollama with tool schemas attached.
2. If the model issues a tool_call → dispatch it, feed the result
   back, and let the model produce the final answer.
3. If the model answers directly (no tool call) → fall through to
   the existing RAG pipeline for a context-grounded answer.
"""

import json
from typing import Dict, Any, List

from ollama import Client

from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, DB_AVAILABLE
from app.rag.chain import ask as rag_ask
from app.tools.schema import TOOL_SCHEMAS, TOOL_DISPATCH


# System prompt for the routing/tool-calling pass
_ROUTER_SYSTEM_PROMPT = (
    "You are KnowledgeBase AI, an internal company assistant. "
    "You have access to tools that can query live company databases. "
    "If the user's question is about live data (revenue, sales, project status, "
    "employee counts), use the appropriate tool. "
    "If the question is about company policies, documents, or general knowledge, "
    "respond with: ROUTE_TO_RAG — do NOT attempt to answer it yourself. "
    "Always be concise and professional."
)


def _execute_tool_call(tool_call: dict) -> Dict[str, Any]:
    """
    Dispatch a tool call from the model.

    Returns the function result dict. Rejects unknown functions.
    """
    func_name = tool_call["function"]["name"]
    arguments = tool_call["function"]["arguments"]

    # Safety gate — only pre-defined functions are callable
    if func_name not in TOOL_DISPATCH:
        return {"error": f"Unknown function '{func_name}' — call rejected."}

    func = TOOL_DISPATCH[func_name]

    # Arguments come from the model as a dict; pass as kwargs
    if isinstance(arguments, str):
        arguments = json.loads(arguments)

    return func(**arguments)


def ask(question: str, k: int = 4) -> Dict[str, Any]:
    """
    Route a question through tool-calling or RAG.

    Returns:
        {
            "answer": str,
            "sources": [...],       # populated for RAG answers
            "tool_calls": [...]     # populated for tool-call answers
        }
    """
    # If DB is not configured, skip tool-calling entirely → pure RAG
    if not DB_AVAILABLE:
        result = rag_ask(question, k=k)
        result["tool_calls"] = []
        return result

    # ------------------------------------------------------------------
    # Step 1: Ask the model WITH tools — let it decide the route
    # ------------------------------------------------------------------
    client = Client(host=OLLAMA_BASE_URL)

    messages = [
        {"role": "system", "content": _ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    response = client.chat(
        model=OLLAMA_CHAT_MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
    )

    response_message = response["message"]

    # ------------------------------------------------------------------
    # Step 2: Check if the model issued tool calls
    # ------------------------------------------------------------------
    tool_calls_raw = response_message.get("tool_calls")

    if not tool_calls_raw:
        # No tool call — the model either answered directly or said
        # ROUTE_TO_RAG. Either way, fall back to the RAG pipeline
        # for a properly grounded, context-backed answer.
        result = rag_ask(question, k=k)
        result["tool_calls"] = []
        return result

    # ------------------------------------------------------------------
    # Step 3: Execute tool calls and collect results
    # ------------------------------------------------------------------
    tool_calls_info: List[Dict[str, Any]] = []

    # Add the assistant's tool-call message to the conversation
    messages.append(response_message)

    for tc in tool_calls_raw:
        func_name = tc["function"]["name"]
        func_args = tc["function"]["arguments"]

        # Execute
        tool_result = _execute_tool_call(tc)

        # Record for the response
        tool_calls_info.append({
            "function": func_name,
            "arguments": func_args if isinstance(func_args, dict) else json.loads(func_args),
            "result": tool_result,
        })

        # Feed the result back to the model as a tool response
        messages.append({
            "role": "tool",
            "content": json.dumps(tool_result),
        })

    # ------------------------------------------------------------------
    # Step 4: Let the model produce the final answer using tool results
    # ------------------------------------------------------------------
    final_response = client.chat(
        model=OLLAMA_CHAT_MODEL,
        messages=messages,
    )

    answer = final_response["message"]["content"]

    return {
        "answer": answer,
        "sources": [],          # tool-call answers don't use document sources
        "tool_calls": tool_calls_info,
    }

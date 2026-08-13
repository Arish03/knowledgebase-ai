"""
FastAPI backend for KnowledgeBase AI.

Endpoints:
    POST /ask       — answer a question using RAG and/or tool-calling
    GET  /health    — app + Ollama + DB connectivity check
    POST /reindex   — re-run the ingestion pipeline
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

import requests

from app.config import OLLAMA_BASE_URL, API_HOST, API_PORT, DB_AVAILABLE
from app.rag.router import ask as router_ask
from app.ingestion.index import run_ingestion

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str


class SourceInfo(BaseModel):
    document: str
    content: str
    page: Optional[int] = None
    chunk_index: Optional[int] = None


class ToolCallInfo(BaseModel):
    function: str
    arguments: Dict[str, Any]
    result: Any


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    tool_calls: List[ToolCallInfo] = []


class HealthResponse(BaseModel):
    status: str
    ollama_status: str
    ollama_url: str
    db_status: str


class ReindexResponse(BaseModel):
    status: str
    documents: int
    chunks: int
    seconds: float


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="KnowledgeBase AI",
    description="Internal RAG assistant — answers grounded in company documents, with optional live database access.",
    version="2.0.0",
)

# Allow Streamlit (or any internal frontend) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(body: AskRequest):
    """Answer a question using RAG and/or tool-calling."""
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = router_ask(body.question)
        return AskResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Vector store not ready: {exc}. Run /reindex first.",
        )
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health", response_model=HealthResponse)
async def health_endpoint():
    """Check application, Ollama, and database connectivity status."""
    # --- Ollama check ---
    ollama_status = "unreachable"
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            ollama_status = "connected"
        else:
            ollama_status = f"unexpected status {resp.status_code}"
    except requests.ConnectionError:
        ollama_status = "connection_refused"
    except requests.Timeout:
        ollama_status = "timeout"
    except Exception as exc:
        ollama_status = f"error: {exc}"

    # --- Database check ---
    db_status = "not_configured"
    if DB_AVAILABLE:
        try:
            from app.tools.db import get_connection
            conn = get_connection()
            conn.close()
            db_status = "connected"
        except Exception as exc:
            db_status = f"error: {exc}"

    return HealthResponse(
        status="ok",
        ollama_status=ollama_status,
        ollama_url=OLLAMA_BASE_URL,
        db_status=db_status,
    )


@app.post("/reindex", response_model=ReindexResponse)
async def reindex_endpoint():
    """Re-run the full ingestion pipeline."""
    try:
        result = run_ingestion()
        return ReindexResponse(status="completed", **result)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")


# ---------------------------------------------------------------------------
# Run with: uvicorn app.api.main:app --host 0.0.0.0 --port 8000
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host=API_HOST, port=API_PORT, reload=True)

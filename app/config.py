"""
Centralized configuration for KnowledgeBase AI.

All environment variables are read here — no other module should call
os.environ directly for app settings. This ensures a single source of
truth and makes it trivial to spot hardcoded values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present (development convenience; in Docker the
# env vars are injected directly).
load_dotenv()

# ---------------------------------------------------------------------------
# Ollama connection — REQUIRED, no default (forces explicit configuration)
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "")
if not OLLAMA_BASE_URL:
    raise RuntimeError(
        "OLLAMA_BASE_URL is not set. "
        "Set it to the URL of your Ollama VM, e.g. http://<vm-ip>:11434"
    )

# ---------------------------------------------------------------------------
# Model names
# ---------------------------------------------------------------------------
OLLAMA_CHAT_MODEL: str = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.1")
OLLAMA_EMBED_MODEL: str = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH: str = os.environ.get(
    "CHROMA_DB_PATH", str(PROJECT_ROOT / "chroma_db")
)
COMPANY_DOCS_PATH: str = os.environ.get(
    "COMPANY_DOCS_PATH", str(PROJECT_ROOT / "company_docs")
)

# ---------------------------------------------------------------------------
# API server
# ---------------------------------------------------------------------------
API_HOST: str = os.environ.get("API_HOST", "0.0.0.0")
API_PORT: int = int(os.environ.get("API_PORT", "8000"))

# ---------------------------------------------------------------------------
# PostgreSQL (Phase 2 — optional, tool-calling disabled if not set)
# ---------------------------------------------------------------------------
DB_HOST: str = os.environ.get("DB_HOST", "")
DB_PORT: int = int(os.environ.get("DB_PORT", "5432"))
DB_NAME: str = os.environ.get("DB_NAME", "")
DB_USER: str = os.environ.get("DB_USER", "")
DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")
DB_AVAILABLE: bool = all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD])

"""
Test configuration — sets required environment variables before
any app module is imported (app.config raises RuntimeError if
OLLAMA_BASE_URL is missing).
"""

import os

# Set a dummy OLLAMA_BASE_URL so app.config doesn't crash during tests.
# Tests that need to call Ollama will mock the client instead.
os.environ.setdefault("OLLAMA_BASE_URL", "http://test-ollama:11434")

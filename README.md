# KnowledgeBase AI

An internal RAG (Retrieval-Augmented Generation) assistant that answers employee questions using company documents — policies, project docs, and internal reports — without sending data to external AI providers.

All inference runs on a self-hosted **Ollama** instance. Document retrieval uses a local **Chroma** vector database.

---

## Project Structure

```
/app
  /ingestion      → document loading, chunking, embedding scripts
  /rag            → retrieval + answer generation logic
  /api            → FastAPI backend (/ask, /health, /reindex)
  /ui             → Streamlit chat interface
/company_docs     → source documents (PDF, .docx, .md, .txt)
/chroma_db        → persisted vector store (gitignored)
```

---

## Prerequisites

- **Python 3.11+**
- **Ollama** running on a reachable VM with these models pulled:
  ```bash
  ollama pull llama3.1
  ollama pull nomic-embed-text
  ```
- Docker & Docker Compose (optional, for containerized deployment)

---

## Quick Start (Local)

### 1. Clone and install

```bash
git clone <repo-url> && cd KnowledgeBase_AI
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set OLLAMA_BASE_URL to your Ollama VM's address
```

### 3. Add documents

Place your PDF, `.docx`, `.md`, or `.txt` files in the `company_docs/` folder.

### 4. Run ingestion

```bash
python -m app.ingestion.index
```

### 5. Start the API server

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### 6. Start the Streamlit UI

```bash
streamlit run app/ui/chat.py --server.port 8501
```

Open http://localhost:8501 in your browser.

---

## Quick Start (Docker Compose)

```bash
cp .env.example .env
# Edit .env with your Ollama VM address
docker compose up --build
```

- API: http://localhost:8000
- UI: http://localhost:8501

---

## API Endpoints

| Method | Path       | Description                                      |
|--------|------------|--------------------------------------------------|
| POST   | `/ask`     | `{"question": "..."}` → answer with sources      |
| GET    | `/health`  | App status + Ollama connectivity check            |
| POST   | `/reindex` | Re-run the ingestion pipeline                     |

---

## Environment Variables

| Variable             | Description                          | Default                |
|----------------------|--------------------------------------|------------------------|
| `OLLAMA_BASE_URL`    | URL of the remote Ollama instance    | *(required)*           |
| `OLLAMA_CHAT_MODEL`  | Chat/answer model name               | `llama3.1`             |
| `OLLAMA_EMBED_MODEL` | Embedding model name                 | `nomic-embed-text`     |
| `CHROMA_DB_PATH`     | Path to persist the vector store     | `./chroma_db`          |
| `COMPANY_DOCS_PATH`  | Path to source documents             | `./company_docs`       |
| `API_HOST`           | FastAPI bind address                 | `0.0.0.0`              |
| `API_PORT`           | FastAPI port                         | `8000`                 |

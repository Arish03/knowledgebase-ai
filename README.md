<div align="center">

# 📚 KnowledgeBase AI

**Enterprise-Grade, Self-Hosted RAG Assistant & Structured Data Tool Engine**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F00?style=for-the-badge)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

</div>

---

## 🌟 Overview

**KnowledgeBase AI** is an internal AI assistant that answers employee questions grounded exclusively in your company's own documents and live databases — **without sending sensitive data to third-party APIs**.

### Key Highlights

- 🔒 **100% Privacy & Data Security**: All inference and storage run on internal infrastructure using self-hosted **Ollama** and local **ChromaDB**.
- 📄 **Multi-Format Document Ingestion**: Ingests `.pdf`, `.docx`, `.md`, and `.txt` files with automated chunking (`RecursiveCharacterTextSplitter`).
- 📌 **Verifiable Source Citations**: Every answer includes expandable citations showing exact source document names, page numbers, and chunk snippets.
- ⚡ **Structured Data Tool-Calling (Phase 2)**: Dynamically routes questions to parameterized PostgreSQL query tools for live operational data (sales revenue, project status, headcount) while keeping raw SQL strictly locked down.
- 🚫 **Zero Hallucinations**: Prompt constraints force the assistant to state *"I don't have enough information"* whenever context is missing.

---

## 🏗️ System Architecture

```
                      +---------------------------------+
                      |     User (Streamlit Web UI)     |
                      +---------------------------------+
                                       |
                                       v  HTTP POST /ask
                      +---------------------------------+
                      |       FastAPI Backend API       |
                      +---------------------------------+
                                       |
                                       v
                      +---------------------------------+
                      |       Smart Router Module       |
                      +---------------------------------+
                               /               \
       (Live Data Question)   /                 \   (Document Question)
                             v                   v
             +-----------------------+   +-----------------------+
             | PostgreSQL Tool Call  |   | ChromaDB Vector Store |
             +-----------------------+   +-----------------------+
             | - Parameterized SQL   |   | - nomic-embed-text    |
             | - Read-Only Queries   |   | - Similarity Search   |
             +-----------------------+   +-----------------------+
                             \                   /
                              \                 /
                               v               v
                      +---------------------------------+
                      |      Remote Ollama LLM VM       |
                      |     (llama3.1 / nomic-embed)    |
                      +---------------------------------+
```

---

## 📂 Project Layout

```
KnowledgeBase_AI/
├── app/
│   ├── api/                  # FastAPI backend server
│   │   └── main.py           # /ask, /health, /reindex endpoints
│   ├── ingestion/            # Pipeline: Load, chunk, embed, store
│   │   ├── loader.py         # Multi-format document loaders
│   │   ├── chunker.py        # Text splitting (800 chars / 100 overlap)
│   │   ├── embedder.py       # Ollama embeddings client
│   │   ├── store.py          # ChromaDB collection lifecycle
│   │   └── index.py          # CLI indexing script
│   ├── rag/                  # RAG Query & Prompt Chain
│   │   ├── retriever.py      # Chroma similarity search
│   │   ├── prompt.py         # Strict no-hallucination prompts
│   │   ├── chain.py          # Document RAG execution
│   │   └── router.py         # Smart router (Tool-calling vs RAG)
│   ├── tools/                # PostgreSQL Tool-Calling (Phase 2)
│   │   ├── db.py             # Psycopg2 connection manager
│   │   ├── queries.py        # Safe, parameterized query functions
│   │   └── schema.py         # Ollama tool schemas & dispatch map
│   ├── ui/                   # Frontend
│   │   └── chat.py           # Streamlit conversational interface
│   └── config.py             # Central environment & system settings
├── company_docs/             # Source docs directory (.pdf, .docx, .md, .txt)
├── chroma_db/                # Local persistent vector database
├── tests/                    # Unit & integration test suite
│   ├── conftest.py           # Test configuration & mocks
│   └── test_tool_calling.py  # Safety & routing verification
├── .env.example              # Environment variables template
├── docker-compose.yml        # Multi-container service orchestrator
├── Dockerfile                # Production container spec
└── requirements.txt          # Python dependency specifications
```

---

## 🚀 Quick Start Guide

### Option A: Docker Compose (Recommended)

1. **Clone repository & prepare configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Configure environment in `.env`:**
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_CHAT_MODEL=llama3.1
   OLLAMA_EMBED_MODEL=nomic-embed-text
   ```

3. **Launch container services:**
   ```bash
   docker compose up --build
   ```

4. **Access Applications:**
   - 💬 **Chat Interface (Streamlit)**: `http://localhost:8501`
   - 🔌 **REST API Docs (Swagger)**: `http://localhost:4040/docs`

---

### Option B: Native Python Environment

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Linux/macOS
   # .venv\Scripts\activate          # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Document Indexing:**
   ```bash
   python -m app.ingestion.index
   ```

4. **Start API Backend:**
   ```bash
   uvicorn app.api.main:app --host 0.0.0.0 --port 4040
   ```

5. **Start Streamlit UI (in a new terminal):**
   ```bash
   streamlit run app/ui/chat.py --server.port 8501
   ```

---

## ⚙️ Environment Configuration (`.env`)

| Parameter | Required | Description | Default |
|---|---|---|---|
| `OLLAMA_BASE_URL` | **Yes** | Endpoint URL for the self-hosted Ollama server | `http://localhost:11434` |
| `OLLAMA_CHAT_MODEL` | No | Model used for answer generation | `llama3.1` |
| `OLLAMA_EMBED_MODEL` | No | Embedding model for vector indexing | `nomic-embed-text` |
| `CHROMA_DB_PATH` | No | Local directory path for ChromaDB storage | `./chroma_db` |
| `COMPANY_DOCS_PATH` | No | Source directory containing company documents | `./company_docs` |
| `API_PORT` | No | Port for FastAPI backend service | `4040` |
| `DB_HOST` | Phase 2 | PostgreSQL host address (leave empty to skip) | *(Optional)* |
| `DB_NAME` | Phase 2 | PostgreSQL database name | *(Optional)* |
| `DB_USER` | Phase 2 | Read-only database username | *(Optional)* |
| `DB_PASSWORD` | Phase 2 | Database user password | *(Optional)* |

---

## 📡 API Reference

### 1. Ask Question (`POST /ask`)
Executes question routing across Document RAG and DB Tool-Calling paths.

**Request:**
```json
{
  "question": "What is the annual leave allowance under the company policy?"
}
```

**Response:**
```json
{
  "answer": "All full-time employees are entitled to 20 working days of paid annual leave per calendar year.",
  "sources": [
    {
      "document": "sample_policy.md",
      "content": "All full-time employees are entitled to 20 working days of paid annual leave...",
      "page": null,
      "chunk_index": 0
    }
  ],
  "tool_calls": []
}
```

### 2. Service Health Check (`GET /health`)
Verifies operational connectivity for FastAPI, Ollama instance, and PostgreSQL.

**Response:**
```json
{
  "status": "ok",
  "ollama_status": "connected",
  "ollama_url": "http://localhost:11434",
  "db_status": "connected"
}
```

### 3. Trigger Re-Indexing (`POST /reindex`)
Re-scans `company_docs/`, re-chunks, and updates the vector index.

**Response:**
```json
{
  "status": "completed",
  "documents": 1,
  "chunks": 5,
  "seconds": 0.42
}
```

---

## 🧪 Testing

Run the automated test suite to verify routing, query parameterized safety, and error handling:

```bash
python -m pytest tests/test_tool_calling.py -v
```

---

## 🔒 Security & Compliance

- **No Third-Party Cloud APIs**: Zero external data leaks — all LLM and vector calculations stay within your internal network.
- **Strict SQL Parameterization**: Every tool query uses explicit `%s` positional placeholders. Dynamic SQL execution is physically impossible.
- **Read-Only Scoping**: Database queries are strictly read-only SELECT operations.

# KnowledgeBase AI

**Version:** 1.0 (Draft)
**Type:** Internal Retrieval-Augmented Generation (RAG) system
**Scope:** Company docs, policies, and project documentation, with optional live PostgreSQL access

---

## 1. Overview

**KnowledgeBase AI** is an internal RAG (Retrieval-Augmented Generation) assistant that lets employees ask natural-language questions and get answers grounded in the company's own documents — policies, project docs, and internal reports — without sending that data to an external AI provider.

The system runs entirely on self-hosted components: **Ollama** for local LLM inference and embeddings, a **vector database** for document retrieval, and optionally direct, read-only **PostgreSQL** access for live structured data.

---

## 2. Problem Statement

- Company knowledge is scattered across PDFs, Word docs, Markdown files, and project folders.
- Employees spend time searching multiple systems to find policy or project details.
- Sending internal documents to third-party AI APIs raises data-privacy and compliance concerns.
- Existing search tools return documents, not direct answers.

---

## 3. Goals & Objectives

| Objective | Description |
|---|---|
| Primary goal | Answer employee questions using company docs/policies with cited source context |
| Data privacy | All inference and storage stay on internal infrastructure (no external API calls) |
| Accuracy | Answers are grounded only in retrieved content; system states when it doesn't know |
| Maintainability | Non-technical staff can add/update source documents without code changes |
| Extensibility | Architecture allows adding live database queries (PostgreSQL) in a later phase |

---

## 4. Scope

### 4.1 In Scope (Phase 1)
- Ingestion of PDF, Word (.docx), Markdown, and plain text documents
- Document chunking, embedding, and storage in a local vector database
- Natural-language Q&A interface backed by a local Ollama model
- Source citation for every answer (which document/section it came from)
- Manual and scheduled re-indexing when documents are added or updated

### 4.2 Out of Scope (Phase 1)
- Live queries against the PostgreSQL production database (Phase 2)
- Fine-tuning or retraining the base language model
- Multi-language support beyond English
- Role-based document access control (single trust level assumed for Phase 1)

---

## 5. Users

| User type | Needs |
|---|---|
| Employees | Ask questions about policies, benefits, and project documentation |
| Project teams | Query project-specific documents (specs, status reports, decisions) |
| Admins / IT | Manage document ingestion, monitor system health, update the model |

---

## 6. Tech Stack

### Core AI Layer
| Component | Choice | Why |
|---|---|---|
| LLM runtime | Ollama | Local, no external API calls, supports tool-calling |
| Chat model | Llama 3.1 (8B) or Qwen2.5 (7B/14B) | Tool-calling capable, good reasoning-to-size ratio |
| Embedding model | nomic-embed-text | Small, fast, purpose-built for retrieval, runs locally via Ollama |

### Retrieval / Storage Layer
| Component | Choice | Why |
|---|---|---|
| Vector database | Chroma | Lightweight, embeds directly in Python, persists to disk |
| Document loaders/chunking | LangChain (`langchain-community`) | Ready-made loaders for PDF, Word, Markdown, txt |
| Structured data (Phase 2) | PostgreSQL (existing DB) | Accessed via read-only, parameterized tool-calling — not vectorized |

### Application / Orchestration Layer
| Component | Choice | Why |
|---|---|---|
| Backend | Python (FastAPI) | Simple to wire Ollama + Chroma + Postgres together; async-friendly |
| DB driver | psycopg2 (or asyncpg for async) | Standard, safe parameterized queries |
| Orchestration | LangChain or plain Python | LangChain speeds up loaders/chunking/retrieval chains |

### Frontend
| Component | Choice | Why |
|---|---|---|
| Quick internal UI | Streamlit | Fastest way to get a usable chat UI running internally |
| Production-grade UI | React + FastAPI backend | Polished, branded internal tool for later phases |

### Infrastructure
| Component | Choice | Why |
|---|---|---|
| Hosting | On-prem server or internal VM/cloud instance (GPU optional) | Ollama runs on CPU too; GPU speeds up inference noticeably |
| Containerization | Docker / Docker Compose | Bundle Ollama, Chroma, FastAPI, Postgres config together |
| Scheduled re-indexing | Cron job / simple Python script | Re-embed new/changed docs on a schedule (e.g. nightly) |

**Note:** Since PostgreSQL is already in use, `pgvector` is worth evaluating later as a way to store embeddings directly in Postgres instead of running a separate Chroma instance.

### Deployment Topology

Ollama runs on a **separate VM**, not on the same host as the app containers or the developer's laptop. This changes a few defaults:

- Ollama on the VM must be bound to all interfaces (`OLLAMA_HOST=0.0.0.0:11434`), not just `localhost`.
- The VM's port `11434` should only be reachable from trusted sources (the app server's private network/VPC or an SSH tunnel/VPN) — never exposed publicly, since Ollama has no built-in auth.
- The app connects to Ollama via `OLLAMA_BASE_URL=http://<vm-private-ip>:11434`, set as an environment variable — never hardcoded, and no `host.docker.internal` assumption.
- If the VM has a GPU, confirm Ollama is actually using it (check via the GPU monitoring tool on the VM) rather than silently falling back to CPU.

---

## 7. System Architecture

**High-level flow:**

1. Documents (PDF/Word/Markdown/text) are loaded and split into chunks.
2. Chunks are embedded using a local embedding model served by Ollama.
3. Embeddings and chunk text are stored in a vector database (Chroma).
4. A user question is embedded the same way and matched against stored vectors.
5. The most relevant chunks are inserted into a prompt sent to a local chat model.
6. The model generates an answer constrained to the provided context, with sources.

**Phase 2 addition:** the model can call a read-only tool function that runs a parameterized query against PostgreSQL for live structured data (e.g. revenue, project status), kept separate from the document-retrieval path.

---

## 8. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | System shall ingest documents from a designated folder or upload interface |
| FR-2 | System shall split documents into chunks with configurable size and overlap |
| FR-3 | System shall generate embeddings for each chunk using a local embedding model |
| FR-4 | System shall store embeddings and metadata in a persistent vector database |
| FR-5 | System shall retrieve the top-k relevant chunks for a given user question |
| FR-6 | System shall generate an answer using only retrieved context, via a local LLM |
| FR-7 | System shall display the source document(s) used for each answer |
| FR-8 | System shall respond "I don't know" when context is insufficient, rather than guessing |
| FR-9 | System shall support re-indexing when source documents change |

## 9. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Privacy | No document content or queries leave internal infrastructure |
| Performance | Answers returned within a few seconds for typical queries on standard hardware |
| Reliability | Vector store persists across restarts; no data loss on service restart |
| Auditability | Every answer is traceable to specific source chunks |
| Scalability | Ingestion pipeline handles growing document volume without redesign |

---

## 10. Setup

### Dependencies

```bash
pip install ollama chromadb langchain langchain-community pypdf psycopg2-binary
```

### Pull required Ollama models

```bash
ollama pull llama3.1          # chat/answer model
ollama pull nomic-embed-text  # embedding model
```

---

## 11. Implementation

### 11.1 Document ingestion & indexing (RAG core)

```python
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Load documents
loader = DirectoryLoader("./company_docs", glob="**/*.pdf", loader_cls=PyPDFLoader)
documents = loader.load()

# 2. Chunk documents
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(documents)

# 3. Embed and store
# OLLAMA_BASE_URL points at the VM running Ollama, e.g. http://<vm-private-ip>:11434
import os
OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]

embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

### 11.2 Query / answer generation

```python
import os
from ollama import Client

# Connects to Ollama running on the VM, not localhost
client = Client(host=os.environ["OLLAMA_BASE_URL"])

def ask(question: str, k: int = 4):
    results = vectorstore.similarity_search(question, k=k)
    context = "\n\n".join([doc.page_content for doc in results])

    prompt = f"""Answer the question using ONLY the context below.
If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {question}
"""

    response = client.chat(
        model="llama3.1",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]
```

### 11.3 Phase 2 — PostgreSQL tool-calling (live structured data)

```python
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "dbname": "your_company_db",
    "user": "your_user",
    "password": "your_password",
    "port": 5432,
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_monthly_revenue(month: int, year: int):
    """Fetch revenue total for a given month/year."""
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT SUM(amount) as total_revenue
               FROM sales
               WHERE EXTRACT(MONTH FROM sale_date) = %s
               AND EXTRACT(YEAR FROM sale_date) = %s""",
            (month, year)
        )
        row = cur.fetchone()
    conn.close()
    return row
```

Tools are described to Ollama via a `tools` schema and dispatched through a `tool_calls` loop — see Section 13 for security notes on this path.

---

## 12. Performance Expectations

### With GPU

| Setup | Model | Typical speed |
|---|---|---|
| Consumer GPU (RTX 3060/4060, 8-12GB VRAM) | Llama 3.1 8B (Q4 quantized) | ~30-60 tokens/sec |
| Mid GPU (RTX 4070/4080, 12-16GB VRAM) | Llama 3.1 8B / Qwen2.5 14B | ~50-100 tokens/sec |
| Server GPU (A100/H100) | 70B+ models | 100+ tokens/sec |

At these speeds, a typical RAG answer (a few hundred tokens) returns in **1-4 seconds**.

### CPU-only

| Setup | Model | Typical speed |
|---|---|---|
| Modern multi-core CPU (8+ cores) | Llama 3.1 8B (Q4 quantized) | ~5-15 tokens/sec |
| Older/weaker CPU | Same | ~2-5 tokens/sec |

CPU-only answers can take **10-30+ seconds** — usable for low-traffic internal tools, less ideal if instant response is expected.

### What affects speed
- **Model size**: 7-8B models are noticeably faster than 14B+; quantization (Q4/Q5) trades some accuracy for speed.
- **Retrieval step**: Chroma similarity search is fast (ms to low seconds) even at tens of thousands of chunks — generation is almost always the bottleneck, not retrieval.
- **Concurrency**: Ollama serves one request at a time per model instance by default; concurrent users need request queuing or multiple model instances.
- **Embedding speed**: `nomic-embed-text` embeds a question in well under a second, even on CPU.

---

## 13. Security Notes

- All PostgreSQL access uses **parameterized queries only** — never format raw SQL with model or user input.
- Phase 2 database tools should be **read-only** and scoped to specific, well-defined functions — never let the model construct arbitrary SQL.
- Phase 1 document sets should be restricted to approved, non-sensitive material until role-based access control is in place.

---

## 14. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Outdated documents in the index | Establish a re-indexing process triggered on document updates |
| Model answers beyond given context | Prompt constraints + evaluation to catch and reduce ungrounded answers |
| Sensitive documents indexed broadly | Restrict Phase 1 to approved, non-sensitive document sets; add access control before expanding scope |
| Chunking loses context | Tune chunk size/overlap; evaluate retrieval quality on representative questions |

---

## 15. Success Metrics

| Metric | Definition |
|---|---|
| Answer relevance | Sampled answers reviewed by stakeholders as accurate and on-topic |
| Source correctness | Cited sources genuinely support the given answer |
| Adoption | Regular usage by target teams after rollout |
| Reduced search time | Qualitative feedback that finding policy/project info takes less time |

---

## 16. Rollout Plan

| Phase | Scope |
|---|---|
| Phase 1 | Document RAG: ingestion, embedding, retrieval, Q&A with citations |
| Phase 2 | Add read-only tool-calling access to PostgreSQL for live structured data |
| Phase 3 | Access control, usage analytics, feedback loop for answer quality |

---

## 17. Open Questions

- Which document sets are approved for inclusion in Phase 1?
- Who owns keeping source documents up to date?
- What hardware will host Ollama and the vector store?
- Is role-based access control required before broader rollout?

---

## 18. Appendix: Build Prompts (for Antigravity / agentic IDEs)

Run these one at a time, in order. Verify each phase works before starting the next.

### 18.1 Phase 1 — Core RAG Build

```
You are building KnowledgeBase AI, an internal RAG (Retrieval-Augmented Generation) assistant.
Follow the attached spec exactly: KnowledgeBase_AI_Project.md

Build Phase 1 only (ignore Phase 2/3 sections for now). Scope:

1. PROJECT STRUCTURE
Create a clean Python project with this layout:
   /app
     /ingestion      -> document loading, chunking, embedding scripts
     /rag            -> retrieval + answer generation logic
     /api            -> FastAPI backend exposing a /ask endpoint
     /ui             -> Streamlit chat interface
   /company_docs     -> folder for source PDFs/Word/Markdown/txt
   /chroma_db        -> persisted vector store (gitignored)
   requirements.txt
   docker-compose.yml
   README.md
   .env.example

2. OLLAMA CONNECTION (IMPORTANT — remote VM, not local)
   - Ollama runs on a separate VM, reachable via OLLAMA_BASE_URL, e.g.
     http://<vm-private-ip>:11434
   - Read this from an environment variable everywhere — never hardcode
     localhost or host.docker.internal
   - Add OLLAMA_BASE_URL to .env.example with a placeholder value
   - Use the ollama Python client's Client(host=...) pattern, and pass
     base_url= to LangChain's OllamaEmbeddings, both sourced from this env var

3. INGESTION PIPELINE (/app/ingestion)
   - Load documents from /company_docs (PDF, .docx, .md, .txt)
   - Chunk with RecursiveCharacterTextSplitter (chunk_size=800, overlap=100)
   - Embed using Ollama's nomic-embed-text model via OLLAMA_BASE_URL
   - Store in a local Chroma vector store at ./chroma_db
   - Make this runnable as a standalone script: python -m app.ingestion.index

4. RAG QUERY LOGIC (/app/rag)
   - Given a question, embed it, retrieve top-k (default 4) relevant chunks from Chroma
   - Build a prompt that restricts the model to ONLY the retrieved context
   - If context is insufficient, the model must say it doesn't know (no hallucination)
   - Call Ollama's llama3.1 model (via OLLAMA_BASE_URL) for the final answer
   - Return both the answer AND the source document/chunk metadata used

5. API LAYER (/app/api)
   - FastAPI app with a POST /ask endpoint: { "question": "..." } -> { "answer": "...", "sources": [...] }
   - Add a GET /health endpoint that also checks Ollama connectivity (not just app status)
   - Add a POST /reindex endpoint that re-runs the ingestion pipeline

6. UI (/app/ui)
   - Simple Streamlit chat interface titled "KnowledgeBase AI" that calls the FastAPI /ask endpoint
   - Show the answer plus which source documents were used, in a collapsible section

7. INFRASTRUCTURE
   - docker-compose.yml that runs the FastAPI backend and Streamlit UI, mounts
     volumes for chroma_db and company_docs, and reads OLLAMA_BASE_URL from
     the environment/.env file — do NOT assume Ollama runs in this compose file
     or on the same host
   - requirements.txt with pinned-reasonable versions: ollama, chromadb, langchain, langchain-community, fastapi, uvicorn, streamlit, pypdf, python-docx, unstructured

8. CONSTRAINTS (follow strictly)
   - No external API calls of any kind — everything must run against the VM's
     Ollama and local Chroma
   - No hardcoded secrets, IPs, or credentials anywhere — all via environment variables
   - Every retrieval-backed answer must cite its source chunk/document
   - Keep code modular and readable — no single giant script

After scaffolding, ask me for the actual OLLAMA_BASE_URL value for my VM before
running anything live. Then run the ingestion pipeline against any sample
.md/.txt file placed in /company_docs, start the FastAPI server, and confirm
/ask returns a grounded answer with sources. Report any errors and fix them
before finishing.
```

### 18.2 Phase 2 — PostgreSQL Tool-Calling

```
You are extending KnowledgeBase AI (Phase 1 is already built and working).
Follow the Phase 2 section of KnowledgeBase_AI_Project.md.

Goal: add read-only, live structured-data access via PostgreSQL, kept completely
separate from the document-retrieval path built in Phase 1.

1. NEW MODULE (/app/tools)
   - Create a Postgres connection module using psycopg2, config via environment
     variables (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT) — never hardcoded
   - Implement a small set of specific, read-only query functions (not generic
     SQL execution) — e.g. get_monthly_revenue(month, year), get_project_status(project_name)
   - Every query MUST use parameterized placeholders (%s) — never string-format
     raw SQL with model or user input, under any circumstance

2. TOOL SCHEMA
   - Define an Ollama tool-calling schema describing each function (name,
     description, parameters) so the model can decide when to call them
   - Register these tools alongside the existing RAG chat call in /app/rag
   - Tool-calling requests still go through the same OLLAMA_BASE_URL client
     used in Phase 1 — no separate connection setup needed

3. ROUTING LOGIC
   - Update the /ask endpoint flow: the model first decides whether the question
     needs document context (RAG), structured data (tool call), or both
   - If a tool is called, execute it, feed the result back to the model, and let
     it produce the final answer
   - Response schema stays consistent: { "answer": ..., "sources": [...],
     "tool_calls": [...] } — tool_calls should be empty when none were used

4. SAFETY CONSTRAINTS (strict)
   - Only the exact functions defined in step 1 are ever callable — no dynamic
     SQL construction by the model, ever
   - Database user should be a read-only role at the DB level, not just in code
   - Add basic error handling: a failed DB query returns a graceful message,
     not a stack trace, to the end user

5. TESTS
   - Add a couple of example questions that exercise the tool-calling path
     (e.g. "what was our revenue in March 2025?") and confirm the model calls
     the right function with the right arguments

Do not touch or regress the Phase 1 document-RAG path — it should keep working
exactly as before for questions that don't need structured data.
```

### 18.3 Phase 3 — Access Control, Analytics, Feedback Loop

```
You are extending KnowledgeBase AI (Phase 1 + Phase 2 are already built and working).
Follow the Phase 3 section of KnowledgeBase_AI_Project.md.

Goal: add access control, usage analytics, and an answer-quality feedback loop.

1. ACCESS CONTROL
   - Add a simple authentication layer to the FastAPI backend (API key or
     session-based — pick the simpler one unless the project already has an
     auth system to plug into)
   - Add a document-level access tag (e.g. "general", "hr-only", "eng-only") in
     the ingestion metadata, and filter retrieval results by the requesting
     user's permitted tags
   - Users with no matching permission for a chunk should never see it in
     sources or have it used in context

2. USAGE ANALYTICS
   - Log every question, whether it was answered from RAG/tool-call/both, which
     sources were used, and response latency
   - Store logs in a lightweight local store (SQLite is fine, or the existing
     Postgres instance in a separate schema/table — read-only assumption from
     Phase 2 does not apply here, this is app-owned data)
   - Add a simple /analytics endpoint or small dashboard (Streamlit page is
     fine) showing: most common questions, questions with no good answer found,
     average response time

3. FEEDBACK LOOP
   - Add a thumbs up/down control in the Streamlit UI under each answer
   - Store feedback linked to the question/answer/sources used
   - Add a simple report (script or endpoint) that surfaces low-rated answers
     for review — this is for humans to review, not for automatic retraining

4. CONSTRAINTS
   - Do not send any logs, analytics, or feedback data to external services —
     everything stays local per the original privacy requirement
   - Access control changes must not break Phase 1/2 functionality for users
     with full permissions

Confirm end-to-end: a restricted user only receives answers grounded in
documents they're permitted to see, and their queries are logged with correct
metadata.
```

---

## 19. Manual Setup Checklist (not automatable by the agent)

- [ ] Install Ollama on the VM; run `ollama pull llama3.1` and `ollama pull nomic-embed-text`
- [ ] Bind Ollama to all interfaces on the VM (`OLLAMA_HOST=0.0.0.0:11434`) and restrict port 11434 to trusted sources only
- [ ] Confirm GPU is actually being used on the VM, if applicable
- [ ] Create a dedicated **read-only** PostgreSQL user/role for Phase 2 (never reuse an admin account)
- [ ] Gather and vet source documents; exclude sensitive docs from Phase 1 until Phase 3 access control exists
- [ ] Create `.env` with real values (`OLLAMA_BASE_URL`, DB credentials); add `.env` and `/chroma_db` to `.gitignore`
- [ ] Install Antigravity IDE from Google's official site
- [ ] Review agent-generated code manually before running, especially SQL and auth logic
- [ ] Decide on final hosting/hardware based on Section 12 performance notes
- [ ] After launch: periodically add new docs and trigger `/reindex`; review low-rated answers from the Phase 3 feedback loop
"""
Streamlit chat interface for KnowledgeBase AI.

Run with:
    streamlit run app/ui/chat.py --server.port 8501
"""

import os
import json
import streamlit as st
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# When running in Docker Compose, the API is reachable via the service name.
# When running locally, default to localhost:8000.
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="KnowledgeBase AI",
    page_icon="📚",
    layout="centered",
)

st.title("📚 KnowledgeBase AI")
st.caption("Ask questions about company documents and live data — answers are grounded in your internal knowledge base.")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Admin")

    # Health check
    if st.button("🩺 Check Health"):
        try:
            resp = requests.get(f"{API_BASE_URL}/health", timeout=10)
            data = resp.json()

            ollama_ok = data["ollama_status"] == "connected"
            db_status = data.get("db_status", "not_configured")
            db_ok = db_status == "connected"
            db_na = db_status == "not_configured"

            ollama_icon = "✅" if ollama_ok else "⚠️"
            if db_na:
                db_icon = "➖"
                db_label = "not configured"
            elif db_ok:
                db_icon = "✅"
                db_label = "connected"
            else:
                db_icon = "⚠️"
                db_label = db_status

            msg = (
                f"**API:** ✅\n\n"
                f"**Ollama:** {ollama_icon} `{data['ollama_url']}`\n\n"
                f"**Database:** {db_icon} {db_label}"
            )
            if ollama_ok and (db_ok or db_na):
                st.success(msg)
            else:
                st.warning(msg)
        except Exception as exc:
            st.error(f"API unreachable: {exc}")

    st.divider()

    # Re-index trigger
    if st.button("🔄 Re-index Documents"):
        with st.spinner("Re-indexing..."):
            try:
                resp = requests.post(f"{API_BASE_URL}/reindex", timeout=300)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(
                        f"Done! {data['documents']} doc section(s), "
                        f"{data['chunks']} chunk(s) in {data['seconds']}s"
                    )
                else:
                    st.error(f"Reindex failed: {resp.text}")
            except Exception as exc:
                st.error(f"Error: {exc}")

# ---------------------------------------------------------------------------
# Helper: render sources and tool calls for a message
# ---------------------------------------------------------------------------

def _render_sources(sources):
    """Render document sources in a collapsible expander."""
    if not sources:
        return
    with st.expander("📄 Sources used"):
        for src in sources:
            page_info = f" (page {src['page'] + 1})" if src.get("page") is not None else ""
            st.markdown(f"**{src['document']}{page_info}**")
            st.code(src["content"], language=None)


def _render_tool_calls(tool_calls):
    """Render tool call metadata in a collapsible expander."""
    if not tool_calls:
        return
    with st.expander("🔧 Tool calls used"):
        for tc in tool_calls:
            st.markdown(f"**`{tc['function']}`**")
            st.markdown("Arguments:")
            args = tc["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            st.json(args)
            st.markdown("Result:")
            result = tc["result"]
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    pass
            st.json(result)
            st.divider()


# ---------------------------------------------------------------------------
# Chat state
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        _render_sources(msg.get("sources"))
        _render_tool_calls(msg.get("tool_calls"))

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

if question := st.chat_input("Ask about company documents or data..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Call the API
    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating answer..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/ask",
                    json={"question": question},
                    timeout=120,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])
                    tool_calls = data.get("tool_calls", [])

                    st.markdown(answer)
                    _render_sources(sources)
                    _render_tool_calls(tool_calls)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "tool_calls": tool_calls,
                    })
                else:
                    error_msg = f"Error ({resp.status_code}): {resp.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                    })

            except requests.ConnectionError:
                msg = "Cannot connect to the API server. Is it running?"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            except Exception as exc:
                msg = f"Unexpected error: {exc}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})

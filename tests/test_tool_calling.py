"""
Tests for Phase 2 — PostgreSQL tool-calling.

These tests verify:
1. Tool schema validity and dispatch map completeness
2. Query functions use parameterized SQL (no string formatting)
3. Router correctly dispatches tool calls vs. RAG
4. Safety: unknown functions are rejected
"""

import json
import inspect
from unittest.mock import patch, MagicMock

import pytest


# -----------------------------------------------------------------------
# 1. Schema & dispatch map tests
# -----------------------------------------------------------------------

class TestToolSchema:
    """Verify that tool schemas are well-formed and match the dispatch map."""

    def test_all_schemas_have_matching_dispatch(self):
        """Every function in TOOL_SCHEMAS must exist in TOOL_DISPATCH."""
        from app.tools.schema import TOOL_SCHEMAS, TOOL_DISPATCH

        schema_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
        dispatch_names = set(TOOL_DISPATCH.keys())

        assert schema_names == dispatch_names, (
            f"Schema/dispatch mismatch — "
            f"in schema only: {schema_names - dispatch_names}, "
            f"in dispatch only: {dispatch_names - schema_names}"
        )

    def test_schemas_are_valid_format(self):
        """Each schema must have the required Ollama tool-calling fields."""
        from app.tools.schema import TOOL_SCHEMAS

        for schema in TOOL_SCHEMAS:
            assert schema["type"] == "function"
            func = schema["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert func["parameters"]["type"] == "object"
            assert "properties" in func["parameters"]

    def test_dispatch_functions_are_callable(self):
        """Every entry in TOOL_DISPATCH must be a callable."""
        from app.tools.schema import TOOL_DISPATCH

        for name, func in TOOL_DISPATCH.items():
            assert callable(func), f"{name} is not callable"


# -----------------------------------------------------------------------
# 2. Query function safety tests
# -----------------------------------------------------------------------

class TestQuerySafety:
    """Verify that all query functions use parameterized SQL."""

    def test_get_monthly_revenue_uses_parameterized_sql(self):
        """get_monthly_revenue must use %s placeholders, not string formatting."""
        from app.tools.queries import get_monthly_revenue
        source = inspect.getsource(get_monthly_revenue)

        # Must contain %s (parameterized placeholder)
        assert "%s" in source, "get_monthly_revenue does not use %s placeholders"

        # Must NOT contain f-string or .format() SQL injection patterns
        assert "f\"SELECT" not in source, "get_monthly_revenue uses f-string SQL"
        assert "f'SELECT" not in source, "get_monthly_revenue uses f-string SQL"
        assert ".format(" not in source, "get_monthly_revenue uses .format() SQL"

    def test_get_project_status_uses_parameterized_sql(self):
        """get_project_status must use %s placeholders."""
        from app.tools.queries import get_project_status
        source = inspect.getsource(get_project_status)

        assert "%s" in source
        assert "f\"SELECT" not in source
        assert "f'SELECT" not in source
        assert ".format(" not in source

    def test_get_quarterly_revenue_uses_parameterized_sql(self):
        """get_quarterly_revenue must use %s placeholders."""
        from app.tools.queries import get_quarterly_revenue
        source = inspect.getsource(get_quarterly_revenue)

        assert "%s" in source
        assert "f\"SELECT" not in source
        assert "f'SELECT" not in source
        assert ".format(" not in source

    def test_get_employee_count_uses_parameterized_sql(self):
        """get_employee_count must use %s placeholders."""
        from app.tools.queries import get_employee_count
        source = inspect.getsource(get_employee_count)

        assert "%s" in source
        assert "f\"SELECT" not in source
        assert "f'SELECT" not in source
        assert ".format(" not in source


# -----------------------------------------------------------------------
# 3. Query function error handling tests
# -----------------------------------------------------------------------

class TestQueryErrorHandling:
    """Verify that query functions return graceful errors, not stack traces."""

    @patch("app.tools.queries.get_connection")
    def test_monthly_revenue_db_error_returns_dict(self, mock_conn):
        """A DB error should return an error dict, not raise."""
        mock_conn.side_effect = Exception("Connection refused")
        from app.tools.queries import get_monthly_revenue

        result = get_monthly_revenue(3, 2025)
        assert "error" in result
        assert "Connection refused" in result["error"]

    @patch("app.tools.queries.get_connection")
    def test_project_status_db_error_returns_dict(self, mock_conn):
        """A DB error should return an error dict, not raise."""
        mock_conn.side_effect = Exception("Timeout")
        from app.tools.queries import get_project_status

        result = get_project_status("Project Alpha")
        assert "error" in result

    def test_quarterly_revenue_invalid_quarter(self):
        """Invalid quarter should return an error dict without hitting DB."""
        from app.tools.queries import get_quarterly_revenue

        result = get_quarterly_revenue(5, 2025)
        assert "error" in result
        assert "1, 2, 3, or 4" in result["error"]


# -----------------------------------------------------------------------
# 4. Router tests
# -----------------------------------------------------------------------

class TestRouter:
    """Verify that the router correctly dispatches tool calls vs. RAG."""

    @patch("app.rag.router.DB_AVAILABLE", False)
    @patch("app.rag.router.rag_ask")
    def test_no_db_falls_through_to_rag(self, mock_rag_ask):
        """When DB is not configured, always use RAG."""
        mock_rag_ask.return_value = {
            "answer": "The policy says 20 days.",
            "sources": [{"document": "policy.md", "content": "..."}],
        }
        from app.rag.router import ask

        result = ask("What is the leave policy?")

        mock_rag_ask.assert_called_once()
        assert result["tool_calls"] == []
        assert "20 days" in result["answer"]

    @patch("app.rag.router.DB_AVAILABLE", True)
    @patch("app.rag.router.Client")
    def test_tool_call_dispatched_correctly(self, mock_client_cls):
        """When the model issues a tool call, it should be dispatched."""
        # Mock the Ollama client
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # First call: model decides to use a tool
        mock_client.chat.side_effect = [
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_monthly_revenue",
                                "arguments": {"month": 3, "year": 2025},
                            }
                        }
                    ],
                }
            },
            # Second call: model produces final answer with tool result
            {
                "message": {
                    "role": "assistant",
                    "content": "The revenue for March 2025 was $150,000.",
                }
            },
        ]

        # Mock the actual DB function
        with patch("app.tools.schema.get_monthly_revenue") as mock_query:
            mock_query.return_value = {
                "month": 3,
                "year": 2025,
                "total_revenue": 150000.0,
            }
            # Need to also patch in TOOL_DISPATCH
            with patch.dict(
                "app.rag.router.TOOL_DISPATCH",
                {"get_monthly_revenue": mock_query},
            ):
                from app.rag.router import ask
                result = ask("What was our revenue in March 2025?")

        assert "150,000" in result["answer"]
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"] == "get_monthly_revenue"
        assert result["sources"] == []

    @patch("app.rag.router.DB_AVAILABLE", True)
    @patch("app.rag.router.Client")
    @patch("app.rag.router.rag_ask")
    def test_no_tool_call_falls_to_rag(self, mock_rag_ask, mock_client_cls):
        """When the model doesn't call a tool, fall through to RAG."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Model responds without tool calls
        mock_client.chat.return_value = {
            "message": {
                "role": "assistant",
                "content": "ROUTE_TO_RAG",
            }
        }

        mock_rag_ask.return_value = {
            "answer": "Employees get 20 days of leave.",
            "sources": [{"document": "policy.md", "content": "..."}],
        }

        from app.rag.router import ask
        result = ask("What is the leave policy?")

        mock_rag_ask.assert_called_once()
        assert result["tool_calls"] == []


# -----------------------------------------------------------------------
# 5. Safety tests
# -----------------------------------------------------------------------

class TestSafety:
    """Verify that unknown functions are rejected."""

    def test_unknown_function_rejected(self):
        """Attempting to call an unregistered function must fail gracefully."""
        from app.rag.router import _execute_tool_call

        result = _execute_tool_call({
            "function": {
                "name": "drop_database",
                "arguments": {},
            }
        })
        assert "error" in result
        assert "rejected" in result["error"].lower()


# -----------------------------------------------------------------------
# Example questions for manual testing
# -----------------------------------------------------------------------
# These are intended for manual end-to-end testing with a real DB:
#
#   "What was our revenue in March 2025?"
#   → Should call get_monthly_revenue(month=3, year=2025)
#
#   "What's the status of Project Alpha?"
#   → Should call get_project_status(project_name="Project Alpha")
#
#   "How many employees do we have in Engineering?"
#   → Should call get_employee_count(department="Engineering")
#
#   "What is the remote work policy?"
#   → Should NOT call any tool; should use RAG

"""
Ollama tool-calling schema definitions and dispatch map.

Each tool schema describes a function the LLM can choose to call.
The TOOL_DISPATCH dict maps function names to their Python callables.

SAFETY: Only functions listed in TOOL_DISPATCH are ever callable.
If the model tries to call anything else, the router rejects it.
"""

from app.tools.queries import (
    get_monthly_revenue,
    get_quarterly_revenue,
    get_project_status,
    get_employee_count,
)


# ---------------------------------------------------------------------------
# Tool schemas — sent to Ollama so the model knows what tools are available
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_monthly_revenue",
            "description": (
                "Get the total revenue for a specific month and year. "
                "Use this when the user asks about revenue, sales totals, "
                "or earnings for a particular month."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {
                        "type": "integer",
                        "description": "Month number (1 = January, 12 = December)",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Four-digit year (e.g. 2025)",
                    },
                },
                "required": ["month", "year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_quarterly_revenue",
            "description": (
                "Get the total revenue for a specific quarter and year. "
                "Use this when the user asks about quarterly revenue, "
                "Q1/Q2/Q3/Q4 earnings, or quarterly sales figures."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "quarter": {
                        "type": "integer",
                        "description": "Quarter number (1-4)",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Four-digit year (e.g. 2025)",
                    },
                },
                "required": ["quarter", "year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_status",
            "description": (
                "Get the current status of a specific project by name. "
                "Use this when the user asks about a project's status, "
                "progress, timeline, or project lead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The name of the project to look up",
                    },
                },
                "required": ["project_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_count",
            "description": (
                "Get the total number of employees, optionally filtered "
                "by department. Use this when the user asks about headcount, "
                "team size, or number of employees."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": (
                            "Department name to filter by (e.g. 'Engineering', "
                            "'Sales'). Omit for company-wide count."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Dispatch map — the ONLY functions the model can ever call
# ---------------------------------------------------------------------------

TOOL_DISPATCH = {
    "get_monthly_revenue": get_monthly_revenue,
    "get_quarterly_revenue": get_quarterly_revenue,
    "get_project_status": get_project_status,
    "get_employee_count": get_employee_count,
}

"""
Pre-defined, read-only PostgreSQL query functions.

SAFETY RULES (strict):
1. Every query uses parameterized placeholders (%s) — NEVER string-format
   raw SQL with user or model input.
2. Only specific, well-defined functions are exposed — no generic SQL
   execution of any kind.
3. The database user should be a read-only role at the DB level.
4. Failed queries return a graceful error dict, never a stack trace.
"""

from typing import Dict, Any, Optional
from app.tools.db import get_connection


def get_monthly_revenue(month: int, year: int) -> Dict[str, Any]:
    """Fetch total revenue for a given month and year."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS total_revenue
                FROM sales
                WHERE EXTRACT(MONTH FROM sale_date) = %s
                  AND EXTRACT(YEAR FROM sale_date) = %s
                """,
                (month, year),
            )
            row = cur.fetchone()
        return {
            "month": month,
            "year": year,
            "total_revenue": float(row["total_revenue"]) if row else 0.0,
        }
    except Exception as exc:
        return {"error": f"Failed to fetch monthly revenue: {exc}"}
    finally:
        if conn:
            conn.close()


def get_quarterly_revenue(quarter: int, year: int) -> Dict[str, Any]:
    """Fetch total revenue for a given quarter (1-4) and year."""
    if quarter not in (1, 2, 3, 4):
        return {"error": "Quarter must be 1, 2, 3, or 4."}

    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS total_revenue
                FROM sales
                WHERE EXTRACT(MONTH FROM sale_date) BETWEEN %s AND %s
                  AND EXTRACT(YEAR FROM sale_date) = %s
                """,
                (start_month, end_month, year),
            )
            row = cur.fetchone()
        return {
            "quarter": quarter,
            "year": year,
            "total_revenue": float(row["total_revenue"]) if row else 0.0,
        }
    except Exception as exc:
        return {"error": f"Failed to fetch quarterly revenue: {exc}"}
    finally:
        if conn:
            conn.close()


def get_project_status(project_name: str) -> Dict[str, Any]:
    """Fetch the current status of a named project."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT project_name, status, start_date, end_date, project_lead
                FROM projects
                WHERE LOWER(project_name) = LOWER(%s)
                """,
                (project_name,),
            )
            row = cur.fetchone()

        if not row:
            return {"message": f"No project found with name '{project_name}'."}

        return {
            "project_name": row["project_name"],
            "status": row["status"],
            "start_date": str(row["start_date"]) if row.get("start_date") else None,
            "end_date": str(row["end_date"]) if row.get("end_date") else None,
            "project_lead": row.get("project_lead"),
        }
    except Exception as exc:
        return {"error": f"Failed to fetch project status: {exc}"}
    finally:
        if conn:
            conn.close()


def get_employee_count(department: Optional[str] = None) -> Dict[str, Any]:
    """Fetch employee headcount, optionally filtered by department."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            if department:
                cur.execute(
                    """
                    SELECT COUNT(*) AS employee_count
                    FROM employees
                    WHERE LOWER(department) = LOWER(%s)
                    """,
                    (department,),
                )
            else:
                cur.execute("SELECT COUNT(*) AS employee_count FROM employees")

            row = cur.fetchone()

        result = {
            "employee_count": int(row["employee_count"]) if row else 0,
        }
        if department:
            result["department"] = department
        return result
    except Exception as exc:
        return {"error": f"Failed to fetch employee count: {exc}"}
    finally:
        if conn:
            conn.close()

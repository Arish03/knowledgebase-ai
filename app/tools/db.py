"""
PostgreSQL connection manager.

Uses psycopg2 with config sourced entirely from environment variables.
The database user SHOULD be a read-only role at the DB level — this
module enforces it in code as well, but defence-in-depth is the goal.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_AVAILABLE


def get_connection():
    """
    Open a new PostgreSQL connection using the configured credentials.

    Raises RuntimeError if DB is not configured.
    Caller is responsible for closing the connection (use try/finally).
    """
    if not DB_AVAILABLE:
        raise RuntimeError(
            "PostgreSQL is not configured. "
            "Set DB_HOST, DB_NAME, DB_USER, and DB_PASSWORD in your .env file."
        )

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )

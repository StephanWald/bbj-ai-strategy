"""Schema application helper for the RAG pipeline.

Reads and executes the standalone DDL file (sql/schema.sql) to create
or update the pgvector schema in PostgreSQL.
"""

from __future__ import annotations

from pathlib import Path

import psycopg

# Path from src/bbj_rag/schema.py -> rag-ingestion/sql/schema.sql
_SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"
_SCHEMA_FILE = _SQL_DIR / "schema.sql"


def apply_schema(conn: psycopg.Connection[object]) -> None:
    """Read sql/schema.sql and execute it against the given connection.

    Creates the pgvector extension, chunks table, and all indexes.
    The DDL uses IF NOT EXISTS / IF NOT EXISTS throughout, making it
    safe to run repeatedly (idempotent).
    """
    sql_content = _SCHEMA_FILE.read_text(encoding="utf-8")
    conn.execute(sql_content)
    conn.commit()

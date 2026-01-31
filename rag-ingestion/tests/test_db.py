"""Unit tests for the database module (no live PostgreSQL required).

Tests verify module exports, schema DDL correctness, pitfall avoidance,
and that the insert SQL uses ON CONFLICT deduplication.
"""

from __future__ import annotations

import inspect
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate project root (rag-ingestion/) for file-based assertions
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_SQL = _PROJECT_ROOT / "sql" / "schema.sql"


# ---------------------------------------------------------------------------
# 1. Module export tests
# ---------------------------------------------------------------------------


def test_db_module_exports():
    from bbj_rag.db import get_connection, insert_chunk, insert_chunks_batch

    assert callable(get_connection)
    assert callable(insert_chunk)
    assert callable(insert_chunks_batch)


def test_schema_module_exports():
    from bbj_rag.schema import apply_schema

    assert callable(apply_schema)


# ---------------------------------------------------------------------------
# 2. Schema SQL file existence and content
# ---------------------------------------------------------------------------


def test_schema_sql_file_exists():
    assert _SCHEMA_SQL.exists(), f"schema.sql not found at {_SCHEMA_SQL}"
    assert _SCHEMA_SQL.stat().st_size > 0, "schema.sql is empty"


def test_schema_sql_contains_required_elements():
    sql = _SCHEMA_SQL.read_text(encoding="utf-8")

    # Extension
    assert "CREATE EXTENSION IF NOT EXISTS vector" in sql

    # Table
    assert "CREATE TABLE IF NOT EXISTS chunks" in sql

    # Key columns
    assert "content_hash" in sql
    assert "UNIQUE" in sql
    assert "vector(1536)" in sql
    assert "GENERATED ALWAYS AS" in sql

    # tsvector with two-arg form
    assert "to_tsvector('english'" in sql

    # Indexes
    assert "hnsw" in sql.lower()
    # At least 2 GIN indexes (search_vector + generations)
    gin_count = sql.upper().count("USING GIN")
    assert gin_count >= 2, f"Expected at least 2 GIN indexes, found {gin_count}"


# ---------------------------------------------------------------------------
# 3. Pitfall avoidance
# ---------------------------------------------------------------------------


def _strip_sql_comments(sql: str) -> str:
    """Remove SQL single-line comments (-- ...) for assertion clarity."""
    return "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )


def test_schema_sql_avoids_pitfalls():
    raw = _SCHEMA_SQL.read_text(encoding="utf-8")
    # Strip comments so references to pitfalls in documentation don't trip asserts
    sql = _strip_sql_comments(raw)

    # Must NOT use concat() or concat_ws() -- they are STABLE, not IMMUTABLE
    assert "concat(" not in sql.lower(), "concat() is STABLE; use || operator instead"
    assert "concat_ws(" not in sql.lower(), (
        "concat_ws() is STABLE; use || operator instead"
    )

    # Must use || for concatenation
    assert "||" in sql, "Expected || operator for string concatenation"

    # Must use coalesce for NULL safety
    assert "coalesce(" in sql.lower(), "Expected coalesce() for NULL handling"


# ---------------------------------------------------------------------------
# 4. Insert SQL uses ON CONFLICT dedup
# ---------------------------------------------------------------------------


def test_chunk_insert_uses_dedup():
    import bbj_rag.db as db_module

    module_source = inspect.getsource(db_module)
    assert "ON CONFLICT (content_hash) DO NOTHING" in module_source, (
        "insert SQL must use ON CONFLICT (content_hash) DO NOTHING for dedup"
    )


def test_insert_sql_has_returning():
    """INSERT should use RETURNING id to detect whether a row was inserted."""
    import bbj_rag.db as db_module

    module_source = inspect.getsource(db_module)
    assert "RETURNING id" in module_source


def test_get_connection_calls_register_vector():
    """get_connection must call register_vector for pgvector type handling."""
    import bbj_rag.db as db_module

    source = inspect.getsource(db_module.get_connection)
    assert "register_vector" in source

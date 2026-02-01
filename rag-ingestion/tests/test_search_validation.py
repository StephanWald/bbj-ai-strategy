"""Parametrized search validation tests loaded from YAML.

These tests require a running PostgreSQL database with embedded Flare data.
They are excluded from the default pytest run via the search_validation marker.

Run manually:
    uv run pytest -m search_validation -v
    uv run bbj-rag validate
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from bbj_rag.search import SearchResult, bm25_search, dense_search, hybrid_search

# All tests in this file require a database with embedded chunks.
pytestmark = pytest.mark.search_validation

CASES_FILE = Path(__file__).parent / "validation_cases.yaml"


def _load_cases(section: str) -> list[dict[str, Any]]:
    """Load test cases from the YAML data file for a given section."""
    with CASES_FILE.open() as f:
        data = yaml.safe_load(f)
    return data.get(section, [])


def _assert_result_matches(
    results: list[SearchResult],
    expectation: dict[str, str],
) -> None:
    """Check that at least one result in the list matches the expectation."""
    for key, value in expectation.items():
        val_lower = value.lower()
        if key == "url_contains":
            urls = [r.source_url for r in results]
            assert any(val_lower in r.source_url.lower() for r in results), (
                f"No result URL contains '{value}'. URLs: {urls}"
            )
        elif key == "title_contains":
            titles = [r.title for r in results]
            assert any(val_lower in r.title.lower() for r in results), (
                f"No result title contains '{value}'. Titles: {titles}"
            )
        elif key == "content_contains":
            assert any(val_lower in r.content.lower() for r in results), (
                f"No result content contains '{value}'"
            )
        elif key == "doc_type":
            types = [r.doc_type for r in results]
            assert any(r.doc_type == value for r in results), (
                f"No result has doc_type '{value}'. Types: {types}"
            )
        elif key == "generations_contains":
            assert any(value in r.generations for r in results), (
                f"No result generations contain '{value}'"
            )
        else:
            msg = f"Unknown expectation key: {key}"
            raise ValueError(msg)


@pytest.fixture(scope="module")
def settings():
    from bbj_rag.config import Settings

    return Settings()


@pytest.fixture(scope="module")
def db_conn(settings):
    from bbj_rag.db import get_connection

    conn = get_connection(settings.database_url)
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def embedder(settings):
    from bbj_rag.embedder import create_embedder

    return create_embedder(settings)


@pytest.mark.parametrize(
    "case",
    _load_cases("dense_search"),
    ids=lambda c: c["query"][:50],
)
def test_dense_search(db_conn, embedder, case):
    query_vec = embedder.embed_batch([case["query"]])[0]
    generation_filter = case.get("filter_generation")
    results = dense_search(
        db_conn, query_vec, limit=5, generation_filter=generation_filter
    )
    assert len(results) > 0, f"No results for dense query: {case['query']}"
    for expectation in case.get("expect_in_top_5", []):
        _assert_result_matches(results, expectation)


@pytest.mark.parametrize(
    "case",
    _load_cases("bm25_search"),
    ids=lambda c: c["query"][:50],
)
def test_bm25_search(db_conn, case):
    generation_filter = case.get("filter_generation")
    results = bm25_search(
        db_conn, case["query"], limit=5, generation_filter=generation_filter
    )
    assert len(results) > 0, f"No results for BM25 query: {case['query']}"
    for expectation in case.get("expect_in_top_5", []):
        _assert_result_matches(results, expectation)


@pytest.mark.parametrize(
    "case",
    _load_cases("filtered_search"),
    ids=lambda c: c["query"][:50],
)
def test_filtered_search(db_conn, embedder, case):
    query_vec = embedder.embed_batch([case["query"]])[0]
    results = dense_search(
        db_conn, query_vec, limit=5, generation_filter=case["filter_generation"]
    )
    assert len(results) > 0, f"No results for filtered query: {case['query']}"
    for expectation in case.get("expect_in_top_5", []):
        _assert_result_matches(results, expectation)


@pytest.mark.parametrize(
    "case",
    _load_cases("hybrid_search"),
    ids=lambda c: c["query"][:50],
)
def test_hybrid_search(db_conn, embedder, case):
    query_vec = embedder.embed_batch([case["query"]])[0]
    generation_filter = case.get("filter_generation")
    results = hybrid_search(
        db_conn,
        query_vec,
        case["query"],
        limit=5,
        generation_filter=generation_filter,
    )
    assert len(results) > 0, f"No results for hybrid query: {case['query']}"
    for expectation in case.get("expect_in_top_5", []):
        _assert_result_matches(results, expectation)

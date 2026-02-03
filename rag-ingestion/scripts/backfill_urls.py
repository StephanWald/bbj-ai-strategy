"""One-time backfill: populate source_type and display_url for existing chunks.

Adds the two new columns (idempotent ALTER TABLE) and then batch-updates
every chunk whose source_type or display_url is still empty, using the
url_mapping module to derive values from the existing source_url.

Usage:
    cd rag-ingestion
    uv run python scripts/backfill_urls.py
"""

from __future__ import annotations

import logging
import sys

from bbj_rag.config import Settings
from bbj_rag.db import get_connection_from_settings
from bbj_rag.url_mapping import classify_source_type, map_display_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)

BATCH_SIZE = 1000


def backfill() -> None:
    """Run the backfill migration."""
    settings = Settings()
    conn = get_connection_from_settings(settings)

    log.info(
        "Connected to %s@%s:%s/%s",
        settings.db_user,
        settings.db_host,
        settings.db_port,
        settings.db_name,
    )

    with conn.cursor() as cur:
        # Idempotent schema migration: add columns if they don't exist yet.
        cur.execute(
            "ALTER TABLE chunks "
            "ADD COLUMN IF NOT EXISTS source_type TEXT NOT NULL DEFAULT ''"
        )
        cur.execute(
            "ALTER TABLE chunks "
            "ADD COLUMN IF NOT EXISTS display_url TEXT NOT NULL DEFAULT ''"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_source_type ON chunks (source_type)"
        )
    conn.commit()
    log.info("Schema migration complete (source_type, display_url columns + index)")

    # Fetch distinct source_urls that still need backfill.
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT source_url FROM chunks "
            "WHERE source_type = '' OR display_url = ''"
        )
        rows = cur.fetchall()

    source_urls = [row[0] for row in rows]
    total = len(source_urls)
    log.info("Found %d distinct source_urls needing backfill", total)

    if total == 0:
        log.info(
            "Nothing to backfill -- all chunks already have source_type and display_url"
        )
        conn.close()
        return

    updated_total = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = source_urls[batch_start : batch_start + BATCH_SIZE]

        with conn.cursor() as cur:
            for source_url in batch:
                source_type = classify_source_type(source_url)
                display_url = map_display_url(source_url)
                cur.execute(
                    "UPDATE chunks SET source_type = %s, display_url = %s "
                    "WHERE source_url = %s AND (source_type = '' OR display_url = '')",
                    (source_type, display_url, source_url),
                )
                updated_total += cur.rowcount

        conn.commit()
        processed = min(batch_start + BATCH_SIZE, total)
        log.info(
            "Progress: %d/%d distinct source_urls processed (%d chunks updated so far)",
            processed,
            total,
            updated_total,
        )

    log.info(
        "Backfill complete: %d chunks updated across %d distinct source_urls",
        updated_total,
        total,
    )
    conn.close()


if __name__ == "__main__":
    try:
        backfill()
    except Exception:
        log.exception("Backfill failed")
        sys.exit(1)

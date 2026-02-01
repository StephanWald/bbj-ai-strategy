#!/usr/bin/env bash
# scripts/reset-db.sh -- Wipe and reinitialize the database
#
# Stops all containers, removes the pgdata directory (full data wipe),
# then starts fresh. Schema is reapplied automatically on first run
# via docker-entrypoint-initdb.d.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Stopping containers..."
docker compose down

echo "Removing pgdata directory..."
rm -rf ./pgdata

echo "Starting fresh (schema will be applied on first run)..."
docker compose up -d

echo "Waiting for healthy state..."
MAX_ATTEMPTS=30
ATTEMPT=0
until docker compose exec app curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
        echo "ERROR: Health check did not pass after ${MAX_ATTEMPTS} attempts."
        docker compose logs --tail=20
        exit 1
    fi
    echo "  Attempt ${ATTEMPT}/${MAX_ATTEMPTS} -- waiting 2s..."
    sleep 2
done

echo "Reset complete."

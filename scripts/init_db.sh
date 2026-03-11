#!/bin/bash
# Initialize database: start containers and run migrations.
set -e

echo "=== Starting PostgreSQL + Redis ==="
docker compose up -d postgres redis

echo "=== Waiting for PostgreSQL to be ready ==="
TIMEOUT=30
ELAPSED=0
until docker compose exec postgres pg_isready -U finvest > /dev/null 2>&1; do
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "ERROR: PostgreSQL did not become ready within ${TIMEOUT}s"
        exit 1
    fi
done
echo "PostgreSQL is ready."

echo "=== Running Alembic migrations ==="
cd backend
poetry run alembic upgrade head

echo "=== Done! Database initialized. ==="

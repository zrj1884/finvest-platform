#!/bin/bash
# Initialize database: start containers and run migrations.
set -e

echo "=== Starting PostgreSQL + Redis ==="
docker compose up -d postgres redis

echo "=== Waiting for PostgreSQL to be ready ==="
until docker compose exec postgres pg_isready -U finvest > /dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "=== Running Alembic migrations ==="
cd backend
poetry run alembic upgrade head

echo "=== Done! Database initialized. ==="

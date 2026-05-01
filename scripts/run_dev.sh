#!/usr/bin/env bash
# Convenience: start postgres + redis via docker, run migrations, start the bot in foreground.
set -euo pipefail

if [[ ! -f .env ]]; then
    echo "Missing .env — copy .env.example to .env and fill in BOT_TOKEN and GEMINI_API_KEY"
    exit 1
fi

docker compose up -d postgres redis
echo "Waiting for postgres..."
until docker compose exec -T postgres pg_isready -U content_bot > /dev/null 2>&1; do
    sleep 1
done

alembic upgrade head
exec python -m src.main

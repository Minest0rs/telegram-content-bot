"""Test config — sets benign environment defaults so settings can load."""

from __future__ import annotations

import os

# stop pydantic-settings from looking for a real .env in dev
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

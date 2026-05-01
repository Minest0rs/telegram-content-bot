"""Tests for the Pollinations URL builder."""

from __future__ import annotations

import pytest

from src.services.images import generate_pollinations


@pytest.mark.asyncio
async def test_pollinations_url_contains_prompt() -> None:
    result = await generate_pollinations("a cat reading a newspaper")
    assert result.url.startswith("https://image.pollinations.ai/prompt/")
    assert "newspaper" in result.url
    assert result.source == "pollinations"


@pytest.mark.asyncio
async def test_pollinations_url_includes_dimensions_and_nologo() -> None:
    result = await generate_pollinations("hello", width=512, height=512)
    assert "width=512" in result.url
    assert "height=512" in result.url
    assert "nologo=true" in result.url


@pytest.mark.asyncio
async def test_pollinations_url_includes_seed_when_provided() -> None:
    result = await generate_pollinations("hello", seed=42)
    assert "seed=42" in result.url


@pytest.mark.asyncio
async def test_pollinations_url_encodes_special_chars() -> None:
    result = await generate_pollinations("hello world & friends")
    assert "hello%20world" in result.url
    assert "%26" in result.url

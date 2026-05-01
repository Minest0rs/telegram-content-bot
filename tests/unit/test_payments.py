"""Tests for the Telegram Stars invoice payload helpers."""

from __future__ import annotations

import pytest

from src.models import SubscriptionTier
from src.services.payments import build_invoice_payload, parse_invoice_payload


@pytest.mark.parametrize(
    "tier",
    [SubscriptionTier.PRO, SubscriptionTier.PREMIUM, SubscriptionTier.FREE],
)
def test_round_trip(tier: SubscriptionTier) -> None:
    payload = build_invoice_payload(user_id=1234567, tier=tier, duration_days=30)
    parsed = parse_invoice_payload(payload)
    assert parsed is not None
    assert parsed.user_id == 1234567
    assert parsed.tier == tier
    assert parsed.duration_days == 30


def test_parse_invalid_returns_none() -> None:
    assert parse_invoice_payload("garbage") is None
    assert parse_invoice_payload("sub:not-an-int:pro:30") is None
    assert parse_invoice_payload("sub:1:not-a-tier:30") is None
    assert parse_invoice_payload("") is None

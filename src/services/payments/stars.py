"""Helpers for Telegram Stars invoice payloads.

Telegram Stars (currency code ``XTR``) is the simplest way to charge inside
the bot — no merchant account needed.

The invoice payload is a small string we get back in ``successful_payment``
events; we use it to map a payment to a tier.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.models import SubscriptionTier

PAYLOAD_PREFIX = "sub:"


@dataclass(frozen=True)
class InvoicePayload:
    user_id: int
    tier: SubscriptionTier
    duration_days: int


def build_invoice_payload(*, user_id: int, tier: SubscriptionTier, duration_days: int = 30) -> str:
    return f"{PAYLOAD_PREFIX}{user_id}:{tier.value}:{duration_days}"


def parse_invoice_payload(payload: str) -> InvoicePayload | None:
    if not payload.startswith(PAYLOAD_PREFIX):
        return None
    try:
        body = payload.removeprefix(PAYLOAD_PREFIX)
        user_id_str, tier_str, dur_str = body.split(":")
        return InvoicePayload(
            user_id=int(user_id_str),
            tier=SubscriptionTier(tier_str),
            duration_days=int(dur_str),
        )
    except (ValueError, KeyError):
        return None

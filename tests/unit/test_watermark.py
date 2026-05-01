"""Tests for the watermark encoder."""

from __future__ import annotations

from src.services.watermark import (
    SIGNATURE_DELIMITER,
    apply_watermark,
    decode_marker,
    encode_marker,
    has_visible_signature,
    strip_watermark,
)


def test_marker_round_trip_zero() -> None:
    encoded = encode_marker(0)
    assert decode_marker(encoded) == 0


def test_marker_round_trip_various_values() -> None:
    for value in (1, 7, 42, 123, 65535):
        encoded = encode_marker(value)
        assert decode_marker(encoded) == value, f"failed for {value}"


def test_marker_decode_returns_none_when_absent() -> None:
    assert decode_marker("regular post text without markers") is None


def test_apply_and_strip_watermark_round_trip() -> None:
    original = "Headline\n\nBody of the post."
    sig = "🤖 by @testbot"
    watermarked = apply_watermark(original, signature=sig, marker_value=99)

    assert sig in watermarked
    assert SIGNATURE_DELIMITER in watermarked
    assert decode_marker(watermarked) == 99
    assert has_visible_signature(watermarked, sig)

    stripped = strip_watermark(watermarked)
    assert sig not in stripped
    assert SIGNATURE_DELIMITER not in stripped
    assert "Headline" in stripped
    # After stripping, no markers remain
    assert decode_marker(stripped) is None


def test_marker_survives_simulated_user_text_edits() -> None:
    """Even if a user adds extra text around the body, the marker is still findable."""
    original = "First line.\n\nSecond paragraph."
    sig = "signature"
    text = apply_watermark(original, signature=sig, marker_value=12345)
    # User pastes extra content before the post
    edited = "Some preamble\n\n" + text + "\n\nuser comment"
    assert decode_marker(edited) == 12345


def test_apply_watermark_idempotent_after_strip() -> None:
    """Re-applying watermark to already watermarked text doesn't double signatures."""
    body = "Hello world"
    sig = "by @bot"
    once = apply_watermark(body, signature=sig, marker_value=5)
    twice = apply_watermark(once, signature=sig, marker_value=5)
    # the second application strips zero-width chars first, so we should still
    # have exactly one signature delimiter
    assert twice.count(SIGNATURE_DELIMITER) == 1
    assert twice.count(sig) == 1
    assert decode_marker(twice) == 5

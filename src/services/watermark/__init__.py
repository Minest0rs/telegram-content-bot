"""Watermarking service: visible signature + hidden zero-width markers."""

from src.services.watermark.encoder import (
    SIGNATURE_DELIMITER,
    apply_watermark,
    decode_marker,
    encode_marker,
    has_visible_signature,
    strip_watermark,
)

__all__ = [
    "SIGNATURE_DELIMITER",
    "apply_watermark",
    "decode_marker",
    "encode_marker",
    "has_visible_signature",
    "strip_watermark",
]

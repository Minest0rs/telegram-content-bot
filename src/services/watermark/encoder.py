"""Watermark encoding.

Two parts:

1. **Visible signature** at the end of the post — what the user sees and may try
   to delete on the free tier.

2. **Invisible zero-width marker** embedded somewhere in the post text. Encodes
   a small integer (typically the post ID) as a binary sequence using
   `\\u200B` for "0" and `\\u200C` for "1", wrapped in `\\u2060` sentinels so
   we can find and decode it later. `\\uFEFF` is reserved as a tier marker.
"""

from __future__ import annotations

import re

# Zero-width characters used for encoding
_ZW_ZERO = "\u200b"  # ZERO WIDTH SPACE  -> bit 0
_ZW_ONE = "\u200c"  # ZERO WIDTH NON-JOINER -> bit 1
_ZW_SENTINEL = "\u2060"  # WORD JOINER -> sentinel
_ZW_ALL = (_ZW_ZERO, _ZW_ONE, _ZW_SENTINEL, "\u200d", "\ufeff")

SIGNATURE_DELIMITER = "\n\n———\n"

_MARKER_RE = re.compile(f"{_ZW_SENTINEL}([{_ZW_ZERO}{_ZW_ONE}]+){_ZW_SENTINEL}")


def encode_marker(value: int) -> str:
    """Encode a non-negative integer as a zero-width binary string."""
    if value < 0:
        raise ValueError("marker value must be non-negative")
    bits = bin(value)[2:].rjust(16, "0")
    body = "".join(_ZW_ONE if b == "1" else _ZW_ZERO for b in bits)
    return f"{_ZW_SENTINEL}{body}{_ZW_SENTINEL}"


def decode_marker(text: str) -> int | None:
    """Find the first zero-width marker in ``text`` and decode it.

    Returns the encoded integer, or ``None`` if no marker is found.
    """
    match = _MARKER_RE.search(text)
    if match is None:
        return None
    body = match.group(1)
    bits = "".join("1" if c == _ZW_ONE else "0" for c in body)
    if not bits:
        return None
    try:
        return int(bits, 2)
    except ValueError:
        return None


def strip_zero_width(text: str) -> str:
    """Remove all zero-width characters we use."""
    out = text
    for ch in _ZW_ALL:
        out = out.replace(ch, "")
    return out


def apply_watermark(text: str, *, signature: str, marker_value: int) -> str:
    """Append visible signature and embed a hidden marker into ``text``.

    The hidden marker is inserted right after the first paragraph break (or at
    the end if there's none) so it survives normal copy-paste in most clients.

    If ``text`` already contains a watermark, it is stripped first so the
    operation is idempotent.
    """
    if SIGNATURE_DELIMITER in text:
        text = text.split(SIGNATURE_DELIMITER, 1)[0]
    cleaned = strip_zero_width(text).rstrip()
    marker = encode_marker(marker_value)

    # insert marker after the first newline if possible, else append before signature
    insertion_point = cleaned.find("\n")
    if insertion_point == -1:
        body = cleaned + marker
    else:
        body = cleaned[: insertion_point + 1] + marker + cleaned[insertion_point + 1 :]

    return f"{body}{SIGNATURE_DELIMITER}{signature}"


def strip_watermark(text: str) -> str:
    """Remove both the visible signature block and any hidden markers."""
    cleaned = strip_zero_width(text)
    if SIGNATURE_DELIMITER in cleaned:
        cleaned = cleaned.split(SIGNATURE_DELIMITER)[0]
    return cleaned.rstrip()


def has_visible_signature(text: str, signature: str) -> bool:
    """Return True if the visible signature is still present in ``text``."""
    return signature in text

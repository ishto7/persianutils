"""Small helpers shared by the persianutils modules."""

from __future__ import annotations

from typing import Any


def ensure_str(value: Any) -> str:
    """Return ``value`` if it is a string, otherwise raise ``TypeError``."""
    if not isinstance(value, str):
        raise TypeError(f"expected str, got {type(value).__name__}")
    return value

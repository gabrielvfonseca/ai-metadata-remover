"""Metadata detection helpers."""

from config import AI_SIGNATURES


def is_ai_metadata_value(value: str) -> bool:
    if not value:
        return False
    text = value.lower()
    return any(sig in text for sig in AI_SIGNATURES)

"""
Logging helpers for consistent event fields in log messages.
"""
from __future__ import annotations

from typing import Any, Optional


def _format_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict)):
        return str(value)

    text = str(value)
    if any(ch.isspace() for ch in text) or '"' in text:
        escaped = text.replace('"', '\\"')
        return f"\"{escaped}\""
    return text


def format_log(message: str, event: Optional[str] = None, **fields: Any) -> str:
    """
    Append structured key-value fields to a log message.
    """
    pairs = []
    if event:
        pairs.append(f"event={_format_value(event)}")

    for key in sorted(fields.keys()):
        value = _format_value(fields[key])
        if value is None:
            continue
        pairs.append(f"{key}={value}")

    if not pairs:
        return message
    return f"{message} | {' '.join(pairs)}"

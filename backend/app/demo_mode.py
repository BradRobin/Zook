"""
Demo mode utilities for masking sensitive data in logs and responses.
"""
from __future__ import annotations

from typing import Optional, Union
import hashlib
import uuid
from fastapi import Request

DEMO_HEADER = "x-demo-mode"
DEMO_TRUE_VALUES = {"1", "true", "yes", "on"}


def is_demo_mode_request(request: Optional[Request]) -> bool:
    """Check if demo mode is enabled for an HTTP request."""
    if request is None:
        return False
    value = request.headers.get(DEMO_HEADER, "").strip().lower()
    return value in DEMO_TRUE_VALUES


def is_demo_mode_ws(demo_param: Optional[str]) -> bool:
    """Check if demo mode is enabled for a WebSocket connection."""
    if demo_param is None:
        return False
    return str(demo_param).strip().lower() in DEMO_TRUE_VALUES


def mask_username(username: Optional[str]) -> str:
    """Mask a username with a stable anonymized token."""
    if not username:
        return "demo-user"
    digest = hashlib.sha256(username.encode("utf-8")).hexdigest()[:6]
    return f"demo-user-{digest}"


def mask_uuid(value: Union[str, uuid.UUID]) -> uuid.UUID:
    """Mask a UUID with a deterministic UUIDv5."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"demo:{value}")


def mask_uuid_str(value: Union[str, uuid.UUID]) -> str:
    """Mask a UUID and return it as a string."""
    return str(mask_uuid(value))

"""Shared FastAPI dependencies."""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_internal_secret(x_internal_secret: str = Header(default="")) -> None:
    """Guard internal endpoints. The Next.js server injects this header when it
    proxies authenticated browser requests; the browser never sees it.
    """
    expected = get_settings().internal_api_secret
    if not hmac.compare_digest(x_internal_secret, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal secret",
        )

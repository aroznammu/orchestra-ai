"""Async HTTP client wrapper for the OrchestraAI API.

Every request automatically attaches the stored JWT as a Bearer token.
"""

from __future__ import annotations

from typing import Any

import httpx

from orchestra.cli import config


class APIError(Exception):
    """Raised when the backend returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


def _headers() -> dict[str, str]:
    token = config.get_token()
    h: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _url(path: str) -> str:
    base = config.get_api_url()
    return f"{base}{path}" if path.startswith("/") else f"{base}/{path}"


def _handle(resp: httpx.Response) -> Any:
    if resp.is_success:
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return resp.text
    detail = resp.text
    try:
        body = resp.json()
        detail = body.get("detail") or body.get("error") or resp.text
    except Exception:
        pass
    raise APIError(resp.status_code, str(detail))


async def get(path: str, *, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=30.0) as c:
        resp = await c.get(_url(path), headers=_headers(), params=params)
    return _handle(resp)


async def post(path: str, *, json: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=60.0) as c:
        resp = await c.post(_url(path), headers=_headers(), json=json or {})
    return _handle(resp)


async def patch(path: str, *, json: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=30.0) as c:
        resp = await c.patch(_url(path), headers=_headers(), json=json or {})
    return _handle(resp)

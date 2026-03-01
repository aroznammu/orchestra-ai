"""CLI configuration persistence.

Stores the API base URL and JWT token in ~/.orchestra/config.json so the
user does not need to re-authenticate on every invocation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".orchestra"
CONFIG_FILE = CONFIG_DIR / "config.json"

_DEFAULTS: dict[str, Any] = {
    "api_url": "http://localhost:8000/api/v1",
    "token": "",
}


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, Any]:
    """Load persisted config, falling back to defaults."""
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return {**_DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def save(data: dict[str, Any]) -> None:
    """Persist config to disk."""
    _ensure_dir()
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_token() -> str:
    return load().get("token", "")


def set_token(token: str) -> None:
    cfg = load()
    cfg["token"] = token
    save(cfg)


def get_api_url() -> str:
    return load().get("api_url", _DEFAULTS["api_url"])


def set_api_url(url: str) -> None:
    cfg = load()
    cfg["api_url"] = url.rstrip("/")
    save(cfg)


def clear() -> None:
    """Remove stored credentials."""
    save(dict(_DEFAULTS))

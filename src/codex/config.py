from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8765
    max_body_bytes: int = 1_000_000
    ifind_user: str = ""
    ifind_password: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            debug=os.getenv("CODEX_DEBUG", "").lower() in {"1", "true", "yes"},
            host=os.getenv("CODEX_HOST", "127.0.0.1"),
            port=_int_env("CODEX_PORT", 8765),
            max_body_bytes=_int_env("CODEX_MAX_BODY_BYTES", 1_000_000),
            ifind_user=os.getenv("IFIND_USER", ""),
            ifind_password=os.getenv("IFIND_PASSWORD", ""),
        )


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default

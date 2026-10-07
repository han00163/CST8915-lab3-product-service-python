"""Deployment configuration is read from environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _integer(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        raise ValueError(f"{name} must be an integer") from None
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class Settings:
    host: str = "0.0.0.0"
    port: int = 3030
    workers: int = 1
    log_level: str = "info"
    cors_origins: tuple[str, ...] = ("*",)

    @classmethod
    def from_env(cls) -> "Settings":
        # Never search parent folders; injected variables take precedence.
        load_dotenv(dotenv_path=".env", override=False)
        host = os.environ.get("HOST", "0.0.0.0").strip()
        if not host:
            raise ValueError("HOST must not be empty")
        log_level = os.environ.get("LOG_LEVEL", "info").strip().lower()
        if log_level not in {"critical", "error", "warning", "info", "debug", "trace"}:
            raise ValueError("LOG_LEVEL must be critical, error, warning, info, debug, or trace")
        origins = tuple(
            origin.strip()
            for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        )
        return cls(
            host=host,
            port=_integer("PORT", 3030, 1, 65535),
            workers=_integer("WORKERS", 1, 1, 128),
            log_level=log_level,
            cors_origins=origins,
        )

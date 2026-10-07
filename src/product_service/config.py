"""Deployment configuration is read only from environment variables."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


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
    database_url: str = field(repr=False)
    host: str = "0.0.0.0"
    port: int = 3030
    workers: int = 1
    log_level: str = "info"
    cors_origins: tuple[str, ...] = ("*",)
    db_connect_timeout: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        # Explicit current-directory file: never search parent repositories.
        # Injected environment variables always take precedence over local .env.
        load_dotenv(dotenv_path=".env", override=False)
        database_url = os.environ.get("DATABASE_URL", "").strip()
        if not database_url:
            raise ValueError("DATABASE_URL is required")
        try:
            url = make_url(database_url)
        except ArgumentError:
            raise ValueError("DATABASE_URL must be a valid database URL") from None
        if url.drivername not in {"postgresql+psycopg", "sqlite"}:
            raise ValueError("DATABASE_URL must use postgresql+psycopg:// or sqlite://")
        if url.drivername == "postgresql+psycopg" and not (url.host and url.database):
            raise ValueError("DATABASE_URL must include a PostgreSQL host and database")
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
            database_url=database_url,
            host=host,
            port=_integer("PORT", 3030, 1, 65535),
            workers=_integer("WORKERS", 1, 1, 128),
            log_level=log_level,
            cors_origins=origins,
            db_connect_timeout=_integer("DB_CONNECT_TIMEOUT", 5, 1, 300),
        )

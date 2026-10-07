"""Bind the HTTP service to the configured host and port."""

import sys

import uvicorn

from product_service.config import Settings


def main() -> None:
    try:
        settings = Settings.from_env()
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    uvicorn.run(
        "product_service.api:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level,
        timeout_graceful_shutdown=15,
    )


if __name__ == "__main__":
    main()

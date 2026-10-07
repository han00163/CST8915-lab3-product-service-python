# 12-Factor App: first four factors

This project's scope is the first four factors of the [12-Factor App methodology](https://12factor.net/): Codebase, Dependencies, Config, and Backing services. The Python API preserves the original fixed product data and response.

## 1. Codebase

`product-service-python` has one independent Git repository under `C:\AC Labs\8915 labs\lab3\product-service-python`. Development, staging, and production use revisions from this same codebase. Deployment settings do not require source copies or environment-specific branches.

Evidence: this project's Git history, `pyproject.toml`, and `src/product_service/`.

Reference: [Codebase](https://12factor.net/codebase).

## 2. Dependencies

All imported third-party libraries are declared in `pyproject.toml`. `uv.lock` records exact resolved versions and distribution hashes, including transitive dependencies. The build backend and dependency-manager version are pinned.

`uv sync --locked` installs into an isolated `.venv` and refuses an outdated lock. The optional Docker setup installs the same locked runtime dependencies with `--no-dev --no-editable`. Python 3.13/3.14 is the declared runtime prerequisite. Request processing does not invoke undeclared shell utilities.

Reference: [Dependencies](https://12factor.net/dependencies).

## 3. Config

`Settings.from_env()` reads deployment settings independently from environment variables: `HOST`, `PORT`, `WORKERS`, `LOG_LEVEL`, and `CORS_ORIGINS`. Invalid values fail startup clearly. These settings are separate from route definitions and the fixed product data.

The optional current-directory `.env` is a local convenience. Injected environment variables take precedence. Parent directories are never searched. Real `.env` files are excluded from version control and Docker builds; `.env.example` documents available settings.

Reference: [Config](https://12factor.net/config).

## 4. Backing services

The original API returns three fixed products directly from code. The Python `/products` handler uses the same data handling: each request creates the same three product dictionaries. There is no database, catalog file, cache, or persistent storage.

The application currently consumes no backing services. This factor does not require adding a database or another service. If a backing service is needed later, its locator and credentials must come from environment variables, and local or hosted resources must be replaceable without changing application code.

Reference: [Backing services](https://12factor.net/backing-services).

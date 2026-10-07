# 12-factor implementation

This project follows the [12-Factor App methodology](https://12factor.net/). Shared deployments use an external PostgreSQL resource, injected environment variables, isolated dependencies, and one version-controlled codebase. SQLite is limited to isolated tests and optional local previews.

## 1. Codebase

The Python service has its own Git repository, separate from lab2's Rust service. Development, staging, and production deploy revisions from this repository. Deployment settings never require separate source copies. The package is named `product-service-python`; its Python import is `product_service`.

Evidence: `.git/`, `pyproject.toml`, `src/product_service/`.

Reference: [Codebase](https://12factor.net/codebase).

## 2. Dependencies

All directly imported libraries are declared in `pyproject.toml`. `uv.lock` resolves exact versions and distribution hashes, including transitive dependencies. The build backend and uv tool version are pinned. `uv sync --locked` installs into an isolated `.venv` and refuses an outdated lock. The Dockerfile installs the same locked runtime dependencies with `--no-dev --no-editable`.

Python 3.13/3.14 is the declared runtime prerequisite. Runtime requests do not shell out to undeclared system utilities. For deliberate dependency updates, run `uv lock --upgrade`, check the service, and commit the manifest and lock together.

Reference: [Dependencies](https://12factor.net/dependencies).

## 3. Config

`Settings.from_env()` reads independently configurable database locator/credentials, bind host/port, worker count, logging, CORS, and connection timeout. `DATABASE_URL` is required; malformed settings fail startup with a clear message excluding credentials.

Only the optional current-directory `.env` is loaded. Injected environment variables take precedence. Parent repository files are never searched. Real `.env` files are excluded from Git and Docker build contexts; `.env.example` contains local examples only. There are no hardcoded staging/production configuration bundles.

Reference: [Config](https://12factor.net/config).

## 4. Backing services

The live product catalog is read from an attached PostgreSQL resource through SQLAlchemy/Psycopg. Sample products are inserted by an explicit administrative seed command, never hardcoded into a request handler.

Local Compose PostgreSQL and hosted PostgreSQL use the same driver, schema, and request code. Attach another resource by changing `DATABASE_URL`, including credentials and TLS query parameters, then provisioning/restoring its catalog. Example deployment variable:

`DATABASE_URL=postgresql+psycopg://USER:ENCODED_PASSWORD@DB_HOST:5432/products?sslmode=require`

Run the built application image with environment variables supplied by the platform; the local Compose database is a development helper. Database connection pools close during shutdown. Failed catalog/readiness requests return 503; process liveness remains independent of database health.

Reference: [Backing services](https://12factor.net/backing-services).

## Remaining factors

| Factor | Implementation and deployment practice |
| --- | --- |
| 5. Build, release, run | `uv build` creates a versioned wheel. The Dockerfile builds the locked code. Release tasks initialize the schema and optionally seed. HTTP startup does neither. Deploy immutable image tags/digests with separately injected configuration. |
| 6. Processes | Workers are stateless and share external PostgreSQL. Persistent database data belongs to the backing service, not the HTTP process. SQLite previews are unsuitable for multiple hosts. |
| 7. Port binding | Uvicorn binds `HOST` and `PORT` directly; the default is `0.0.0.0:3030`. |
| 8. Concurrency | `WORKERS` controls worker processes. A platform can run multiple instances sharing PostgreSQL behind a load balancer. |
| 9. Disposability | Startup performs no schema changes or seeding. Uvicorn handles process signals, allows 15 seconds for graceful request shutdown, and lifespan cleanup disposes the pool. |
| 10. Dev/prod parity | Use PostgreSQL and the same dependency lock/container in dev, staging, and production. Fast isolated SQLite tests supplement PostgreSQL integration coverage in CI. |
| 11. Logs | HTTP and application logs go to standard streams. The platform collects them. The app writes no log files and avoids credential-bearing database exception messages. |
| 12. Admin processes | `python -m product_service.manage init-db` and `seed` run as one-off processes using the same package/config. They are repeatable, preserve existing data, and should run serially as release tasks. |

`init-db` creates only the initial schema; use versioned migrations for future deployed schema changes. Deployment infrastructure owns TLS termination, backups, routing, resource sizing, secret injection, and release orchestration.

## Verification

Tests cover the original API contract, database-driven catalog changes, swapping the database URL, CORS configuration, environment precedence, validation, independent liveness, unavailable database responses, and repeatable administration. CI also provisions an ephemeral PostgreSQL 17 database for network-backed integration.

The optional PostgreSQL integration test runs only when `TEST_DATABASE_URL` is set. Use a dedicated test database: the test creates the product table and inserts the sample catalog. It does not remove existing data.

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://USER:PASSWORD@localhost:5432/test_products'
uv run --locked pytest -q
```

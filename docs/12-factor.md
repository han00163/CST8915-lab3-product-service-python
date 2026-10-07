# 12-factor implementation

This service follows the [12-Factor App methodology](https://12factor.net/) while preserving the original fixed product catalog. Deployment infrastructure supplies routing, TLS, log collection, and release orchestration.

## 1. Codebase

`product-service-python` has one independent Git repository. The same package and source revision supply local development, staging, and production. Deployment settings do not require source copies or environment-specific branches.

Evidence: `pyproject.toml`, `src/product_service/`, and this project's Git history.

Reference: [Codebase](https://12factor.net/codebase).

## 2. Dependencies

All imported third-party libraries are declared in `pyproject.toml`. `uv.lock` records exact resolved versions and distribution hashes, including transitive dependencies. The build backend and dependency-manager version are pinned.

`uv sync --locked` installs into an isolated `.venv` and refuses an outdated lock. Docker installs the same locked runtime dependencies with `--no-dev --no-editable`. Python 3.13/3.14 is the declared runtime prerequisite. Request processing does not invoke undeclared shell tools.

Reference: [Dependencies](https://12factor.net/dependencies).

## 3. Config

`Settings.from_env()` reads `HOST`, `PORT`, `WORKERS`, `LOG_LEVEL`, and `CORS_ORIGINS` independently from environment variables. Invalid values fail startup clearly. Deployment configuration is separated from route definitions and the fixed application catalog.

The optional current-directory `.env` is for local convenience. Injected variables take precedence, parent directories are never searched, and real `.env` files are excluded from version control and Docker builds.

Reference: [Config](https://12factor.net/config).

## 4. Backing services

The original API has a fixed, read-only catalog. This implementation consumes no database, queue, cache, or external network service. The methodology does not require introducing a backing service where the application does not need one.

`products.json` is immutable application data shipped with the release, not a per-deployment resource or mutable datastore. All instances of the same release serve the same catalog.

If an external catalog or another backing service is introduced later, its locator and credentials must be injected through environment variables, and local/hosted instances must be interchangeable without source changes. No backing-service locator or credential is hardcoded in the current service.

Reference: [Backing services](https://12factor.net/backing-services).

## Remaining factors

| Factor | Implementation and deployment practice |
| --- | --- |
| 5. Build, release, run | `uv build` produces a wheel; Docker builds from the locked codebase. Supply deployment configuration when releasing/running. Deploy immutable image tags/digests and do not edit running containers. |
| 6. Processes | Workers have no mutable catalog/session state and write no persistent data. Each instance loads the same bundled catalog. |
| 7. Port binding | Uvicorn binds `HOST` and `PORT` directly; defaults are `0.0.0.0:3030`. |
| 8. Concurrency | `WORKERS` controls worker processes. A platform can run multiple independent instances behind a load balancer. |
| 9. Disposability | Startup validates settings and loads the small catalog. Uvicorn handles process signals and allows 15 seconds for graceful request shutdown. |
| 10. Dev/prod parity | Use the same Python runtime family, lockfile, package, and catalog across deployments. No separate database products or provisioning steps are involved. |
| 11. Logs | HTTP and error logs go to standard streams for platform collection; the service writes no log files. |
| 12. Admin processes | The fixed read-only API needs no database administration jobs. Any future one-off maintenance job should use the same released package and environment as the running service. |

## Verification

Tests cover the exact original product response, startup without a database or resource configuration, identical catalogs across instances, health endpoints, GET-only behavior, CORS controls, environment precedence, and configuration validation. CI uses the locked dependencies and builds the package after checks.

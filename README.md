# product-service-python

A Python implementation of the original read-only product service. It returns the same three products from `GET /products`, uses numeric prices, permits GET CORS by default, and listens on port 3030. It runs without a database or separate backing-service process. The methodology scope is the first four factors: Codebase, Dependencies, Config, and Backing services.

## Run on Windows

Prerequisites: Python 3.13 or 3.14.

```powershell
Set-Location 'C:\AC Labs\8915 labs\lab3\product-service-python'
py -3.13 -m pip install uv==0.12.23
uv sync --locked
uv run --locked python -m product_service
```

From another terminal:

```powershell
Invoke-RestMethod http://localhost:3030/products
```

Stop the service with Ctrl+C. You can also use `uv run --locked product-service`.

On Linux/macOS, install the pinned tool with `python3 -m pip install uv==0.12.23`, then use the same uv commands. Optional local settings can be copied from `.env.example`.

## Run with Docker

With Docker and Docker Compose installed:

```powershell
docker compose up --build
```

Compose starts only the API. The image uses the same locked runtime dependencies and runs as an unprivileged user.

## Azure App Service

For Azure's Linux Python Code deployment, use Startup Command `sh startup.sh` and keep `SCM_DO_BUILD_DURING_DEPLOYMENT=1`. The committed `requirements.txt` is generated from `uv.lock` for Azure's default GitHub workflow. See [Azure setup and troubleshooting](docs/azure-app-service.md).

## API

| Route | Response |
| --- | --- |
| `GET /products` | The original JSON array of three products |
| `GET /health/live` | 200 with `{"status":"ok"}` |
| `GET /health/ready` | 200 with `{"status":"ready"}` |
| `GET /docs` | Interactive OpenAPI documentation |

```json
[
  {"id": 1, "name": "Dog Food", "price": 19.99},
  {"id": 2, "name": "Cat Food", "price": 34.99},
  {"id": 3, "name": "Bird Seeds", "price": 10.99}
]
```

The `/products` handler returns the three fixed product dictionaries directly from Python code, matching the original service. Each request creates the response array; there is no database, catalog file, cache, or persistence.

## Configuration

| Variable | Default / purpose |
| --- | --- |
| `HOST` | `0.0.0.0` |
| `PORT` | `3030`, valid range 1-65535 |
| `WORKERS` | `1`, independent Uvicorn worker processes |
| `LOG_LEVEL` | `info` |
| `CORS_ORIGINS` | `*`, comma-separated origins, or empty to disable CORS origins |

All deployment settings come from environment variables. Only the current directory's optional `.env` is loaded; injected environment variables take precedence. Real `.env` files are excluded from Git and Docker build contexts.

## Verify and build

```powershell
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
uv build
```

`uv.lock` records exact dependency versions and distribution hashes. `uv sync --locked` installs into an isolated `.venv` and refuses stale locks. For intentional upgrades, run `uv lock --upgrade`, verify the service, and commit the manifest and lock together.

See [the first four 12-Factor principles](docs/12-factor.md) for Codebase, Dependencies, Config, and Backing services.

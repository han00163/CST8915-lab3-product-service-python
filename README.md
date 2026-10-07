# product-service-python

Python rewrite of the lab2 Rust product service. The API retains `GET /products`, numeric prices, the three sample products, GET CORS, and default port 3030. FastAPI serves HTTP; SQLAlchemy and Psycopg attach a PostgreSQL catalog using `DATABASE_URL`.

## Run with PostgreSQL (recommended)

Prerequisites: Docker Engine/Desktop with Docker Compose. Run in PowerShell:

```powershell
Set-Location 'C:\AC Labs\8915 labs\lab3\product-service-python'
Copy-Item .env.example .env
docker compose build
docker compose up -d db
docker compose run --rm api python -m product_service.manage init-db
docker compose run --rm api python -m product_service.manage seed
docker compose up -d api
Invoke-RestMethod http://localhost:3030/products
```

Use `docker compose logs -f api` to view logs. `docker compose down` stops the services and preserves the database volume. The sample password is for local development; set deployment credentials through the environment or your platform's secret manager.

## Run Python on Windows

Prerequisites: Python 3.13 or 3.14, plus PostgreSQL for a shared deployment.

```powershell
Set-Location 'C:\AC Labs\8915 labs\lab3\product-service-python'
py -3.13 -m pip install uv==0.12.23
uv sync --locked
Copy-Item .env.example .env
```

For PostgreSQL running on the host, change `db` in the copied `.env` URL to `localhost` and supply your database credentials. If using the Compose database, start it with `docker compose up -d db` first.

For a quick local preview without PostgreSQL, set this environment variable instead:

```powershell
$env:DATABASE_URL = 'sqlite:///./products.db'
```

SQLite is a preview/test convenience. Use PostgreSQL for dev/staging/production parity and shared storage.

Then provision the selected resource and start the service:

```powershell
uv run --locked python -m product_service.manage init-db
uv run --locked python -m product_service.manage seed
uv run --locked python -m product_service
```

Stop the foreground service with Ctrl+C. Remove the preview override with `Remove-Item Env:DATABASE_URL`. On Linux/macOS, install uv with `python3 -m pip install uv==0.12.23`; subsequent uv commands are the same. Use `cp .env.example .env` and shell `export` commands for environment variables.

## API

| Route | Response |
| --- | --- |
| `GET /products` | Ordered JSON array of products from the attached catalog |
| `GET /health/live` | 200 when the HTTP process is alive |
| `GET /health/ready` | 200 when the database and catalog table are accessible; otherwise 503 |
| `GET /docs` | Interactive OpenAPI documentation |

After seeding, `/products` returns:

```json
[
  {"id": 1, "name": "Dog Food", "price": 19.99},
  {"id": 2, "name": "Cat Food", "price": 34.99},
  {"id": 3, "name": "Bird Seeds", "price": 10.99}
]
```

Unavailable databases return 503 without exposing connection strings. An initialized, unseeded catalog returns an empty array. The web process never creates tables or inserts sample data during startup.

## Configuration

| Variable | Default / purpose |
| --- | --- |
| `DATABASE_URL` | Required. PostgreSQL URL using `postgresql+psycopg://`; SQLite for previews/tests |
| `HOST` | `0.0.0.0` |
| `PORT` | `3030`, valid range 1-65535 |
| `WORKERS` | `1`, independent Uvicorn worker processes |
| `LOG_LEVEL` | `info` |
| `CORS_ORIGINS` | `*`, or comma-separated origins; empty disables CORS origins |
| `DB_CONNECT_TIMEOUT` | `5` seconds for PostgreSQL connections |

Only the current directory's optional `.env` is loaded; existing environment variables take precedence. `.env`, databases, virtual environments, and credentials are excluded from Git and Docker build contexts. Compose-only `POSTGRES_*` and `DB_PORT` variables provision the local database.

## Verify and build

```powershell
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
uv build
```

`uv.lock` records resolved dependency versions and hashes; `uv sync --locked` refuses stale locks and installs into an isolated `.venv`. Commit changes to the manifest and lock together. To update dependencies deliberately, use `uv lock --upgrade`, then run the checks.

See [the 12-factor implementation](docs/12-factor.md) for the four focus factors and the remaining deployment practices. `init-db` creates the initial schema idempotently; it is not a schema evolution tool. Future schema changes need versioned migrations.

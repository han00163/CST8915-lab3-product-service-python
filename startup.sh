#!/bin/sh
set -eu

# App Service's built-in Python image listens on port 8000.
# Environment overrides still take precedence.
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"

exec python -m product_service

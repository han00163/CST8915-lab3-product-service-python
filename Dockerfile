FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.23
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
USER appuser
EXPOSE 3030
CMD ["python", "-m", "product_service"]

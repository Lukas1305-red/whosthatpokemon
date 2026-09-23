FROM ghcr.io/astral-sh/uv:0.8.9-python3.13-bookworm-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.13-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app . /app

USER app
EXPOSE 8000

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --limit-concurrency ${MAX_CONCURRENT_REQUESTS:-20} --timeout-keep-alive 5"]

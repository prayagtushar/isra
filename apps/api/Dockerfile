# syntax=docker/dockerfile:1
#
# Build from the repo root, not apps/api:  docker build -f apps/api/Dockerfile -t isra-api .

# Builder: resolve deps and bake the models in.
FROM python:3.11-slim-bookworm AS builder

# Pin uv to the version this repo's lockfile was produced with.
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON_PREFERENCE=only-system \
    HF_HOME=/opt/hf

WORKDIR /app

# api plus ingest, because /ingest shells out to the scraper. evals is not installed.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package isra-api --package isra-ingest

# Pre-download the models so the first request does not pay for it.
RUN mkdir -p /opt/hf && \
    .venv/bin/python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('BAAI/bge-small-en-v1.5'); CrossEncoder('BAAI/bge-reranker-base')"

# Runtime.
FROM python:3.11-slim-bookworm AS runtime

# libgomp1 is required by the CPU torch wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/hf \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /opt/hf /opt/hf

# uvicorn imports "src.main:app", so the working dir must be the api package.
WORKDIR /app/apps/api

# Cloud Run injects $PORT (defaults to 8080). Bind 0.0.0.0 so it is reachable.
EXPOSE 8080
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

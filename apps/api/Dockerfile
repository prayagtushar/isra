# syntax=docker/dockerfile:1
#
# Production image for the ISRA FastAPI service (apps/api).
#
# Build from the REPO ROOT (the uv workspace root), not from apps/api:
#   docker build -f apps/api/Dockerfile -t isra-api .
#
# The image bakes the BGE embedding + reranker models into the HuggingFace
# cache so the first request does not pay a multi-hundred-MB download. torch is
# CPU-only: the root pyproject pins it to the PyTorch CPU wheel index for Linux,
# so no CUDA libraries are pulled into the image.

############################################
# Builder: resolve deps + bake models
############################################
FROM python:3.11-slim-bookworm AS builder

# Pin uv to the version this repo's lockfile was produced with.
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON_PREFERENCE=only-system \
    HF_HOME=/opt/hf

WORKDIR /app

# Copy the whole workspace (see .dockerignore for what is excluded) and sync
# Install the api package (+ its workspace dep isra-retrieval) AND the ingest
# package, so the /ingest endpoint's subprocess has its scraper deps
# (beautifulsoup4, lxml). evals is not installed.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package isra-api --package isra-ingest

# Pre-download the models used by retrieve(): embeddings for every mode and the
# cross-encoder reranker for the default "hybrid+rerank" mode.
RUN mkdir -p /opt/hf && \
    .venv/bin/python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('BAAI/bge-small-en-v1.5'); CrossEncoder('BAAI/bge-reranker-base')"

############################################
# Runtime
############################################
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

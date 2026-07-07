#!/usr/bin/env bash
# Deploy the ISRA API to the `isra` Cloud Run service with a strict $1/month
# budget config.
#
# This script assumes:
#   - GCP billing is enabled
#   - gcloud is authenticated and project is set
#   - The image already exists in Artifact Registry
#   - Secrets isra-database-url and isra-openrouter-key exist in Secret Manager
#
# Usage:
#   infra/deploy-api.sh [IMAGE_TAG]
# Default tag: latest

set -euo pipefail

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
REGION="asia-south1"
SERVICE="isra"
TAG="${1:-latest}"
IMAGE="asia-south1-docker.pkg.dev/${PROJECT_ID}/isra/api:${TAG}"

echo "Deploying ${IMAGE} to Cloud Run service ${SERVICE} (${PROJECT_ID}/${REGION})..."

# Cost guardrails:
#   --min-instances 0        -> scale to zero, no always-on cost
#   --max-instances 1        -> never more than one instance
#   --concurrency 20         -> modest concurrent requests per instance
#   --cpu-boost              -> faster cold start, no always-on cost
#   --memory 2Gi --cpu 1     -> smallest size that can load the models
#   --timeout 300            -> 5 min request ceiling
#   --execution-environment gen2 -> required for CPU boost
#
# With this config, at most 1 vCPU is ever running, and only while requests are
# active. Light traffic stays well under $1/month; Artifact Registry storage is
# the main fixed cost (~$0.15/mo).
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --platform managed \
  --execution-environment gen2 \
  --memory 2Gi \
  --cpu 1 \
  --cpu-boost \
  --min-instances 0 \
  --max-instances 1 \
  --concurrency 20 \
  --timeout 300 \
  --set-env-vars 'ISRA_LLM_MODEL=anthropic/claude-haiku-4.5,ISRA_ENABLE_RETRIEVAL_TRACE=true' \
  --set-secrets 'ISRA_DATABASE_URL=isra-database-url:latest,ISRA_OPENROUTER_API_KEY=isra-openrouter-key:latest' \
  --no-use-http2 \
  --ingress all

echo "Deployed. Smoke test with:"
echo "  API=\$(gcloud run services describe ${SERVICE} --region ${REGION} --format 'value(status.url)')"
echo "  curl -s \"\$API/health\""

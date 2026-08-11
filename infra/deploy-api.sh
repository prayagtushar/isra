#!/usr/bin/env bash
# Deploy the ISRA API to Cloud Run.
#
# Usage: infra/deploy-api.sh [IMAGE_TAG]      (default tag: latest)

set -euo pipefail

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
REGION="asia-south1"
SERVICE="isra"
TAG="${1:-latest}"
IMAGE="asia-south1-docker.pkg.dev/${PROJECT_ID}/isra/api:${TAG}"

echo "Deploying ${IMAGE} to Cloud Run service ${SERVICE} (${PROJECT_ID}/${REGION})..."

# 4 vCPU is a cost choice: Cloud Run bills vCPU-seconds, so 4 for ~5s costs what 1 for ~20s does.
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --platform managed \
  --execution-environment gen2 \
  --memory 4Gi \
  --cpu 4 \
  --cpu-boost \
  --min-instances 0 \
  --max-instances 1 \
  --concurrency 20 \
  --timeout 300 \
  --set-env-vars 'ISRA_LLM_MODEL=anthropic/claude-haiku-4.5,ISRA_ENABLE_RETRIEVAL_TRACE=true,ISRA_LANGFUSE_HOST=https://us.cloud.langfuse.com,ISRA_LANGFUSE_PUBLIC_KEY=pk-lf-4a9d5d6c-96a2-45b4-84f0-bb61767f5987' \
  --set-secrets 'ISRA_DATABASE_URL=isra-database-url:latest,ISRA_OPENROUTER_API_KEY=isra-openrouter-key:latest,ISRA_LANGFUSE_SECRET_KEY=isra-langfuse-secret:latest' \
  --no-use-http2 \
  --ingress all

echo "Deployed. Smoke test with:"
echo "  API=\$(gcloud run services describe ${SERVICE} --region ${REGION} --format 'value(status.url)')"
echo "  curl -s \"\$API/health\""

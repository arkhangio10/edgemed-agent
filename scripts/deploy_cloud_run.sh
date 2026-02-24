#!/usr/bin/env bash
# Deploy EdgeMed API to Cloud Run.
# Optional: set EDGEMED_GOOGLE_API_KEY_SECRET=projects/PROJECT_ID/secrets/SECRET_NAME/versions/latest
#   to inject the Google API key from Secret Manager (recommended; do not pass the key as plain env).
set -euo pipefail

PROJECT_ID="${EDGEMED_PROJECT_ID:-edgemed-agent}"
REGION="${EDGEMED_REGION:-us-central1}"
SERVICE_NAME="edgemed-api"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Env vars for Cloud Run (no secrets here)
ENV_VARS="EDGEMED_PROJECT_ID=${PROJECT_ID},EDGEMED_GOOGLE_CLOUD_PROJECT=${PROJECT_ID},EDGEMED_DEMO_MODE_ENABLED=true,EDGEMED_PROD_MODE_ENABLED=false"

echo "=== Building Docker image ==="
docker build -t "${IMAGE}" -f cloud/Dockerfile .

echo "=== Pushing to GCR ==="
docker push "${IMAGE}"

echo "=== Deploying to Cloud Run ==="
DEPLOY_CMD=(
  gcloud run deploy "${SERVICE_NAME}"
  --image "${IMAGE}"
  --region "${REGION}"
  --project "${PROJECT_ID}"
  --platform managed
  --allow-unauthenticated
  --set-env-vars "${ENV_VARS}"
  --memory 1Gi
  --cpu 1
  --min-instances 0
  --max-instances 5
  --timeout 300
)

# Optional: inject Google API key from Secret Manager (recommended; never put the key in env).
#   Create secret in Console: Secret Manager > Create secret > name e.g. edgemed-google-api-key, value = your key.
#   Or: echo -n "YOUR_API_KEY" | gcloud secrets create edgemed-google-api-key --data-file=-
#   Grant Cloud Run SA access: Secret Manager > secret > Permissions > Add principal: PROJECT_NUMBER-compute@developer.gserviceaccount.com, role Secret Manager Secret Accessor
#   Then: EDGEMED_GOOGLE_API_KEY_SECRET=edgemed-google-api-key ./scripts/deploy_cloud_run.sh
if [[ -n "${EDGEMED_GOOGLE_API_KEY_SECRET:-}" ]]; then
  SECRET_REF="${EDGEMED_GOOGLE_API_KEY_SECRET}"
  [[ "${SECRET_REF}" != *:* ]] && SECRET_REF="${SECRET_REF}:latest"
  DEPLOY_CMD+=(--set-secrets="EDGEMED_GOOGLE_API_KEY=${SECRET_REF}")
fi

"${DEPLOY_CMD[@]}"

echo "=== Deployment complete ==="
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --project "${PROJECT_ID}" --format "value(status.url)"

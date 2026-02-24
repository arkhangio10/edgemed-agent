#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${EDGEMED_PROJECT_ID:-edgemed-agent}"
DATASET="edgemed_analytics"
LOCATION="${EDGEMED_BQ_LOCATION:-US}"

echo "=== Creating BigQuery dataset ==="
bq --project_id="${PROJECT_ID}" mk \
  --dataset \
  --location="${LOCATION}" \
  --description="EdgeMed Agent analytics — metrics only, NO PHI" \
  "${DATASET}" 2>/dev/null || echo "Dataset already exists"

echo "=== Creating tables ==="
for sql in bigquery/extraction_metrics.sql bigquery/sync_metrics.sql bigquery/usage_metrics.sql; do
  echo "Running ${sql}..."
  bq --project_id="${PROJECT_ID}" query --use_legacy_sql=false < "${sql}"
done

echo "=== BigQuery setup complete ==="

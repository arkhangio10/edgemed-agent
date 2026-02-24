"""Create BigQuery dataset and tables for EdgeMed analytics.

Usage:
    python scripts/setup_bigquery_py.py

Workaround for when the `bq` CLI is broken.
"""

from google.cloud import bigquery

PROJECT_ID = "edgemedsoinar"
DATASET_ID = "edgemed_analytics"
LOCATION = "US"

client = bigquery.Client(project=PROJECT_ID)

# 1. Create dataset
dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION
dataset.description = "EdgeMed Agent analytics — metrics only, NO PHI"

try:
    client.create_dataset(dataset)
    print(f"✅ Created dataset: {DATASET_ID}")
except Exception as e:
    if "Already Exists" in str(e):
        print(f"⏭️  Dataset already exists: {DATASET_ID}")
    else:
        raise

# 2. Create tables via SQL
TABLE_SQLS = {
    "extraction_metrics": """
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.extraction_metrics` (
            uid_hash             STRING    NOT NULL,
            device_id_hash       STRING,
            note_id_hash         STRING    NOT NULL,
            mode                 STRING    NOT NULL,
            timing_ms            INT64     NOT NULL,
            completeness_score   FLOAT64,
            missing_fields_count INT64,
            contradictions_count INT64,
            model_version        STRING,
            schema_version       STRING,
            created_at           TIMESTAMP NOT NULL
        )
        PARTITION BY DATE(created_at)
        OPTIONS (
            description = 'Extraction pipeline metrics — NO PHI, hashed identifiers only'
        )
    """,
    "sync_metrics": """
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.sync_metrics` (
            device_id_hash STRING    NOT NULL,
            mode           STRING    NOT NULL,
            synced_count   INT64     NOT NULL,
            failed_count   INT64     NOT NULL,
            timing_ms      INT64     NOT NULL,
            created_at     TIMESTAMP NOT NULL
        )
        PARTITION BY DATE(created_at)
        OPTIONS (
            description = 'Sync pipeline metrics — NO PHI, hashed identifiers only'
        )
    """,
    "usage_metrics": """
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.usage_metrics` (
            uid_hash    STRING    NOT NULL,
            mode        STRING    NOT NULL,
            action_type STRING    NOT NULL,
            timing_ms   INT64     NOT NULL,
            created_at  TIMESTAMP NOT NULL
        )
        PARTITION BY DATE(created_at)
        OPTIONS (
            description = 'Usage metrics by action type — NO PHI, hashed identifiers only'
        )
    """,
}

for name, sql in TABLE_SQLS.items():
    query = sql.format(project=PROJECT_ID, dataset=DATASET_ID)
    try:
        client.query(query).result()
        print(f"✅ Created table: {name}")
    except Exception as e:
        print(f"❌ Error creating {name}: {e}")

print("\n🎉 BigQuery setup complete!")

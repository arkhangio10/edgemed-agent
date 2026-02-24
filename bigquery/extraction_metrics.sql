CREATE TABLE IF NOT EXISTS edgemed_analytics.extraction_metrics (
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
);

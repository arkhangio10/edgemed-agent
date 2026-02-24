CREATE TABLE IF NOT EXISTS edgemed_analytics.sync_metrics (
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
);

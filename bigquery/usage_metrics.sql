CREATE TABLE IF NOT EXISTS edgemed_analytics.usage_metrics (
    uid_hash    STRING    NOT NULL,
    mode        STRING    NOT NULL,
    action_type STRING    NOT NULL,
    timing_ms   INT64     NOT NULL,
    created_at  TIMESTAMP NOT NULL
)
PARTITION BY DATE(created_at)
OPTIONS (
    description = 'Usage metrics by action type — NO PHI, hashed identifiers only'
);

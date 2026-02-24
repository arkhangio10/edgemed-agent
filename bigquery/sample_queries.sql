-- ============================================================
-- EdgeMed Agent — Judge-Friendly BigQuery Analytics Queries
-- All data is hashed/non-PHI metrics only
-- ============================================================

-- Q1: Average latency by mode and action type (with P95)
SELECT
    mode,
    action_type,
    COUNT(*)                                                      AS total_requests,
    ROUND(AVG(timing_ms), 1)                                      AS avg_latency_ms,
    ROUND(APPROX_QUANTILES(timing_ms, 100)[OFFSET(50)], 1)       AS p50_latency_ms,
    ROUND(APPROX_QUANTILES(timing_ms, 100)[OFFSET(95)], 1)       AS p95_latency_ms
FROM `edgemed_analytics.usage_metrics`
GROUP BY mode, action_type
ORDER BY mode, action_type;


-- Q2: Completeness distribution and quality breakdown
SELECT
    mode,
    COUNT(*)                                 AS total_extractions,
    ROUND(AVG(completeness_score), 3)        AS avg_completeness,
    ROUND(STDDEV(completeness_score), 3)     AS stddev_completeness,
    COUNTIF(completeness_score >= 0.8)       AS high_quality_count,
    COUNTIF(completeness_score >= 0.5 AND completeness_score < 0.8) AS medium_quality_count,
    COUNTIF(completeness_score < 0.5)        AS low_quality_count,
    ROUND(AVG(missing_fields_count), 1)      AS avg_missing_fields,
    ROUND(AVG(contradictions_count), 1)      AS avg_contradictions
FROM `edgemed_analytics.extraction_metrics`
GROUP BY mode;


-- Q3: Sync success rate and reliability overview
SELECT
    mode,
    COUNT(*)                          AS total_sync_batches,
    SUM(synced_count)                 AS total_items_synced,
    SUM(failed_count)                 AS total_items_failed,
    ROUND(
        SAFE_DIVIDE(SUM(synced_count), SUM(synced_count) + SUM(failed_count)) * 100,
        1
    )                                 AS success_rate_pct,
    ROUND(AVG(timing_ms), 1)          AS avg_sync_latency_ms,
    ROUND(APPROX_QUANTILES(timing_ms, 100)[OFFSET(95)], 1) AS p95_sync_latency_ms
FROM `edgemed_analytics.sync_metrics`
GROUP BY mode;

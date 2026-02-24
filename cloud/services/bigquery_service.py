"""BigQuery metrics writer.

Writes ONLY hashed identifiers and numeric metrics. NEVER writes PHI, note_text,
or full clinical records.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from google.cloud import bigquery

from cloud.config import get_settings

logger = logging.getLogger(__name__)

_client: bigquery.Client | None = None


def _get_client() -> bigquery.Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT or settings.PROJECT_ID)
    return _client


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _dataset() -> str:
    return get_settings().BQ_DATASET


async def log_extraction_metrics(
    uid_hash: str,
    note_id: str,
    mode: str,
    timing_ms: int,
    completeness_score: float,
    missing_fields_count: int,
    contradictions_count: int,
    model_version: str,
    schema_version: str,
    device_id: str | None = None,
) -> None:
    client = _get_client()
    table = f"{_dataset()}.extraction_metrics"
    rows = [
        {
            "uid_hash": uid_hash,
            "device_id_hash": _hash(device_id) if device_id else None,
            "note_id_hash": _hash(note_id),
            "mode": mode,
            "timing_ms": timing_ms,
            "completeness_score": completeness_score,
            "missing_fields_count": missing_fields_count,
            "contradictions_count": contradictions_count,
            "model_version": model_version,
            "schema_version": schema_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ]
    errors = client.insert_rows_json(table, rows)
    if errors:
        logger.error("BigQuery insert errors (extraction_metrics): %s", errors)


async def log_sync_metrics(
    device_id: str,
    mode: str,
    synced_count: int,
    failed_count: int,
    timing_ms: int,
) -> None:
    client = _get_client()
    table = f"{_dataset()}.sync_metrics"
    rows = [
        {
            "device_id_hash": _hash(device_id),
            "mode": mode,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "timing_ms": timing_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ]
    errors = client.insert_rows_json(table, rows)
    if errors:
        logger.error("BigQuery insert errors (sync_metrics): %s", errors)


async def log_usage_metrics(
    uid_hash: str,
    mode: str,
    action_type: str,
    timing_ms: int,
) -> None:
    client = _get_client()
    table = f"{_dataset()}.usage_metrics"
    rows = [
        {
            "uid_hash": uid_hash,
            "mode": mode,
            "action_type": action_type,
            "timing_ms": timing_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ]
    errors = client.insert_rows_json(table, rows)
    if errors:
        logger.error("BigQuery insert errors (usage_metrics): %s", errors)


async def query_analytics_summary() -> dict:
    """Run aggregated queries for the web demo analytics dashboard."""
    client = _get_client()
    ds = _dataset()

    summary = {
        "avg_latency_ms": 0,
        "total_extractions": 0,
        "avg_completeness": 0,
        "top_missing_fields": [],
        "sync_success_rate": 0,
        "usage_by_action": [],
    }

    try:
        q1 = f"""
            SELECT
                COUNT(*) AS total,
                ROUND(AVG(timing_ms), 1) AS avg_latency,
                ROUND(AVG(completeness_score), 3) AS avg_completeness
            FROM `{ds}.extraction_metrics`
            WHERE mode = 'demo'
        """
        result = client.query(q1).result()
        for row in result:
            summary["total_extractions"] = row.total or 0
            summary["avg_latency_ms"] = row.avg_latency or 0
            summary["avg_completeness"] = row.avg_completeness or 0
    except Exception:
        logger.exception("Analytics query q1 failed")

    try:
        q2 = f"""
            SELECT
                action_type,
                COUNT(*) AS count,
                ROUND(AVG(timing_ms), 1) AS avg_latency
            FROM `{ds}.usage_metrics`
            WHERE mode = 'demo'
            GROUP BY action_type
        """
        result = client.query(q2).result()
        summary["usage_by_action"] = [
            {"action": row.action_type, "count": row.count, "avg_latency_ms": row.avg_latency}
            for row in result
        ]
    except Exception:
        logger.exception("Analytics query q2 failed")

    try:
        q3 = f"""
            SELECT
                ROUND(SAFE_DIVIDE(SUM(synced_count), SUM(synced_count) + SUM(failed_count)) * 100, 1)
                    AS success_rate
            FROM `{ds}.sync_metrics`
            WHERE mode = 'demo'
        """
        result = client.query(q3).result()
        for row in result:
            summary["sync_success_rate"] = row.success_rate or 0
    except Exception:
        logger.exception("Analytics query q3 failed")

    return summary

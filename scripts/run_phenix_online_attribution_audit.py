#!/usr/bin/env python3
"""Bounded, aggregate-only BigQuery audit for Phenix attribution.

The audit compares Firebase Analytics export datasets by complete event day.
It persists table metadata and aggregate channel/event coverage only. It never
persists event rows, parameter values, user identifiers, or credentials.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from google.auth import default as default_credentials
from google.auth.transport.requests import Request
from google.cloud import bigquery


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "wajenigeria"
LOCATION = "europe-west4"
MAX_BYTES_PER_QUERY = 5 * 1024**3
MAX_BYTES_PER_RUN = 25 * 1024**3
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")
OUT_DIR = ROOT / "analysis/phenix_online_attribution_audit_2026_09_02"
SQL_DIR = OUT_DIR / "sql"
RESULTS_PATH = OUT_DIR / "daily_channel_audit.json"
RECEIPT_PATH = OUT_DIR / "run_receipt.json"

# Complete daily tables available at the time of the audit. Intraday tables
# are inventoried but deliberately excluded from channel comparisons.
DATASETS = [
    "analytics_470712959",
    "analytics_504208609",
    "analytics_517134955",
    "analytics_546634805",
    "waje_ng_firebase_h5",
]
COMPLETE_DAYS = ["20260827", "20260828", "20260829", "20260830", "20260831", "20260901"]
INTRADAY_DAYS = ["20260902"]


def safe(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if hasattr(value, "items") and not isinstance(value, (str, bytes, list, tuple)):
        return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, dict):
        return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe(v) for v in value]
    return value


def validate_sql(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["python3", str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "message": (result.stdout + result.stderr).strip(),
    }


def sql_for(dataset_id: str, day: str) -> str:
    table_ref = f"`{PROJECT_ID}.{dataset_id}.events_{day}`"
    return f"""-- Aggregate-only Firebase attribution audit.
-- Date is a complete event day; no event rows or parameter values are returned.
WITH base AS (
  SELECT
    platform,
    app_info.id AS app_id,
    app_info.version AS app_version,
    device.web_info.hostname AS hostname,
    event_name,
    user_pseudo_id,
    traffic_source.source AS first_source,
    traffic_source.medium AS first_medium,
    collected_traffic_source.manual_source AS manual_source,
    collected_traffic_source.manual_medium AS manual_medium,
    traffic_source.source IS NOT NULL AND traffic_source.source != '' AS first_source_present,
    collected_traffic_source.manual_source IS NOT NULL
      AND collected_traffic_source.manual_source != '' AS manual_source_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(LOWER(COALESCE(p.key, '')), r'(package|bundle|app[_-]?id)')
    ) AS package_key_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(LOWER(COALESCE(p.key, '')), r'(channel|media|source|medium|referrer)')
    ) AS channel_key_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(LOWER(COALESCE(p.key, '')), r'(campaign|utm_)')
    ) AS campaign_key_present,
    REGEXP_CONTAINS(
      LOWER(CONCAT(
        COALESCE(app_info.id, ''), '|',
        COALESCE(app_info.version, ''), '|',
        COALESCE(device.web_info.hostname, ''), '|',
        COALESCE(traffic_source.source, ''), '|',
        COALESCE(traffic_source.medium, '')
      )),
      r'(wajeh5phx|waje5phx|phenix)'
    )
    OR EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(
        LOWER(CONCAT(COALESCE(p.key, ''), '=', COALESCE(p.value.string_value, ''))),
        r'(wajeh5phx|waje5phx|phenix)'
      )
    )
    OR EXISTS (
      SELECT 1 FROM UNNEST(user_properties) p
      WHERE REGEXP_CONTAINS(
        LOWER(CONCAT(COALESCE(p.key, ''), '=', COALESCE(p.value.string_value, ''))),
        r'(wajeh5phx|waje5phx|phenix)'
      )
    ) AS phx_marker_present
  FROM {table_ref}
  WHERE event_date = '{day}'
), normalized AS (
  SELECT
    platform,
    app_id,
    app_version,
    hostname,
    event_name,
    user_pseudo_id,
    first_source,
    first_medium,
    manual_source,
    manual_medium,
    first_source_present,
    manual_source_present,
    package_key_present,
    channel_key_present,
    campaign_key_present,
    phx_marker_present,
    CASE
      WHEN manual_source_present OR (manual_medium IS NOT NULL AND manual_medium != '') THEN 'manual_collected'
      WHEN first_source_present OR (first_medium IS NOT NULL AND first_medium != '') THEN 'first_user_traffic'
      ELSE 'unattributed'
    END AS attribution_basis,
    CASE
      WHEN manual_source_present OR (manual_medium IS NOT NULL AND manual_medium != '') THEN
        CONCAT(COALESCE(NULLIF(manual_source, ''), '(not_set)'), ' / ', COALESCE(NULLIF(manual_medium, ''), '(not_set)'))
      WHEN first_source_present OR (first_medium IS NOT NULL AND first_medium != '') THEN
        CONCAT(COALESCE(NULLIF(first_source, ''), '(not_set)'), ' / ', COALESCE(NULLIF(first_medium, ''), '(not_set)'))
      ELSE '(unattributed)'
    END AS channel_key
  FROM base
)
SELECT
  'channel' AS row_scope,
  COALESCE(platform, '(blank)') AS platform,
  COALESCE(app_id, '(blank)') AS app_id,
  COALESCE(hostname, '(blank)') AS hostname,
  COALESCE(attribution_basis, '(all)') AS attribution_basis,
  COALESCE(channel_key, '(all)') AS channel_key,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) AS approx_subject_count,
  COUNT(DISTINCT event_name) AS distinct_event_name_count,
  COUNTIF(event_name = 'page_view') AS page_view_event_count,
  COUNTIF(event_name = 'session_start') AS session_start_event_count,
  COUNTIF(event_name = 'first_visit') AS first_visit_event_count,
  COUNTIF(event_name = 'first_open') AS first_open_event_count,
  COUNTIF(event_name = 'user_engagement') AS user_engagement_event_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(register|recharge|purchase|withdraw|payment|login|pay)')) AS business_event_candidate_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(game|bet|round|settle|reward|play)')) AS game_event_candidate_count,
  COUNTIF(first_source_present) AS first_source_present_count,
  COUNTIF(manual_source_present) AS manual_source_present_count,
  COUNTIF(package_key_present) AS package_key_present_count,
  COUNTIF(channel_key_present) AS channel_key_present_count,
  COUNTIF(campaign_key_present) AS campaign_key_present_count,
  COUNTIF(phx_marker_present) AS phx_marker_count,
  APPROX_COUNT_DISTINCT(NULLIF(app_version, '')) AS approx_version_count,
  APPROX_TOP_COUNT(event_name, 50) AS top_event_names
FROM normalized
GROUP BY platform, app_id, hostname, attribution_basis, channel_key
HAVING APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) >= 10
ORDER BY event_count DESC, channel_key
"""


def table_inventory(client: bigquery.Client) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset_id in DATASETS:
        try:
            dataset = client.get_dataset(f"{PROJECT_ID}.{dataset_id}")
            dataset_info = {
                "dataset_id": dataset_id,
                "location": dataset.location,
                "description_present": bool(dataset.description),
                "dataset_created": safe(dataset.created),
                "dataset_modified": safe(dataset.modified),
                "status": "visible",
            }
        except Exception as exc:
            rows.append({"dataset_id": dataset_id, "status": "blocked_or_missing", "error_type": type(exc).__name__})
            continue
        for day in COMPLETE_DAYS:
            table_id = f"events_{day}"
            try:
                dataset_info_for_table = dataset_info
                table = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
                rows.append({
                    **dataset_info_for_table,
                    "table_id": table_id,
                    "event_day": day,
                    "table_class": "complete_daily",
                    "table_type": table.table_type,
                    "num_rows": table.num_rows,
                    "num_bytes": table.num_bytes,
                    "created": safe(table.created),
                    "modified": safe(table.modified),
                    "status": "available",
                })
            except Exception as exc:
                rows.append({
                    **dataset_info_for_table,
                    "table_id": table_id,
                    "event_day": day,
                    "table_class": "complete_daily",
                    "status": "not_observed",
                    "error_type": type(exc).__name__,
                })
        for day in INTRADAY_DAYS:
            table_id = f"events_intraday_{day}"
            try:
                table = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
                rows.append({
                    **dataset_info,
                    "table_id": table_id,
                    "event_day": day,
                    "table_class": "intraday",
                    "table_type": table.table_type,
                    "num_rows": table.num_rows,
                    "num_bytes": table.num_bytes,
                    "created": safe(table.created),
                    "modified": safe(table.modified),
                    "status": "available",
                })
            except Exception as exc:
                # A missing daily table is a coverage fact, not a zero-valued table.
                rows.append({
                    **dataset_info,
                    "table_id": table_id,
                    "event_day": day,
                    "table_class": "intraday",
                    "status": "not_observed",
                    "error_type": type(exc).__name__,
                })
    return rows


def execute_one(client: bigquery.Client, dataset_id: str, day: str) -> dict[str, Any]:
    path = SQL_DIR / f"channel_{dataset_id}_{day}.sql"
    sql = sql_for(dataset_id, day)
    path.write_text(sql, encoding="utf-8")
    record: dict[str, Any] = {
        "dataset_id": dataset_id,
        "event_day": day,
        "sql_file": str(path.relative_to(ROOT)),
        "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(),
        "validation": validate_sql(path),
    }
    if record["validation"]["status"] != "passed":
        record["status"] = "blocked_sql_validation"
        return record
    table_ref = f"{PROJECT_ID}.{dataset_id}.events_{day}"
    try:
        dry = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False,
                maximum_bytes_billed=MAX_BYTES_PER_QUERY,
            ),
            location=LOCATION,
        )
        dry_bytes = int(dry.total_bytes_processed or 0)
        record["dry_run"] = {
            "status": "passed" if dry_bytes <= MAX_BYTES_PER_QUERY else "blocked_cost",
            "total_bytes_processed": dry_bytes,
            "maximum_bytes_billed": MAX_BYTES_PER_QUERY,
            "table_ref": table_ref,
        }
        if dry_bytes > MAX_BYTES_PER_QUERY:
            record["status"] = "blocked_cost"
            return record
        job = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                use_legacy_sql=False,
                use_query_cache=False,
                maximum_bytes_billed=MAX_BYTES_PER_QUERY,
            ),
            location=LOCATION,
        )
        rows = list(job.result(timeout=180))
        aggregate_rows = [safe(dict(row.items())) for row in rows]
        record["status"] = "ok" if aggregate_rows else "no_visible_channel"
        record["execution"] = {
            "job_id": job.job_id,
            "row_count": len(aggregate_rows),
            "total_bytes_processed": int(job.total_bytes_processed or 0),
            "total_bytes_billed": int(job.total_bytes_billed or 0),
            "created": safe(job.created),
            "started": safe(job.started),
            "ended": safe(job.ended),
            "aggregate_rows": aggregate_rows,
        }
    except Exception as exc:
        record["status"] = "query_failed"
        record["error_type"] = type(exc).__name__
        record["error"] = str(exc)[:500]
    return record


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SQL_DIR.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "run_id": "phenix_online_attribution_audit_2026_09_02",
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "business_timezone": "Africa/Lagos",
        "complete_day_window": ["2026-08-27", "2026-09-01"],
        "intraday_inventory_day": "2026-09-02",
        "datasets_requested": DATASETS,
        "status": "not_started",
        "safety": {
            "metadata_or_aggregate_only": True,
            "raw_rows_saved": False,
            "event_parameter_values_saved": False,
            "user_identifiers_saved": False,
            "credentials_saved": False,
            "remote_systems_modified": False,
            "small_subject_groups_suppressed": True,
        },
    }
    try:
        credentials, adc_project = default_credentials(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not credentials.valid:
            credentials.refresh(Request())
        receipt["auth"] = {
            "status": "valid" if credentials.valid else "invalid",
            "credential_type": type(credentials).__name__,
            "adc_project": adc_project,
        }
        if not credentials.valid:
            raise RuntimeError("ADC is not valid")
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
    except Exception as exc:
        receipt["status"] = "blocked_authentication"
        receipt["auth"] = {"status": "blocked_authentication", "error_type": type(exc).__name__, "error": str(exc)[:500]}
        RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2

    inventory = table_inventory(client)
    (OUT_DIR / "table_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    available = {(row["dataset_id"], row["event_day"]) for row in inventory if row.get("status") == "available" and row.get("table_class") == "complete_daily"}
    queries: list[dict[str, Any]] = []
    cumulative_dry_bytes = 0
    for dataset_id in DATASETS:
        for day in COMPLETE_DAYS:
            if (dataset_id, day) not in available:
                continue
            item = execute_one(client, dataset_id, day)
            queries.append(item)
            cumulative_dry_bytes += int(item.get("dry_run", {}).get("total_bytes_processed") or 0)
            if cumulative_dry_bytes > MAX_BYTES_PER_RUN:
                receipt["status"] = "blocked_run_cost"
                receipt["queries"] = queries
                receipt["inventory_file"] = str((OUT_DIR / "table_inventory.json").relative_to(ROOT))
                receipt["cumulative_dry_run_bytes"] = cumulative_dry_bytes
                receipt["cost_guard"] = {"maximum_bytes_per_query": MAX_BYTES_PER_QUERY, "maximum_bytes_per_run": MAX_BYTES_PER_RUN}
                RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                RESULTS_PATH.write_text(json.dumps(queries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(receipt, ensure_ascii=False, indent=2))
                return 1

    receipt["queries"] = queries
    receipt["inventory_file"] = str((OUT_DIR / "table_inventory.json").relative_to(ROOT))
    receipt["results_file"] = str(RESULTS_PATH.relative_to(ROOT))
    receipt["cumulative_dry_run_bytes"] = cumulative_dry_bytes
    receipt["aggregate_result_rows"] = sum(int(item.get("execution", {}).get("row_count") or 0) for item in queries)
    receipt["successful_query_count"] = sum(item.get("status") == "ok" for item in queries)
    receipt["failed_query_count"] = sum(item.get("status") not in {"ok"} for item in queries)
    receipt["cost_guard"] = {"maximum_bytes_per_query": MAX_BYTES_PER_QUERY, "maximum_bytes_per_run": MAX_BYTES_PER_RUN}
    receipt["status"] = "ok" if receipt["queries"] and receipt["failed_query_count"] == 0 else "degraded"
    RESULTS_PATH.write_text(json.dumps(queries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

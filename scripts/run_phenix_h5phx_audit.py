#!/usr/bin/env python3
"""Audit the exact p=h5phx channel marker with aggregate-only BigQuery queries."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from google.auth import default as default_credentials
from google.auth.transport.requests import Request
from google.cloud import bigquery


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "wajenigeria"
EU_LOCATION = "europe-west4"
US_LOCATION = "US"
MAX_BYTES_PER_QUERY = 5 * 1024**3
MAX_BYTES_PER_RUN = 25 * 1024**3
OUT_DIR = ROOT / "analysis/phenix_h5phx_audit_2026_09_03"
SQL_DIR = OUT_DIR / "sql"
RESULTS_PATH = OUT_DIR / "audit_results.json"
RECEIPT_PATH = OUT_DIR / "run_receipt.json"
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")

DATASETS = [
    "analytics_470712959",
    "analytics_504208609",
    "analytics_517134955",
    "analytics_546634805",
    "waje_ng_firebase_h5",
]
COMPLETE_DAYS = ["20260827", "20260828", "20260829", "20260830", "20260831", "20260901"]
INTRADAY_DAYS = ["20260902", "20260903"]


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
    result = subprocess.run(["python3", str(VALIDATOR), str(path)], capture_output=True, text=True, check=False)
    return {"status": "passed" if result.returncode == 0 else "failed", "returncode": result.returncode, "message": (result.stdout + result.stderr).strip()}


def firebase_sql(dataset_id: str, day: str) -> str:
    table_ref = f"`{PROJECT_ID}.{dataset_id}.events_{day}`"
    return f"""-- Exact p=h5phx aggregate audit for one complete Firebase day.
-- No event rows, URL values, parameter values or identifiers are returned.
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
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE LOWER(COALESCE(p.key, '')) = 'p'
    ) AS p_key_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE LOWER(COALESCE(p.key, '')) = 'p'
        AND LOWER(COALESCE(p.value.string_value, '')) = 'h5phx'
    ) AS p_exact_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(LOWER(COALESCE(p.value.string_value, '')), r'(^|[?&])p=h5phx([&#]|$)')
    ) AS p_url_marker_present,
    EXISTS (
      SELECT 1 FROM UNNEST(user_properties) p
      WHERE LOWER(COALESCE(p.key, '')) = 'p'
        AND LOWER(COALESCE(p.value.string_value, '')) = 'h5phx'
    ) AS user_property_p_exact_present,
    REGEXP_CONTAINS(
      LOWER(CONCAT(
        COALESCE(app_info.id, ''), '|', COALESCE(app_info.version, ''), '|',
        COALESCE(device.web_info.hostname, ''), '|', COALESCE(traffic_source.source, ''), '|',
        COALESCE(traffic_source.medium, ''), '|', COALESCE(collected_traffic_source.manual_source, ''), '|',
        COALESCE(collected_traffic_source.manual_medium, '')
      )),
      r'(h5phx|phenix)'
    ) AS package_or_source_marker_present,
    REGEXP_CONTAINS(
      LOWER(CONCAT(COALESCE(event_name, ''), '|', COALESCE(app_info.version, ''))),
      r'(h5phx|phenix)'
    ) AS event_or_version_marker_present,
    traffic_source.source IS NOT NULL AND traffic_source.source != '' AS first_source_present,
    collected_traffic_source.manual_source IS NOT NULL
      AND collected_traffic_source.manual_source != '' AS manual_source_present
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
    CASE
      WHEN manual_source IS NOT NULL AND manual_source != '' THEN manual_source
      WHEN first_source IS NOT NULL AND first_source != '' THEN first_source
      ELSE '(blank)'
    END AS observed_source,
    CASE
      WHEN manual_medium IS NOT NULL AND manual_medium != '' THEN manual_medium
      WHEN first_medium IS NOT NULL AND first_medium != '' THEN first_medium
      ELSE '(blank)'
    END AS observed_medium,
    p_key_present,
    p_exact_present,
    p_url_marker_present,
    user_property_p_exact_present,
    package_or_source_marker_present,
    event_or_version_marker_present,
    first_source_present,
    manual_source_present
  FROM base
)
SELECT
  platform,
  COALESCE(app_id, '(blank)') AS app_id,
  COALESCE(hostname, '(blank)') AS hostname,
  COALESCE(observed_source, '(blank)') AS observed_source,
  COALESCE(observed_medium, '(blank)') AS observed_medium,
  event_name,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) AS approx_subject_count,
  COUNTIF(p_key_present) AS p_key_present_count,
  COUNTIF(p_exact_present) AS p_exact_count,
  COUNTIF(p_url_marker_present) AS p_url_marker_count,
  COUNTIF(user_property_p_exact_present) AS user_property_p_exact_count,
  COUNTIF(package_or_source_marker_present) AS package_or_source_marker_count,
  COUNTIF(event_or_version_marker_present) AS event_or_version_marker_count,
  COUNTIF(first_source_present) AS first_source_present_count,
  COUNTIF(manual_source_present) AS manual_source_present_count,
  COUNTIF(event_name = 'first_visit') AS first_visit_event_count,
  COUNTIF(event_name = 'first_open') AS first_open_event_count,
  COUNTIF(event_name = 'session_start') AS session_start_event_count,
  COUNTIF(event_name = 'page_view') AS page_view_event_count
FROM normalized
GROUP BY platform, app_id, hostname, observed_source, observed_medium, event_name
HAVING APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) >= 10
ORDER BY event_count DESC, observed_source, event_name
LIMIT 3000
"""


def origin_web_sql() -> str:
    return """-- Exact p=h5phx marker audit in Origin realtime H5 events.
-- URL and parameter fields are searched but never returned.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
), base AS (
  SELECT
    target_day,
    event_type,
    user_id,
    event_id,
    session_id,
    utm_source,
    utm_medium,
    utm_campaign,
    REGEXP_CONTAINS(
      LOWER(CONCAT(
        COALESCE(url, ''), '|', COALESCE(element_target_url, ''), '|', COALESCE(url_path, ''), '|',
        COALESCE(path_name, ''), '|', COALESCE(referrer, ''), '|', COALESCE(latest_referrer, ''), '|',
        COALESCE(custom, ''), '|', COALESCE(elements, '')
      )),
      r'(^|[?&])p=h5phx([&#]|$)'
    ) AS p_url_marker_present,
    REGEXP_CONTAINS(
      LOWER(CONCAT(
        COALESCE(url, ''), '|', COALESCE(element_target_url, ''), '|', COALESCE(url_path, ''), '|',
        COALESCE(path_name, ''), '|', COALESCE(referrer, ''), '|', COALESCE(latest_referrer, ''), '|',
        COALESCE(custom, ''), '|', COALESCE(elements, ''), '|', COALESCE(utm_source, ''), '|',
        COALESCE(utm_medium, ''), '|', COALESCE(utm_campaign, ''), '|', COALESCE(traffic_source_type, '')
      )),
      r'(h5phx|phenix)'
    ) AS any_h5phx_marker_present
  FROM `wajenigeria.origin_hfyl.realtime_event_web`
  CROSS JOIN date_bounds
  WHERE target_day BETWEEN event_date AND DATE '2026-09-01'
)
SELECT
  target_day,
  COALESCE(NULLIF(event_type, ''), '(blank)') AS event_type,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count,
  COUNTIF(p_url_marker_present) AS p_url_marker_count,
  COUNTIF(any_h5phx_marker_present) AS any_h5phx_marker_count,
  COUNTIF(LOWER(COALESCE(utm_source, '')) = 'h5phx') AS utm_source_h5phx_count,
  COUNTIF(LOWER(COALESCE(utm_medium, '')) = 'h5phx') AS utm_medium_h5phx_count,
  COUNTIF(LOWER(COALESCE(utm_campaign, '')) = 'h5phx') AS utm_campaign_h5phx_count,
  COUNTIF(event_id IS NULL OR event_id = '') AS missing_event_id_count,
  COUNTIF(session_id IS NULL OR session_id = '') AS missing_session_id_count
FROM base
GROUP BY target_day, event_type
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY target_day, event_count DESC
LIMIT 3000
"""


def origin_change_sql() -> str:
    return """-- Exact h5phx marker audit in Origin attribution changes.
-- Field names, field values and user identifiers are not returned.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
)
SELECT
  target_day,
  COUNT(*) AS attribution_change_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(COALESCE(field_value, '')), r'(^|[^a-z0-9])(h5phx|phenix)([^a-z0-9]|$)')) AS h5phx_value_match_count
FROM `wajenigeria.origin_hfyl.realtime_attribution_change`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2026-09-01'
GROUP BY target_day
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY target_day
LIMIT 3000
"""


def origin_user_events_sql() -> str:
    return """-- Exact download_channel=h5phx aggregate check in the Origin user view.
-- Only channel-level counts are returned.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
)
SELECT
  target_day,
  LOWER(download_channel) AS observed_download_channel,
  COUNT(*) AS row_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count,
  COUNTIF(first_pay_date IS NOT NULL) AS first_pay_presence_count,
  COUNTIF(active_days IS NOT NULL AND active_days > 0) AS active_days_present_count
FROM `wajenigeria.origin_hfyl.user_events`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2026-09-01'
  AND LOWER(download_channel) IN ('h5phx', 'wajeh5phx', 'phenix')
GROUP BY target_day, observed_download_channel
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY target_day, observed_download_channel
LIMIT 3000
"""


def origin_90006_sql() -> str:
    return """-- Exact download_channel=h5phx aggregate check in the US-region Origin table.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
)
SELECT
  target_day,
  LOWER(download_channel) AS observed_download_channel,
  SUM(cost_amount) AS spend_amount,
  SUM(new_users_today) AS new_users,
  SUM(register_users) AS registered_users,
  SUM(pay_users_count) AS paying_users,
  SUM(first_pay_users) AS first_paying_users,
  COUNT(*) AS source_row_count
FROM `wajenigeria.90006.campaign_conversion_cost`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2026-09-02'
  AND LOWER(download_channel) IN ('h5phx', 'wajeh5phx', 'phenix')
GROUP BY target_day, observed_download_channel
ORDER BY target_day, observed_download_channel
LIMIT 3000
"""


def write_sql(path: Path, sql: str) -> dict[str, Any]:
    path.write_text(sql, encoding="utf-8")
    return {"sql_file": str(path.relative_to(ROOT)), "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(), "validation": validate_sql(path)}


def execute(client: bigquery.Client, path: Path, location: str, metadata: dict[str, Any]) -> dict[str, Any]:
    sql = path.read_text(encoding="utf-8").strip()
    item = {**metadata, "sql_file": str(path.relative_to(ROOT)), "query_location": location, "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(), "validation": validate_sql(path)}
    if item["validation"]["status"] != "passed":
        item["status"] = "blocked_sql_validation"
        return item
    try:
        dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=location)
        dry_bytes = int(dry.total_bytes_processed or 0)
        item["dry_run"] = {"status": "passed" if dry_bytes <= MAX_BYTES_PER_QUERY else "blocked_cost", "total_bytes_processed": dry_bytes, "maximum_bytes_billed": MAX_BYTES_PER_QUERY}
        if dry_bytes > MAX_BYTES_PER_QUERY:
            item["status"] = "blocked_cost"
            return item
        job = client.query(sql, job_config=bigquery.QueryJobConfig(use_legacy_sql=False, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=location)
        rows = [safe(dict(row.items())) for row in job.result(timeout=180)]
        item["status"] = "ok" if rows else "no_data"
        item["execution"] = {"job_id": job.job_id, "row_count": len(rows), "total_bytes_processed": int(job.total_bytes_processed or 0), "total_bytes_billed": int(job.total_bytes_billed or 0), "created": safe(job.created), "started": safe(job.started), "ended": safe(job.ended), "aggregate_rows": rows}
    except Exception as exc:
        item["status"] = "query_failed"
        item["error_type"] = type(exc).__name__
        item["error"] = str(exc)[:500]
    return item


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SQL_DIR.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {"run_id": "phenix_h5phx_audit_2026_09_03", "project_id": PROJECT_ID, "complete_day_window": ["2026-08-27", "2026-09-01"], "intraday_days_inventoried": ["2026-09-02", "2026-09-03"], "status": "not_started", "safety": {"aggregate_only": True, "raw_rows_saved": False, "raw_urls_saved": False, "event_parameter_values_saved": False, "user_identifiers_saved": False, "credentials_saved": False, "remote_systems_modified": False, "small_subject_groups_suppressed": True}}
    try:
        creds, adc_project = default_credentials(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not creds.valid:
            creds.refresh(Request())
        if not creds.valid:
            raise RuntimeError("ADC is not valid")
        receipt["auth"] = {"status": "valid", "credential_type": type(creds).__name__, "adc_project": adc_project}
        eu_client = bigquery.Client(project=PROJECT_ID, credentials=creds, location=EU_LOCATION)
        us_client = bigquery.Client(project=PROJECT_ID, credentials=creds, location=US_LOCATION)
    except Exception as exc:
        receipt["status"] = "blocked_authentication"
        receipt["auth"] = {"status": "blocked_authentication", "error_type": type(exc).__name__, "error": str(exc)[:500]}
        RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2

    inventory: list[dict[str, Any]] = []
    available: set[tuple[str, str]] = set()
    for dataset_id in DATASETS:
        for day in COMPLETE_DAYS:
            table_id = f"events_{day}"
            try:
                table = eu_client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
                row = {"dataset_id": dataset_id, "table_id": table_id, "event_day": day, "table_class": "complete_daily", "status": "available", "num_rows": table.num_rows, "num_bytes": table.num_bytes, "modified": safe(table.modified)}
                available.add((dataset_id, day))
            except Exception as exc:
                row = {"dataset_id": dataset_id, "table_id": table_id, "event_day": day, "table_class": "complete_daily", "status": "not_observed", "error_type": type(exc).__name__}
            inventory.append(row)
        for day in INTRADAY_DAYS:
            table_id = f"events_intraday_{day}"
            try:
                table = eu_client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
                row = {"dataset_id": dataset_id, "table_id": table_id, "event_day": day, "table_class": "intraday", "status": "available", "num_rows": table.num_rows, "num_bytes": table.num_bytes, "modified": safe(table.modified)}
            except Exception as exc:
                row = {"dataset_id": dataset_id, "table_id": table_id, "event_day": day, "table_class": "intraday", "status": "not_observed", "error_type": type(exc).__name__}
            inventory.append(row)
    (OUT_DIR / "table_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    results: list[dict[str, Any]] = []
    for dataset_id in DATASETS:
        for day in COMPLETE_DAYS:
            if (dataset_id, day) not in available:
                continue
            path = SQL_DIR / f"firebase_{dataset_id}_{day}_p_h5phx.sql"
            write_sql(path, firebase_sql(dataset_id, day))
            results.append(execute(eu_client, path, EU_LOCATION, {"source_kind": "firebase_analytics", "dataset_id": dataset_id, "event_day": day}))

    origin_specs = [
        ("origin_realtime_web_p_h5phx.sql", origin_web_sql(), eu_client, EU_LOCATION, {"source_kind": "origin_realtime_web"}),
        ("origin_attribution_changes_p_h5phx.sql", origin_change_sql(), eu_client, EU_LOCATION, {"source_kind": "origin_attribution_changes"}),
        ("origin_user_events_p_h5phx.sql", origin_user_events_sql(), eu_client, EU_LOCATION, {"source_kind": "origin_user_events_view"}),
        ("origin_90006_p_h5phx.sql", origin_90006_sql(), us_client, US_LOCATION, {"source_kind": "origin_90006_campaign_aggregate"}),
    ]
    for filename, sql, client, location, metadata in origin_specs:
        path = SQL_DIR / filename
        write_sql(path, sql)
        results.append(execute(client, path, location, metadata))

    dry_bytes = sum(int(item.get("dry_run", {}).get("total_bytes_processed") or 0) for item in results)
    receipt["inventory_file"] = str((OUT_DIR / "table_inventory.json").relative_to(ROOT))
    receipt["results_file"] = str(RESULTS_PATH.relative_to(ROOT))
    receipt["queries"] = results
    receipt["query_count"] = len(results)
    receipt["successful_or_expected_empty_count"] = sum(item.get("status") in {"ok", "no_data"} for item in results)
    receipt["failed_query_count"] = sum(item.get("status") not in {"ok", "no_data"} for item in results)
    receipt["dry_run_total_bytes"] = dry_bytes
    receipt["cost_guard"] = {"maximum_bytes_per_query": MAX_BYTES_PER_QUERY, "maximum_bytes_per_run": MAX_BYTES_PER_RUN}
    receipt["status"] = "ok" if receipt["query_count"] and receipt["failed_query_count"] == 0 and dry_bytes <= MAX_BYTES_PER_RUN else "degraded"
    RESULTS_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "query_count": receipt["query_count"], "successful_or_expected_empty_count": receipt["successful_or_expected_empty_count"], "failed_query_count": receipt["failed_query_count"], "dry_run_total_bytes": dry_bytes, "results_file": receipt["results_file"]}, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run bounded Origin channel/cohort cross-checks for the Phenix audit."""

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
LOCATION = "europe-west4"
MAX_BYTES_PER_QUERY = 5 * 1024**3
SQL_DIR = ROOT / "analysis/phenix_online_attribution_audit_2026_09_02/sql"
OUT_DIR = ROOT / "analysis/phenix_online_attribution_audit_2026_09_02"
RESULTS = OUT_DIR / "origin_crosscheck.json"
RECEIPT = OUT_DIR / "origin_crosscheck_receipt.json"
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")
SQL_FILES = [
    SQL_DIR / "origin_channel_aggregate.sql",
    SQL_DIR / "origin_cohort_aggregate.sql",
    SQL_DIR / "origin_source_freshness.sql",
    SQL_DIR / "origin_source_freshness_eu.sql",
    SQL_DIR / "origin_realtime_web_channel.sql",
    SQL_DIR / "origin_realtime_attribution_changes.sql",
    SQL_DIR / "origin_realtime_client_event_summary.sql",
]
QUERY_LOCATIONS = {
    "origin_channel_aggregate.sql": "US",
    "origin_source_freshness.sql": "US",
    "origin_cohort_aggregate.sql": "europe-west4",
    "origin_source_freshness_eu.sql": "europe-west4",
    "origin_realtime_web_channel.sql": "europe-west4",
    "origin_realtime_attribution_changes.sql": "europe-west4",
    "origin_realtime_client_event_summary.sql": "europe-west4",
}


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


def validate(path: Path) -> dict[str, Any]:
    result = subprocess.run(["python3", str(VALIDATOR), str(path)], capture_output=True, text=True, check=False)
    return {"status": "passed" if result.returncode == 0 else "failed", "returncode": result.returncode, "message": (result.stdout + result.stderr).strip()}


def execute(client: bigquery.Client, path: Path) -> dict[str, Any]:
    sql = path.read_text(encoding="utf-8").strip()
    query_location = QUERY_LOCATIONS[path.name]
    item: dict[str, Any] = {"sql_file": str(path.relative_to(ROOT)), "query_location": query_location, "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(), "validation": validate(path)}
    if item["validation"]["status"] != "passed":
        item["status"] = "blocked_sql_validation"
        return item
    try:
        dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=query_location)
        item["dry_run"] = {"status": "passed" if int(dry.total_bytes_processed or 0) <= MAX_BYTES_PER_QUERY else "blocked_cost", "total_bytes_processed": int(dry.total_bytes_processed or 0), "maximum_bytes_billed": MAX_BYTES_PER_QUERY}
        if item["dry_run"]["status"] != "passed":
            item["status"] = "blocked_cost"
            return item
        job = client.query(sql, job_config=bigquery.QueryJobConfig(use_legacy_sql=False, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=query_location)
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
    receipt: dict[str, Any] = {"run_id": "phenix_origin_crosscheck_2026_09_02", "project_id": PROJECT_ID, "location": LOCATION, "window": ["2026-08-27", "2026-09-02"], "status": "not_started", "safety": {"aggregate_only": True, "raw_rows_saved": False, "user_identifiers_saved": False, "credentials_saved": False, "remote_systems_modified": False}}
    try:
        creds, adc_project = default_credentials(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not creds.valid:
            creds.refresh(Request())
        if not creds.valid:
            raise RuntimeError("ADC is not valid")
        receipt["auth"] = {"status": "valid", "credential_type": type(creds).__name__, "adc_project": adc_project}
        client = bigquery.Client(project=PROJECT_ID, credentials=creds, location=LOCATION)
    except Exception as exc:
        receipt["status"] = "blocked_authentication"
        receipt["auth"] = {"status": "blocked_authentication", "error_type": type(exc).__name__, "error": str(exc)[:500]}
        RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2
    items = [execute(client, path) for path in SQL_FILES]
    total_dry = sum(int(item.get("dry_run", {}).get("total_bytes_processed") or 0) for item in items)
    receipt["queries"] = items
    receipt["query_locations"] = sorted({item.get("query_location") for item in items})
    receipt["total_dry_run_bytes"] = total_dry
    receipt["aggregate_result_rows"] = sum(int(item.get("execution", {}).get("row_count") or 0) for item in items)
    receipt["status"] = "ok" if all(item.get("status") in {"ok", "no_data"} for item in items) else "degraded"
    RESULTS.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt["results_file"] = str(RESULTS.relative_to(ROOT))
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

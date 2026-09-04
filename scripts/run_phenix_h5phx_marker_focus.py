#!/usr/bin/env python3
"""Run focused p=h5phx marker queries against Firebase Analytics."""

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
OUT_DIR = ROOT / "analysis/phenix_h5phx_audit_2026_09_03"
SQL_DIR = OUT_DIR / "sql"
RESULTS = OUT_DIR / "marker_focus_results.json"
RECEIPT = OUT_DIR / "marker_focus_receipt.json"
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")
SQL_FILES = [
    SQL_DIR / "firebase_analytics_504208609_p_h5phx_focus.sql",
    SQL_DIR / "firebase_analytics_517134955_p_h5phx_focus.sql",
    SQL_DIR / "firebase_waje_ng_firebase_h5_p_h5phx_focus.sql",
]


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
    item: dict[str, Any] = {"sql_file": str(path.relative_to(ROOT)), "query_location": LOCATION, "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(), "validation": validate(path)}
    if item["validation"]["status"] != "passed":
        item["status"] = "blocked_sql_validation"
        return item
    try:
        dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=LOCATION)
        dry_bytes = int(dry.total_bytes_processed or 0)
        item["dry_run"] = {"status": "passed" if dry_bytes <= MAX_BYTES_PER_QUERY else "blocked_cost", "total_bytes_processed": dry_bytes, "maximum_bytes_billed": MAX_BYTES_PER_QUERY}
        if dry_bytes > MAX_BYTES_PER_QUERY:
            item["status"] = "blocked_cost"
            return item
        job = client.query(sql, job_config=bigquery.QueryJobConfig(use_legacy_sql=False, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=LOCATION)
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
    receipt: dict[str, Any] = {"run_id": "phenix_h5phx_marker_focus_2026_09_03", "project_id": PROJECT_ID, "location": LOCATION, "marker": "p=h5phx", "status": "not_started", "safety": {"aggregate_only": True, "raw_rows_saved": False, "raw_urls_saved": False, "parameter_values_saved": False, "user_identifiers_saved": False, "credentials_saved": False, "remote_systems_modified": False, "small_subject_groups_suppressed": True}}
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
    results = [execute(client, path) for path in SQL_FILES]
    receipt["queries"] = results
    receipt["query_count"] = len(results)
    receipt["successful_or_expected_empty_count"] = sum(item.get("status") in {"ok", "no_data"} for item in results)
    receipt["failed_query_count"] = sum(item.get("status") not in {"ok", "no_data"} for item in results)
    receipt["dry_run_total_bytes"] = sum(int(item.get("dry_run", {}).get("total_bytes_processed") or 0) for item in results)
    receipt["results_file"] = str(RESULTS.relative_to(ROOT))
    receipt["status"] = "ok" if receipt["failed_query_count"] == 0 else "degraded"
    RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "query_count": receipt["query_count"], "successful_or_expected_empty_count": receipt["successful_or_expected_empty_count"], "failed_query_count": receipt["failed_query_count"], "dry_run_total_bytes": receipt["dry_run_total_bytes"], "results_file": receipt["results_file"]}, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

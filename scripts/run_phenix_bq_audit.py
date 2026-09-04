#!/usr/bin/env python3
"""Run the bounded enterprise BigQuery audit for wajeh5phx.

Only metadata and one-day aggregate counts are persisted.  The script never
prints or stores event rows, parameter keys/values, identifiers or tokens.
"""

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
SQL_ROOT = ROOT / "analysis/phenix_channel_retention_2026_09_02/sql"
OUTPUT = ROOT / "analysis/phenix_channel_retention_2026_09_02/bigquery_audit.json"
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")


def safe(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
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
    result: dict[str, Any] = {"id": path.stem, "sql_file": str(path.relative_to(ROOT)), "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(), "validation": validate(path)}
    if result["validation"]["status"] != "passed":
        result["status"] = "blocked_sql_validation"
        return result
    try:
        dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=LOCATION)
        result["dry_run"] = {"status": "passed", "total_bytes_processed": dry.total_bytes_processed, "maximum_bytes_billed": MAX_BYTES_PER_QUERY}
        job = client.query(sql, job_config=bigquery.QueryJobConfig(use_legacy_sql=False, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=LOCATION)
        rows = list(job.result(timeout=180))
        result["status"] = "ok" if rows else "no_data"
        result["execution"] = {"job_id": job.job_id, "row_count": len(rows), "total_bytes_processed": job.total_bytes_processed, "total_bytes_billed": job.total_bytes_billed, "created": safe(job.created), "started": safe(job.started), "ended": safe(job.ended), "aggregate_rows": [safe(dict(row.items())) for row in rows]}
    except Exception as exc:
        result["status"] = "query_failed"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:400]
    return result


def main() -> int:
    receipt: dict[str, Any] = {"run_id": "phenix_bq_audit_2026_09_02", "project_id": PROJECT_ID, "location": LOCATION, "business_timezone": "Africa/Lagos", "query_window": ["2026-08-27", "2026-08-27"], "status": "not_started", "queries": [], "safety": {"metadata_only_or_aggregate_only": True, "raw_rows_saved": False, "parameter_values_saved": False, "user_identifiers_saved": False, "credentials_saved": False, "remote_systems_modified": False}}
    try:
        credentials, adc_project = default_credentials(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not credentials.valid:
            credentials.refresh(Request())
        receipt["auth"] = {"status": "valid" if credentials.valid else "invalid", "credential_type": type(credentials).__name__, "adc_project": adc_project}
        if not credentials.valid:
            raise RuntimeError("ADC is not valid")
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
    except Exception as exc:
        receipt["status"] = "blocked_authentication"
        receipt["auth"] = {"status": "blocked_authentication", "error_type": type(exc).__name__, "error": str(exc)[:400]}
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2
    paths = [SQL_ROOT / "01_bq_h5_table_coverage.sql", SQL_ROOT / "02_bq_phx_marker_coverage.sql"]
    receipt["queries"] = [execute(client, path) for path in paths]
    receipt["dry_run_total_bytes"] = sum(int(item.get("dry_run", {}).get("total_bytes_processed") or 0) for item in receipt["queries"])
    receipt["aggregate_result_rows"] = sum(int(item.get("execution", {}).get("row_count") or 0) for item in receipt["queries"])
    receipt["status"] = "ok" if all(item.get("status") == "ok" for item in receipt["queries"]) else "degraded"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a bounded, read-only BigQuery Python client smoke test."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from google.auth import default as default_credentials
from google.auth.transport.requests import Request
from google.cloud import bigquery


ROOT = Path(__file__).resolve().parent
PROJECT_ID = "wajenigeria"
LOCATION = "europe-west4"
MAX_BYTES_BILLED = 5 * 1024**3


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    return str(value)


def query_hash(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def json_value(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


def row_to_safe_dict(row: bigquery.table.Row) -> dict[str, Any]:
    """Return only the already-aggregate smoke-test row."""
    return {str(key): json_value(value) for key, value in row.items()}


def execute_one(
    client: bigquery.Client,
    sql_path: Path,
    *,
    execute: bool,
) -> dict[str, Any]:
    sql = sql_path.read_text(encoding="utf-8").strip()
    digest = query_hash(sql)
    result: dict[str, Any] = {
        "id": sql_path.stem,
        "sql_file": str(sql_path.relative_to(ROOT.parent)),
        "query_sha256": digest,
        "location": LOCATION,
        "status": "prepared",
        "dry_run": None,
        "execution": None,
    }

    dry_config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,
        maximum_bytes_billed=MAX_BYTES_BILLED,
    )
    try:
        dry_job = client.query(sql, job_config=dry_config, location=LOCATION)
        result["dry_run"] = {
            "status": "passed",
            "job_id": dry_job.job_id,
            "total_bytes_processed": dry_job.total_bytes_processed,
            "maximum_bytes_billed": MAX_BYTES_BILLED,
        }
    except Exception as exc:  # API errors are recorded without credentials.
        result["status"] = "dry_run_failed"
        result["dry_run"] = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        return result

    if not execute:
        result["status"] = "dry_run_only"
        return result

    job_config = bigquery.QueryJobConfig(
        use_legacy_sql=False,
        use_query_cache=False,
        maximum_bytes_billed=MAX_BYTES_BILLED,
    )
    try:
        job = client.query(sql, job_config=job_config, location=LOCATION)
        rows = list(job.result(timeout=180))
        safe_rows = [row_to_safe_dict(row) for row in rows]
        result["status"] = "ok" if safe_rows else "no_data_or_empty_aggregate"
        result["execution"] = {
            "status": "ok" if safe_rows else "empty",
            "job_id": job.job_id,
            "row_count": len(safe_rows),
            "total_bytes_processed": job.total_bytes_processed,
            "total_bytes_billed": job.total_bytes_billed,
            "created": iso(job.created),
            "started": iso(job.started),
            "ended": iso(job.ended),
            "aggregate_rows": safe_rows,
        }
    except Exception as exc:  # Do not print SQL or credential material.
        result["status"] = "query_failed"
        result["execution"] = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Run the two bounded read-only queries after dry run.")
    parser.add_argument("--output", type=Path, default=ROOT / "client-test-receipt.json")
    args = parser.parse_args()

    receipt: dict[str, Any] = {
        "run_id": "android_bq_api_client_2026_08_27",
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "timezone": "Africa/Lagos",
        "client_library": "google-cloud-bigquery",
        "client_library_version": None,
        "auth": {"status": "not_checked", "credential_type": None, "adc_project_id": None},
        "queries": [],
        "data_rows_read": 0,
        "external_changes_made": False,
    }

    try:
        receipt["client_library_version"] = bigquery.__version__
        credentials, adc_project_id = default_credentials(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        receipt["auth"] = {
            "status": "resolved",
            "credential_type": type(credentials).__name__,
            "adc_project_id": adc_project_id,
        }
        if not credentials.valid:
            credentials.refresh(Request())
        receipt["auth"]["status"] = "valid" if credentials.valid else "invalid"
        client = bigquery.Client(
            project=PROJECT_ID,
            credentials=credentials,
            location=LOCATION,
        )
    except Exception as exc:
        receipt["status"] = "blocked_authentication"
        receipt["auth"] = {
            "status": "blocked_authentication",
            "credential_type": receipt["auth"].get("credential_type"),
            "adc_project_id": receipt["auth"].get("adc_project_id"),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2

    for filename in ("01_metadata_smoke.sql", "02_android_performance_smoke.sql"):
        result = execute_one(client, ROOT / "sql" / filename, execute=args.execute)
        receipt["queries"].append(result)
        execution = result.get("execution") or {}
        receipt["data_rows_read"] += int(execution.get("row_count") or 0)

    statuses = [str(item.get("status")) for item in receipt["queries"]]
    if not args.execute:
        receipt["status"] = "dry_run_passed" if all(status == "dry_run_only" for status in statuses) else "degraded"
    elif all(status == "ok" for status in statuses):
        receipt["status"] = "ok"
    elif any(status in {"query_failed", "dry_run_failed"} for status in statuses):
        receipt["status"] = "degraded"
    else:
        receipt["status"] = "no_data_or_partial"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] in {"ok", "dry_run_passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

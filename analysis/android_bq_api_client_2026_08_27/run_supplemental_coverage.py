#!/usr/bin/env python3
"""Run the low-cardinality Android Analytics coverage check through BigQuery API."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from google.auth import default as default_credentials
from google.auth.transport.requests import Request
from google.cloud import bigquery


ROOT = Path(__file__).resolve().parent
SQL_PATH = ROOT / "sql" / "03_android_analytics_coverage.sql"
OUTPUT = ROOT / "supplemental-coverage-receipt.json"
PROJECT_ID = "wajenigeria"
LOCATION = "europe-west4"
MAX_BYTES_BILLED = 5 * 1024**3


def json_value(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


def main() -> int:
    sql = SQL_PATH.read_text(encoding="utf-8").strip()
    receipt: dict[str, Any] = {
        "run_id": "android_analytics_coverage_2026_08_27",
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "timezone": "Africa/Lagos",
        "sql_file": str(SQL_PATH.relative_to(ROOT.parent)),
        "query_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "status": "not_started",
        "data_rows_read": 0,
        "external_changes_made": False,
    }
    try:
        credentials, adc_project_id = default_credentials(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        if not credentials.valid:
            credentials.refresh(Request())
        if not credentials.valid:
            raise RuntimeError("ADC did not produce valid credentials")
        receipt["auth"] = {
            "status": "valid",
            "credential_type": type(credentials).__name__,
            "adc_project_id": adc_project_id,
        }
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
        dry_config = bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
            maximum_bytes_billed=MAX_BYTES_BILLED,
        )
        dry_job = client.query(sql, job_config=dry_config, location=LOCATION)
        receipt["dry_run"] = {
            "status": "passed",
            "total_bytes_processed": dry_job.total_bytes_processed,
            "maximum_bytes_billed": MAX_BYTES_BILLED,
        }
        job_config = bigquery.QueryJobConfig(
            use_legacy_sql=False,
            use_query_cache=False,
            maximum_bytes_billed=MAX_BYTES_BILLED,
        )
        job = client.query(sql, job_config=job_config, location=LOCATION)
        rows = list(job.result(timeout=180))
        aggregate_rows = [json_value(dict(row.items())) for row in rows]
        receipt["status"] = "ok" if aggregate_rows else "no_data_or_empty_aggregate"
        receipt["data_rows_read"] = len(aggregate_rows)
        receipt["execution"] = {
            "job_id": job.job_id,
            "row_count": len(aggregate_rows),
            "total_bytes_processed": job.total_bytes_processed,
            "total_bytes_billed": job.total_bytes_billed,
            "created": json_value(job.created),
            "started": json_value(job.started),
            "ended": json_value(job.ended),
            "aggregate_rows": aggregate_rows,
        }
    except Exception as exc:
        receipt["status"] = "blocked_or_failed"
        receipt["error_type"] = type(exc).__name__
        receipt["error"] = str(exc)

    OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

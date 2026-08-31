#!/usr/bin/env python3
"""Run the bounded Android BigQuery SQL validation pack through the Python API."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from google.auth import default as default_credentials
from google.auth.transport.requests import Request
from google.cloud import bigquery


PROJECT_ID = "wajenigeria"
LOCATION = "europe-west4"
MAX_BYTES_PER_QUERY = 5 * 1024**3
MAX_BYTES_PER_RUN = 25 * 1024**3
SQL_ROOT = Path(__file__).resolve().parents[1] / "android_bq_api_validation_2026_08_27" / "sql"
OUTPUT_DEFAULT = Path(__file__).resolve().parent / "full-validation-receipt.json"
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    return str(value)


def safe_json(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_json(item) for item in value]
    return value


def validate_sql(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["python3", str(VALIDATOR), str(path)],
        text=True,
        capture_output=True,
    )
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "message": (result.stdout + result.stderr).strip(),
    }


def run_dry_run(client: bigquery.Client, path: Path) -> dict[str, Any]:
    sql = path.read_text(encoding="utf-8").strip()
    result: dict[str, Any] = {
        "id": path.stem,
        "file": str(path.relative_to(SQL_ROOT.parent.parent)),
        "query_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "static_validation": validate_sql(path),
    }
    if result["static_validation"]["status"] != "passed":
        result["status"] = "blocked_sql_validation"
        return result

    config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,
        maximum_bytes_billed=MAX_BYTES_PER_QUERY,
    )
    try:
        job = client.query(sql, job_config=config, location=LOCATION)
        result["status"] = "dry_run_passed"
        result["dry_run"] = {
            "total_bytes_processed": job.total_bytes_processed,
            "maximum_bytes_billed": MAX_BYTES_PER_QUERY,
        }
    except Exception as exc:
        result["status"] = "dry_run_failed"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def execute_query(client: bigquery.Client, path: Path, prior: dict[str, Any]) -> dict[str, Any]:
    sql = path.read_text(encoding="utf-8").strip()
    config = bigquery.QueryJobConfig(
        use_legacy_sql=False,
        use_query_cache=False,
        maximum_bytes_billed=MAX_BYTES_PER_QUERY,
    )
    result = dict(prior)
    try:
        job = client.query(sql, job_config=config, location=LOCATION)
        rows = list(job.result(timeout=180))
        result["status"] = "ok" if rows else "no_data_or_empty_aggregate"
        result["execution"] = {
            "job_id": job.job_id,
            "row_count": len(rows),
            "total_bytes_processed": job.total_bytes_processed,
            "total_bytes_billed": job.total_bytes_billed,
            "created": iso(job.created),
            "started": iso(job.started),
            "ended": iso(job.ended),
            "aggregate_rows": [safe_json(dict(row.items())) for row in rows],
        }
    except Exception as exc:
        result["status"] = "query_failed"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Execute queries after all dry runs pass and stay within budget.")
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()

    receipt: dict[str, Any] = {
        "run_id": "android_bq_api_full_validation_2026_08_27",
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "timezone": "Africa/Lagos",
        "window": {"start": "2026-08-20", "end": "2026-08-26"},
        "max_bytes_per_query": MAX_BYTES_PER_QUERY,
        "max_bytes_per_run": MAX_BYTES_PER_RUN,
        "auth": {"status": "not_checked"},
        "dry_run": {"status": "not_started", "total_bytes_processed": 0},
        "queries": [],
        "data_rows_read": 0,
        "external_changes_made": False,
    }

    try:
        credentials, adc_project_id = default_credentials(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        if not credentials.valid:
            credentials.refresh(Request())
        receipt["auth"] = {
            "status": "valid" if credentials.valid else "invalid",
            "credential_type": type(credentials).__name__,
            "adc_project_id": adc_project_id,
        }
        if not credentials.valid:
            raise RuntimeError("ADC did not produce valid credentials")
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
    except Exception as exc:
        receipt["status"] = "blocked_authentication"
        receipt["auth"] = {
            "status": "blocked_authentication",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2

    paths = sorted(SQL_ROOT.glob("*.sql"))
    dry_results = [run_dry_run(client, path) for path in paths]
    total = sum(int(item.get("dry_run", {}).get("total_bytes_processed") or 0) for item in dry_results)
    receipt["queries"] = dry_results
    receipt["dry_run"] = {
        "status": "passed" if all(item["status"] == "dry_run_passed" for item in dry_results) else "failed",
        "query_count": len(dry_results),
        "total_bytes_processed": total,
        "total_bytes_processed_gib": round(total / 1024**3, 4),
    }

    if receipt["dry_run"]["status"] != "passed":
        receipt["status"] = "blocked_dry_run"
    elif total > MAX_BYTES_PER_RUN:
        receipt["status"] = "blocked_cost"
        receipt["dry_run"]["budget_error"] = "aggregate dry-run estimate exceeds 25 GiB audit limit"
    elif not args.execute:
        receipt["status"] = "dry_run_passed"
    else:
        executed = []
        for path, prior in zip(paths, dry_results):
            result = execute_query(client, path, prior)
            executed.append(result)
            receipt["data_rows_read"] += int(result.get("execution", {}).get("row_count") or 0)
            if result["status"] in {"query_failed", "blocked_sql_validation"}:
                break
        receipt["queries"] = executed
        receipt["status"] = "ok" if len(executed) == len(paths) and all(item["status"] == "ok" for item in executed) else "degraded"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt["query_count"] = len(paths)
    receipt["source_sql_root"] = str(SQL_ROOT)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] in {"ok", "dry_run_passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

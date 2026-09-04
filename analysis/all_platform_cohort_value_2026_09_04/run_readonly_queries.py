#!/usr/bin/env python3
"""Execute reviewed aggregate-only BigQuery SQL for the refreshed cohort report.

The runner uses ADC from the active gcloud identity, dry-runs every statement,
limits each statement to 5 GiB and the whole run to 25 GiB, and writes only
aggregated query results and execution receipts.  It never persists identities,
orders, URLs, payment references, or credentials.
"""

from __future__ import annotations

import datetime as dt
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from google.auth import default as default_credentials
from google.auth.transport.requests import Request
from google.cloud import bigquery


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = Path(__file__).resolve().parent
SQL_DIR = ANALYSIS_DIR / "sql"
RESULTS_DIR = ANALYSIS_DIR / "results"
PROJECT_ID = "wajenigeria"
LOCATION = "europe-west4"
MAX_BYTES_PER_QUERY = 5 * 1024**3
MAX_BYTES_PER_RUN = 25 * 1024**3
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")


def safe(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe(v) for v in value]
    if hasattr(value, "items") and not isinstance(value, (str, bytes)):
        return {str(k): safe(v) for k, v in value.items()}
    return value


def validate_sql(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["python3", str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "message": (completed.stdout + completed.stderr).strip(),
    }


def execute(client: bigquery.Client, path: Path, cumulative_dry_bytes: int) -> tuple[dict[str, Any], int]:
    sql = path.read_text(encoding="utf-8").strip()
    item: dict[str, Any] = {
        "sql_file": str(path.relative_to(ROOT)),
        "sql_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "query_location": LOCATION,
        "validation": validate_sql(path),
    }
    if item["validation"]["status"] != "passed":
        item["status"] = "blocked_sql_validation"
        return item, cumulative_dry_bytes

    dry_job = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
            maximum_bytes_billed=MAX_BYTES_PER_QUERY,
        ),
        location=LOCATION,
    )
    dry_bytes = int(dry_job.total_bytes_processed or 0)
    cumulative_dry_bytes += dry_bytes
    item["dry_run"] = {
        "bytes_processed": dry_bytes,
        "limit_per_query": MAX_BYTES_PER_QUERY,
        "cumulative_bytes": cumulative_dry_bytes,
        "limit_per_run": MAX_BYTES_PER_RUN,
    }
    if dry_bytes > MAX_BYTES_PER_QUERY or cumulative_dry_bytes > MAX_BYTES_PER_RUN:
        item["status"] = "blocked_cost"
        return item, cumulative_dry_bytes

    job = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            use_legacy_sql=False,
            use_query_cache=False,
            maximum_bytes_billed=MAX_BYTES_PER_QUERY,
        ),
        location=LOCATION,
    )
    rows = [safe(dict(row.items())) for row in job.result(timeout=240)]
    item.update(
        {
            "status": "ok" if rows else "no_data",
            "execution": {
                "job_id": job.job_id,
                "row_count": len(rows),
                "bytes_processed": int(job.total_bytes_processed or 0),
                "bytes_billed": int(job.total_bytes_billed or 0),
                "created": safe(job.created),
                "started": safe(job.started),
                "ended": safe(job.ended),
            },
            "aggregate_rows": rows,
        }
    )
    return item, cumulative_dry_bytes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Run only the named SQL file(s), for example --only 02_h5_natural_lifecycle_value.sql.",
    )
    parser.add_argument(
        "--result-set",
        default="results",
        help="Subdirectory for an independently budgeted audit result set.",
    )
    args = parser.parse_args()
    if Path(args.result_set).name != args.result_set:
        raise SystemExit("--result-set must be a simple directory name")
    global RESULTS_DIR
    RESULTS_DIR = ANALYSIS_DIR / args.result_set
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "run_id": f"all_platform_cohort_value_2026_09_04_{args.result_set}",
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "status": "not_started",
        "safety": {
            "aggregate_only": True,
            "raw_user_rows_saved": False,
            "raw_order_rows_saved": False,
            "credentials_saved": False,
            "remote_systems_modified": False,
        },
        "queries": [],
    }
    try:
        credentials, adc_project = default_credentials(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not credentials.valid:
            credentials.refresh(Request())
        if not credentials.valid:
            raise RuntimeError("ADC did not produce a valid credential")
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
        receipt["auth"] = {"status": "valid", "adc_project": adc_project}
    except Exception as exc:
        receipt.update({"status": "blocked_authentication", "error_type": type(exc).__name__, "error": str(exc)[:360]})
        (RESULTS_DIR / "execution_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False))
        return 2

    total_dry_bytes = 0
    sql_paths = sorted(SQL_DIR.glob("*.sql"))
    if args.only:
        allowed = set(args.only)
        sql_paths = [path for path in sql_paths if path.name in allowed]
        missing = sorted(allowed - {path.name for path in sql_paths})
        if missing:
            raise SystemExit("Unknown SQL file(s): " + ", ".join(missing))
    for path in sql_paths:
        try:
            item, total_dry_bytes = execute(client, path, total_dry_bytes)
        except Exception as exc:
            item = {
                "sql_file": str(path.relative_to(ROOT)),
                "status": "query_failed",
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            }
        receipt["queries"].append(item)
        (RESULTS_DIR / f"{path.stem}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if item["status"] not in {"ok", "no_data"}:
            break

    receipt["total_dry_run_bytes"] = total_dry_bytes
    receipt["status"] = "ok" if receipt["queries"] and all(q["status"] in {"ok", "no_data"} for q in receipt["queries"]) else "degraded"
    (RESULTS_DIR / "execution_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "query_count": len(receipt["queries"]), "total_dry_run_bytes": total_dry_bytes}, ensure_ascii=False))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

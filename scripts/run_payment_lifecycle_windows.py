#!/usr/bin/env python3
"""Run aggregate-only lifecycle payment segmentation in cost-bounded date windows."""

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
MAX_BYTES_PER_RUN = 25 * 1024**3
ANALYSIS_DIR = ROOT / "analysis/all_platform_cohort_value_2026_09_03"
TEMPLATE = ANALYSIS_DIR / "sql/13_recent_old_payer_probe.sql"
SQL_DIR = ANALYSIS_DIR / "sql/payment_lifecycle_windows"
RESULTS_PATH = ANALYSIS_DIR / "results/13_payment_lifecycle_windows.json"
RECEIPT_PATH = ANALYSIS_DIR / "results/13_payment_lifecycle_windows_receipt.json"
CHUNK_DIR = ANALYSIS_DIR / "results/payment_lifecycle_windows"
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")

WINDOWS = [
    ("2026-06", "2026-06-01", "2026-06-30"),
    ("2026-07", "2026-07-01", "2026-07-31"),
    ("2026-08-a", "2026-08-01", "2026-08-15"),
    ("2026-08-b", "2026-08-16", "2026-08-31"),
    ("2026-09-mtd", "2026-09-01", "2026-09-02"),
]


def safe(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe(item) for item in value]
    if hasattr(value, "items") and not isinstance(value, (str, bytes)):
        return {str(key): safe(item) for key, item in value.items()}
    return value


def validate(path: Path) -> dict[str, Any]:
    result = subprocess.run(["python3", str(VALIDATOR), str(path)], capture_output=True, text=True, check=False)
    return {"status": "passed" if result.returncode == 0 else "failed", "message": (result.stdout + result.stderr).strip()}


def main() -> int:
    SQL_DIR.mkdir(parents=True, exist_ok=True)
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    template = TEMPLATE.read_text(encoding="utf-8")
    default_receipt: dict[str, Any] = {
        "run_id": "payment_lifecycle_windows_2026_09_03",
        "status": "not_started",
        "source": "origin_hfyl.view_event_pay + origin_hfyl.user_info_all",
        "definition": {
            "success_order": "event_type = order_success; deduplicate target_day x user_id x order_no using maximum order amount",
            "new_registered_payer": "register_date = payment_day",
            "historical_first_payer": "first_pay_date = payment_day",
            "old_payer_excluding_first_pay": "first_pay_date < payment_day",
        },
        "safety": {"aggregate_only": True, "user_rows_saved": False, "order_rows_saved": False, "credentials_saved": False, "remote_systems_modified": False},
        "windows": [],
    }
    receipt = default_receipt
    if RECEIPT_PATH.exists():
        existing = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        if existing.get("run_id") == default_receipt["run_id"]:
            receipt = existing
    try:
        credentials, adc_project = default_credentials(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not credentials.valid:
            credentials.refresh(Request())
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
        receipt["auth"] = {"status": "valid", "adc_project": adc_project}
    except Exception as exc:
        receipt.update({"status": "blocked_authentication", "error_type": type(exc).__name__, "error": str(exc)[:360]})
        RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2

    completed = {item["label"]: item for item in receipt.get("windows", []) if item.get("status") == "ok"}
    all_rows: list[dict[str, Any]] = []
    total_dry_bytes = sum(int(item.get("dry_run_bytes") or 0) for item in completed.values())
    for label, _, _ in WINDOWS:
        item = completed.get(label)
        if not item:
            continue
        chunk_path = CHUNK_DIR / f"{label}.json"
        try:
            if chunk_path.exists():
                saved = json.loads(chunk_path.read_text(encoding="utf-8"))
                rows = saved.get("rows", [])
            else:
                print(json.dumps({"stage": "recover_completed_job", "label": label, "job_id": item["job_id"]}, ensure_ascii=False), flush=True)
                job = client.get_job(item["job_id"], location=LOCATION)
                rows = [safe(dict(row.items())) for row in job.result(timeout=240)]
                chunk_path.write_text(json.dumps({"job_id": item["job_id"], "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            all_rows.extend([{**row, "source_window": label} for row in rows])
        except Exception as exc:
            receipt.update({"status": "blocked_recover_completed_window", "error_type": type(exc).__name__, "error": str(exc)[:360]})
            RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 3
    for label, start, end in WINDOWS:
        if label in completed:
            print(json.dumps({"stage": "skip_completed_window", "label": label}, ensure_ascii=False), flush=True)
            continue
        print(json.dumps({"stage": "start_window", "label": label, "start_date": start, "end_date": end}, ensure_ascii=False), flush=True)
        sql = template.replace("DATE '2026-08-27'", f"DATE '{start}'").replace("DATE '2026-09-02'", f"DATE '{end}'")
        sql_path = SQL_DIR / f"payment_lifecycle_{label}.sql"
        sql_path.write_text(sql, encoding="utf-8")
        item: dict[str, Any] = {
            "label": label,
            "start_date": start,
            "end_date": end,
            "sql_file": str(sql_path.relative_to(ROOT)),
            "sql_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            "validation": validate(sql_path),
        }
        if item["validation"]["status"] != "passed":
            item["status"] = "blocked_sql_validation"
            receipt["windows"].append(item)
            receipt["status"] = "blocked_sql_validation"
            RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 3
        try:
            dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=LOCATION)
            dry_bytes = int(dry.total_bytes_processed or 0)
            item["dry_run_bytes"] = dry_bytes
            total_dry_bytes += dry_bytes
            print(json.dumps({"stage": "dry_run", "label": label, "dry_run_bytes": dry_bytes, "total_dry_run_bytes": total_dry_bytes}, ensure_ascii=False), flush=True)
            if dry_bytes > MAX_BYTES_PER_QUERY or total_dry_bytes > MAX_BYTES_PER_RUN:
                item["status"] = "blocked_cost"
                receipt["windows"].append(item)
                receipt.update({"status": "blocked_cost", "total_dry_run_bytes": total_dry_bytes})
                RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                return 3
            job = client.query(sql, job_config=bigquery.QueryJobConfig(use_query_cache=False, maximum_bytes_billed=MAX_BYTES_PER_QUERY), location=LOCATION)
            rows = [safe(dict(row.items())) for row in job.result(timeout=240)]
            item.update({"status": "ok", "job_id": job.job_id, "processed_bytes": int(job.total_bytes_processed or 0), "row_count": len(rows)})
            all_rows.extend([{**row, "source_window": label} for row in rows])
            (CHUNK_DIR / f"{label}.json").write_text(json.dumps({"job_id": job.job_id, "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"stage": "window_complete", "label": label, "job_id": job.job_id, "row_count": len(rows)}, ensure_ascii=False), flush=True)
        except Exception as exc:
            item.update({"status": "query_failed", "error_type": type(exc).__name__, "error": str(exc)[:360]})
            receipt["windows"].append(item)
            receipt.update({"status": "query_failed", "total_dry_run_bytes": total_dry_bytes})
            RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 3
        receipt["windows"] = [existing for existing in receipt["windows"] if existing.get("label") != label]
        receipt["windows"].append(item)
        receipt.update({"status": "in_progress", "total_dry_run_bytes": total_dry_bytes, "aggregate_row_count": len(all_rows)})
        RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        RESULTS_PATH.write_text(json.dumps({"rows": all_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    RESULTS_PATH.write_text(json.dumps({"rows": all_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt.update({"status": "ok", "total_dry_run_bytes": total_dry_bytes, "aggregate_row_count": len(all_rows), "results": str(RESULTS_PATH.relative_to(ROOT))})
    RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "aggregate_row_count": len(all_rows), "total_dry_run_bytes": total_dry_bytes}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

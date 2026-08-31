#!/usr/bin/env python3
"""Run the approved INFORMATION_SCHEMA-only inventory SQL and save metadata.

This program is intentionally narrow: it submits two read-only metadata queries
to the `wajenigeria` execution project.  Each SQL file reads only BigQuery
INFORMATION_SCHEMA views and returns object/field metadata, never table rows.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PROJECT = "wajenigeria"
CONFIGURATION = "waje-enterprise-gemini"


def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def run_query(sql_file: Path, location: str) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
    environment = os.environ.copy()
    environment["CLOUDSDK_ACTIVE_CONFIG_NAME"] = CONFIGURATION
    environment["CLOUDSDK_CORE_DISABLE_PROMPTS"] = "1"
    completed = subprocess.run(
        [
            "bq",
            f"--project_id={PROJECT}",
            f"--location={location}",
            "query",
            "--use_legacy_sql=false",
            "--format=json",
            "--max_rows=200000",
        ],
        cwd=ROOT,
        env=environment,
        input=sql_file.read_text(encoding="utf-8"),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if completed.returncode:
        return None, {
            "sql_file": str(sql_file.relative_to(ROOT)),
            "location": location,
            "returncode": completed.returncode,
            "error": (completed.stderr or completed.stdout).strip()[:6000],
        }
    try:
        result = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as exc:
        return None, {
            "sql_file": str(sql_file.relative_to(ROOT)),
            "location": location,
            "returncode": 0,
            "error": f"invalid JSON response: {exc}",
        }
    if not isinstance(result, list):
        return None, {
            "sql_file": str(sql_file.relative_to(ROOT)),
            "location": location,
            "returncode": 0,
            "error": "metadata result was not an array",
        }
    return result, None


def main() -> int:
    started = timestamp()
    query_specs = [
        (ROOT / "sql" / "field_inventory_us.sql", "US"),
        (ROOT / "sql" / "field_inventory_europe_west4.sql", "europe-west4"),
    ]
    all_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    query_receipts: list[dict[str, Any]] = []
    for sql_file, location in query_specs:
        rows, issue = run_query(sql_file, location)
        if issue:
            issues.append(issue)
            query_receipts.append({"sql_file": issue["sql_file"], "location": location, "status": "blocked"})
            continue
        normalized = []
        for row in rows or []:
            copy = dict(row)
            copy["location"] = location
            normalized.append(copy)
        all_rows.extend(normalized)
        query_receipts.append({"sql_file": str(sql_file.relative_to(ROOT)), "location": location, "status": "ok", "row_count": len(normalized)})
    payload = {
        "schema_version": 1,
        "collection_type": "read_only_information_schema",
        "project_id": PROJECT,
        "gcloud_configuration": CONFIGURATION,
        "started_at": started,
        "completed_at": timestamp(),
        "privacy_boundary": {
            "source_objects": "INFORMATION_SCHEMA.TABLES and INFORMATION_SCHEMA.COLUMN_FIELD_PATHS only",
            "business_table_rows_read": False,
            "user_or_transaction_values_read": False,
            "sensitive_field_values_output": False,
        },
        "query_receipts": query_receipts,
        "access_issues": issues,
        "rows": all_rows,
    }
    (ROOT / "raw_metadata" / "field_inventory.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"field_metadata_rows": len(all_rows), "access_issue_count": len(issues)}, ensure_ascii=False))
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())

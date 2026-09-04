#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SQL_DIR = ROOT / "sql"
RESULT_DIR = ROOT / "results"
MAX_BYTES = 500 * 1024 * 1024


def run_bq(sql: str, dry_run: bool) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CLOUDSDK_ACTIVE_CONFIG_NAME"] = "waje-h5-readonly"
    cmd = [
        "bq",
        "query",
        "--project_id=waje-analytics-readonly",
        "--location=US",
        "--use_legacy_sql=false",
        "--format=json",
    ]
    if dry_run:
        cmd.append("--dry_run")
    else:
        cmd.append(f"--maximum_bytes_billed={MAX_BYTES}")
    return subprocess.run(cmd, input=sql, text=True, capture_output=True, env=env, check=False)


def parse_dry_run_bytes(text: str) -> int | None:
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            value = payload.get("statistics", {}).get("totalBytesProcessed")
            if value is not None:
                return int(value)
        if isinstance(payload, list) and payload:
            value = payload[0].get("statistics", {}).get("totalBytesProcessed")
            if value is not None:
                return int(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    match = re.search(r"process(?: upper bound of)? (\d+) bytes", text)
    return int(match.group(1)) if match else None


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "waje-analytics-readonly",
        "dataset": "analytics_504208609",
        "window": ["2026-08-21", "2026-08-27"],
        "privacy": "aggregate_only",
        "queries": [],
    }
    failed = False
    for path in sorted(SQL_DIR.glob("*.sql")):
        sql = path.read_text("utf-8")
        if re.search(r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|EXPORT|CALL)\b", sql, re.I):
            raise RuntimeError(f"unsafe SQL: {path.name}")
        dry = run_bq(sql, True)
        dry_text = f"{dry.stdout}\n{dry.stderr}"
        processed = parse_dry_run_bytes(dry_text)
        row: dict[str, object] = {
            "sql_file": path.name,
            "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(),
            "dry_run_exit": dry.returncode,
            "estimated_bytes": processed,
        }
        if dry.returncode != 0 or processed is None or processed > MAX_BYTES:
            row["status"] = "blocked_dry_run"
            row["message"] = dry_text[-1000:]
            failed = True
            receipt["queries"].append(row)
            continue
        result = run_bq(sql, False)
        row["query_exit"] = result.returncode
        if result.returncode != 0:
            row["status"] = "blocked_query"
            row["message"] = f"{result.stdout}\n{result.stderr}"[-1000:]
            failed = True
        else:
            data = json.loads(result.stdout or "[]")
            output = RESULT_DIR / f"{path.stem}.json"
            output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            row["status"] = "ok"
            row["rows"] = len(data)
            row["output"] = str(output.relative_to(ROOT))
        receipt["queries"].append(row)
    receipt["status"] = "degraded" if failed else "ok"
    (ROOT / "ga4_query_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": receipt["status"], "queries": len(receipt["queries"])}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

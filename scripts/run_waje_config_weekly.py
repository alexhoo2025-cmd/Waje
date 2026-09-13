#!/usr/bin/env python3
"""Run the Waje configuration-workbook weekly refresh."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from execution_graph_hook import emit as emit_execution_graph


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    execution_run_id = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    emit_execution_graph(
        ROOT,
        job_id="waje_config_weekly",
        run_id=execution_run_id,
        phase="started",
        status="started",
    )
    command = [sys.executable, str(ROOT / "scripts/waje_config_workbook.py"), "--date", args.date]
    if args.force:
        command.append("--force")
    returncode = subprocess.run(command, cwd=ROOT, check=False).returncode
    receipt = ROOT / "data/outputs/waje_config" / args.date / "run-log.json"
    status = "ok" if returncode == 0 else "failed"
    if receipt.exists():
        try:
            import json
            status = str(json.loads(receipt.read_text(encoding="utf-8")).get("status", status))
        except (OSError, json.JSONDecodeError):
            pass
    emit_execution_graph(
        ROOT,
        job_id="waje_config_weekly",
        run_id=execution_run_id,
        phase="finished",
        status=status,
        receipts=[str(receipt.relative_to(ROOT))] if receipt.exists() else [],
    )
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())

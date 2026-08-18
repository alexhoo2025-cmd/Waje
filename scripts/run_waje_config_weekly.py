#!/usr/bin/env python3
"""Run the Waje configuration-workbook weekly refresh."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    command = [sys.executable, str(ROOT / "scripts/waje_config_workbook.py"), "--date", args.date]
    if args.force:
        command.append("--force")
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

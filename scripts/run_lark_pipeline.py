#!/usr/bin/env python3
"""Run the local Lark read-only, silent ingestion pipeline."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(script: str, *args: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--source-dir", default=None)
    args = parser.parse_args()
    collect_args = ["--date", args.date]
    if args.source_dir:
        collect_args.extend(["--source-dir", args.source_dir])
    run("collect_lark_messages.py", *collect_args)
    run("parse_lark_messages.py", "--date", args.date)
    print(f"lark pipeline completed: {args.date}; outbound_actions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

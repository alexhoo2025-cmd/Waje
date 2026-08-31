#!/usr/bin/env python3
"""Write a safe, local preflight receipt for the Waje BigQuery MCP pilot."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.bigquery_mcp_policy import build_preflight, load_policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=ROOT / "config" / "bigquery_mcp_policy.json")
    parser.add_argument("--mcp-status", choices=["ok", "blocked_authentication", "blocked_iam", "not_checked"], default="not_checked")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    policy = load_policy(args.policy)
    receipt = build_preflight(policy, args.mcp_status)
    receipt["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    receipt["data_rows_read"] = False
    receipt["external_changes_made"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

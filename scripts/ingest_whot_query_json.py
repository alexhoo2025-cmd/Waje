#!/usr/bin/env python3
"""Validate and persist one aggregate-only BigQuery JSON result from stdin."""

from __future__ import annotations

import json
import sys
from pathlib import Path


FORBIDDEN_KEYS = {
    "user_id",
    "device_id",
    "order_id",
    "order_no",
    "cookie",
    "token",
    "raw_event",
    "event_params",
}


def walk(value: object) -> None:
    if isinstance(value, dict):
        keys = {str(key).lower() for key in value}
        forbidden = sorted(keys & FORBIDDEN_KEYS)
        if forbidden:
            raise ValueError(f"forbidden output keys: {', '.join(forbidden)}")
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ingest_whot_query_json.py OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    payload = json.load(sys.stdin)
    if not isinstance(payload, list):
        raise ValueError("aggregate query output must be a JSON list")
    walk(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "rows": len(payload)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

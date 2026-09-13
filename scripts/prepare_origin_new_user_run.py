#!/usr/bin/env python3
"""Validate immutable Origin exports and prepare a local workbook update run.

This does not transform source values.  It only establishes the 8-sheet,
43-field, contiguous-date contract, copies logical snapshots into a dated run
directory, and records any overlap changes against the last accepted run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import date, timedelta, datetime, timezone
from pathlib import Path


SHEETS = [
    "WajeSpecial-facebook",
    "WajeSpecial-googleadwords_int",
    "WajeSpecial-Google商店",
    "wajeios-AppStore商店",
    "wajebetH5-facebook",
    "pww",
    "wajeH5-fb",
    "wajeH5ga-googlewors_int",
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: object) -> object:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def make_dates(start_text: str, end_text: str) -> list[str]:
    current = date.fromisoformat(start_text)
    end = date.fromisoformat(end_text)
    output = []
    while current <= end:
        output.append(current.isoformat())
        current += timedelta(days=1)
    return output


def row_map(rows: list[list[object]], label: str) -> dict[str, list[object]]:
    result: dict[str, list[object]] = {}
    for row in rows:
        if not row or not row[0]:
            continue
        key = str(row[0])[:10]
        if key in result:
            raise ValueError(f"{label}: duplicate date {key}")
        result[key] = row
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--prior-source", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    args = parser.parse_args()

    raw_root = Path(args.raw_root).resolve()
    run_dir = Path(args.run_dir).resolve()
    prior = json.loads(Path(args.prior_source).read_text())
    expected_dates = make_dates(args.start_date, args.end_date)
    raw_input = run_dir / "raw-input"
    raw_input.mkdir(parents=True, exist_ok=False)

    headers_reference: list[object] | None = None
    validations: dict[str, object] = {}
    overlap: dict[str, object] = {}
    receipts: dict[str, object] = {}
    for sheet in SHEETS:
        source_file = raw_root / sheet / "source-data.json"
        if not source_file.is_file():
            raise ValueError(f"missing immutable source snapshot: {source_file}")
        raw_bytes = source_file.read_bytes()
        payload = json.loads(raw_bytes)
        headers = payload.get("headers")
        rows = payload.get("rows")
        if not isinstance(headers, list) or len(headers) != 43:
            raise ValueError(f"{sheet}: expected 43 headers")
        if not isinstance(rows, list):
            raise ValueError(f"{sheet}: rows absent")
        if headers_reference is None:
            headers_reference = headers
        elif headers != headers_reference:
            raise ValueError(f"{sheet}: header order differs from other Origin sheets")
        if any(not isinstance(row, list) or len(row) != 43 for row in rows):
            raise ValueError(f"{sheet}: source row width differs from 43")
        by_date = row_map(rows, sheet)
        observed_dates = sorted(by_date)
        if not set(expected_dates).issubset(by_date):
            raise ValueError(f"{sheet}: requested date coverage is incomplete")
        destination = raw_input / f"{sheet}.json"
        shutil.copy2(source_file, destination)
        validations[sheet] = {
            "status": "ok",
            "source_path": str(source_file),
            "source_sha256": sha256_bytes(raw_bytes),
            "archive_copy": str(destination),
            "source_date_count": len(by_date),
            "selected_date_count": len(expected_dates),
            "field_count": len(headers),
            "source_first_date": min(by_date),
            "source_last_date": max(by_date),
            "selected_first_date": expected_dates[0],
            "selected_last_date": expected_dates[-1],
            "source_extra_dates_not_used": [day for day in observed_dates if day not in expected_dates],
            "newest_sample": by_date[expected_dates[-1]][:7],
            "oldest_sample": by_date[expected_dates[0]][:7],
        }
        prior_rows = prior.get("sheets", {}).get(sheet, {}).get("rows", [])
        prior_by_date = row_map(prior_rows, f"prior/{sheet}")
        changed = []
        for day in expected_dates:
            if day not in prior_by_date:
                continue
            field_changes = []
            for index, (old, new) in enumerate(zip(prior_by_date[day], by_date[day])):
                if canonical(old) != canonical(new):
                    field_changes.append({"column_index": index + 1, "header": headers[index], "before": old, "after": new})
            if field_changes:
                changed.append({"date": day, "changed_field_count": len(field_changes), "changes": field_changes})
        overlap[sheet] = {
            "prior_overlap_dates": sorted(set(prior_by_date) & set(expected_dates)),
            "changed_dates": [item["date"] for item in changed],
            "changed_date_count": len(changed),
            "changed_field_count": sum(item["changed_field_count"] for item in changed),
            "changes": changed,
            "interpretation": "A source revision is recorded, not auto-classified as an error. Fresh browser filters, date coverage, and raw-export validation remain the acceptance gates.",
        }
        receipts[sheet] = {
            "source": payload.get("source"),
            "query": payload.get("query"),
            "validation": payload.get("validation"),
            "source_sha256": sha256_bytes(raw_bytes),
        }

    summary = {
        "schema_version": 1,
        "status": "ok",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "requested_dates": expected_dates,
        "sheet_count": len(SHEETS),
        "field_count": len(headers_reference or []),
        "all_sheets_contiguous": True,
    }
    (run_dir / "source-validation.json").write_text(json.dumps({**summary, "sheets": validations}, ensure_ascii=False, indent=2) + "\n")
    (run_dir / "overlap-reconciliation.json").write_text(json.dumps({"schema_version": 1, "status": "recorded", "sheets": overlap}, ensure_ascii=False, indent=2) + "\n")
    (run_dir / "query-receipts.json").write_text(json.dumps({"schema_version": 1, "status": "validated_raw_exports", "sheets": receipts}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "ok", "sheets": len(SHEETS), "dates": len(expected_dates), "raw_input": str(raw_input)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

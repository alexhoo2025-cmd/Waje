#!/usr/bin/env python3
"""Ingest explicitly mapped GM Lifecycle Pool v2 (Joint) exports.

The browser download directory is not treated as a data source.  A caller
must provide a date->table mapping so that every workbook is bound to the
business date and query receipt that produced it.  This keeps the raw layer
re-runnable and prevents a late download from being attached to the wrong
date.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


EXPECTED_HEADERS = {"summary": 10, "detail": 20, "game": 18, "active": 30}
EXPECTED_OUTPUT_ROWS = {"summary": 1, "detail": 155, "game": 31, "active": 4}
TABLE_KINDS = ("summary", "detail", "game", "active")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def read_table(path: Path) -> tuple[list[Any], list[list[Any]]]:
    workbook = load_workbook(path, data_only=False, read_only=True)
    sheet = workbook.active
    rows = [[json_value(value) for value in row] for row in sheet.iter_rows(values_only=True)]
    workbook.close()
    if not rows:
        raise ValueError(f"empty workbook: {path}")
    return rows[0], rows[1:]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--mapping", required=True, help="JSON date -> {kind: source path, metadata: ...}")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_root = Path(args.raw_root).expanduser().resolve()
    mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    if not mapping:
        raise ValueError("mapping is empty")

    run_receipts: dict[str, Any] = {}
    for business_date in sorted(mapping):
        entry = mapping[business_date]
        date_dir = raw_root / business_date
        date_dir.mkdir(parents=True, exist_ok=False)
        tables: dict[str, Any] = {"date": business_date, "headers": {}, "rows": {}}
        exports: dict[str, Any] = {}

        for kind in TABLE_KINDS:
            source = Path(entry[kind]).expanduser().resolve()
            if not source.is_file():
                raise FileNotFoundError(f"{business_date} {kind}: {source}")
            destination = date_dir / f"{kind}.xlsx"
            shutil.copy2(source, destination)
            headers, rows = read_table(destination)
            expected_cols = EXPECTED_HEADERS[kind]
            if len(headers) != expected_cols:
                raise ValueError(f"{business_date} {kind}: {len(headers)} columns != {expected_cols}")
            if any(len(row) != expected_cols for row in rows):
                raise ValueError(f"{business_date} {kind}: row width drift")
            tables["headers"][kind] = headers
            tables["rows"][kind] = rows
            exports[kind] = {
                "path": str(destination),
                "source_path": str(source),
                "sha256": sha256(destination),
                "source_sha256": sha256(source),
                "row_count": len(rows),
                "column_count": len(headers),
                "expected_output_rows": EXPECTED_OUTPUT_ROWS[kind],
            }

        detail_output_rows = [row for row in tables["rows"]["detail"] if _number(row[0]) is not None and 0 <= _number(row[0]) <= 4]
        active_output_rows = [row for row in tables["rows"]["active"] if _number(row[0]) is not None and 1 <= _number(row[0]) <= 4]
        if len(tables["rows"]["summary"]) != 1:
            raise ValueError(f"{business_date} summary must have 1 row")
        if len(tables["rows"]["game"]) != EXPECTED_OUTPUT_ROWS["game"]:
            raise ValueError(f"{business_date} game must have 31 rows")
        if len(detail_output_rows) != EXPECTED_OUTPUT_ROWS["detail"]:
            raise ValueError(f"{business_date} detail output rows {len(detail_output_rows)} != 155")
        if len(active_output_rows) != EXPECTED_OUTPUT_ROWS["active"]:
            raise ValueError(f"{business_date} active output rows {len(active_output_rows)} != 4")

        metadata = {
            "schema_version": 1,
            "source_url": entry.get("source_url", "https://prod-ac.waje-special.com:8443/sys/dynamic/lifecyclev2/pool/co"),
            "page_title": entry.get("page_title", "Lifecycle Pool v2 (Joint)"),
            "mode": entry.get("mode", "v2_joint"),
            "business_date": business_date,
            "selected_date": entry.get("selected_date", business_date),
            "query_submitted_at": entry.get("query_submitted_at"),
            "query_completed_at": entry.get("query_completed_at"),
            "status": entry.get("status", "complete"),
            "stable_reads": entry.get("stable_reads", 2),
            "loading_observed": entry.get("loading_observed", True),
            "auth_state": entry.get("auth_state", "authenticated"),
            "verification_note": entry.get("verification_note", "Exports were bound to the visible date and checked twice before ingest."),
        }
        receipt = {
            "schema_version": 1,
            "business_date": business_date,
            "source_url": metadata["source_url"],
            "mode": metadata["mode"],
            "selected_date": metadata["selected_date"],
            "query_submitted_at": metadata["query_submitted_at"],
            "query_completed_at": metadata["query_completed_at"],
            "stable_reads": metadata["stable_reads"],
            "status": metadata["status"],
            "row_counts": {kind: len(tables["rows"][kind]) for kind in TABLE_KINDS},
            "column_counts": {kind: len(tables["headers"][kind]) for kind in TABLE_KINDS},
            "output_row_counts": {
                "summary": len(tables["rows"]["summary"]),
                "detail": len(detail_output_rows),
                "game": len(tables["rows"]["game"]),
                "active": len(active_output_rows),
            },
            "exports": exports,
            "quality_gate": {
                "date_matches_request": metadata["selected_date"] == business_date,
                "joint_url": metadata["source_url"].rstrip("/").endswith("/sys/dynamic/lifecyclev2/pool/co"),
                "core_tables_present": all(len(tables["rows"][kind]) > 0 for kind in TABLE_KINDS),
                "header_widths_ok": all(len(tables["headers"][kind]) == EXPECTED_HEADERS[kind] for kind in TABLE_KINDS),
                "output_shapes_ok": {
                    "summary": len(tables["rows"]["summary"]),
                    "detail": len(detail_output_rows),
                    "game": len(tables["rows"]["game"]),
                    "active": len(active_output_rows),
                } == EXPECTED_OUTPUT_ROWS,
            },
        }
        if not all(receipt["quality_gate"].values()):
            raise ValueError(f"{business_date}: quality gate failed: {receipt['quality_gate']}")

        (date_dir / "tables.json").write_text(json.dumps(tables, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (date_dir / "page-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (date_dir / "query-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run_receipts[business_date] = receipt

    manifest = {
        "schema_version": 1,
        "status": "ok",
        "source": "GM Lifecycle Pool v2 (Joint)",
        "source_url": "https://prod-ac.waje-special.com:8443/sys/dynamic/lifecyclev2/pool/co",
        "mode": "v2_joint",
        "raw_root": str(raw_root),
        "dates": sorted(run_receipts),
        "dates_count": len(run_receipts),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date_receipts": run_receipts,
    }
    raw_root.mkdir(parents=True, exist_ok=True)
    (raw_root / "run-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "raw_root": str(raw_root), "dates": sorted(run_receipts)}, ensure_ascii=False, indent=2))


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()

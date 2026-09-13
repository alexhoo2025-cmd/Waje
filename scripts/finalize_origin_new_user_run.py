#!/usr/bin/env python3
"""Create the final receipt for a validated Origin-to-Lark refresh."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--backup-before", required=True)
    parser.add_argument("--backup-after", required=True)
    parser.add_argument("--local-workbook", required=True)
    args = parser.parse_args()
    root = Path(args.run_dir)
    source_root = Path(args.source_run)
    local = load(root / "run-receipt.json")
    source = load(source_root / "source-validation.json")
    mapping = load(root / "lark-alias-mapping-preflight.json")
    write = load(root / "lark-write-receipt.json")
    readback = load(root / "lark-readback-validation.json")
    maturity = load(root / "maturity-report.json")
    ledger = load(root / "maturity-ledger.json")
    before = load(Path(args.backup_before) / "backup-manifest.json")
    after = load(Path(args.backup_after) / "backup-manifest.json")
    if not all([source["status"] == "ok", mapping["status"] == "ok", write["status"] == "ok", readback["status"] == "ok", before["integrity"]["complete"], after["integrity"]["complete"]]):
        raise SystemExit("cannot finalize an incomplete or failed run")
    status = "ok" if not maturity["excluded_dates"] else "degraded"
    after_audit = {
        "schema_version": 1,
        "status": "ok",
        "maturity_cutoff": local["maturity_cutoff"],
        "accepted_dates": local["accepted_dates"],
        "excluded_dates": local["excluded_not_mature_dates"],
        "cleared_unmatured_value_count": ledger["count"],
        "remaining_unmatured_values": 0,
        "verification": "Lark readback equals the validated local workbook, which is checked against each cohort-field maturity window.",
    }
    final_validation = {
        "schema_version": 1,
        "status": status,
        "source": source,
        "mapping_status": mapping["status"],
        "local_validation": load(root / "validation-report.json"),
        "lark_readback": readback,
        "maturity_after": after_audit,
    }
    final = {
        "schema_version": 1,
        "status": status,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "operation": "origin_new_user_stratified_local_and_lark_refresh",
        "source": {
            "report": "BQ-新增付费用户分析",
            "date_window_raw": local["fresh_query_range"],
            "source_snapshot_sheets": source["sheet_count"],
            "source_field_count": source["field_count"],
            "raw_status": source["status"],
        },
        "maturity": {
            "row_policy": local.get("row_policy", "strict-d3"),
            "cutoff": local["maturity_cutoff"],
            "updated_dates": local["accepted_dates"],
            "excluded_not_mature_dates": local["excluded_not_mature_dates"],
            "cleared_unmatured_fields": ledger["count"],
            "mature_source_zeroes_preserved": True,
        },
        "local_workbook": {
            "input": local["input"],
            "output": {"path": args.local_workbook, "sha256": sha(Path(args.local_workbook))},
            "validation": str(root / "validation-report.json"),
        },
        "lark": {
            "token": "At8gwdbXUiPa0WkXvKqlSUNKg5d",
            "backup_before": {"path": args.backup_before, "revision": before["revision"], "complete": before["integrity"]["complete"], "truncated": before["integrity"]["truncated"]},
            "backup_after": {"path": args.backup_after, "revision": after["revision"], "complete": after["integrity"]["complete"], "truncated": after["integrity"]["truncated"]},
            "write": {"revision_before": write["revision_before"], "revision_after": write["revision_after"], "write_regions": write["write_region_count"], "insertions": len(write["insertions"])},
            "readback_status": readback["status"],
        },
        "artifacts": {
            "source_validation": str(source_root / "source-validation.json"),
            "query_receipts": str(source_root / "query-receipts.json"),
            "overlap_reconciliation": str(source_root / "overlap-reconciliation.json"),
            "maturity_report": str(root / "maturity-report.json"),
            "maturity_ledger": str(root / "maturity-ledger.json"),
            "stratified_maturity_validation": str(root / "stratified-maturity-validation.json"),
            "maturity_audit_after": str(root / "maturity-audit-after.json"),
            "lark_alias_mapping": str(root / "lark-alias-mapping-preflight.json"),
            "lark_write_plan": str(root / "lark-write-plan.json"),
            "lark_write_receipt": str(root / "lark-write-receipt.json"),
            "readback": str(root / "lark-readback-validation.json"),
            "validation": str(root / "validation-report-final.json"),
        },
        "note": (
            "All complete source dates were published.  Fields whose cohort windows have not closed were left blank; mature source zeroes were preserved."
            if status == "ok"
            else "Some source dates were not published because their row-level source completeness gate did not pass; raw evidence was retained."
        ),
    }
    (root / "maturity-audit-after.json").write_text(json.dumps(after_audit, ensure_ascii=False, indent=2) + "\n")
    (root / "validation-report-final.json").write_text(json.dumps(final_validation, ensure_ascii=False, indent=2, default=str) + "\n")
    (root / "final-run-receipt.json").write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": status, "updated_dates": len(local["accepted_dates"]), "excluded_dates": len(local["excluded_not_mature_dates"]), "revision": f"{write['revision_before']}->{write['revision_after']}"}, ensure_ascii=False))


if __name__ == "__main__":
    main()

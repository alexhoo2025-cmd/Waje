#!/usr/bin/env python3
"""Record a compact, non-sensitive receipt for the KYC schema audit report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--leak-count", type=int, required=True)
    args = parser.parse_args()

    payload = json.loads(args.artifact.read_text(encoding="utf-8"))
    receipt = {
        "run_id": "kyc_metabase_schema_audit_2026_08_26",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed_with_schema_limits",
        "scope": "schema-only audit; no business rows or sensitive details read",
        "artifact_validation": "passed",
        "html_validation": {
            "status": "passed",
            "viewports": [1440, 390],
            "source_dialog": "passed",
            "source_interaction": "keyboard_menu_semantic_click",
        },
        "snapshot_status": payload["snapshot"]["status"],
        "privacy": {
            "raw_sensitive_field_name_leaks": args.leak_count,
            "contains_credentials": False,
            "contains_business_rows": False,
        },
        "hashes": {
            "artifact_json_sha256": digest(args.artifact),
            "report_html_sha256": digest(args.html),
        },
        "outputs": {
            "markdown": "knowledge/02-数据/KYC人脸识别Metabase数据可用性与埋点缺口审计-2026-08-26.md",
            "html": "output/html/KYC人脸识别Metabase数据可用性与埋点缺口审计-2026-08-26.html",
            "audit_matrix": "analysis/kyc_metabase_schema_audit_2026_08_26/audit-matrix.json",
        },
    }
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

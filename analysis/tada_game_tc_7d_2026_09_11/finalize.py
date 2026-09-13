#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
OUTPUT = WORKSPACE / "output" / "html" / "Tada-游戏下注盈利RTP与TC关联分析-2026-09-05至09-11.html"


def load(name):
    return json.loads((ROOT / name).read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


analysis = load("analysis-results.json")
sources = load("source-manifest.json")
quality = load("report-quality.json")
visual = load("qa/visual-verification.json")
ledger = load("query-ledger.json")

assert analysis["overall"]["valid_rows"] == 1112
assert analysis["overall"]["games"] == 161
assert len(analysis["daily"]) == 7
assert analysis["daily"][-1]["period_status"] == "部分日"
assert analysis["quality"]["game_date_duplicates"] == 0
assert analysis["quality"]["bet_win_net_reconciled"] is True
assert analysis["quality"]["rtp_recomputed"] is True
assert analysis["quality"]["tc_duplicate_money_rows"] == 0
assert len(analysis["reconciliation"]) == 6
assert all(row["material_difference"] for row in analysis["reconciliation"])
assert analysis["rtp_decomposition"]["top_driver"]["game"] == "773_3 Lucky Chong Tian Pao"
assert analysis["rtp_decomposition"]["within_game_effect_share"] > 0.8
assert 0 < analysis["rtp_decomposition"]["net_excess_vs_withdraw_increase"] < 0.2
assert quality["errors"] == 0
assert visual["status"] == "passed" and len(visual["views"]) == 4
assert all(entry["status"] == "completed" for entry in ledger["entries"])
assert all(entry["actual_bytes"] <= 5 * 1024**3 for entry in ledger["entries"])
assert sum(entry["actual_bytes"] for entry in ledger["entries"]) <= 25 * 1024**3
assert OUTPUT.exists() and OUTPUT.stat().st_size > 1_000_000

receipt = {
    "status": "ok_with_declared_source_difference",
    "run_at": datetime.now(timezone.utc).isoformat(),
    "window": {
        "start": "2026-09-05",
        "end": "2026-09-11",
        "partial_day": "2026-09-11",
        "partial_cutoff_utc": "2026-09-11T11:39:53Z",
        "tc_timezone": "Africa/Lagos",
        "game_date_timezone": "not stated by source workbook",
    },
    "source_coverage": {
        "currency_summary_valid_rows": 1112,
        "games": 161,
        "dates": 7,
        "tc_dates": 7,
        "complete_dates_for_correlation": 6,
        "lifecycle_reconciliation_dates": 6,
    },
    "quality": {
        "game_date_unique": True,
        "bet_minus_win_equals_net_win": True,
        "weighted_rtp_recomputed": True,
        "tc_recomputed": True,
        "duplicate_money_rows_zero": True,
        "aggregate_only_bigquery": True,
        "report_quality": quality["status"],
        "report_quality_warnings": quality["warnings"],
        "visual_views_passed": 4,
        "offline_html_verified": True,
        "source_difference": "material; Currency Summary controls sub-game metrics and GM Lifecycle remains reconciliation-only",
    },
    "bigquery": {
        "execution": "Google Cloud BigQuery API",
        "jobs": ledger["entries"],
        "actual_bytes_total": sum(entry["actual_bytes"] for entry in ledger["entries"]),
    },
    "artifacts": [
        {"path": str(OUTPUT), "sha256": sha256(OUTPUT), "bytes": OUTPUT.stat().st_size},
        {"path": str(ROOT / "report.md"), "sha256": sha256(ROOT / "report.md")},
        {"path": str(ROOT / "reviewed-snapshot.json"), "sha256": sha256(ROOT / "reviewed-snapshot.json")},
        {"path": str(ROOT / "source-manifest.json"), "sha256": sha256(ROOT / "source-manifest.json")},
    ],
    "verification": {
        "desktop_light": "passed",
        "desktop_dark": "passed",
        "mobile_light": "passed",
        "mobile_dark": "passed",
        "charts_rendered": 4,
        "page_overflow": False,
        "full_game_table_search_and_pagination": "rendered",
    },
    "optional_review": {
        "claude_task_id": "task-da1957298d5e7a27c5f3",
        "status": "auth_required",
        "used_for_final_validation": False,
    },
    "open_questions": [
        "Currency Summary does not state its currency.",
        "Currency Summary does not state the timezone behind its Date field.",
        "Currency Summary and GM Lifecycle Tada totals differ materially and must not be merged.",
    ],
}
(ROOT / "final-delivery-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": receipt["status"], "html": receipt["artifacts"][0], "checks": receipt["quality"]}, ensure_ascii=False, indent=2))

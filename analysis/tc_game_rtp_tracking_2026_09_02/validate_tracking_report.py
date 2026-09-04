#!/usr/bin/env python3
"""Recompute and validate the aggregate-only V2 RTP report before handoff."""
from __future__ import annotations

import importlib.util
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
DATA = json.loads((ROOT / "report_data.json").read_text(encoding="utf-8"))
QUALITY = json.loads((ROOT / "quality_checks.json").read_text(encoding="utf-8"))
HTML = PROJECT / "output/html/Waje-全产品TC与新上线游戏RTP追踪分析-V2-2026-09-02.html"
MARKDOWN = PROJECT / "knowledge/02-数据/Waje-全产品TC与新上线游戏RTP追踪分析-V2-2026-09-02.md"
FEISHU = ROOT / "feishu_refresh_20260901_readback.json"
INDEX = PROJECT / "data/outputs/lifecycle_joint/2026-09-02-2d/lark-after/after-index.json"
TC = ROOT / "metabase_tc_2026_09_01.json"
OUT = ROOT / "validation_report.json"


def load_builder():
    spec = importlib.util.spec_from_file_location("tracker", ROOT / "build_tracking_report.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(a, b, tolerance=1e-9):
    return a is None and b is None or a is not None and b is not None and abs(a - b) <= tolerance


def main():
    checks: list[dict] = []
    build = load_builder()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    checks.append({"check": "source_revision", "passed": index["revision"] == 1588 == DATA["source"]["workbook_revision"], "actual": index["revision"]})

    all_records = [build.game_row(row) for row in build.annotated_rows(build.GAME_SOURCE)]
    raw = [row for row in all_records if build.ALL_START <= row["date"] <= build.AS_OF]
    usable = [row for row in raw if row["complete_bet"] > 0 and row["complete_actual_profit"] is not None]
    grouped = defaultdict(list)
    for row in usable:
        grouped[row["game"]].append(row)
    recomputed = {game: build.aggregate(rows) for game, rows in grouped.items()}
    report_games = {row["game"]: row for row in DATA["all_games_7d"]}
    checks.append({"check": "game_count", "passed": len(raw) == 217 and len(grouped) == 25 and len(report_games) == 25, "actual": {"raw_records": len(raw), "usable_games": len(grouped), "report_games": len(report_games)}})
    duplicate_keys = sorted({(row["date"].isoformat(), row["game"]) for row in raw if sum(1 for other in raw if other["date"] == row["date"] and other["game"] == row["game"]) > 1})
    checks.append({"check": "no_game_date_duplicates", "passed": not duplicate_keys, "actual": duplicate_keys})

    metric_failures = []
    fields = ["complete_bet", "complete_actual_profit", "actual_rtp", "expected_coverage", "expected_rtp", "rtp_gap_pp", "adjustment_pp"]
    for game, metric in recomputed.items():
        reported = report_games[game]
        for field in fields:
            if not close(metric.get(field), reported.get(field), 1e-8):
                metric_failures.append({"game": game, "field": field, "recomputed": metric.get(field), "reported": reported.get(field)})
    checks.append({"check": "all_game_recalculation", "passed": not metric_failures, "actual": metric_failures})

    new_failures = []
    required = {"Hilo": (date(2026, 8, 21), 12), "Plinko": (date(2026, 8, 21), 12), "Tower": (date(2026, 8, 25), 8)}
    for game, (start, days) in required.items():
        rows = [row for row in all_records if row["game"] == game and start <= row["date"] <= build.AS_OF and row["complete_bet"] > 0 and row["complete_actual_profit"] is not None]
        metric = build.aggregate(rows)
        reported = DATA["new_games"][game]
        for field in fields + ["days", "start", "end"]:
            if metric.get(field) != reported.get(field) if field in {"days", "start", "end"} else not close(metric.get(field), reported.get(field), 1e-8):
                new_failures.append({"game": game, "field": field, "recomputed": metric.get(field), "reported": reported.get(field)})
        if metric["days"] != days:
            new_failures.append({"game": game, "field": "expected_days", "recomputed": metric["days"], "reported": days})
    checks.append({"check": "new_game_window_recalculation", "passed": not new_failures, "actual": new_failures})

    expected = QUALITY["expected_valid_rows"]
    checks.append({"check": "expected_value_gate", "passed": expected == 154 and not QUALITY["raw_duplicate_game_date_keys"] and not QUALITY["duplicate_game_date_keys"], "actual": {"expected_valid_rows": expected, "invalid_keys": QUALITY["raw_duplicate_game_date_keys"] + QUALITY["duplicate_game_date_keys"]}})

    html_text = HTML.read_text(encoding="utf-8")
    md_text = MARKDOWN.read_text(encoding="utf-8")
    external_src = re.findall(r"<(?:script|link|img)\\b[^>]*(?:src|href)=['\"](https?://[^'\"]+)", html_text, flags=re.I)
    checks.append({"check": "offline_html", "passed": not external_src and "data:image/png;base64," in html_text, "actual": external_src})
    markdown_required = ["revision 1588", "2026-09-01", "分别观察12 / 12 / 8个完整自然日"]
    checks.append({"check": "markdown_core_values", "passed": all(value in md_text for value in markdown_required), "actual": {value: value in md_text for value in markdown_required}})

    tc = json.loads(TC.read_text(encoding="utf-8"))
    tc_current = tc["period_comparison"]["after_0829_0901"]
    tc_previous = tc["period_comparison"]["before_0825_0828"]
    tc_checks = (
        len(tc["daily"]) == 14 and tc["daily"][-1]["date"] == "2026-09-01"
        and close(tc_current["tc"], tc_current["withdraw"] / tc_current["recharge"], 1e-12)
        and close(tc_previous["tc"], tc_previous["withdraw"] / tc_previous["recharge"], 1e-12)
        and close(tc["period_comparison"]["tc_change_pp"], (tc_current["tc"] - tc_previous["tc"]) * 100, 1e-12)
    )
    checks.append({"check": "metabase_tc_refresh", "passed": tc_checks, "actual": {"cutoff": tc["cutoff"], "current_tc": tc_current["tc"], "previous_tc": tc_previous["tc"], "delta_pp": tc["period_comparison"]["tc_change_pp"]}})

    feishu_text = json.loads(FEISHU.read_text(encoding="utf-8"))["data"]["document"]["content"]
    feishu_required = ["Waje 全产品TC与新上线游戏RTP追踪分析 V2｜截至2026年9月1日", "76.97%", "-1.18pp", "96.55%", "Hilo、Plinko、Tower：上线后专项", "EasyWin｜30日独立观察", "Blackjack｜近7日独立观察", "Tower｜近7日独立观察", "Plinko｜近7日独立观察", "204.70%"]
    checks.append({"check": "feishu_readback", "passed": all(value in feishu_text for value in feishu_required) and feishu_text.count("<img") == 8, "actual": {"images": feishu_text.count("<img"), **{value: value in feishu_text for value in feishu_required}}})

    result = {"status": "passed" if all(check["passed"] for check in checks) else "failed", "checks": checks}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUMMARY = json.loads((ROOT / "results/reaudit_summary.json").read_text("utf-8"))
REPORT = (ROOT.parent.parent / "knowledge/01-产品/Waje-H5轻量化游戏首充用户路径分析-V5-2026-08-28.md").read_text("utf-8")

checks = []


def check(name: str, passed: bool, detail):
    checks.append({"check": name, "pass": bool(passed), "detail": detail})


pre, post = SUMMARY["master_overall"]
check("old_71_9_withdrawn", "71.9%的首充用户7天未玩”结论错误" in REPORT, None)
check("post_no_game_rate_4pct", abs(post["no_game_d7_rate"] - 0.0404014861) < 1e-8, post["no_game_d7_rate"])
check("post_rate_not_71_9", post["no_game_d7_rate"] < 0.1, post["no_game_d7_rate"])
check("master_count_conservation_pre", pre["game_d7_users"] + pre["no_game_d7_users"] == pre["users"], pre)
check("master_count_conservation_post", post["game_d7_users"] + post["no_game_d7_users"] == post["users"], post)
check("paid_free_funnel_rows", len(SUMMARY["new_paid_free_overall"]) == 4, len(SUMMARY["new_paid_free_overall"]))
check("zero_date_contradictions", all(r["contradictory_game_dates"] == 0 for r in SUMMARY["segment_rows"]), None)
check("report_has_channel_split", all(x in REPORT for x in ["H5自然", "H5 Facebook", "H5 Google"]), None)
check("report_has_paid_free_funnel", "当日新增首充与当日新增未付费对比" in REPORT, None)
check("chart_10_exists", (ROOT / "charts/10_首充用户7天无游戏记录复核.png").stat().st_size > 10000, None)
check("chart_11_exists", (ROOT / "charts/11_新增首充与新增未付费7天游戏参与.png").stat().st_size > 10000, None)

status = "passed" if all(item["pass"] for item in checks) else "failed"
receipt = {
    "status": status,
    "audit_type": "gamestart_coverage_and_paid_free_funnel",
    "controlling_source": "origin_hfyl.user_xlid first_game_date/last_game_date",
    "invalidated_metric": "71.9% first-pay users no GAMESTART within 7 days",
    "corrected_metric": {
        "pre_no_game_d7": pre["no_game_d7_rate"],
        "post_no_game_d7": post["no_game_d7_rate"],
    },
    "feishu_sync": "pending_browser_fallback_confirmation",
    "checks": checks,
}
(ROOT / "reaudit_validation.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": status, "checks": len(checks)}, ensure_ascii=False))
raise SystemExit(0 if status == "passed" else 1)

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"
REPORT = ROOT.parents[1] / "knowledge" / "01-产品" / "Waje-H5轻量化游戏首充用户路径分析-V5-2026-08-28.md"

summary = json.loads((RESULTS / "provisional_summary.json").read_text(encoding="utf-8"))
pre = pd.read_csv(RESULTS / "01_bq_first_pay_game_path_pre.csv")
post = pd.read_csv(RESULTS / "01_bq_first_pay_game_path_post.csv")
report_text = REPORT.read_text(encoding="utf-8")

checks = []

def add(name: str, passed: bool, detail=None):
    checks.append({"check": name, "pass": bool(passed), "detail": detail})

add("pre_share_sum", abs(pre.user_share.sum() - 1) < 1e-9, float(pre.user_share.sum()))
add("post_share_sum", abs(post.user_share.sum() - 1) < 1e-9, float(post.user_share.sum()))
add("pre_total", int(pre.first_pay_users.sum()) == summary["pre_first_pay_users"], int(pre.first_pay_users.sum()))
add("post_total", int(post.first_pay_users.sum()) == summary["post_first_pay_users"], int(post.first_pay_users.sum()))
add("no_game_direction", summary["no_game_7d_post"] < summary["no_game_7d_pre"], summary["no_game_7d_change_pp"])
add("report_core_numbers", all(value in report_text for value in ["71.9%", "73.6%", "16.6%", "15.2%", "27,245", "26,725", "6.27%", "2.26%", "0.98%", "0.55%", "31.4%", "30.1%", "32.2%", "30.9%", "70.7%", "26.0%", "14.0%", "20.2%", "65.8%", "84.2%"]))
add("report_status", "status: published_with_blocked_dimensions" in report_text)
add("report_names_limit", "不是轻量化单游戏" not in report_text or "全部GAMESTART" in report_text)

for name in ["01_首充用户路径结构.png", "02_首充后首次开局累计转化.png", "03_首充与开局事件规模指数.png", "04_T0-D15游戏复玩率.png", "05_关键日复玩率变化.png", "06_不同路径D7复充率.png", "07_首充用户累计复充率.png", "08_D7复充与首次开局顺序.png", "09_上线后各路径复充开局顺序.png"]:
    path = CHARTS / name
    add(f"chart:{name}", path.exists() and path.stat().st_size > 20_000, path.stat().st_size if path.exists() else 0)

for path in RESULTS.glob("*.csv"):
    try:
        columns = {c.lower() for c in pd.read_csv(path, nrows=1).columns}
    except pd.errors.EmptyDataError:
        columns = set()
    leaked = columns & {"user_id", "用户id", "gid", "order_id", "round_id", "device_id"}
    add(f"aggregate_only:{path.name}", not leaked, sorted(leaked))

status = "passed" if all(item["pass"] for item in checks) else "failed"
payload = {"status": status, "checks": checks}
(ROOT / "provisional_validation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2))
if status != "passed":
    raise SystemExit(1)

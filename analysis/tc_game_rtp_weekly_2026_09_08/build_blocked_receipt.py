#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
RAW = PROJECT / "data/raw/lifecycle_joint/2026-09-08-report"
DAILY = ROOT / "sources/metabase_tc_daily_2026-08-25_2026-09-07.csv"
CHANNELS = ROOT / "sources/metabase_tc_channels_top7_2026-08-25_2026-09-07.csv"
PRIOR = PROJECT / "data/outputs/lifecycle_joint/2026-09-07/source-data.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_header(value: object) -> str:
    return str(value).replace("\n", "").replace(" ", "")


def find_col(frame: pd.DataFrame, fragment: str) -> str:
    return next(c for c in frame.columns if fragment in compact_header(c))


def read_day(day: str) -> dict:
    folder = RAW / day
    frames = {name: pd.read_excel(folder / f"{name}.xlsx") for name in ("summary", "detail", "game", "active")}
    summary = frames["summary"]
    complete_bet_col = find_col(summary, "总完全下注额")
    people_col = find_col(summary, "总人数")
    summary_bet = float(summary.iloc[0][complete_bet_col])
    people = int(summary.iloc[0][people_col])
    totals = {}
    for name, frame in frames.items():
        frag = "总完全下注额" if name == "summary" else "完全下注额"
        col = find_col(frame, frag)
        totals[name] = float(pd.to_numeric(frame[col], errors="coerce").sum())
    return {
        "row_counts": {name: len(frame) for name, frame in frames.items()},
        "summary_complete_bet": summary_bet,
        "summary_people": people,
        "complete_bet_reconciliation": totals,
        "summary_vs_game_abs_delta": abs(totals["summary"] - totals["game"]),
        "summary_vs_active_abs_delta": abs(totals["summary"] - totals["active"]),
        "files": {name: {"path": str(folder / f"{name}.xlsx"), "sha256": sha(folder / f"{name}.xlsx")} for name in frames},
    }


def tc_week(rows: list[dict], start: str, end: str) -> dict:
    selected = [r for r in rows if start <= r["business_date"] <= end]
    recharge = sum(float(r["success_recharge_amount"]) for r in selected)
    withdraw = sum(float(r["success_withdraw_amount"]) for r in selected)
    return {"start": start, "end": end, "days": len(selected), "recharge": recharge, "withdraw": withdraw, "tc": withdraw / recharge if recharge else None}


def main() -> None:
    day3, day7 = read_day("2026-09-03"), read_day("2026-09-07")
    assert day3["row_counts"] == {"summary": 1, "detail": 372, "game": 31, "active": 11}
    assert day7["row_counts"] == {"summary": 1, "detail": 372, "game": 31, "active": 4}
    for day in (day3, day7):
        assert day["summary_vs_game_abs_delta"] < 0.01
        assert day["summary_vs_active_abs_delta"] < 0.01
        day["cross_table_status"] = "passed_summary_game_active"
    prior = json.loads(PRIOR.read_text())
    stable_days = [prior["dates"][d]["metrics"] for d in ("2026-09-04", "2026-09-05", "2026-09-06")]
    median_bet = statistics.median([day3["summary_complete_bet"]] + [x["total_full_bet"] for x in stable_days])
    median_people = statistics.median([day3["summary_people"]] + [x["total_people"] for x in stable_days])
    day7["volume_ratio_vs_recent_median"] = day7["summary_complete_bet"] / median_bet
    day7["people_ratio_vs_recent_median"] = day7["summary_people"] / median_people
    day7["stable_read_observed"] = True
    day7["quality_status"] = "not_mature"
    day7["quality_reason"] = "结构完整且45秒稳定，但完全下注和人数仅为9月3日至6日中位数的约4.8%和6.9%；与同日Metabase完整TC规模不一致。"

    tc_rows = list(csv.DictReader(DAILY.open()))
    assert [r["business_date"] for r in tc_rows] == [f"2026-08-{d:02d}" for d in range(25, 32)] + [f"2026-09-{d:02d}" for d in range(1, 8)]
    prev = tc_week(tc_rows, "2026-08-25", "2026-08-31")
    curr = tc_week(tc_rows, "2026-09-01", "2026-09-07")
    tc = {
        "status": "complete",
        "daily_row_count": len(tc_rows),
        "date_min": tc_rows[0]["business_date"],
        "date_max": tc_rows[-1]["business_date"],
        "previous_week": prev,
        "current_week": curr,
        "tc_change_pp": (curr["tc"] - prev["tc"]) * 100,
        "recharge_change": curr["recharge"] - prev["recharge"],
        "recharge_change_pct": curr["recharge"] / prev["recharge"] - 1,
        "withdraw_change": curr["withdraw"] - prev["withdraw"],
        "withdraw_change_pct": curr["withdraw"] / prev["withdraw"] - 1,
        "source_file": str(DAILY),
        "source_sha256": sha(DAILY),
    }
    channel_rows = list(csv.DictReader(CHANNELS.open()))
    assert len(channel_rows) == 7
    channel_summary = []
    for row in channel_rows:
        rp, wp, rc, wc = (float(row[k]) for k in ("recharge_prev", "withdraw_prev", "recharge_curr", "withdraw_curr"))
        channel_summary.append({"channel": row["channel"], "tc_prev": wp / rp, "tc_curr": wc / rc, "tc_change_pp": (wc / rc - wp / rp) * 100, "recharge_curr": rc})

    quality = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "blocked",
        "publication_allowed": False,
        "required_window": {"previous_week": ["2026-08-25", "2026-08-31"], "current_week": ["2026-09-01", "2026-09-07"]},
        "lifecycle": {"2026-09-03": {**day3, "quality_status": "complete"}, "2026-09-07": day7},
        "metabase_tc": tc,
        "channels_top7": channel_summary,
        "blockers": ["Lifecycle Pool v2 (Joint) 2026-09-07 snapshot is not mature enough for a complete seven-day game/RTP comparison."],
        "rules": ["missing or immature dates are never zero-filled", "formal weekly RTP conclusions require all seven current-week dates", "source workbook and original report remain unchanged"],
    }
    (ROOT / "quality-checks.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2))
    (ROOT / "weekly-tc-summary.json").write_text(json.dumps({"tc": tc, "channels_top7": channel_summary}, ensure_ascii=False, indent=2))
    receipt = {
        "schema_version": 1,
        "status": "blocked_source_not_mature",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "requested_report_title": "Waje 全产品TC与新上线游戏RTP周度对比分析 V3｜截至2026年9月7日",
        "original_report_unchanged": True,
        "new_lark_document_created": False,
        "reason": day7["quality_reason"],
        "completed": ["9月3日生命周期四表重查并通过结构、规模及汇总/分游戏/活跃勾稽", "9月7日生命周期四表导出并完成稳定读取与成熟度检查", "8月25日—9月7日全产品TC完整查询", "两周TC及Top7渠道聚合复算"],
        "next_action": "待Lifecycle Pool v2 (Joint)完成9月7日数据后，仅重查该日，再继续游戏RTP周度分析和飞书发布。",
        "artifacts": ["quality-checks.json", "weekly-tc-summary.json", "sources/", "queries/"],
    }
    (ROOT / "source-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
    report = f"""# Waje TC与游戏RTP周度报告｜数据准备状态

## 当前状态

正式周度RTP报告暂缓发布。9月3日已重新取得完整生命周期数据；9月7日快照虽结构完整且稳定，但总完全下注额仅{day7['summary_complete_bet']:,.2f}、总人数{day7['summary_people']:,}，分别约为近期完整日中位数的{day7['volume_ratio_vs_recent_median']:.1%}和{day7['people_ratio_vs_recent_median']:.1%}，不满足成熟度要求。

## 已完成的TC周度结果

- 9月1日—7日加权TC：{curr['tc']:.2%}；8月25日—31日：{prev['tc']:.2%}；变化{tc['tc_change_pp']:+.2f}个百分点。
- 本周成功充值{curr['recharge']:,.2f}，周环比{tc['recharge_change_pct']:+.2%}；成功提现{curr['withdraw']:,.2f}，周环比{tc['withdraw_change_pct']:+.2%}。

这些TC结果来自完整14日生产聚合，但不能替代缺失的9月7日游戏RTP事实。待源数据成熟后再生成正式飞书文档。
"""
    (ROOT / "blocked-status.md").write_text(report)
    print(json.dumps({"status": quality["status"], "day3_complete_bet": day3["summary_complete_bet"], "day7_complete_bet": day7["summary_complete_bet"], "day7_volume_ratio": day7["volume_ratio_vs_recent_median"], "tc_prev": prev["tc"], "tc_curr": curr["tc"], "tc_change_pp": tc["tc_change_pp"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "Currency_Summary_Report_2026-09-11_11-39-53.xlsx"
LIFECYCLE = ROOT / "source" / "新包生命周期V2 - 含联运2026.9.4-9.10_Joint修正版.xlsx"
LIFECYCLE_INSPECT = ROOT / "source" / "lifecycle-joint.inspect.ndjson"
QUERY_DIR = ROOT / "queries"
START = "2026-09-05"
END = "2026-09-11"
COMPLETE_END = "2026-09-10"
PARTIAL_CUTOFF = "2026-09-11T11:39:53Z"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pearson(xs, ys):
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else None


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j + 2) / 2
        for k in range(i, j + 1):
            result[order[k]] = avg
        i = j + 1
    return result


def pct(v, digits=2):
    return "N/A" if v is None else f"{v * 100:.{digits}f}%"


def change(v, digits=2):
    return "N/A" if v is None else f"{v * 100:+.{digits}f}%"


def amount(v):
    if v is None:
        return "N/A"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1e8:
        return f"{sign}{v / 1e8:.2f}亿"
    if v >= 1e4:
        return f"{sign}{v / 1e4:.2f}万"
    return f"{sign}{v:,.2f}"


def md_table(headers, rows):
    def esc(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---:" if index else "---" for index, _ in enumerate(headers)) + "|",
        *("| " + " | ".join(esc(value) for value in row) + " |" for row in rows),
    ])


def load_currency_rows():
    ws = load_workbook(SOURCE, read_only=True, data_only=True)["Summary"]
    rows = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        if not values[1] or not values[3]:
            continue
        bet = float(values[4] or 0)
        win = float(values[5] or 0)
        net = float(values[6] or 0)
        rows.append(
            {
                "api_id": str(values[0]),
                "game": str(values[1]),
                "game_type": str(values[2]),
                "date": str(values[3]),
                "bet": bet,
                "win": win,
                "net_win": net,
                "rtp": win / bet if bet else None,
                "total_count": int(values[8] or 0),
                "partial_day": str(values[3]) == END,
            }
        )
    return rows


def load_tc_rows():
    rows = []
    for path in sorted(QUERY_DIR.glob("0*_tada_tc_*.result.json")):
        rows.extend(json.loads(path.read_text())["rows"])
    return sorted(rows, key=lambda row: row["biz_date"])


def load_lifecycle_tada():
    for line in LIFECYCLE_INSPECT.open():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("kind") == "table" and obj.get("sheet") == "生命周期奖池分游戏汇总":
            headers = obj["values"][0]
            out = []
            for values in obj["values"][1:]:
                if len(values) < 19 or str(values[1]).lower() != "tada":
                    continue
                date_value = (datetime(1899, 12, 30) + timedelta(days=int(values[0]))).date().isoformat()
                if START <= date_value <= COMPLETE_END:
                    out.append(
                        {
                            "date": date_value,
                            "lifecycle_bet": float(values[12]),
                            "lifecycle_profit": float(values[14]),
                            "lifecycle_rtp": float(values[15]),
                        }
                    )
            return sorted(out, key=lambda row: row["date"])
    raise RuntimeError("Lifecycle Tada table not found in inspect snapshot")


raw = load_currency_rows()
tc_rows = load_tc_rows()
lifecycle_rows = load_lifecycle_tada()

assert len(raw) == 1112
assert sorted({row["date"] for row in raw}) == [
    "2026-09-05", "2026-09-06", "2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"
]
assert len({row["game"] for row in raw}) == 161
assert len({(row["game"], row["date"]) for row in raw}) == len(raw)
assert max(abs(row["bet"] - row["win"] - row["net_win"]) for row in raw) < 1e-5
assert len(tc_rows) == 7
assert all(row["duplicate_recharge_rows"] == 0 and row["duplicate_withdraw_rows"] == 0 for row in tc_rows)

daily_map = defaultdict(lambda: {"bet": 0.0, "win": 0.0, "net_win": 0.0, "total_count": 0, "games": 0})
game_map = defaultdict(lambda: {"bet": 0.0, "win": 0.0, "net_win": 0.0, "total_count": 0, "days": 0, "game_type": None})
category_map = defaultdict(lambda: {"bet": 0.0, "win": 0.0, "net_win": 0.0, "total_count": 0, "games": set()})

for row in raw:
    day = daily_map[row["date"]]
    day["bet"] += row["bet"]
    day["win"] += row["win"]
    day["net_win"] += row["net_win"]
    day["total_count"] += row["total_count"]
    day["games"] += 1
    game = game_map[row["game"]]
    game["bet"] += row["bet"]
    game["win"] += row["win"]
    game["net_win"] += row["net_win"]
    game["total_count"] += row["total_count"]
    game["days"] += 1
    game["game_type"] = row["game_type"]
    cat = category_map[row["game_type"]]
    cat["bet"] += row["bet"]
    cat["win"] += row["win"]
    cat["net_win"] += row["net_win"]
    cat["total_count"] += row["total_count"]
    cat["games"].add(row["game"])

tc_by_date = {row["biz_date"]: row for row in tc_rows}
daily = []
for date_value in sorted(daily_map):
    row = daily_map[date_value]
    tc = tc_by_date[date_value]
    daily.append(
        {
            "date": date_value,
            "period_status": "部分日" if date_value == END else "完整日",
            "partial_note": "截至12:39（拉各斯）" if date_value == END else None,
            "sep10_note": "TC与RTP同步高点" if date_value == COMPLETE_END else None,
            **row,
            "rtp": row["win"] / row["bet"],
            "profit_margin": row["net_win"] / row["bet"],
            "tada_bettors": tc["tada_bettors"],
            "recharge_users": tc["recharge_users"],
            "withdraw_users": tc["withdraw_users"],
            "recharge": tc["recharge"],
            "withdraw": tc["withdraw"],
            "tc_rate": tc["tc_rate"],
        }
    )

games = []
for game_name, row in game_map.items():
    games.append(
        {
            "game": game_name,
            "game_type": row["game_type"],
            "days": row["days"],
            "bet": row["bet"],
            "win": row["win"],
            "net_win": row["net_win"],
            "player_net_gain": max(-row["net_win"], 0),
            "rtp": row["win"] / row["bet"] if row["bet"] else None,
            "profit_margin": row["net_win"] / row["bet"] if row["bet"] else None,
            "total_count": row["total_count"],
        }
    )
games.sort(key=lambda row: row["bet"], reverse=True)
total_bet = sum(row["bet"] for row in games)
total_net = sum(row["net_win"] for row in games)
for index, row in enumerate(games, 1):
    row["bet_rank"] = index
    row["bet_share"] = row["bet"] / total_bet
    row["net_share"] = row["net_win"] / total_net if total_net else None

categories = []
for category, row in category_map.items():
    categories.append(
        {
            "game_type": category,
            "games": len(row["games"]),
            "bet": row["bet"],
            "win": row["win"],
            "net_win": row["net_win"],
            "rtp": row["win"] / row["bet"],
            "bet_share": row["bet"] / total_bet,
            "net_share": row["net_win"] / total_net if total_net else None,
            "total_count": row["total_count"],
        }
    )
categories.sort(key=lambda row: row["bet"], reverse=True)

weekly_player_gains = sorted((row for row in games if row["player_net_gain"] > 0), key=lambda row: row["player_net_gain"], reverse=True)
high_rtp = sorted(
    (row for row in games if row["rtp"] > 1 and row["total_count"] >= 10000 and row["bet"] >= 1_000_000),
    key=lambda row: row["player_net_gain"],
    reverse=True,
)
low_sample_high_rtp = sorted(
    (row for row in games if row["rtp"] > 1 and (row["total_count"] < 10000 or row["bet"] < 1_000_000)),
    key=lambda row: row["rtp"],
    reverse=True,
)

sep10 = [row for row in raw if row["date"] == COMPLETE_END]
sep10_losses = sorted(
    (
        {
            **row,
            "player_net_gain": max(-row["net_win"], 0),
        }
        for row in sep10
        if row["net_win"] < 0
    ),
    key=lambda row: row["player_net_gain"],
    reverse=True,
)

baseline_by_game = defaultdict(lambda: {"bet": 0.0, "win": 0.0, "days": 0})
sep10_by_game = {}
for row in raw:
    if START <= row["date"] <= "2026-09-09":
        baseline = baseline_by_game[row["game"]]
        baseline["bet"] += row["bet"]
        baseline["win"] += row["win"]
        baseline["days"] += 1
    elif row["date"] == COMPLETE_END:
        sep10_by_game[row["game"]] = row

rtp_drivers = []
for game_name, current in sep10_by_game.items():
    baseline = baseline_by_game[game_name]
    if baseline["bet"] <= 0:
        continue
    baseline_rtp = baseline["win"] / baseline["bet"]
    expected_win = current["bet"] * baseline_rtp
    excess_payout = current["win"] - expected_win
    rtp_drivers.append(
        {
            "game": game_name,
            "game_type": current["game_type"],
            "sep10_bet": current["bet"],
            "sep10_win": current["win"],
            "sep10_net_win": current["net_win"],
            "sep10_rtp": current["rtp"],
            "baseline_days": baseline["days"],
            "baseline_bet": baseline["bet"],
            "baseline_rtp": baseline_rtp,
            "rtp_change_pp": (current["rtp"] - baseline_rtp) * 100,
            "expected_win_at_baseline_rtp": expected_win,
            "excess_payout": excess_payout,
            "total_count": current["total_count"],
        }
    )
rtp_drivers.sort(key=lambda row: row["excess_payout"], reverse=True)

complete = [row for row in daily if row["date"] <= COMPLETE_END]
rtps = [row["rtp"] for row in complete]
tcs = [row["tc_rate"] for row in complete]
correlation = {
    "days": len(complete),
    "pearson_rtp_tc": pearson(rtps, tcs),
    "spearman_rtp_tc": pearson(ranks(rtps), ranks(tcs)),
    "pearson_bet_tc": pearson([row["bet"] for row in complete], tcs),
    "pearson_profit_tc": pearson([row["net_win"] for row in complete], tcs),
    "scope": "2026-09-05 through 2026-09-10 complete dates only",
}

prior5 = complete[:-1]
sep10_daily = complete[-1]
prior5_bet = statistics.fmean(row["bet"] for row in prior5)
prior5_win = statistics.fmean(row["win"] for row in prior5)
prior5_profit = statistics.fmean(row["net_win"] for row in prior5)
prior5_rtp = sum(row["win"] for row in prior5) / sum(row["bet"] for row in prior5)
prior5_tc = sum(row["withdraw"] for row in prior5) / sum(row["recharge"] for row in prior5)
sep10_change = {
    "bet_change": sep10_daily["bet"] / prior5_bet - 1,
    "win_change": sep10_daily["win"] / prior5_win - 1,
    "profit_change": sep10_daily["net_win"] / prior5_profit - 1,
    "rtp_change_pp": (sep10_daily["rtp"] - prior5_rtp) * 100,
    "tc_change_pp": (sep10_daily["tc_rate"] - prior5_tc) * 100,
    "recharge_change": sep10_daily["recharge"] / statistics.fmean(row["recharge"] for row in prior5) - 1,
    "withdraw_change": sep10_daily["withdraw"] / statistics.fmean(row["withdraw"] for row in prior5) - 1,
    "recharge_increase": sep10_daily["recharge"] - statistics.fmean(row["recharge"] for row in prior5),
    "withdraw_increase": sep10_daily["withdraw"] - statistics.fmean(row["withdraw"] for row in prior5),
}

expected_sep10_win_same_mix = sum(row["expected_win_at_baseline_rtp"] for row in rtp_drivers)
net_excess_payout = sum(row["excess_payout"] for row in rtp_drivers)
positive_excess_payout = sum(max(row["excess_payout"], 0) for row in rtp_drivers)
negative_excess_payout = sum(min(row["excess_payout"], 0) for row in rtp_drivers)
mix_expected_rtp = expected_sep10_win_same_mix / sep10_daily["bet"]
rtp_decomposition = {
    "baseline_rtp": prior5_rtp,
    "sep10_rtp": sep10_daily["rtp"],
    "total_change_pp": (sep10_daily["rtp"] - prior5_rtp) * 100,
    "mix_effect_pp": (mix_expected_rtp - prior5_rtp) * 100,
    "within_game_effect_pp": (sep10_daily["rtp"] - mix_expected_rtp) * 100,
    "mix_effect_share": (mix_expected_rtp - prior5_rtp) / (sep10_daily["rtp"] - prior5_rtp),
    "within_game_effect_share": (sep10_daily["rtp"] - mix_expected_rtp) / (sep10_daily["rtp"] - prior5_rtp),
    "net_excess_payout": net_excess_payout,
    "positive_excess_payout": positive_excess_payout,
    "negative_excess_payout": negative_excess_payout,
    "net_excess_vs_withdraw_increase": net_excess_payout / sep10_change["withdraw_increase"],
    "top_driver": rtp_drivers[0],
}

currency_by_date = {row["date"]: row for row in daily if row["date"] <= COMPLETE_END}
reconciliation = []
for row in lifecycle_rows:
    vendor = currency_by_date.get(row["date"])
    if not vendor:
        continue
    bet_diff = vendor["bet"] / row["lifecycle_bet"] - 1
    profit_diff = vendor["net_win"] / row["lifecycle_profit"] - 1 if row["lifecycle_profit"] else None
    rtp_diff_pp = (vendor["rtp"] - row["lifecycle_rtp"]) * 100
    reconciliation.append(
        {
            "date": row["date"],
            "vendor_bet": vendor["bet"],
            "lifecycle_bet": row["lifecycle_bet"],
            "bet_difference_pct": bet_diff,
            "vendor_profit": vendor["net_win"],
            "lifecycle_profit": row["lifecycle_profit"],
            "profit_difference_pct": profit_diff,
            "vendor_rtp": vendor["rtp"],
            "lifecycle_rtp": row["lifecycle_rtp"],
            "rtp_difference_pp": rtp_diff_pp,
            "material_difference": abs(bet_diff) > 0.005 or (profit_diff is not None and abs(profit_diff) > 0.005),
        }
    )

focus_names = []
for row in rtp_drivers[:8] + sorted(rtp_drivers, key=lambda item: item["excess_payout"])[:4]:
    if row["game"] not in focus_names:
        focus_names.append(row["game"])
heatmap = [
    {
        "date": row["date"],
        "game": row["game"],
        "rtp": row["rtp"],
        "bet": row["bet"],
        "net_win": row["net_win"],
        "partial_day": row["partial_day"],
    }
    for row in raw
    if row["game"] in focus_names
]

top5_share = sum(row["bet"] for row in games[:5]) / total_bet
top10_share = sum(row["bet"] for row in games[:10]) / total_bet
overall = {
    "date_start": START,
    "date_end": END,
    "partial_cutoff": PARTIAL_CUTOFF,
    "valid_rows": len(raw),
    "games": len(games),
    "bet": total_bet,
    "win": sum(row["win"] for row in games),
    "net_win": total_net,
    "rtp": sum(row["win"] for row in games) / total_bet,
    "profit_margin": total_net / total_bet,
    "total_count": sum(row["total_count"] for row in games),
    "top5_bet_share": top5_share,
    "top10_bet_share": top10_share,
    "partial_day_bet_share_vs_prior6_average": daily[-1]["bet"] / statistics.fmean(row["bet"] for row in complete),
}

analysis = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "status": "validated_with_partial_day_and_source_difference",
    "scope": {
        "date_start": START,
        "date_end": END,
        "complete_dates": [START, COMPLETE_END],
        "partial_date": END,
        "partial_cutoff_utc": PARTIAL_CUTOFF,
        "tc_timezone": "Africa/Lagos",
        "game_date_timezone": "not stated by source workbook",
        "amount_unit": "source report unit; currency not supplied",
    },
    "overall": overall,
    "daily": daily,
    "games": games,
    "categories": categories,
    "weekly_player_gains": weekly_player_gains,
    "high_rtp": high_rtp,
    "low_sample_high_rtp": low_sample_high_rtp,
    "sep10_player_gains": sep10_losses,
    "rtp_drivers": rtp_drivers,
    "rtp_decomposition": rtp_decomposition,
    "correlation": correlation,
    "sep10_change_vs_prior5": sep10_change,
    "reconciliation": reconciliation,
    "heatmap": heatmap,
    "quality": {
        "game_date_duplicates": 0,
        "bet_win_net_reconciled": True,
        "rtp_recomputed": True,
        "tc_duplicate_money_rows": 0,
        "aggregate_only_bigquery": True,
        "source_difference_threshold": 0.005,
    },
}
(ROOT / "analysis-results.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")

source_manifest = {
    "generated_at": analysis["generated_at"],
    "sources": [
        {
            "file": SOURCE.name,
            "sha256": sha256(SOURCE),
            "role": "controlling source for Tada sub-game bet, win, Net Win, RTP and Total Count",
            "range": "Summary!A1:I1114",
            "valid_rows": len(raw),
        },
        {
            "file": LIFECYCLE.name,
            "sha256": sha256(LIFECYCLE),
            "role": "secondary source reconciliation for Tada daily complete bet and actual profit",
        },
        {
            "file": LIFECYCLE_INSPECT.name,
            "sha256": sha256(LIFECYCLE_INSPECT),
            "role": "frozen inspected values used to read the lifecycle workbook reliably",
        },
    ],
    "bigquery_jobs": json.loads((ROOT / "query-ledger.json").read_text())["entries"],
}
(ROOT / "source-manifest.json").write_text(json.dumps(source_manifest, ensure_ascii=False, indent=2) + "\n")

file_source = {
    "label": "Tada Currency Summary｜2026-09-05至2026-09-11",
    "files": [SOURCE.name],
    "filters": ["API ID=10689_WAJE_Seamless", "日期=2026-09-05至2026-09-11", "金额单位沿用源报表", "2026-09-11为部分日"],
    "executedAt": analysis["generated_at"],
    "caveats": ["源文件未提供币种与日期时区。", "2026-09-11仅覆盖到2026-09-11T11:39:53Z。"],
}
tc_sql = "\n\n".join(path.read_text() for path in sorted(QUERY_DIR.glob("0*_tada_tc_*.sql")))
tc_source = {
    "label": "Google Cloud BigQuery API｜Tada参与用户同日资金事件",
    "tables": ["wajenigeria.origin_hfyl.view_event_server"],
    "sql": tc_sql,
    "filters": ["app_id=90006", "mode_id=11", "play_id=9150001—9159999", "Africa/Lagos业务日", "仅成功充值和成功提现", "机器人和测试用户排除"],
    "executedAt": max(entry["ended"] for entry in source_manifest["bigquery_jobs"]),
    "caveats": ["资金为Tada参与用户同日全部钱包行为，不是对子游戏的交易归因。", "2026-09-11使用源文件相同UTC截止时间。"],
}
lifecycle_source = {
    "label": "GM Lifecycle Pool v2 (Joint)｜Tada日汇总对账",
    "files": [LIFECYCLE.name, LIFECYCLE_INSPECT.name],
    "filters": ["游戏=Tada", "日期=2026-09-05至2026-09-10", "完全下注额与完全实际盈利"],
    "executedAt": "2026-09-11T10:43:00+08:00",
    "caveats": ["该来源仅用于口径对账，不与Currency Summary金额合并。"],
}

snapshot = {
    "id": "report:a26dff7b-0a6c-4fff-839c-4032d7c6df9d",
    "surface": "report",
    "title": "Tada TC升至87.40%：提现增速高，RTP异常集中于3 Lucky Chong Tian Pao",
    "generatedAt": analysis["generated_at"],
    "asOf": "2026-09-11",
    "buildStatus": "complete",
    "status": "provisional",
    "queries": {
        "daily_overview": {
            "rows": daily,
            "source": {
                **file_source,
                "metricDefinitions": [
                    {"label": "加权RTP", "definition": "同一范围内Total Win合计除以Total Bet合计。", "formula": "sum(win) / sum(bet)", "componentIds": ["summary", "daily-trends", "daily-table"]},
                    {"label": "平台净盈利", "definition": "Total Bet减Total Win，沿用源表Net Win定义。", "formula": "bet - win", "componentIds": ["summary", "daily-trends", "daily-table"]},
                ],
            },
        },
        "game_summary": {
            "rows": games,
            "source": {
                **file_source,
                "metricDefinitions": [
                    {"label": "玩家净赢", "definition": "游戏聚合后平台Net Win为负的绝对值。", "formula": "max(-net_win, 0)", "componentIds": ["game-ranking", "profit-loss", "game-table"]},
                    {"label": "下注份额", "definition": "单游戏Total Bet除以报告期全部Tada子游戏Total Bet。", "formula": "game_bet / total_bet", "componentIds": ["game-ranking", "game-table"]},
                ],
            },
        },
        "category_summary": {"rows": categories, "source": file_source},
        "tc_daily": {
            "rows": daily,
            "source": {
                **tc_source,
                "metricDefinitions": [
                    {"label": "Tada参与用户TC", "definition": "当日有Tada正向下注用户的同日成功提现额除以成功充值额。", "formula": "withdraw / recharge", "componentIds": ["summary", "tc-rtp-link", "tc-table"]}
                ],
            },
        },
        "anomalies": {"rows": weekly_player_gains, "source": file_source},
        "rtp_drivers": {
            "rows": rtp_drivers,
            "source": {
                **file_source,
                "metricDefinitions": [
                    {"label": "相对基线多派奖", "definition": "9月10日实际派奖减去按该游戏9月5—9日加权RTP计算的同下注额基准派奖。", "formula": "sep10_win - sep10_bet * baseline_rtp", "componentIds": ["summary", "rtp-driver", "driver-table"]},
                    {"label": "RTP抬升分解", "definition": "总RTP变化拆为游戏结构变化和同游戏RTP变化。", "componentIds": ["summary", "rtp-driver"]}
                ],
            },
        },
        "heatmap": {"rows": heatmap, "source": file_source},
        "reconciliation": {"rows": reconciliation, "source": lifecycle_source},
    },
    "analysis": {
        "overall": overall,
        "correlation": correlation,
        "sep10_change_vs_prior5": sep10_change,
        "high_rtp": high_rtp,
        "low_sample_high_rtp": low_sample_high_rtp,
        "sep10_player_gains": sep10_losses,
        "rtp_decomposition": rtp_decomposition,
        "focus_games": focus_names,
    },
}
(ROOT / "reviewed-snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")

top = games[0]
top_loss = weekly_player_gains[0]
sep10_loss = sep10_losses[0]
report_md = f"""# Tada TC升至87.40%：提现增速高，RTP异常集中于3 Lucky Chong Tian Pao

## 执行摘要

**TC异常的直接原因是提现增长快于充值。** 9月10日Tada参与用户提现较9月5—9日日均增加{change(sep10_change['withdraw_change'])}，充值增加{change(sep10_change['recharge_change'])}，TC因此上升{sep10_change['tc_change_pp']:.2f}个百分点至{pct(sep10_daily['tc_rate'])}。

**游戏侧RTP抬升主要来自同款游戏回报变化，3 Lucky Chong Tian Pao贡献最大。** 9月10日RTP上升{rtp_decomposition['total_change_pp']:.2f}个百分点，其中同游戏RTP变化贡献{rtp_decomposition['within_game_effect_share']:.1%}，游戏结构变化贡献{rtp_decomposition['mix_effect_share']:.1%}。3 Lucky Chong Tian Pao相对自身前5日RTP基线多派奖{amount(rtp_drivers[0]['excess_payout'])}。

**现有证据不能认定某款游戏直接造成TC异常。** 游戏侧净多派奖{amount(rtp_decomposition['net_excess_payout'])}，只相当于当日提现增量的{rtp_decomposition['net_excess_vs_withdraw_increase']:.1%}；资金记录也未绑定具体子游戏。该游戏是首要复核对象，不是已确认的提现来源。

## 01｜TC异常：提现增长是直接原因

{md_table(
    ['对比', '成功充值', '成功提现', 'TC'],
    [
        ['9月5—9日日均', amount(statistics.fmean(row['recharge'] for row in prior5)), amount(statistics.fmean(row['withdraw'] for row in prior5)), pct(prior5_tc)],
        ['9月10日', amount(sep10_daily['recharge']), amount(sep10_daily['withdraw']), pct(sep10_daily['tc_rate'])],
        ['变化', change(sep10_change['recharge_change']), change(sep10_change['withdraw_change']), f"+{sep10_change['tc_change_pp']:.2f}个百分点"],
    ]
)}

9月11日仅统计至{PARTIAL_CUTOFF}，不参与完整日趋势判断。

## 02｜游戏侧：RTP为何升高

在保持9月10日各游戏下注结构不变的情况下，按每款游戏9月5—9日自身加权RTP计算基准派奖。9月10日实际派奖较该基准多{amount(rtp_decomposition['net_excess_payout'])}。

{md_table(
    ['游戏', '9月10日RTP', '前5日RTP', 'RTP变化', '相对基线多/少派奖'],
    [[row['game'], pct(row['sep10_rtp']), pct(row['baseline_rtp']), f"{row['rtp_change_pp']:+.2f}个百分点", amount(row['excess_payout'])] for row in rtp_drivers[:10]]
)}

正向多派奖合计{amount(rtp_decomposition['positive_excess_payout'])}，被其他游戏少派奖{amount(abs(rtp_decomposition['negative_excess_payout']))}抵消后，净多派奖为{amount(rtp_decomposition['net_excess_payout'])}。

## 03｜具体异常游戏

**3 Lucky Chong Tian Pao是9月10日最主要的RTP抬升来源。** 当日下注{amount(rtp_drivers[0]['sep10_bet'])}，RTP由前5日{pct(rtp_drivers[0]['baseline_rtp'])}升至{pct(rtp_drivers[0]['sep10_rtp'])}，相对基线多派奖{amount(rtp_drivers[0]['excess_payout'])}，当日玩家净赢{amount(max(-rtp_drivers[0]['sep10_net_win'], 0))}。

其次是{rtp_drivers[1]['game']}、{rtp_drivers[2]['game']}和{rtp_drivers[3]['game']}。但X7 HOT当日相对自身基线少派奖{amount(abs(next(row for row in rtp_drivers if row['game'] == '680_X7 HOT')['excess_payout']))}，不是本次RTP抬升来源。

## 04｜结论：游戏RTP异常是核心原因，但不是全部原因

**分析判断（待验证）：将游戏RTP异常作为TC异常的核心原因假设，仍需核验派奖到提现的资金关联。**

9月5—10日六个完整日的RTP与TC Pearson相关为{correlation['pearson_rtp_tc']:.2f}，Spearman为{correlation['spearman_rtp_tc']:.2f}。样本短且共同受9月10日高点影响；用户可能同时玩其他游戏或提取历史余额，因此不能把提现增量分配到具体子游戏。

## 05｜行动

1. **优先复核3 Lucky Chong Tian Pao。** 核对9月10日最终派奖、取消退款、Bonus、版本和高倍结果。
2. **继续观察完整日TC。** 若后续仍显著高于9月5—9日水平，再拆解提现人数、金额分布和资金节奏。
3. **统一两套Tada金额口径。** Currency Summary与GM Lifecycle的每日下注差异为1.78%—5.41%，未完成结算状态、时区和Bonus范围对齐前不合并金额。

完整161款游戏、逐日RTP和来源对账保留在HTML报告附表。
"""
(ROOT / "report.md").write_text(report_md)

receipt = {
    "status": "ok",
    "run_at": analysis["generated_at"],
    "window": {"start": START, "end": END, "timezone": "source date labels; TC uses Africa/Lagos", "partial_cutoff_utc": PARTIAL_CUTOFF},
    "source_coverage": {"currency_rows": len(raw), "games": len(games), "dates": 7, "tc_dates": len(tc_rows), "lifecycle_reconciliation_dates": len(reconciliation)},
    "quality": analysis["quality"],
    "artifacts": ["analysis-results.json", "reviewed-snapshot.json", "report.md", "source-manifest.json"],
    "verification": {"formulas": "passed", "duplicate_keys": "passed", "report_render": "pending", "visual_qa": "pending"},
    "open_questions": ["Currency Summary does not state currency or date timezone.", "Currency Summary and GM Lifecycle use materially different Tada amount scopes."],
}
(ROOT / "analysis-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")

print(json.dumps({
    "status": analysis["status"],
    "overall": overall,
    "top_bet": games[:3],
    "top_player_gain": weekly_player_gains[:3],
    "sep10_top_player_gain": sep10_losses[:3],
    "correlation": correlation,
    "sep10_change": sep10_change,
    "reconciliation": reconciliation,
}, ensure_ascii=False, indent=2))

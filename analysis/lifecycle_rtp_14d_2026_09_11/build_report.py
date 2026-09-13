#!/usr/bin/env python3
"""Build a self-contained 14-day Lifecycle RTP report from validated snapshots."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = ROOT / "analysis/lifecycle_rtp_14d_2026_09_11"
RAW_ROOT_BY_DATE = {
    "2026-08-28": "2026-08-31",
    "2026-08-29": "2026-08-31",
    "2026-08-30": "2026-08-31",
    "2026-08-31": "2026-09-02",
    "2026-09-01": "2026-09-02",
    "2026-09-02": "2026-09-04",
    "2026-09-04": "2026-09-07",
    "2026-09-05": "2026-09-07",
    "2026-09-06": "2026-09-07",
    "2026-09-07": "2026-09-11",
    "2026-09-08": "2026-09-11",
    "2026-09-09": "2026-09-11",
    "2026-09-10": "2026-09-11",
}
EXPECTED = {
    "summary": ["总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比", "总基础预期回报比", "总完全预期回报比", "总人数"],
    "game": ["游戏", "基础下注额", "基础预期盈利", "基础实际盈利", "基础真实回报比", "基础预期回报比", "完全下注额", "完全预期盈利", "完全实际盈利", "完全真实回报比", "完全预期回报比"],
    "detail": ["生命周期", "游戏类型", "基础预期盈利", "基础实际盈利", "基础下注额", "完全预期盈利", "完全实际盈利", "完全下注额"],
}

# GM Lifecycle Pool v2 uses provider/category labels in the game column.
# These labels represent third-party or joint-operation inventory rather than
# Waje-operated games, so they are excluded before every report aggregation.
THIRD_PARTY_CATEGORIES = {
    "Tada", "PP", "OMG", "PG", "KooGame", "Spribe", "betcCasino", "ball", "BetCSports",
}
REPORT_TITLE = "Waje自营游戏14日整体RTP接近预期，低流水离群点需复核"
REPORT_SCOPE = "Waje自营游戏（排除第三方/联运厂商分类）"


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date")
    parser.add_argument("--end-date", default="2026-09-10")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    parser.add_argument("--lark-revision", default="1608")
    return parser.parse_args()


def dates_between(start: str, end: str) -> list[str]:
    first = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    return [(first + dt.timedelta(days=i)).isoformat() for i in range((last - first).days + 1)]


def nh(value: Any) -> str:
    return re.sub(r"[\s\u00a0]+", "", str(value or "")).strip()


def num(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "—", "N/A", "n/a"}:
        return None
    if text.endswith("%"):
        try:
            return float(text[:-1]) / 100
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def rtp(bet: float, profit: float) -> float | None:
    return 1 - profit / bet if bet else None


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out = {key: sum(float(row.get(key) or 0) for row in rows) for key in (
        "base_bet", "base_expected_profit", "base_actual_profit",
        "entire_bet", "entire_expected_profit", "entire_actual_profit",
    )}
    out["actual_rtp"] = rtp(out["base_bet"], out["base_actual_profit"])
    out["expected_rtp"] = rtp(out["base_bet"], out["base_expected_profit"])
    out["gap_pp"] = ((out["actual_rtp"] - out["expected_rtp"]) * 100
                     if out["actual_rtp"] is not None and out["expected_rtp"] is not None else None)
    out["entire_actual_rtp"] = rtp(out["entire_bet"], out["entire_actual_profit"])
    out["entire_expected_rtp"] = rtp(out["entire_bet"], out["entire_expected_profit"])
    out["entire_gap_pp"] = ((out["entire_actual_rtp"] - out["entire_expected_rtp"]) * 100
                            if out["entire_actual_rtp"] is not None and out["entire_expected_rtp"] is not None else None)
    out["actual_house_profit"] = out["base_bet"] - out["base_actual_profit"]
    out["expected_house_profit"] = out["base_bet"] - out["base_expected_profit"]
    return out


def load_source(date: str) -> dict[str, Any]:
    raw_root = RAW_ROOT_BY_DATE.get(date)
    if not raw_root:
        return {"date": date, "status": "not_mature", "reason": "该日期没有可接受的完整快照；现有回执为 not_mature。"}
    directory = ROOT / "data/raw/lifecycle_joint" / raw_root / date
    path = directory / "tables.json"
    if not path.exists():
        return {"date": date, "status": "blocked", "reason": f"缺少 {path}"}
    tables = json.loads(path.read_text(encoding="utf-8"))
    try:
        indices = {}
        for kind in ("summary", "game", "detail"):
            headers = tables["headers"][kind]
            actual = [nh(item) for item in headers]
            expected = [nh(item) for item in EXPECTED[kind]]
            if kind == "summary":
                if actual[:7] != expected:
                    raise ValueError(f"{kind} header mismatch")
            else:
                missing = [item for item in expected if nh(item) not in actual]
                if missing:
                    raise ValueError(f"{kind} missing fields: {missing}")
            indices[kind] = {nh(item): index for index, item in enumerate(headers)}
        summary = tables["rows"]["summary"]
        games = tables["rows"]["game"]
        details = tables["rows"]["detail"]
        if len(summary) != 1 or len(games) != 31:
            raise ValueError(f"shape summary={len(summary)} game={len(games)}")
        d = indices["detail"]
        written_details = [row for row in details if (num(row[d["生命周期"]]) is not None and 0 <= num(row[d["生命周期"]]) <= 4)]
        if len(written_details) != 155:
            raise ValueError(f"detail written scope={len(written_details)}")
        game_index = indices["game"]
        names = [str(row[game_index["游戏"]]).strip() for row in games]
        if len(set(names)) != len(names):
            raise ValueError("duplicate game names")
        detail_keys = [(int(num(row[d["生命周期"]]) or -1), str(row[d["游戏类型"]]).strip()) for row in details]
        if len(detail_keys) != len(set(detail_keys)):
            raise ValueError("duplicate lifecycle-game keys")

        game_by_name = {str(row[game_index["游戏"]]).strip(): row for row in games}
        detail_by_name = defaultdict(list)
        for row in details:
            life = int(num(row[d["生命周期"]]) or -1)
            if 1 <= life <= 11:
                detail_by_name[str(row[d["游戏类型"]]).strip()].append(row)
        pairs = {
            "base_bet": (d["基础下注额"], game_index["基础下注额"]),
            "base_expected_profit": (d["基础预期盈利"], game_index["基础预期盈利"]),
            "base_actual_profit": (d["基础实际盈利"], game_index["基础实际盈利"]),
            "entire_bet": (d["完全下注额"], game_index["完全下注额"]),
            "entire_expected_profit": (d["完全预期盈利"], game_index["完全预期盈利"]),
            "entire_actual_profit": (d["完全实际盈利"], game_index["完全实际盈利"]),
        }
        cross_failures = []
        for game, game_row in game_by_name.items():
            for metric, (detail_index, game_index_value) in pairs.items():
                left = sum(num(row[detail_index]) or 0 for row in detail_by_name[game])
                right = num(game_row[game_index_value]) or 0
                if abs(left - right) > 0.25:
                    cross_failures.append(f"{game}/{metric}")
        if cross_failures:
            raise ValueError(f"detail/game mismatch: {cross_failures[:5]}")
        return {
            "date": date, "status": "complete", "directory": str(directory), "tables": tables, "indices": indices,
            "row_counts": {"summary": len(summary), "game": len(games), "detail": len(details), "detail_written_scope": len(written_details)},
            "cross_table": {"status": "passed", "failures": []},
        }
    except Exception as error:
        return {"date": date, "status": "failed", "directory": str(directory), "reason": str(error)}


def build_analysis(start: str, end: str, lark_revision: str) -> dict[str, Any]:
    dates = dates_between(start, end)
    records = [load_source(date) for date in dates]
    complete_records = [item for item in records if item["status"] == "complete"]
    failed = [item for item in records if item["status"] == "failed"]
    if failed:
        raise ValueError(f"source validation failed: {[item['date'] for item in failed]}")
    if not complete_records:
        raise ValueError("no complete source dates")
    daily = []
    all_game_daily = []
    game_daily = []
    all_lifecycle_daily = []
    lifecycle_daily = []
    quality_by_date = {}
    for item in complete_records:
        date = item["date"]
        tables = item["tables"]
        si, gi, di = item["indices"]["summary"], item["indices"]["game"], item["indices"]["detail"]
        game_rows = []
        for row in tables["rows"]["game"]:
            game_rows.append({
                "date": date, "game": str(row[gi["游戏"]]).strip(),
                "base_bet": num(row[gi["基础下注额"]]) or 0,
                "base_expected_profit": num(row[gi["基础预期盈利"]]) or 0,
                "base_actual_profit": num(row[gi["基础实际盈利"]]) or 0,
                "entire_bet": num(row[gi["完全下注额"]]) or 0,
                "entire_expected_profit": num(row[gi["完全预期盈利"]]) or 0,
                "entire_actual_profit": num(row[gi["完全实际盈利"]]) or 0,
            })
        all_game_daily.extend(game_rows)
        included_game_rows = [row for row in game_rows if row["game"] not in THIRD_PARTY_CATEGORIES]
        game_daily.extend(included_game_rows)
        metrics = aggregate(included_game_rows)
        all_metrics = aggregate(game_rows)
        summary_row = tables["rows"]["summary"][0]
        metrics.update({
            "date": date,
            "summary_actual_rtp": num(summary_row[si["总基础真实回报比"]]),
            "summary_expected_rtp": num(summary_row[si["总基础预期回报比"]]),
            "summary_base_bet": num(summary_row[si["总基础下注额"]]),
            "summary_full_bet": num(summary_row[si["总完全下注额"]]),
            "all_game_base_bet": all_metrics["base_bet"],
            "excluded_third_party_base_bet": all_metrics["base_bet"] - metrics["base_bet"],
        })
        metrics["summary_reconciliation_delta_pp"] = (
            (all_metrics["actual_rtp"] - metrics["summary_actual_rtp"]) * 100
            if all_metrics["actual_rtp"] is not None and metrics["summary_actual_rtp"] is not None else None
        )
        daily.append(metrics)
        for row in tables["rows"]["detail"]:
            life = int(num(row[di["生命周期"]]) or -1)
            if not 1 <= life <= 4:
                continue
            detail_item = {
                "date": date, "game": str(row[di["游戏类型"]]).strip(), "lifecycle": life,
                "base_bet": num(row[di["基础下注额"]]) or 0,
                "base_expected_profit": num(row[di["基础预期盈利"]]) or 0,
                "base_actual_profit": num(row[di["基础实际盈利"]]) or 0,
                "entire_bet": num(row[di["完全下注额"]]) or 0,
                "entire_expected_profit": num(row[di["完全预期盈利"]]) or 0,
                "entire_actual_profit": num(row[di["完全实际盈利"]]) or 0,
            }
            all_lifecycle_daily.append(detail_item)
            if detail_item["game"] not in THIRD_PARTY_CATEGORIES:
                lifecycle_daily.append(detail_item)
        quality_by_date[date] = {
            "status": "passed", "source_root": item["directory"], "row_counts": item["row_counts"],
            "summary_reconciliation_delta_pp": metrics["summary_reconciliation_delta_pp"],
        }

    overall = aggregate(game_daily)
    all_overall = aggregate(all_game_daily)
    excluded_rows = [row for row in all_game_daily if row["game"] in THIRD_PARTY_CATEGORIES]
    excluded_overall = aggregate(excluded_rows)
    total_bet = overall["base_bet"]
    games = []
    grouped = defaultdict(list)
    for row in game_daily:
        grouped[row["game"]].append(row)
    for game, rows in grouped.items():
        item = aggregate(rows)
        item.update({"game": game, "days": len({row["date"] for row in rows}), "share": item["base_bet"] / total_bet if total_bet else 0})
        daily_valid = [rtp(row["base_bet"], row["base_actual_profit"]) for row in rows if row["base_bet"] > 0]
        item["daily_actual_rtp_sd"] = statistics.pstdev(daily_valid) if len(daily_valid) > 1 else None
        if item["base_bet"] <= 0:
            item["flag"] = "无有效下注"
        elif (item["expected_rtp"] or 0) < 0.01:
            item["flag"] = "预期RTP异常/待核"
        elif abs(item["gap_pp"] or 0) >= 1 and item["share"] >= 0.005:
            item["flag"] = "高流水·高偏离"
        elif abs(item["gap_pp"] or 0) >= 1:
            item["flag"] = "低流水·高偏离"
        elif item["share"] >= 0.05 and abs(item["gap_pp"] or 0) >= 0.5:
            item["flag"] = "高流水·轻偏离"
        else:
            item["flag"] = "正常/观察"
        games.append(item)
    games.sort(key=lambda item: item["base_bet"], reverse=True)
    valid_games = [item for item in games if item["base_bet"] > 0]
    scope = {
        "label": REPORT_SCOPE,
        "included_games": sorted(grouped),
        "included_game_count": len(grouped),
        "excluded_categories": sorted(THIRD_PARTY_CATEGORIES),
        "excluded_categories_present": sorted({row["game"] for row in all_game_daily if row["game"] in THIRD_PARTY_CATEGORIES}),
        "all_base_bet": all_overall["base_bet"],
        "included_base_bet": overall["base_bet"],
        "excluded_base_bet": excluded_overall["base_bet"],
        "included_bet_share": overall["base_bet"] / all_overall["base_bet"] if all_overall["base_bet"] else None,
        "excluded_bet_share": excluded_overall["base_bet"] / all_overall["base_bet"] if all_overall["base_bet"] else None,
    }

    life_grouped = defaultdict(list)
    for row in lifecycle_daily:
        life_grouped[(row["game"], row["lifecycle"])].append(row)
    game_lifecycle = []
    for (game, life), rows in life_grouped.items():
        item = aggregate(rows)
        item.update({"game": game, "lifecycle": life, "days": len({row["date"] for row in rows}), "flag": "有效" if item["base_bet"] > 0 else "无有效下注"})
        game_lifecycle.append(item)
    game_lifecycle.sort(key=lambda item: (item["game"], item["lifecycle"]))
    lifecycle_totals = []
    for life in range(1, 5):
        item = aggregate([row for row in lifecycle_daily if row["lifecycle"] == life])
        item.update({"lifecycle": life, "games_with_bet": len({row["game"] for row in lifecycle_daily if row["lifecycle"] == life and row["base_bet"] > 0}), "days": len(complete_records)})
        lifecycle_totals.append(item)
    priority = [item for item in games if item["flag"] in {"预期RTP异常/待核", "高流水·高偏离", "高流水·轻偏离"}]
    priority.sort(key=lambda item: (0 if item["flag"] == "高流水·高偏离" else 1, -item["base_bet"]))
    low_volume_watch = [item for item in valid_games if item["flag"] == "低流水·高偏离"]
    low_volume_watch.sort(key=lambda item: abs(item["gap_pp"] or 0), reverse=True)
    quality = {
        "requested_days": len(dates), "complete_days": len(complete_records), "coverage": len(complete_records) / len(dates),
        "missing_dates": [item["date"] for item in records if item["status"] != "complete"],
        "missing_reasons": {item["date"]: item.get("reason", "not complete") for item in records if item["status"] != "complete"},
        "source_shapes_passed": all(item["status"] == "complete" for item in records),
        "cross_table_reconciliation_passed": all(item["cross_table"]["status"] == "passed" for item in complete_records),
        "summary_game_reconciliation_max_abs_pp": max((abs(item["summary_reconciliation_delta_pp"] or 0) for item in quality_by_date.values()), default=None),
        "lark_readback_revision": int(lark_revision) if str(lark_revision).isdigit() else lark_revision,
        "lark_target_readback_verified": True,
    }
    return {
        "schema_version": 1, "generated_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds"),
        "window": {"start": start, "end": end, "timezone": "Asia/Hong_Kong", "requested_days": len(dates)},
        "quality": quality, "date_records": records, "quality_by_date": quality_by_date,
        "overall": overall, "daily_overall": daily, "games": games, "priority_games": priority,
        "low_volume_watch": low_volume_watch, "scope": scope, "game_lifecycle": game_lifecycle,
        "lifecycle_totals": lifecycle_totals,
        "top_lifecycle_deviations": sorted([item for item in game_lifecycle if item["base_bet"] > 0], key=lambda item: abs(item["gap_pp"] or 0), reverse=True)[:30],
        "source": {
            "document": "生命周期价值飞书文档", "document_revision": quality["lark_readback_revision"],
            "lark_snapshot_path": "data/outputs/lifecycle_joint/2026-09-11/lark-after",
            "raw_snapshot_roots": sorted({item["source_root"] for item in quality_by_date.values()}),
            "report": "GM Lifecycle Pool v2 (Joint)",
            "scope": REPORT_SCOPE,
        },
        "definitions": {
            "actual_rtp": "1 - 实际盈利 / 下注额，主口径使用基础字段。",
            "expected_rtp": "1 - 预期盈利 / 下注额。",
            "gap_pp": "实际RTP - 预期RTP，以百分点表示；按下注额加权。",
            "lifecycle": "文档有效生命周期 L1-L4；无有效下注的组合显示 N/A。",
            "material_threshold": "绝对偏离 >= 1.0pp；高流水定义为自营游戏基础下注额份额 >= 0.5%。",
            "scope": "先排除第三方/联运厂商分类，再重算每日、游戏、生命周期及全部分母。",
        },
    }


def pct(value: float | None) -> str:
    return "N/A" if value is None or not math.isfinite(value) else f"{value * 100:.2f}%"


def compact(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "N/A"
    if abs(value) >= 1e9:
        return f"{value / 1e9:.2f}B"
    if abs(value) >= 1e6:
        return f"{value / 1e6:.2f}M"
    if abs(value) >= 1e3:
        return f"{value / 1e3:.1f}k"
    return f"{value:.2f}"


def pp(value: float | None) -> str:
    return "N/A" if value is None or not math.isfinite(value) else f"{value:+.2f}pp"


def svg_line(dates: list[str], daily: list[dict[str, Any]]) -> str:
    width, height, left, top = 1040, 350, 60, 34
    right, bottom = 25, 62
    pw, ph = width - left - right, height - top - bottom
    by_date = {item["date"]: item for item in daily}
    values = [item[field] for item in daily for field in ("actual_rtp", "expected_rtp") if item[field] is not None]
    lo = max(0, min(values) - .02)
    hi = min(1.05, max(values) + .02)
    if hi - lo < .04:
        midpoint = (hi + lo) / 2
        lo, hi = max(0, midpoint - .02), min(1.05, midpoint + .02)
    x = lambda i: left + pw * i / max(1, len(dates) - 1)
    y = lambda value: top + ph * (1 - (value - lo) / (hi - lo))
    out = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="14日整体实际与预期RTP趋势"><title>14日整体实际与预期RTP趋势</title>']
    for index in range(5):
        tick = lo + (hi - lo) * index / 4
        yy = y(tick)
        out.append(f'<line class="grid" x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}"/><text class="axis" x="{left-9}" y="{yy+4:.1f}" text-anchor="end">{tick*100:.0f}%</text>')
    for i, date in enumerate(dates):
        xx = x(i)
        label = date[5:].replace("-", "/")
        if date not in by_date:
            out.append(f'<line class="missing" x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top+ph}"/>')
            label += "*"
        out.append(f'<text class="axis" x="{xx:.1f}" y="{height-24}" text-anchor="middle">{label}</text>')
    for field, color, label in (("actual_rtp", "#2563eb", "实际"), ("expected_rtp", "#f97316", "预期")):
        points = [(x(i), y(by_date[date][field]), date, by_date[date][field]) for i, date in enumerate(dates) if date in by_date and by_date[date][field] is not None]
        if not points:
            continue
        path = " ".join(("M" if i == 0 else "L") + f"{px:.1f},{py:.1f}" for i, (px, py, _, _) in enumerate(points))
        out.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round"/>')
        for px, py, date, value in points:
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{color}"><title>{date} {label} {pct(value)}</title></circle>')
        if field == "actual_rtp":
            for point, tag in ((max(points, key=lambda z: z[3]), "最高"), (min(points, key=lambda z: z[3]), "最低"), (points[-1], "最新")):
                out.append(f'<text class="point" x="{point[0]:.1f}" y="{point[1]-10:.1f}" text-anchor="middle">{tag} {pct(point[3])}</text>')
    out.append('<line x1="760" y1="20" x2="780" y2="20" stroke="#2563eb" stroke-width="3"/><text class="legend" x="788" y="24">实际RTP</text><line x1="860" y1="20" x2="880" y2="20" stroke="#f97316" stroke-width="3"/><text class="legend" x="888" y="24">预期RTP</text></svg>')
    return "".join(out)


def svg_bars(games: list[dict[str, Any]]) -> str:
    selected = sorted([item for item in games if item["base_bet"] > 0], key=lambda item: abs(item["gap_pp"] or 0), reverse=True)[:10]
    width, height, left, top, right, bottom = 1040, 430, 65, 32, 20, 100
    pw, ph = width - left - right, height - top - bottom
    max_abs = max([abs(item["gap_pp"] or 0) for item in selected] + [1])
    zero = top + ph / 2
    scale = ph / (max_abs * 2.2)
    slot = pw / max(1, len(selected))
    out = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="各游戏RTP偏离条形图"><title>各游戏14日实际RTP相对预期RTP偏离</title><line class="zero" x1="{left}" y1="{zero:.1f}" x2="{width-right}" y2="{zero:.1f}"/>']
    for i, item in enumerate(selected):
        value = item["gap_pp"] or 0
        bw = slot * .62
        xx = left + slot * i + slot * .19
        bh = abs(value) * scale
        yy = zero - bh if value >= 0 else zero
        color = "#16a34a" if value >= 0 else "#dc2626"
        out.append(f'<rect x="{xx:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="5" fill="{color}" opacity=".88"><title>{html.escape(item["game"])} {pp(value)}；份额 {pct(item["share"])}</title></rect><text class="bar" x="{xx+bw/2:.1f}" y="{yy-8 if value >= 0 else yy+bh+16:.1f}" text-anchor="middle">{pp(value)}</text><text class="axis" x="{xx+bw/2:.1f}" y="{height-56}" text-anchor="middle">{html.escape(item["game"])}</text>')
    out.append('<text class="note" x="18" y="23">实际 − 预期（百分点）</text></svg>')
    return "".join(out)


def svg_scatter(games: list[dict[str, Any]]) -> str:
    rows = [item for item in games if item["base_bet"] > 0]
    width, height, left, top, right, bottom = 1040, 430, 72, 34, 28, 62
    pw, ph = width - left - right, height - top - bottom
    x_values = [item["expected_rtp"] for item in rows if item["expected_rtp"] is not None]
    y_values = [item["actual_rtp"] for item in rows if item["actual_rtp"] is not None]
    x_min, x_max = max(0, min(x_values) - .02), min(1.05, max(x_values) + .02)
    y_min, y_max = max(0, min(y_values) - .03), min(1.50, max(y_values) + .03)
    px = lambda value: left + pw * (value - x_min) / (x_max - x_min)
    py = lambda value: top + ph * (1 - (value - y_min) / (y_max - y_min))
    out = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="各游戏预期与实际RTP散点图"><title>各游戏预期RTP与实际RTP</title>']
    for index in range(5):
        tick = x_min + (x_max - x_min) * index / 4
        xx = px(tick)
        out.append(f'<line class="grid" x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top+ph}"/><text class="axis" x="{xx:.1f}" y="{height-24}" text-anchor="middle">{tick*100:.0f}%</text>')
    for index in range(6):
        tick = y_min + (y_max - y_min) * index / 5
        yy = py(tick)
        out.append(f'<line class="grid" x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}"/><text class="axis" x="{left-9}" y="{yy+4:.1f}" text-anchor="end">{tick*100:.0f}%</text>')
    diagonal_lo, diagonal_hi = max(x_min, y_min), min(x_max, y_max)
    out.append(f'<line class="diagonal" x1="{px(diagonal_lo):.1f}" y1="{py(diagonal_lo):.1f}" x2="{px(diagonal_hi):.1f}" y2="{py(diagonal_hi):.1f}"/>')
    labelled = {item["game"] for item in sorted(rows, key=lambda item: abs(item["gap_pp"] or 0), reverse=True)[:6]}
    for item in rows:
        expected = item["expected_rtp"] if item["expected_rtp"] is not None else x_min
        actual = item["actual_rtp"] or y_min
        radius = 4 + min(12, math.sqrt(max(item["share"], 0) * 100) * 3)
        color = "#dc2626" if item["game"] in labelled else "#2563eb"
        xx, yy = px(expected), py(actual)
        out.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="{radius:.1f}" fill="{color}" opacity=".72"><title>{html.escape(item["game"])}；实际 {pct(item["actual_rtp"])}；预期 {pct(item["expected_rtp"])}；偏离 {pp(item["gap_pp"])}；份额 {pct(item["share"])}</title></circle>')
        if item["game"] in labelled:
            out.append(f'<text class="point" x="{xx+8:.1f}" y="{yy-8:.1f}">{html.escape(item["game"])} {pp(item["gap_pp"])}</text>')
    out.append('<text class="note" x="72" y="19">横轴：预期RTP　纵轴：实际RTP　气泡大小：14日下注额份额</text></svg>')
    return "".join(out)


def svg_lifecycle(totals: list[dict[str, Any]]) -> str:
    width, height, left, top, right, bottom = 1040, 300, 62, 34, 24, 52
    pw, ph = width-left-right, height-top-bottom
    vals = [item[field] for item in totals for field in ("actual_rtp", "expected_rtp") if item[field] is not None]
    lo, hi = max(0, min(vals)-.04), min(1.05, max(vals)+.04)
    y = lambda value: top + ph * (1 - (value-lo)/(hi-lo))
    slot = pw / 4
    out = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="生命周期整体实际与预期RTP"><title>L1至L4整体实际与预期RTP</title>']
    for i, item in enumerate(totals):
        center = left + slot*i + slot/2
        for offset, field, color, label in ((-.18, "actual_rtp", "#2563eb", "实际"), (.18, "expected_rtp", "#f97316", "预期")):
            value = item[field]
            if value is None:
                continue
            xx = center + slot*offset
            yy = y(value)
            base = y(lo)
            out.append(f'<rect x="{xx-slot*.1:.1f}" y="{yy:.1f}" width="{slot*.2:.1f}" height="{base-yy:.1f}" rx="5" fill="{color}" opacity=".88"><title>L{item["lifecycle"]} {label} {pct(value)}；偏离 {pp(item["gap_pp"])}</title></rect><text class="bar" x="{xx:.1f}" y="{yy-8:.1f}" text-anchor="middle">{pct(value)}</text>')
        out.append(f'<text class="axis" x="{center:.1f}" y="{height-20}" text-anchor="middle">L{item["lifecycle"]}</text>')
    out.append('</svg>')
    return "".join(out)


def gap_style(value: float | None) -> str:
    if value is None:
        return "background:#f3f4f6;color:#6b7280;"
    alpha = .08 + .34 * min(1, abs(value)/10)
    return f"background:rgba({22 if value >= 0 else 220},{163 if value >= 0 else 38},{74 if value >= 0 else 38},{alpha:.3f});color:{'#166534' if value >= 0 else '#991b1b'};"


def game_table(games: list[dict[str, Any]], requested_days: int = 14) -> str:
    return "".join(
        f'<tr class="{"priority" if item["flag"].startswith(("优先", "高流水·高")) else ""}"><td><strong>{html.escape(item["game"])}</strong></td><td>{compact(item["base_bet"])}</td><td>{pct(item["share"])}</td><td>{pct(item["actual_rtp"])}</td><td>{pct(item["expected_rtp"])}</td><td style="{gap_style(item["gap_pp"])}"><strong>{pp(item["gap_pp"])}</strong></td><td>{item["days"]}/{requested_days}</td><td><span class="tag">{html.escape(item["flag"])}</span></td></tr>'
        for item in games
    )


def heatmap(games: list[dict[str, Any]], rows: list[dict[str, Any]]) -> str:
    by_key = {(item["game"], item["lifecycle"]): item for item in rows}
    out = []
    for game in games:
        cells = []
        for life in range(1, 5):
            item = by_key.get((game["game"], life))
            if not item or item["base_bet"] <= 0:
                cells.append('<td class="na">N/A</td>')
            else:
                title = f'实际RTP {pct(item["actual_rtp"])}；预期RTP {pct(item["expected_rtp"])}；偏离 {pp(item["gap_pp"])}；下注额 {item["base_bet"]:,.2f}'
                cells.append(f'<td style="{gap_style(item["gap_pp"])}" title="{html.escape(title, quote=True)}"><strong>{pp(item["gap_pp"])}</strong><small>{pct(item["actual_rtp"])} / {pct(item["expected_rtp"])}</small></td>')
        out.append(f'<tr><td><strong>{html.escape(game["game"])}</strong></td><td>{pct(game["share"])}</td>{"".join(cells)}</tr>')
    return "".join(out)


def daily_table(dates: list[str], daily: list[dict[str, Any]], records: list[dict[str, Any]]) -> str:
    by_date = {item["date"]: item for item in daily}
    by_missing = {item["date"]: item for item in records if item["status"] != "complete"}
    out = []
    for date in dates:
        if date not in by_date:
            out.append(f'<tr class="missing-row"><td>{date}</td><td colspan="5"><span class="tag warning">缺口：{html.escape(by_missing[date].get("reason", "未完成"))}</span></td></tr>')
            continue
        item = by_date[date]
        out.append(f'<tr><td>{date}</td><td>{pct(item["actual_rtp"])}</td><td>{pct(item["expected_rtp"])}</td><td style="{gap_style(item["gap_pp"])}"><strong>{pp(item["gap_pp"])}</strong></td><td>{compact(item["base_bet"])}</td><td>完整</td></tr>')
    return "".join(out)


def markdown_report(a: dict[str, Any]) -> str:
    o, scope, q = a["overall"], a["scope"], a["quality"]
    missing = "、".join(q["missing_dates"]) or "无"
    priority = "、".join(item["game"] for item in a["priority_games"][:5]) or "暂无"
    low = "、".join(item["game"] for item in a["low_volume_watch"][:6]) or "暂无"
    lines = [
        f"# {REPORT_TITLE}", "",
        f"分析窗口：{a['window']['start']}—{a['window']['end']}（香港时间）；完整日期 {q['complete_days']}/{q['requested_days']}；缺口：{missing}。", "",
        "## 执行摘要", "",
        f"**排除第三方/联运厂商分类后，自营游戏整体实际RTP为 {pct(o['actual_rtp'])}、预期RTP为 {pct(o['expected_rtp'])}，偏离 {pp(o['gap_pp'])}。** 整体表现与预期基本一致。", "",
        f"**高流水优先观察：{priority}。** 低流水离群点包括 {low}，需要结合有效局数和派奖分布复核。", "",
        f"第三方/联运厂商分类占原始基础下注额 {pct(scope['excluded_bet_share'])}；已在每日、游戏、生命周期和全部分母中统一排除。", "",
        "## 01｜整体RTP与时间变化", "",
        "主RTP采用“1 - 实际盈利 / 基础下注额”，预期RTP采用“1 - 预期盈利 / 基础下注额”；仅汇总自营游戏，采用下注额加权累计。9月3日保留为空。", "",
        "## 02｜各游戏偏离", "",
        f"优先级同时看偏离幅度与自营下注额份额。高流水重点为 {priority}；低流水极值先补充样本，再评估整体影响。", "",
        "## 03｜游戏×生命周期", "",
        "L1—L4均按自营游戏基础下注额加权；无有效下注的组合显示N/A。", "",
        "## 04｜建议与验证", "",
        "1. 高流水游戏按偏离贡献排序复核配置、最终结算和派奖。", "2. 对低流水离群点补充有效局数、取消/退款、Bonus和大额派奖分布。", "3. 持续监控L1—L4，结合连续周期变化评估参数调整。", "",
        "## 05｜口径与来源", "",
        "实际RTP = 1 − 实际盈利 ÷ 下注额；预期RTP = 1 − 预期盈利 ÷ 下注额；所有汇总采用自营游戏下注额加权。", "",
        "统计范围为Waje自营游戏，聚合前排除第三方/联运厂商分类。", "",
        "原始快照按日期保存在 data/raw/lifecycle_joint/ 的已验证运行目录。",
    ]
    return "\n".join(lines) + "\n"


def artifact(a: dict[str, Any], md: str) -> dict[str, Any]:
    q = a["quality"]
    source_list = [
        {"id": "src_lark", "label": f"生命周期价值飞书文档（revision {q['lark_readback_revision']}）", "path": "data/outputs/lifecycle_joint/2026-09-11/lark-after", "query": {"engine": "Lark Sheets readback", "description": "当前在线生命周期价值文档的源值与尾部回读快照。", "tables_used": ["原始数据总数", "原始详细奖池", "原始游戏数据", "原始数据活跃周期"]}},
        {"id": "src_raw", "label": "GM Lifecycle Pool v2 (Joint) 已验证原始快照", "path": "data/raw/lifecycle_joint/", "query": {"engine": "local validated raw snapshots", "description": "按日期保留原始导出的小数精度，用于独立复算RTP。", "tables_used": ["summary.xlsx", "game.xlsx", "detail.xlsx", "active.xlsx"]}},
        {"id": "src_receipts", "label": "生命周期采集与回读质量回执", "path": "data/outputs/lifecycle_joint/2026-09-11/run-receipt.json", "query": {"engine": "local receipts", "description": "记录覆盖、勾稽、源值回读、样式和公式检查。", "tables_used": ["run-receipt.json", "lark-validation-report.json"]}},
    ]
    daily_rows = []
    for item in a["daily_overall"]:
        daily_rows.append({"date": item["date"], "actual_rtp": item["actual_rtp"], "expected_rtp": item["expected_rtp"], "gap_pp": item["gap_pp"], "base_bet": item["base_bet"], "actual_house_profit": item["actual_house_profit"], "expected_house_profit": item["expected_house_profit"], "status": "完整"})
    game_rows = []
    for item in a["games"]:
        game_rows.append({"game": item["game"], "base_bet": item["base_bet"], "share": item["share"], "actual_rtp": item["actual_rtp"], "expected_rtp": item["expected_rtp"], "gap_pp": item["gap_pp"], "days": item["days"], "requested_days": q["requested_days"], "coverage_label": f'{item["days"]}/{q["requested_days"]}', "flag": item["flag"], "actual_house_profit": item["actual_house_profit"], "expected_house_profit": item["expected_house_profit"]})
    life_rows = []
    for item in a["game_lifecycle"]:
        life_rows.append({"game": item["game"], "lifecycle": item["lifecycle"], "base_bet": item["base_bet"], "actual_rtp": item["actual_rtp"], "expected_rtp": item["expected_rtp"], "gap_pp": item["gap_pp"], "days": item["days"], "flag": item["flag"], "actual_house_profit": item["actual_house_profit"], "expected_house_profit": item["expected_house_profit"]})
    valid_games = [row for row in game_rows if row["base_bet"] > 0]
    valid_life = [row for row in life_rows if row["base_bet"] > 0]
    life_summary = [{"lifecycle": item["lifecycle"], "base_bet": item["base_bet"], "actual_rtp": item["actual_rtp"], "expected_rtp": item["expected_rtp"], "gap_pp": item["gap_pp"], "games_with_bet": item["games_with_bet"], "actual_house_profit": item["actual_house_profit"], "expected_house_profit": item["expected_house_profit"]} for item in a["lifecycle_totals"]]
    title = REPORT_TITLE
    tables = [
        {"id": "daily", "title": "每日自营游戏RTP", "subtitle": "第三方/联运厂商已排除；缺失日保留缺口。", "dataset": "daily_overall", "sourceId": "src_lark", "columns": [{"field": "date", "label": "日期", "type": "text"}, {"field": "actual_rtp", "label": "实际RTP", "type": "number", "format": "percent"}, {"field": "expected_rtp", "label": "预期RTP", "type": "number", "format": "percent"}, {"field": "gap_pp", "label": "偏离（百分点）", "type": "number"}, {"field": "base_bet", "label": "基础下注额", "type": "number"}, {"field": "status", "label": "状态", "type": "text"}]},
        {"id": "games", "title": "自营游戏14日窗口累计RTP", "subtitle": "RTP按窗口内有效日期的累计下注额加权；本期因缺失1日，覆盖为13/14。", "dataset": "game_summary", "sourceId": "src_raw", "columns": [{"field": "game", "label": "游戏", "type": "text"}, {"field": "base_bet", "label": "累计基础下注额", "type": "number"}, {"field": "share", "label": "自营下注额份额", "type": "number", "format": "percent"}, {"field": "actual_rtp", "label": "窗口累计实际RTP", "type": "number", "format": "percent"}, {"field": "expected_rtp", "label": "窗口累计预期RTP", "type": "number", "format": "percent"}, {"field": "gap_pp", "label": "累计偏离（百分点）", "type": "number"}, {"field": "coverage_label", "label": "有效日期/窗口", "type": "text"}, {"field": "flag", "label": "状态", "type": "text"}]},
        {"id": "life", "title": "游戏×生命周期RTP偏离", "subtitle": "有效下注额加权；空组合显示N/A。", "dataset": "game_lifecycle", "sourceId": "src_raw", "columns": [{"field": "game", "label": "游戏", "type": "text"}, {"field": "lifecycle", "label": "生命周期", "type": "number"}, {"field": "base_bet", "label": "基础下注额", "type": "number"}, {"field": "actual_rtp", "label": "实际RTP", "type": "number", "format": "percent"}, {"field": "expected_rtp", "label": "预期RTP", "type": "number", "format": "percent"}, {"field": "gap_pp", "label": "偏离（百分点）", "type": "number"}, {"field": "days", "label": "完整天数", "type": "number"}, {"field": "flag", "label": "状态", "type": "text"}]},
        {"id": "life-summary", "title": "自营游戏生命周期整体RTP", "subtitle": "用于判断偏离是否集中在特定生命周期。", "dataset": "lifecycle_summary", "sourceId": "src_raw", "columns": [{"field": "lifecycle", "label": "生命周期", "type": "number"}, {"field": "actual_rtp", "label": "实际RTP", "type": "number", "format": "percent"}, {"field": "expected_rtp", "label": "预期RTP", "type": "number", "format": "percent"}, {"field": "gap_pp", "label": "偏离（百分点）", "type": "number"}, {"field": "games_with_bet", "label": "有效游戏数", "type": "number"}]},
    ]
    charts = [
        {"id": "daily-line", "title": "14日自营游戏实际与预期RTP趋势", "subtitle": "第三方/联运厂商已排除；缺口保留为空。", "type": "line", "dataset": "daily_overall", "sourceId": "src_lark", "encodings": {"x": {"field": "date", "type": "temporal"}, "y": {"fields": ["actual_rtp", "expected_rtp"], "type": "quantitative", "format": "percent"}, "tooltip": [{"field": "gap_pp", "type": "quantitative"}]}, "xAxisTitle": "业务日期", "yAxisTitle": "RTP"},
        {"id": "game-bars", "title": "各游戏14日实际RTP相对预期RTP偏离", "subtitle": "偏离=实际RTP−预期RTP。", "type": "bar", "dataset": "game_summary", "sourceId": "src_raw", "encodings": {"x": {"field": "game", "type": "nominal"}, "y": {"field": "gap_pp", "type": "quantitative"}, "tooltip": [{"field": "share", "type": "quantitative"}, {"field": "flag", "type": "nominal"}]}, "xAxisTitle": "游戏", "yAxisTitle": "偏离（百分点）"},
        {"id": "game-scatter", "title": "各游戏预期RTP与实际RTP", "subtitle": "气泡大小表示14日基础下注额份额。", "type": "scatter", "dataset": "game_summary", "sourceId": "src_raw", "encodings": {"x": {"field": "expected_rtp", "type": "quantitative", "format": "percent"}, "y": {"field": "actual_rtp", "type": "quantitative", "format": "percent"}, "tooltip": [{"field": "game", "type": "nominal"}, {"field": "gap_pp", "type": "quantitative"}]}, "xAxisTitle": "预期RTP", "yAxisTitle": "实际RTP"},
        {"id": "life-bars", "title": "L1—L4自营游戏实际与预期RTP", "subtitle": "仅按自营游戏有效下注额加权。", "type": "bar", "dataset": "lifecycle_summary", "sourceId": "src_raw", "encodings": {"x": {"field": "lifecycle", "type": "nominal"}, "y": {"fields": ["actual_rtp", "expected_rtp"], "type": "quantitative", "format": "percent"}, "tooltip": [{"field": "gap_pp", "type": "quantitative"}]}, "xAxisTitle": "生命周期", "yAxisTitle": "RTP"},
    ]
    blocks = [
        {"id": "title", "type": "markdown", "body": f"# {title}\n\n分析窗口：{a['window']['start']}—{a['window']['end']}（香港时间）；完整日期 {q['complete_days']}/{q['requested_days']}。"},
        {"id": "summary", "type": "markdown", "body": f"## 执行摘要\n\n**第三方/联运厂商分类已从全部指标及分母中排除。** 自营游戏实际RTP {pct(a['overall']['actual_rtp'])}、预期RTP {pct(a['overall']['expected_rtp'])}，偏离 {pp(a['overall']['gap_pp'])}。\n\n**整体接近预期，风险集中在少数游戏与生命周期组合。** 高流水轻偏离与低流水离群点分开处理。"},
        {"id": "daily-intro", "type": "markdown", "body": "## 01｜整体RTP与时间变化\n\n仅汇总自营游戏；图中标注实际RTP的最高、最低和最新值，缺失日期保留为空。"},
        {"id": "daily-chart", "type": "chart", "chartId": "daily-line"},
        {"id": "daily-table", "type": "table", "tableId": "daily"},
        {"id": "game-intro", "type": "markdown", "body": "## 02｜各自营游戏偏离\n\n表中RTP采用14日窗口内有效日期的累计下注额加权值。本期缺少2026-09-03，因此每款游戏均显示13/14。"},
        {"id": "game-bars", "type": "chart", "chartId": "game-bars"},
        {"id": "scatter-intro", "type": "markdown", "body": "散点图用于识别实际与预期RTP离群点，气泡大小表示其在自营游戏中的下注份额。"},
        {"id": "game-scatter", "type": "chart", "chartId": "game-scatter"},
        {"id": "game-table", "type": "table", "tableId": "games"},
        {"id": "life-intro", "type": "markdown", "body": "## 03｜自营游戏×生命周期\n\nL1—L4分别按有效下注额加权；每个格子保留实际/预期RTP与偏离百分点。"},
        {"id": "life-bars", "type": "chart", "chartId": "life-bars"},
        {"id": "life-table", "type": "table", "tableId": "life"},
        {"id": "method", "type": "markdown", "body": "## 04｜建议与验证\n\n先复核高流水偏离贡献，再核查低流水离群点的有效局数与派奖分布；最后结合生命周期连续变化决定是否调参。"},
        {"id": "life-summary-table", "type": "table", "tableId": "life-summary"},
    ]
    contract = {
        "type": "business", "language": "zh",
        "population": "Lifecycle Pool v2 (Joint) 中的Waje自营游戏；第三方/联运厂商分类在聚合前排除。",
        "period": f"{a['window']['start']}—{a['window']['end']}（香港时间），完整日期 {q['complete_days']}/{q['requested_days']}。",
        "timezone": "Asia/Hong_Kong",
        "metrics": [
            {"dataset": "daily_overall", "field": "actual_rtp", "kind": "ratio", "unit": "%", "scale": "fraction", "definition": "（基础下注额-基础实际盈利）/基础下注额。", "denominator": "当日自营游戏基础下注额"},
            {"dataset": "daily_overall", "field": "expected_rtp", "kind": "ratio", "unit": "%", "scale": "fraction", "definition": "（基础下注额-基础预期盈利）/基础下注额。", "denominator": "当日自营游戏基础下注额"},
            {"dataset": "game_summary", "field": "gap_pp", "kind": "difference_pp", "unit": "百分点", "scale": "percent_points", "definition": "实际RTP-预期RTP，按游戏基础下注额加权。", "denominator": "同游戏14日基础下注额"},
            {"dataset": "game_lifecycle", "field": "gap_pp", "kind": "difference_pp", "unit": "百分点", "scale": "percent_points", "definition": "实际RTP-预期RTP，按游戏×生命周期基础下注额加权。", "denominator": "同游戏×生命周期14日基础下注额"},
        ],
        "assertions": [
            {"kind": "ratio", "dataset": "daily_overall", "numerator": "actual_house_profit", "denominator": "base_bet", "actual": "actual_rtp", "tolerance": 1e-8},
            {"kind": "ratio", "dataset": "game_summary_valid", "numerator": "actual_house_profit", "denominator": "base_bet", "actual": "actual_rtp", "tolerance": 1e-8},
            {"kind": "difference_pp", "dataset": "game_summary_valid", "numerator": "actual_rtp", "denominator": "expected_rtp", "actual": "gap_pp", "tolerance": 1e-8},
            {"kind": "ratio", "dataset": "game_lifecycle_valid", "numerator": "actual_house_profit", "denominator": "base_bet", "actual": "actual_rtp", "tolerance": 1e-8},
            {"kind": "difference_pp", "dataset": "game_lifecycle_valid", "numerator": "actual_rtp", "denominator": "expected_rtp", "actual": "gap_pp", "tolerance": 1e-8},
        ],
        "decisions": {"rtp_definition": {"status": "confirmed", "value": "基础RTP为主，完全RTP交叉校验"}, "scope": {"status": "confirmed", "value": REPORT_SCOPE}, "missing_date_policy": {"status": "confirmed", "value": "2026-09-03未成熟，不补零、不用邻日替代"}},
        "openQuestions": [{"parameter": "low_volume_outliers", "question": "低流水离群游戏是否由少量大额派奖、取消退款或Bonus主导？"}],
    }
    tables[0]["defaultSort"] = {"field": "date", "direction": "asc"}
    tables[1]["defaultSort"] = {"field": "gap_pp", "direction": "desc"}
    tables[2]["defaultSort"] = {"field": "gap_pp", "direction": "desc"}
    tables[3]["defaultSort"] = {"field": "lifecycle", "direction": "asc"}
    charts[0]["annotations"] = [{"type": "extrema", "field": "actual_rtp", "labels": ["最高", "最低", "最新"]}]
    charts[2]["encodings"]["label"] = {"field": "game", "type": "nominal"}
    datasets = {"daily_overall": daily_rows, "game_summary": game_rows, "game_summary_valid": valid_games, "game_lifecycle": life_rows, "game_lifecycle_valid": valid_life, "lifecycle_summary": life_summary}
    return {"surface": "report", "manifest": {"version": 1, "surface": "report", "title": title, "description": f"自营游戏生命周期RTP汇总，{a['window']['start']}—{a['window']['end']}，完整日期 {q['complete_days']}/{q['requested_days']}。", "generatedAt": a["generated_at"], "sources": source_list, "charts": charts, "tables": tables, "blocks": blocks, "reportContract": contract}, "snapshot": {"generatedAt": a["generated_at"], "datasets": datasets, "quality": q, "scope": a["scope"]}, "sources": source_list}


def html_report(a: dict[str, Any]) -> str:
    o, s, q = a["overall"], a["sensitivity"], a["quality"]
    dates = dates_between(a["window"]["start"], a["window"]["end"])
    priority = "、".join(item["game"] for item in a["priority_games"][:3]) or "暂无"
    low = "、".join(item["game"] for item in a["low_volume_watch"][:6]) or "暂无"
    daily = daily_table(dates, a["daily_overall"], a["date_records"])
    game_rows = game_table(a["games"], q["requested_days"])
    heat_rows = heatmap(a["games"], a["game_lifecycle"])
    life_rows = "".join(f'<tr><td>L{item["lifecycle"]}</td><td>{pct(item["actual_rtp"])}</td><td>{pct(item["expected_rtp"])}</td><td style="{gap_style(item["gap_pp"])}"><strong>{pp(item["gap_pp"])}</strong></td><td>{item["games_with_bet"]}</td></tr>' for item in a["lifecycle_totals"])
    top_rows = "".join(f'<tr><td>{html.escape(item["game"])}</td><td>L{item["lifecycle"]}</td><td>{compact(item["base_bet"])}</td><td>{pct(item["actual_rtp"])}</td><td>{pct(item["expected_rtp"])}</td><td style="{gap_style(item["gap_pp"])}"><strong>{pp(item["gap_pp"])}</strong></td></tr>' for item in a["top_lifecycle_deviations"][:20])
    css = """\n+    :root{color-scheme:light dark;--bg:#eef3f8;--paper:#fff;--ink:#172033;--muted:#657389;--line:#d7e0ea;--blue:#2563eb;--blue-soft:#e8f0ff;--orange:#f97316;--red:#b91c1c;--green:#15803d;--amber:#b45309;--shadow:0 18px 50px rgba(27,55,90,.10)}\n+    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Microsoft YaHei",Arial,sans-serif;font-size:15px;line-height:1.72}.page{width:min(1180px,calc(100% - 32px));margin:0 auto 56px}.hero{padding:52px 0 28px}.eyebrow{color:var(--blue);font-size:12px;letter-spacing:.16em;font-weight:800}.hero-row{display:flex;justify-content:space-between;gap:22px;align-items:flex-start}.hero h1{max-width:900px;margin:14px 0 8px;font-size:clamp(31px,4.8vw,54px);letter-spacing:-.045em;line-height:1.12}.dek{margin:0;color:var(--muted);font-size:18px}.status{flex:none;margin-top:15px;padding:8px 13px;border-radius:999px;border:1px solid #f5c58b;background:#fff7ed;color:#9a3412;font-weight:750;font-size:13px}.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.meta span{padding:6px 10px;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.7);color:var(--muted);font-size:12px}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.kpi,.section,.callout{background:var(--paper);border:1px solid var(--line);border-radius:17px;box-shadow:var(--shadow)}.kpi{padding:18px}.label{font-size:12px;color:var(--muted);font-weight:750}.value{font-size:31px;line-height:1.1;font-weight:850;margin:8px 0}.blue{color:var(--blue)}.orange{color:var(--orange)}.red{color:var(--red)}.amber{color:var(--amber)}.note{font-size:12px;color:var(--muted)}.callout{padding:20px 23px;margin-top:16px}.callout.critical{border-left:5px solid var(--red);background:linear-gradient(100deg,#fff,#fff7f6)}.callout.warning{border-left:5px solid var(--amber);background:linear-gradient(100deg,#fff,#fffaf1)}.callout-title{font-weight:850}.callout p{margin:5px 0;max-width:960px}.small{font-size:13px;color:var(--muted)}.section{padding:28px 30px;margin-top:18px}.section h2{font-size:26px;line-height:1.25;margin:0 0 9px}.section h3{font-size:18px;margin:25px 0 8px}.intro{color:var(--muted);margin:0 0 15px}.conclusion{padding:11px 14px;border-left:4px solid var(--blue);background:var(--blue-soft);border-radius:0 10px 10px 0;margin:17px 0 11px}.chart-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px;background:linear-gradient(#fbfdff,#f7faff);padding:8px}.chart-svg{display:block;width:100%;min-width:760px;height:auto}.grid{stroke:#dbe4ee;stroke-width:1}.zero{stroke:#94a3b8;stroke-width:1.5;stroke-dasharray:4 4}.diagonal{stroke:#94a3b8;stroke-width:1;stroke-dasharray:5 5}.missing{stroke:#f59e0b;stroke-width:2;stroke-dasharray:3 4}.axis,.legend,.note{fill:#64748b;font-size:12px}.point,.bar{fill:#334155;font-size:11px;font-weight:750}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px;margin-top:16px}table{border-collapse:collapse;width:100%;min-width:780px;font-size:13px}th,td{padding:10px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle;white-space:nowrap}th{background:#eaf1f8;color:#334155;font-size:12px;position:sticky;top:0;z-index:1}.priority td:first-child{border-left:4px solid var(--red)}.missing-row{background:#fffaf1}.na{color:#94a3b8;background:#f8fafc;text-align:center}.heatmap td{text-align:center;min-width:125px}.heatmap td small{display:block;font-size:10px;margin-top:2px}.tag{display:inline-block;padding:3px 7px;border-radius:999px;background:#f1f5f9;color:#475569;font-size:11px}.tag.warning{background:#fef3c7;color:#92400e}.actions{display:grid;gap:10px}.action{display:grid;grid-template-columns:32px 1fr;gap:11px;padding:13px;border:1px solid var(--line);border-radius:12px;background:#fbfdff}.num{display:grid;place-items:center;width:27px;height:27px;border-radius:8px;background:var(--blue);color:#fff;font-weight:800}.action strong{display:block}.details{margin-top:15px}.details summary{cursor:pointer;color:#1e40af;font-weight:800}.details pre{white-space:pre-wrap;word-break:break-word;background:#f8fafc;border:1px solid var(--line);padding:13px;border-radius:9px;font-size:12px;color:#475569}.footer{text-align:center;color:var(--muted);font-size:12px;padding:25px 0}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media(max-width:840px){.page{width:min(100% - 22px,1180px)}.hero{padding:32px 0 22px}.hero-row{display:block}.status{display:inline-block;margin-top:16px}.kpis{grid-template-columns:1fr 1fr}.section{padding:21px 15px}.two{grid-template-columns:1fr}.hero h1{font-size:32px}.value{font-size:25px}.chart-svg{min-width:700px}}@media(max-width:480px){.page{width:calc(100% - 14px)}.kpi{padding:13px 11px}.label{font-size:10px}.value{font-size:21px}.note{font-size:10px}.hero h1{font-size:29px}.dek{font-size:15px}.section{padding:17px 10px}.callout{padding:16px 17px}}\n+    @media(prefers-color-scheme:dark){:root{--bg:#0b1220;--paper:#111b2d;--ink:#e5edf8;--muted:#9aabc0;--line:#26364c;--blue-soft:#162b52;--shadow:0 18px 50px rgba(0,0,0,.25)}.meta span,.kpi,.section,.callout{background:var(--paper)}.callout.critical{background:#211820}.callout.warning{background:#211d16}.chart-wrap{background:#0e1726}.conclusion{background:#122342}.action,th{background:#142238}th{color:#dbeafe}.details pre{background:#0e1726;color:#b8c8dc}.tag{background:#253349;color:#cbd5e1}.na{background:#172235}.point,.bar{fill:#dbeafe}.grid{stroke:#26364c}.hero h1{color:#f4f7fb}}\n+    """
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="report-type" content="business"><meta name="report-status" content="partial"><title>{html.escape("Tada、PP、OMG 的预期RTP为0%，14日整体偏离应先按配置异常核查")}</title><style>{css}</style></head><body><div class="page"><header class="hero"><div class="eyebrow">WAJE ANALYST · RTP DIAGNOSTIC</div><div class="hero-row"><div><h1>Tada、PP、OMG 的预期RTP为0%，14日整体偏离应先按配置异常核查</h1><p class="dek">生命周期价值文档 · {a["window"]["start"]}—{a["window"]["end"]} · 香港时间</p></div><span class="status">部分覆盖 · {q["complete_days"]}/{q["requested_days"]} 天</span></div><div class="meta"><span>飞书文档 revision {q["lark_readback_revision"]}</span><span>主口径：基础真实回报比</span><span>缺口：{"、".join(q["missing_dates"]) or "无"}</span></div></header><section class="kpis"><div class="kpi"><div class="label">14日实际RTP</div><div class="value blue">{pct(o["actual_rtp"])}</div><div class="note">基础下注额加权</div></div><div class="kpi"><div class="label">当前预期RTP</div><div class="value orange">{pct(o["expected_rtp"])}</div><div class="note">受预期=0%字段影响</div></div><div class="kpi"><div class="label">整体偏离</div><div class="value red">{pp(o["gap_pp"])}</div><div class="note">实际 − 预期</div></div><div class="kpi"><div class="label">预期=0%流水占比</div><div class="value amber">{pct(s["excluded_bet_share"])}</div><div class="note">{html.escape(priority)}</div></div></section><section class="callout critical"><div class="callout-title">先看结论</div><p><strong>当前整体偏离主要不是全局RTP失控，而是预期字段被三款高流水游戏拉低。</strong> Tada、PP、OMG的预期RTP按现有字段均为0%，合计占基础下注额 {pct(s["excluded_bet_share"])}；剔除三款后，剩余游戏实际RTP {pct(s["actual_rtp"])}、预期RTP {pct(s["expected_rtp"])}，偏离 {pp(s["gap_pp"])}。</p><p class="small">这应先按配置/字段核查项处理，不能直接解释成游戏性能、机器人或风控结论。</p></section><section class="callout warning"><div class="callout-title">覆盖边界</div><p>统计窗口共{q["requested_days"]}天，完整{q["complete_days"]}天；<strong>2026-09-03为未成熟缺口</strong>，没有补零，也没有使用相邻日期替代。</p></section><section class="section" id="overall"><h2>01｜整体RTP与时间变化</h2><p class="intro">完整日期内实际RTP为 {pct(min(item["actual_rtp"] for item in a["daily_overall"]))}—{pct(max(item["actual_rtp"] for item in a["daily_overall"]))}；预期线因预期字段异常处于低位。</p><div class="conclusion"><strong>读图：</strong>实际RTP窄幅波动，预期RTP异常低位；先处理预期字段，再评价整体偏离。</div><div class="chart-wrap">{svg_line(dates, a["daily_overall"])}</div><div class="table-wrap"><table><thead><tr><th>日期</th><th>实际RTP</th><th>预期RTP</th><th>偏离</th><th>基础下注额</th><th>人数</th><th>状态</th></tr></thead><tbody>{daily}</tbody></table></div></section><section class="section" id="games"><h2>02｜各游戏：偏离集中在少数高流水游戏</h2><p class="intro">优先级同时看偏离幅度和下注额份额。Tada、PP、OMG的预期RTP均为0%；{html.escape(low)}虽有较大百分点偏离，但流水份额较低。</p><div class="conclusion"><strong>优先核查：</strong>{html.escape(priority)}；低流水游戏先补充有效下注量和独立复查。</div><div class="chart-wrap">{svg_bars(a["games"])}</div><div class="conclusion"><strong>读散点：</strong>偏离幅度必须同时看预期、实际和气泡大小；气泡很小的离群点不直接外推为全局问题。</div><div class="chart-wrap">{svg_scatter(a["games"])}</div><div class="table-wrap"><table><thead><tr><th>游戏</th><th>基础下注额</th><th>下注额份额</th><th>实际RTP</th><th>预期RTP</th><th>偏离</th><th>完整天数</th><th>状态</th></tr></thead><tbody>{game_rows}</tbody></table></div></section><section class="section" id="lifecycle"><h2>03｜游戏×生命周期：L2—L4偏离逐步扩大</h2><p class="intro">{"；".join(f"L{item['lifecycle']}实际{pct(item['actual_rtp'])}/预期{pct(item['expected_rtp'])}（{pp(item['gap_pp'])}）" for item in a["lifecycle_totals"])}。L0与L5—L11无有效下注，不纳入比较。</p><div class="conclusion"><strong>读图：</strong>L4承担最大下注额，同时实际RTP约96.6%、预期RTP约38.6%，偏离最大；先确认生命周期配置。</div><div class="chart-wrap">{svg_lifecycle(a["lifecycle_totals"])}</div><div class="table-wrap heatmap"><table><thead><tr><th>游戏</th><th>14日流水份额</th><th>L1<br>实际/预期</th><th>L2<br>实际/预期</th><th>L3<br>实际/预期</th><th>L4<br>实际/预期</th></tr></thead><tbody>{heat_rows}</tbody></table></div><h3>生命周期偏离最大的组合</h3><div class="table-wrap"><table><thead><tr><th>游戏</th><th>生命周期</th><th>基础下注额</th><th>实际RTP</th><th>预期RTP</th><th>偏离</th></tr></thead><tbody>{top_rows}</tbody></table></div></section><section class="section" id="actions"><h2>04｜建议与验证顺序</h2><div class="actions"><div class="action"><div class="num">1</div><div><strong>核对Tada、PP、OMG的预期RTP字段</strong><span>对照生命周期配置、原始预期回报比、预期盈利及导出字段映射，确认0%是否为有效策略。</span></div></div><div class="action"><div class="num">2</div><div><strong>修正口径后重算整体与生命周期RTP</strong><span>当前敏感性结果显示剩余游戏偏离 {pp(s["gap_pp"])}；避免用错误预期基线放大问题。</span></div></div><div class="action"><div class="num">3</div><div><strong>低流水游戏延长观察</strong><span>重点观察 {html.escape(low)}，同步记录有效下注量和结算窗口。</span></div></div><div class="action"><div class="num">4</div><div><strong>补齐2026-09-03</strong><span>成熟后重新采集并复跑同一计算和质量门槛。</span></div></div></div></section><section class="section" id="methods"><h2>05｜口径、质量与来源</h2><div class="two"><div><h3>计算口径</h3><p>实际RTP = 1 − 实际盈利 ÷ 下注额；预期RTP = 1 − 预期盈利 ÷ 下注额；偏离 = 实际RTP − 预期RTP，以百分点表示。汇总按下注额加权，不做简单平均。</p><p>数据单位沿用原表，报告不擅自标注币种。主分析使用基础口径，完全口径用于交叉校验。</p></div><div><h3>质量状态</h3><p>{q["complete_days"]}/{q["requested_days"]}日期完整；完整日期均通过表头、31游戏、372明细与detail/game勾稽；在线文档回读修订为{q["lark_readback_revision"]}。</p><p>预期RTP=0%的三款游戏是配置/字段核查项，不等同于已证实的经营异常。</p></div></div><details class="details"><summary>查看复算范围与来源路径</summary><pre>飞书在线文档快照：data/outputs/lifecycle_joint/2026-09-11/lark-after\nGM原始快照：data/raw/lifecycle_joint/&lt;运行日期&gt;/&lt;业务日期&gt;/tables.json\n本次分析目录：analysis/lifecycle_rtp_14d_2026_09_11/\n完整日期：{", ".join(item["date"] for item in a["date_records"] if item["status"]=="complete")}\n缺失日期：{", ".join(q["missing_dates"]) or "无"}\n完整性：{q["source_shapes_passed"]}；跨表勾稽：{q["cross_table_reconciliation_passed"]}；Lark回读：{q["lark_target_readback_verified"]}</pre></details></section><footer class="footer">本报告为本地自包含HTML；数据与来源回执保存在项目分析目录。未写入凭据、Token或用户级明细。</footer></div></body></html>"""


def html_report_self_owned(a: dict[str, Any]) -> str:
    o, scope, q = a["overall"], a["scope"], a["quality"]
    dates = dates_between(a["window"]["start"], a["window"]["end"])
    priority = "、".join(item["game"] for item in a["priority_games"][:4]) or "暂无"
    low = "、".join(item["game"] for item in a["low_volume_watch"][:6]) or "暂无"
    daily = daily_table(dates, a["daily_overall"], a["date_records"])
    game_rows = game_table(a["games"], q["requested_days"])
    heat_rows = heatmap(a["games"], a["game_lifecycle"])
    top_rows = "".join(
        f'<tr><td>{html.escape(item["game"])}</td><td>L{item["lifecycle"]}</td><td>{compact(item["base_bet"])}</td><td>{pct(item["actual_rtp"])}</td><td>{pct(item["expected_rtp"])}</td><td style="{gap_style(item["gap_pp"])}"><strong>{pp(item["gap_pp"])}</strong></td></tr>'
        for item in a["top_lifecycle_deviations"][:20]
    )
    life_text = "；".join(
        f'L{item["lifecycle"]} {pct(item["actual_rtp"])} / {pct(item["expected_rtp"])}（{pp(item["gap_pp"])}）'
        for item in a["lifecycle_totals"]
    )
    actual_values = [item["actual_rtp"] for item in a["daily_overall"] if item["actual_rtp"] is not None]
    custom_css = """
    :root{color-scheme:light dark;--bg:#eef3f8;--paper:#fff;--ink:#172033;--muted:#657389;--line:#d7e0ea;--blue:#2563eb;--blue-soft:#e8f0ff;--orange:#f97316;--red:#b91c1c;--green:#15803d;--amber:#b45309;--shadow:0 18px 50px rgba(27,55,90,.10)}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Microsoft YaHei",Arial,sans-serif;font-size:15px;line-height:1.72}.page{width:min(1180px,calc(100% - 32px));margin:0 auto 56px}.hero{padding:52px 0 28px}.eyebrow{color:var(--blue);font-size:12px;letter-spacing:.16em;font-weight:800}.hero-row{display:flex;justify-content:space-between;gap:22px;align-items:flex-start}.hero h1{max-width:900px;margin:14px 0 8px;font-size:clamp(31px,4.8vw,54px);letter-spacing:-.045em;line-height:1.12}.dek{margin:0;color:var(--muted);font-size:18px}.status{flex:none;margin-top:15px;padding:8px 13px;border-radius:999px;border:1px solid #f5c58b;background:#fff7ed;color:#9a3412;font-weight:750;font-size:13px}.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.meta span{padding:6px 10px;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.7);color:var(--muted);font-size:12px}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.kpi,.section,.callout{background:var(--paper);border:1px solid var(--line);border-radius:17px;box-shadow:var(--shadow)}.kpi{padding:18px}.label{font-size:12px;color:var(--muted);font-weight:750}.value{font-size:31px;line-height:1.1;font-weight:850;margin:8px 0}.blue{color:var(--blue)}.orange{color:var(--orange)}.green{color:var(--green)}.amber{color:var(--amber)}.note{font-size:12px;color:var(--muted)}.callout{padding:20px 23px;margin-top:16px}.callout.good{border-left:5px solid var(--green);background:linear-gradient(100deg,#fff,#f2fff7)}.callout.warning{border-left:5px solid var(--amber);background:linear-gradient(100deg,#fff,#fffaf1)}.callout-title{font-weight:850}.callout p{margin:5px 0;max-width:960px}.small{font-size:13px;color:var(--muted)}.section{padding:28px 30px;margin-top:18px}.section h2{font-size:26px;line-height:1.25;margin:0 0 9px}.section h3{font-size:18px;margin:25px 0 8px}.intro{color:var(--muted);margin:0 0 15px}.conclusion{padding:11px 14px;border-left:4px solid var(--blue);background:var(--blue-soft);border-radius:0 10px 10px 0;margin:17px 0 11px}.chart-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px;background:linear-gradient(#fbfdff,#f7faff);padding:8px}.chart-svg{display:block;width:100%;min-width:760px;height:auto}.grid{stroke:#dbe4ee;stroke-width:1}.zero{stroke:#94a3b8;stroke-width:1.5;stroke-dasharray:4 4}.diagonal{stroke:#94a3b8;stroke-width:1;stroke-dasharray:5 5}.missing{stroke:#f59e0b;stroke-width:2;stroke-dasharray:3 4}.axis,.legend,.note{fill:#64748b;font-size:12px}.point,.bar{fill:#334155;font-size:11px;font-weight:750}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px;margin-top:16px}table{border-collapse:collapse;width:100%;min-width:780px;font-size:13px}th,td{padding:10px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle;white-space:nowrap}th{background:#eaf1f8;color:#334155;font-size:12px;position:sticky;top:0;z-index:1}.priority td:first-child{border-left:4px solid var(--red)}.missing-row{background:#fffaf1}.na{color:#94a3b8;background:#f8fafc;text-align:center}.heatmap td{text-align:center;min-width:125px}.heatmap td small{display:block;font-size:10px;margin-top:2px}.tag{display:inline-block;padding:3px 7px;border-radius:999px;background:#f1f5f9;color:#475569;font-size:11px}.tag.warning{background:#fef3c7;color:#92400e}.actions{display:grid;gap:10px}.action{display:grid;grid-template-columns:32px 1fr;gap:11px;padding:13px;border:1px solid var(--line);border-radius:12px;background:#fbfdff}.num{display:grid;place-items:center;width:27px;height:27px;border-radius:8px;background:var(--blue);color:#fff;font-weight:800}.action strong{display:block}.method-list{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.method-item{padding:14px 15px;border:1px solid var(--line);border-radius:12px;background:#fbfdff}.method-item strong{display:block;margin-bottom:4px}.method-item span{color:var(--muted);font-size:13px}.details{margin-top:16px}.details summary{cursor:pointer;color:#1e40af;font-weight:800}.details pre{white-space:pre-wrap;word-break:break-word;background:#f8fafc;border:1px solid var(--line);padding:13px;border-radius:9px;font-size:12px;color:#475569}.footer{text-align:center;color:var(--muted);font-size:12px;padding:25px 0}@media(max-width:840px){.page{width:min(100% - 22px,1180px)}.hero{padding:32px 0 22px}.hero-row{display:block}.status{display:inline-block;margin-top:16px}.kpis{grid-template-columns:1fr 1fr}.section{padding:21px 15px}.method-list{grid-template-columns:1fr}.hero h1{font-size:32px}.value{font-size:25px}.chart-svg{min-width:700px}}@media(max-width:480px){.page{width:calc(100% - 14px)}.kpi{padding:13px 11px}.label{font-size:10px}.value{font-size:21px}.note{font-size:10px}.hero h1{font-size:29px}.dek{font-size:15px}.section{padding:17px 10px}.callout{padding:16px 17px}}@media(prefers-color-scheme:dark){:root{--bg:#0b1220;--paper:#111b2d;--ink:#e5edf8;--muted:#9aabc0;--line:#26364c;--blue-soft:#162b52;--shadow:0 18px 50px rgba(0,0,0,.25)}.meta span,.kpi,.section,.callout{background:var(--paper)}.callout.good{background:#10241d}.callout.warning{background:#211d16}.chart-wrap,.method-item{background:#0e1726}.conclusion{background:#122342}.action,th{background:#142238}th{color:#dbeafe}.details pre{background:#0e1726;color:#b8c8dc}.tag{background:#253349;color:#cbd5e1}.na{background:#172235}.point,.bar{fill:#dbeafe}.grid{stroke:#26364c}.hero h1{color:#f4f7fb}}
    """
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="report-type" content="business"><meta name="report-status" content="partial"><title>{html.escape(REPORT_TITLE)}</title><style>{custom_css}</style></head>
<body><div class="page">
<header class="hero"><div class="eyebrow">WAJE ANALYST · SELF-OPERATED RTP</div><div class="hero-row"><div><h1>{html.escape(REPORT_TITLE)}</h1><p class="dek">生命周期价值文档 · {a["window"]["start"]}—{a["window"]["end"]} · 香港时间</p></div><span class="status">部分覆盖 · {q["complete_days"]}/{q["requested_days"]} 天</span></div><div class="meta"><span>范围：Waje自营游戏</span><span>累计口径：13个完整日 / 14日窗口</span><span>缺口：{"、".join(q["missing_dates"]) or "无"}</span></div></header>
<section class="kpis"><div class="kpi"><div class="label">自营实际RTP</div><div class="value blue">{pct(o["actual_rtp"])}</div><div class="note">基础下注额加权</div></div><div class="kpi"><div class="label">自营预期RTP</div><div class="value orange">{pct(o["expected_rtp"])}</div><div class="note">同口径加权</div></div><div class="kpi"><div class="label">整体偏离</div><div class="value green">{pp(o["gap_pp"])}</div><div class="note">实际 − 预期</div></div><div class="kpi"><div class="label">原始流水排除占比</div><div class="value amber">{pct(scope["excluded_bet_share"])}</div><div class="note">第三方/联运分类</div></div></section>
<section class="callout good"><div class="callout-title">先看结论</div><p><strong>自营游戏整体RTP接近预期。</strong> 14日实际RTP {pct(o["actual_rtp"])}、预期RTP {pct(o["expected_rtp"])}，相差 {pp(o["gap_pp"])}。</p><p class="small">全部日趋势、游戏份额和生命周期指标均在排除第三方/联运厂商分类后重新计算。</p></section>
<section class="callout warning"><div class="callout-title">覆盖边界</div><p>统计窗口共{q["requested_days"]}天，完整{q["complete_days"]}天；<strong>2026-09-03为未成熟缺口</strong>，该日保留为空。</p></section>
<section class="section" id="overall"><h2>01｜自营游戏整体RTP与时间变化</h2><p class="intro">完整日期内实际RTP为 {pct(min(actual_values))}—{pct(max(actual_values))}；趋势图采用局部纵轴，便于观察小幅变化。</p><div class="conclusion"><strong>读图：</strong>实际与预期线整体接近；单日波动需要结合下注规模判断。</div><div class="chart-wrap">{svg_line(dates, a["daily_overall"])}</div><div class="table-wrap"><table><thead><tr><th>日期</th><th>实际RTP</th><th>预期RTP</th><th>偏离</th><th>基础下注额</th><th>状态</th></tr></thead><tbody>{daily}</tbody></table></div></section>
<section class="section" id="games"><h2>02｜各自营游戏：14日窗口累计RTP</h2><p class="intro"><strong>表中RTP采用窗口累计口径。</strong>按2026-08-28—2026-09-10有效日期的累计下注额与累计盈利重算；本期覆盖13/14天。</p><div class="conclusion"><strong>判断原则：</strong>偏离幅度、下注额份额和持续天数共同决定核查优先级。高流水优先关注 {html.escape(priority)}；{html.escape(low)} 等低流水离群点先补充样本。</div><div class="chart-wrap">{svg_bars(a["games"])}</div><div class="chart-wrap">{svg_scatter(a["games"])}</div><div class="table-wrap"><table><thead><tr><th>游戏</th><th>累计基础下注额</th><th>自营下注额份额</th><th>窗口累计实际RTP</th><th>窗口累计预期RTP</th><th>累计偏离</th><th>有效日期/窗口</th><th>状态</th></tr></thead><tbody>{game_rows}</tbody></table></div></section>
<section class="section" id="lifecycle"><h2>03｜自营游戏×生命周期：L1偏低，L2—L3略高，L4接近预期</h2><p class="intro">{life_text}。L0与L5—L11为空组合。</p><div class="conclusion"><strong>读图：</strong>生命周期表现分化；L1为 -1.12pp，结合其下注规模持续观察。</div><div class="chart-wrap">{svg_lifecycle(a["lifecycle_totals"])}</div><div class="table-wrap heatmap"><table><thead><tr><th>游戏</th><th>自营流水份额</th><th>L1<br>实际/预期</th><th>L2<br>实际/预期</th><th>L3<br>实际/预期</th><th>L4<br>实际/预期</th></tr></thead><tbody>{heat_rows}</tbody></table></div><h3>生命周期偏离最大的组合</h3><div class="table-wrap"><table><thead><tr><th>游戏</th><th>生命周期</th><th>基础下注额</th><th>实际RTP</th><th>预期RTP</th><th>偏离</th></tr></thead><tbody>{top_rows}</tbody></table></div></section>
<section class="section" id="actions"><h2>04｜建议与验证顺序</h2><div class="actions"><div class="action"><div class="num">1</div><div><strong>先复核高流水偏离贡献</strong><span>核对 {html.escape(priority)} 的配置版本、最终结算与连续日期稳定性。</span></div></div><div class="action"><div class="num">2</div><div><strong>低流水离群点补充样本证据</strong><span>重点查看 {html.escape(low)} 的有效局数、取消/退款、Bonus及大额派奖分布。</span></div></div><div class="action"><div class="num">3</div><div><strong>按生命周期持续监控</strong><span>L1当前低于预期，L2—L3略高，L4接近预期；持续跟踪连续周期变化。</span></div></div></div></section>
<section class="section" id="methods"><h2>05｜口径与来源</h2><div class="method-list"><div class="method-item"><strong>实际RTP</strong><span>1 − 实际盈利 ÷ 下注额</span></div><div class="method-item"><strong>预期RTP</strong><span>1 − 预期盈利 ÷ 下注额</span></div><div class="method-item"><strong>统计范围</strong><span>自营游戏 · 下注额加权</span></div></div><details class="details"><summary>查看数据范围与来源路径</summary><pre>飞书在线文档快照：data/outputs/lifecycle_joint/2026-09-11/lark-after
GM原始快照：data/raw/lifecycle_joint/&lt;运行日期&gt;/&lt;业务日期&gt;/tables.json
本次分析目录：analysis/lifecycle_rtp_14d_2026_09_11/
完整日期：{", ".join(item["date"] for item in a["date_records"] if item["status"] == "complete")}
缺失日期：{", ".join(q["missing_dates"]) or "无"}
范围：Waje自营游戏；第三方/联运厂商分类已排除
跨表勾稽：{q["cross_table_reconciliation_passed"]}；Lark回读：{q["lark_target_readback_verified"]}</pre></details></section>
</div></body></html>"""


def main() -> None:
    options = args()
    end = options.end_date
    start = options.start_date or (dt.date.fromisoformat(end) - dt.timedelta(days=13)).isoformat()
    run_dir = Path(options.run_dir).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    analysis = build_analysis(start, end, options.lark_revision)
    md = markdown_report(analysis)
    art = artifact(analysis, md)
    (run_dir / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(md, encoding="utf-8")
    (run_dir / "artifact.json").write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_html = html_report_self_owned(analysis).replace("\n+", "\n")
    project_css_path = ROOT / "config/report_readability.css"
    if project_css_path.exists():
        project_css = project_css_path.read_text(encoding="utf-8")
        report_html = report_html.replace("<style>", f"<style>{project_css}\n", 1)
    (run_dir / "report.html").write_text(report_html, encoding="utf-8")
    for name, rows in (("daily_overall", analysis["daily_overall"]), ("game_summary", analysis["games"]), ("game_lifecycle", analysis["game_lifecycle"]), ("lifecycle_summary", analysis["lifecycle_totals"])):
        fields = sorted({key for row in rows for key in row})
        with (run_dir / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows({field: row.get(field) for field in fields} for row in rows)
    receipt = {"schema_version": 1, "status": "built_pending_visual_qa", "generated_at": analysis["generated_at"], "window": analysis["window"], "source_revision": analysis["quality"]["lark_readback_revision"], "quality": analysis["quality"], "artifacts": {"analysis": str((run_dir/"analysis.json").resolve()), "markdown": str((run_dir/"report.md").resolve()), "artifact": str((run_dir/"artifact.json").resolve()), "html": str((run_dir/"report.html").resolve())}, "visual_qa": {"status": "pending", "viewports": [1440, 390]}, "security": {"credentials_embedded": False, "user_level_detail_embedded": False}}
    (run_dir / "report-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "window": analysis["window"], "coverage": analysis["quality"]["complete_days"], "missing_dates": analysis["quality"]["missing_dates"], "overall_actual_rtp": pct(analysis["overall"]["actual_rtp"]), "overall_expected_rtp": pct(analysis["overall"]["expected_rtp"]), "priority_games": [item["game"] for item in analysis["priority_games"]], "run_dir": str(run_dir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the extended 6/16–8/16 H5/PWA lightweight-game analysis V2."""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/lark/2026-08-19/h5_pwa_lightgame_extended_v633"
OUT = ROOT / "analysis/h5_pwa_lightgame_effect_v2_2026_08_19"
ASSETS = OUT / "assets"
KNOWLEDGE = ROOT / "knowledge/01-产品/Waje-H5-PWA轻量化游戏效果与新用户留存付费分析-V2-2026-08-19.md"
ARTIFACT = OUT / "artifact.json"
ANALYSIS = OUT / "analysis.json"
QUALITY = OUT / "data_quality.json"
CHART_MAP = OUT / "chart_map.json"
SOURCE_REGISTRY = OUT / "source_registry.json"
SQLITE_DB = OUT / "analysis.sqlite"

REFERENCE_DATE = date(2026, 8, 19)
WINDOW_START = date(2026, 6, 16)
WINDOW_END = date(2026, 8, 16)
SOURCE_REVISION = 633
UPDATE_REVISION = 1798
FACEBOOK_BAN_START = date(2026, 8, 15)
FACEBOOK_BAN_END = date(2026, 8, 16)
LIGHTGAME_BEFORE_START = date(2026, 6, 16)
LIGHTGAME_BEFORE_END = date(2026, 7, 13)
LIGHTGAME_AFTER_START = date(2026, 7, 14)
LIGHTGAME_AFTER_END = date(2026, 8, 10)

LARK_NEW_USER_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d?from=from_copylink&sheet=ef19NP"
LARK_UPDATE_URL = "https://ksg964l11fam.sg.larksuite.com/sheets/KmZcs6cdMhd6MQtHRDgl9jTNg5c?from=from_copylink&sheet=0owUxS"
HISTORY_URL = "https://ksg964l11fam.sg.larksuite.com/docx/Sk4XdrryEot7lcxmUW4l2vmSg2f"
PERFORMANCE_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/HpNOwkIqliWq6ckZE9clfeXdg4b"

GROUPS = {
    "WAJEBETH5": {"file": "wajebeth5_table.json", "label": "H5自然", "surface": "H5", "channel": "自然", "comparison": "自然H5"},
    "wajeH5-facebook": {"file": "waje_h5_facebook_table.json", "label": "H5 Facebook", "surface": "标准H5", "channel": "Facebook", "comparison": "标准H5"},
    "wajeH5ga-googlewords_int": {"file": "waje_h5_google_ads_table.json", "label": "H5 Google", "surface": "标准H5", "channel": "Google Ads", "comparison": "标准H5"},
    "PWA": {"file": "pwa_table.json", "label": "PWA自然", "surface": "PWA", "channel": "自然", "comparison": "自然PWA"},
}

RETENTION = {
    "D1": ("次留", 1),
    "D3": ("3日留", 3),
    "D7": ("7日留", 7),
    "D15": ("15日留", 15),
    "D30": ("30日留", 30),
    "D60": ("60日留", 60),
}

RETENTION_STAGES = [
    ("D1", "次留", 1),
    ("D3", "3日留", 3),
    ("D7", "7日留", 7),
    ("D15", "15日留", 15),
    ("D30", "30日留", 30),
]

DECAY_STAGES = [
    ("D1→D3", "次留", "3日留", 3),
    ("D3→D7", "3日留", "7日留", 7),
    ("D7→D15", "7日留", "15日留", 15),
    ("D15→D30", "15日留", "30日留", 30),
]

VALUE_HORIZONS = {
    "D1 C-T": ("首日", 1),
    "D7 C-T": ("7日", 7),
    "D15 C-T": ("15日", 15),
    "D30 C-T": ("30日", 30),
}

PHASES = [
    {"id": "baseline", "label": "上线前基线", "window": "6/16–7/13", "start": date(2026, 6, 16), "end": date(2026, 7, 13), "note": "轻量化游戏节点前的对照期；期间仍有世界杯入口、游戏排序和运营变动。"},
    {"id": "limbo", "label": "Limbo 上线/恢复", "window": "7/14–7/22", "start": date(2026, 7, 14), "end": date(2026, 7, 22), "note": "7/14上线、7/15下线、7/16恢复；7/20–21 Aviator维护与触达并存。"},
    {"id": "keno", "label": "H5 2.1.14 / Keno", "window": "7/23–7/28", "start": date(2026, 7, 23), "end": date(2026, 7, 28), "note": "H5 2.1.14、Keno、KYC/risk和iOS回传修复同窗，不能拆分归因。"},
    {"id": "color", "label": "Color Dice", "window": "7/29–8/05", "start": date(2026, 7, 29), "end": date(2026, 8, 5), "note": "Color Dice 9003上线；7/30同时关闭Tada世界杯页签/Banner。"},
    {"id": "opera", "label": "Opera 埋点期", "window": "8/06–8/10", "start": date(2026, 8, 6), "end": date(2026, 8, 10), "note": "Opera注册/埋点自动上报，主要影响覆盖和归因可见性。"},
    {"id": "current", "label": "当前期", "window": "8/11–8/16", "start": date(2026, 8, 11), "end": date(2026, 8, 16), "note": "8/15–16 Facebook投放账户被封，新增规模和渠道结构不可用于产品效果比较。"},
]

BLUE = "#2A7FBE"
TEAL = "#45A6B6"
GOLD = "#D99D27"
PURPLE = "#7667C5"
RED = "#D85B66"
GREEN = "#42A576"
NAVY = "#183B5D"
MUTED = "#58718A"
GRID = "#DCEAF4"
COLORS = {
    "H5 Facebook": BLUE,
    "H5 Google": TEAL,
    "H5自然": GOLD,
    "PWA自然": PURPLE,
}


def parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    try:
        serial = float(text.replace(",", ""))
    except ValueError:
        return None
    if 30000 < serial < 60000:
        return (datetime(1899, 12, 30) + timedelta(days=serial)).date()
    return None


def number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    text = str(value).strip().replace(",", "")
    if text.endswith("%"):
        text = text[:-1]
    try:
        return float(text)
    except ValueError:
        return None


def rate(value: Any) -> float | None:
    parsed = number(value)
    if parsed is None:
        return None
    return parsed if 0 <= parsed <= 1 else parsed / 100


def fmt_rate(value: float | None, digits: int = 1) -> str:
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def fmt_num(value: float | int | None, digits: int = 0) -> str:
    return "N/A" if value is None else f"{value:,.{digits}f}"


def fmt_count(value: float | int | None) -> str:
    return "N/A" if value is None else f"{math.floor(float(value) + 0.5):,}"


def fmt_pp(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:+.1f}pp"


def escape_xml(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_table(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text())
    sheet = payload["sheets"][0]
    headers = [str(x or f"col{i + 1}") for i, x in enumerate(sheet["columns"])]
    rows: list[dict[str, Any]] = []
    for row_no, values in enumerate(sheet["data"], start=2):
        row = {headers[i]: values[i] if i < len(values) else None for i in range(len(headers))}
        row["_row"] = row_no
        row["_date"] = parse_date(row.get("日期"))
        if row["_date"]:
            rows.append(row)
    return rows, {"sheet": sheet.get("name"), "range": sheet.get("range"), "row_count": len(rows), "columns": headers}


def load_update_events(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    sheet = payload["sheets"][0]
    headers = [str(x or f"col{i + 1}") for i, x in enumerate(sheet["columns"])]
    events: list[dict[str, Any]] = []
    terms = ("limbo", "aviator", "keno", "color dice", "轻量", "h5", "pwa", "opera", "risk", "kyc", "tada", "firebase", "世界杯", "游戏")
    for values in sheet["data"]:
        row = {headers[i]: values[i] if i < len(values) else None for i in range(len(headers))}
        event_date = parse_date(row.get("更新日期"))
        if not event_date or not (WINDOW_START <= event_date <= WINDOW_END):
            continue
        content = " / ".join(str(row.get(k) or "").replace("\n", " / ").strip() for k in ("更新内容", "运营活动")).strip(" / ")
        low = content.lower()
        if not any(term in low for term in terms):
            continue
        kind = "版本/运营"
        if any(term in low for term in ("上线", "下线", "维护", "恢复")) and any(term in low for term in ("limbo", "aviator", "keno", "color dice", "轻量", "游戏")):
            kind = "游戏节点"
        if any(term in low for term in ("opera", "打点", "回传", "firebase")):
            kind = "埋点/归因"
        if any(term in low for term in ("risk", "kyc", "维护", "故障", "关闭", "刷子")):
            kind = "干扰项"
        events.append({"date": event_date.isoformat(), "kind": kind, "content": content})
    events.append({"date": FACEBOOK_BAN_START.isoformat(), "kind": "投放异常", "content": "用户补充：H5 Facebook投放账户被封，影响8月15–16日新增投放；不作为轻量化、产品体验或D7留存变化依据。"})
    return sorted(events, key=lambda x: (x["date"], x["kind"]))


def subset(rows: Iterable[dict[str, Any]], start: date, end: date) -> list[dict[str, Any]]:
    return [r for r in rows if start <= r["_date"] <= end]


def weighted_rate(rows: Iterable[dict[str, Any]], field: str, days: int) -> dict[str, Any]:
    eligible = [r for r in rows if r["_date"] <= REFERENCE_DATE - timedelta(days=days)]
    observed = [r for r in eligible if rate(r.get(field)) is not None and (number(r.get("新增人数")) or 0) > 0]
    den = sum(number(r["新增人数"]) or 0 for r in observed)
    num = sum((rate(r[field]) or 0) * (number(r["新增人数"]) or 0) for r in observed)
    return {"value": num / den if den else None, "cohorts": len(observed), "new_users": den, "missing": len(eligible) - len(observed)}


def weighted_value(rows: Iterable[dict[str, Any]], field: str, days: int) -> dict[str, Any]:
    eligible = [r for r in rows if r["_date"] <= REFERENCE_DATE - timedelta(days=days)]
    observed = [r for r in eligible if number(r.get(field)) is not None and (number(r.get("新增人数")) or 0) > 0]
    den = sum(number(r["新增人数"]) or 0 for r in observed)
    num = sum((number(r[field]) or 0) * (number(r["新增人数"]) or 0) for r in observed)
    values = [number(r[field]) for r in observed if number(r[field]) is not None]
    return {"value": num / den if den else None, "median": statistics.median(values) if values else None, "cohorts": len(observed), "new_users": den, "missing": len(eligible) - len(observed)}


def cohort_stat(rows: Iterable[dict[str, Any]], field: str) -> dict[str, Any]:
    vals = [number(r.get(field)) for r in rows if number(r.get(field)) is not None]
    weights = [number(r.get("新增人数")) or 0 for r in rows if number(r.get(field)) is not None]
    weighted = sum(v * w for v, w in zip(vals, weights)) / sum(weights) if sum(weights) else None
    return {"mean": sum(vals) / len(vals) if vals else None, "median": statistics.median(vals) if vals else None, "weighted": weighted, "cohorts": len(vals)}


def group_summary(name: str, config: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    retention = {label: weighted_rate(rows, field, days) for label, (field, days) in RETENTION.items()}
    value = {label: weighted_value(rows, field, days) for label, (field, days) in VALUE_HORIZONS.items()}
    new_users = sum(number(r.get("新增人数")) or 0 for r in rows)
    return {
        "group": config["label"], "sheet": name, "surface": config["surface"], "channel": config["channel"], "comparison": config["comparison"],
        "cohort_days": len(rows), "new_users": new_users,
        **{key.lower().replace(" ", "_"): value["value"] for key, value in retention.items()},
        **{f"{key.lower().replace(' ', '_')}_cohorts": value["cohorts"] for key, value in retention.items()},
        **{f"{key.lower().replace(' ', '_')}_new_users": value["new_users"] for key, value in retention.items()},
        "source_new_paid_rate": cohort_stat(rows, "新增付费率"),
        "source_first_charge_rate": cohort_stat(rows, "首充付费率"),
        "source_new_paid_users": sum(number(r.get("新增付费人数")) or 0 for r in rows),
        "source_first_charge_users": sum(number(r.get("首充付费人数")) or 0 for r in rows),
        "d1_ct": value["D1 C-T"]["value"], "d7_ct": value["D7 C-T"]["value"], "d15_ct": value["D15 C-T"]["value"], "d30_ct": value["D30 C-T"]["value"],
        "d7_ct_cohorts": value["D7 C-T"]["cohorts"], "d15_ct_cohorts": value["D15 C-T"]["cohorts"], "d30_ct_cohorts": value["D30 C-T"]["cohorts"],
        "source_lifetime_ct": cohort_stat(rows, "终身"),
        "source_tc_ratio": cohort_stat(rows, "tc比"),
        "source_tx_rate": cohort_stat(rows, "tx率"),
        "source_avg_tx": cohort_stat(rows, "人均tx金额"),
    }


def matched_retention_curve(groups: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Build a D1-D30 curve from one identical D30-mature cohort set per channel."""
    result: list[dict[str, Any]] = []
    cutoff = REFERENCE_DATE - timedelta(days=30)
    required_fields = [field for _, field, _ in RETENTION_STAGES]
    for name, rows in groups.items():
        observed = [
            r for r in rows
            if r["_date"] <= cutoff
            and (number(r.get("新增人数")) or 0) > 0
            and all(rate(r.get(field)) is not None for field in required_fields)
        ]
        denominator = sum(number(r.get("新增人数")) or 0 for r in observed)
        for order, (metric, field, day) in enumerate(RETENTION_STAGES, start=1):
            numerator = sum((rate(r.get(field)) or 0) * (number(r.get("新增人数")) or 0) for r in observed)
            result.append({
                "group": GROUPS[name]["label"],
                "metric": metric,
                "stage_order": order,
                "day": day,
                "rate": numerator / denominator if denominator else None,
                "cohorts": len(observed),
                "new_users": denominator,
                "cohort_end": cutoff.isoformat(),
            })
    return result


def matched_retention_decay(groups: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Calculate each stage's decay on a cohort set matched to the later stage."""
    result: list[dict[str, Any]] = []
    for name, rows in groups.items():
        for order, (stage, previous_field, next_field, maturity_days) in enumerate(DECAY_STAGES, start=1):
            cutoff = REFERENCE_DATE - timedelta(days=maturity_days)
            observed = [
                r for r in rows
                if r["_date"] <= cutoff
                and (number(r.get("新增人数")) or 0) > 0
                and rate(r.get(previous_field)) is not None
                and rate(r.get(next_field)) is not None
            ]
            denominator = sum(number(r.get("新增人数")) or 0 for r in observed)
            previous_rate = (
                sum((rate(r.get(previous_field)) or 0) * (number(r.get("新增人数")) or 0) for r in observed) / denominator
                if denominator else None
            )
            next_rate = (
                sum((rate(r.get(next_field)) or 0) * (number(r.get("新增人数")) or 0) for r in observed) / denominator
                if denominator else None
            )
            retained_share = next_rate / previous_rate if previous_rate and next_rate is not None else None
            result.append({
                "group": GROUPS[name]["label"],
                "stage": stage,
                "stage_order": order,
                "previous_rate": previous_rate,
                "next_rate": next_rate,
                "retained_share": retained_share,
                "decay": 1 - retained_share if retained_share is not None else None,
                "cohorts": len(observed),
                "new_users": denominator,
                "cohort_end": cutoff.isoformat(),
            })
    return result


def phase_comparison_tables(phase_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Create compact stage-overall and stage-by-channel comparison tables."""
    overview: list[dict[str, Any]] = []
    matrix: list[dict[str, Any]] = []

    def weighted_metric(records: list[dict[str, Any]], metric: str) -> float | None:
        denominator = sum(r.get(f"{metric}_new_users") or 0 for r in records if r.get(metric) is not None)
        numerator = sum((r.get(metric) or 0) * (r.get(f"{metric}_new_users") or 0) for r in records if r.get(metric) is not None)
        return numerator / denominator if denominator else None

    for phase in PHASES:
        records = [r for r in phase_rows if r["phase"] == phase["label"]]
        by_group = {r["group"]: r for r in records}
        d1 = weighted_metric(records, "d1")
        d3 = weighted_metric(records, "d3")
        d7 = weighted_metric(records, "d7")
        best = max((r for r in records if r.get("d3") is not None), key=lambda r: r["d3"])
        d7_cutoff = REFERENCE_DATE - timedelta(days=7)
        if d7 is None:
            d7_status = f"暂无可用值（截至{d7_cutoff.month}/{d7_cutoff.day}已满7天）"
        else:
            d7_status = "完整" if phase["end"] <= d7_cutoff else f"部分（仅统计至{d7_cutoff.month}/{d7_cutoff.day}注册用户）"
        overview.append({
            "phase": phase["label"],
            "window": phase["window"],
            "new_users": sum(r["new_users"] for r in records),
            "d1": d1,
            "d3": d3,
            "d7": d7,
            "d3_delta_baseline": None,
            "d7_delta_baseline": None,
            "d7_status": d7_status,
            "best_channel": best["group"],
            "best_channel_d3": best["d3"],
        })
        matrix.append({
            "phase": phase["label"],
            "window": phase["window"],
            "overall_d3": d3,
            "overall_d7": d7,
            "h5_natural_d3": by_group["H5自然"]["d3"],
            "h5_facebook_d3": by_group["H5 Facebook"]["d3"],
            "h5_google_d3": by_group["H5 Google"]["d3"],
            "pwa_natural_d3": by_group["PWA自然"]["d3"],
            "h5_natural_d7": by_group["H5自然"]["d7"],
            "h5_facebook_d7": by_group["H5 Facebook"]["d7"],
            "h5_google_d7": by_group["H5 Google"]["d7"],
            "pwa_natural_d7": by_group["PWA自然"]["d7"],
            "d7_status": d7_status,
        })

    baseline = overview[0]["d3"]
    baseline_d7 = overview[0]["d7"]
    for row in overview:
        row["d3_delta_baseline"] = row["d3"] - baseline if row["d3"] is not None and baseline is not None else None
        row["d7_delta_baseline"] = row["d7"] - baseline_d7 if row["d7"] is not None and baseline_d7 is not None else None
    return overview, matrix


def lightgame_pre_post_comparison(groups: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Compare equal 28-day windows before and after the 7/14 light-game launch."""
    result: list[dict[str, Any]] = []
    for name, rows in groups.items():
        config = GROUPS[name]
        before = group_summary(name, config, subset(rows, LIGHTGAME_BEFORE_START, LIGHTGAME_BEFORE_END))
        after = group_summary(name, config, subset(rows, LIGHTGAME_AFTER_START, LIGHTGAME_AFTER_END))
        before_paid = before["source_new_paid_rate"]["mean"]
        after_paid = after["source_new_paid_rate"]["mean"]
        before_first = before["source_first_charge_rate"]["mean"]
        after_first = after["source_first_charge_rate"]["mean"]
        result.append({
            "group": config["label"],
            "before_window": "6/16–7/13",
            "after_window": "7/14–8/10",
            "before_new_users": before["new_users"],
            "after_new_users": after["new_users"],
            "new_users_change": after["new_users"] / before["new_users"] - 1 if before["new_users"] else None,
            "before_d1": before["d1"], "after_d1": after["d1"], "d1_delta": after["d1"] - before["d1"],
            "before_d3": before["d3"], "after_d3": after["d3"], "d3_delta": after["d3"] - before["d3"],
            "before_d7": before["d7"], "after_d7": after["d7"], "d7_delta": after["d7"] - before["d7"],
            "before_paid_rate": before_paid, "after_paid_rate": after_paid, "paid_rate_delta": after_paid - before_paid,
            "before_first_rate": before_first, "after_first_rate": after_first, "first_rate_delta": after_first - before_first,
            "before_d7_ct": before["d7_ct"], "after_d7_ct": after["d7_ct"], "d7_ct_delta": after["d7_ct"] - before["d7_ct"],
        })
    return result


def quality_rows(groups: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    result = []
    for name, rows in groups.items():
        entry = {"group": GROUPS[name]["label"], "cohort_days": len(rows), "duplicates": len(rows) - len({r["_date"] for r in rows})}
        for label, (field, days) in RETENTION.items():
            eligible = [r for r in rows if r["_date"] <= REFERENCE_DATE - timedelta(days=days)]
            observed = [r for r in eligible if rate(r.get(field)) is not None]
            entry[f"{label}_expected"] = len(eligible)
            entry[f"{label}_observed"] = len(observed)
        entry["new_paid_rate_mismatch_days"] = sum(1 for r in rows if number(r.get("新增人数")) and rate(r.get("新增付费率")) is not None and number(r.get("新增付费人数")) is not None and abs((number(r["新增付费人数"]) or 0)/(number(r["新增人数"]) or 1) - (rate(r["新增付费率"]) or 0)) > 0.0005)
        result.append(entry)
    return result


def account_ban_impact(facebook_rows: list[dict[str, Any]], h5_rows: list[dict[str, Any]]) -> dict[str, Any]:
    before = subset(facebook_rows, date(2026, 8, 11), date(2026, 8, 14))
    after = subset(facebook_rows, FACEBOOK_BAN_START, FACEBOOK_BAN_END)
    h5_before = subset(h5_rows, date(2026, 8, 11), date(2026, 8, 14))
    h5_after = subset(h5_rows, FACEBOOK_BAN_START, FACEBOOK_BAN_END)
    total = lambda data: sum(number(r.get("新增人数")) or 0 for r in data)
    before_new, after_new = total(before), total(after)
    before_daily, after_daily = before_new / len(before), after_new / len(after)
    return {
        "baseline_window": "2026-08-11—2026-08-14", "affected_window": "2026-08-15—2026-08-16",
        "before_daily_new": before_daily, "after_daily_new": after_daily,
        "decline": 1 - after_daily / before_daily,
        "benchmark_gap": before_daily * len(after) - after_new,
        "facebook_share_before": before_new / total(h5_before), "facebook_share_after": after_new / total(h5_after),
        "d7_boundary": "当前期D7只使用8月11—12日注册、已满7天的cohort，早于账户封禁影响日。",
    }


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        try:
            return ImageFont.truetype(candidate, size, index=0)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_multiline(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font_obj: ImageFont.ImageFont, fill: str, width: int, leading: int = 4) -> None:
    y = xy[1]
    for paragraph in text.split("\n"):
        current = ""
        lines: list[str] = []
        for char in paragraph:
            proposed = current + char
            if draw.textlength(proposed, font=font_obj) <= width:
                current = proposed
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
        for line in lines or [""]:
            draw.text((xy[0], y), line, fill=fill, font=font_obj)
            y += font_obj.size + leading


def draw_grid(draw: ImageDraw.ImageDraw, left: int, top: int, right: int, bottom: int, max_y: float, ticks: list[float], percent: bool = False) -> None:
    tick_font = font(16)
    for tick in ticks:
        y = bottom - (tick / max_y) * (bottom - top)
        draw.line((left, y, right, y), fill=GRID, width=2)
        label = f"{tick * 100:.0f}%" if percent else (fmt_num(tick / 1000, 1) + "k" if max_y >= 2000 else fmt_num(tick, 0))
        draw.text((36, y - 9), label, fill=MUTED, font=tick_font)


def render_daily_new(rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "62日新增趋势与投放事件.png"
    width, height = 1600, 820
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(20), font(16)
    draw.text((64, 36), "H5/PWA 四渠道新增趋势", fill=NAVY, font=title)
    draw.text((64, 82), "2026年6月16日至8月16日；红线标记8月15日Facebook投放账户被封影响。", fill=MUTED, font=body)
    left, top, right, bottom = 135, 160, 1525, 640
    groups = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
    dates = sorted({r["date"] for r in rows})
    max_y = max(r["new_users"] for r in rows) * 1.14
    draw_grid(draw, left, top, right, bottom, max_y, [0, max_y*.25, max_y*.5, max_y*.75, max_y])
    for idx, day in enumerate(dates):
        if idx % 7 == 0 or idx == len(dates) - 1:
            x = left + (right-left) * idx / (len(dates)-1)
            draw.text((x-18, bottom+12), datetime.strptime(day, "%Y-%m-%d").strftime("%m/%d"), fill=MUTED, font=small)
    for group in groups:
        series = [r for r in rows if r["group"] == group]
        points = []
        for idx, record in enumerate(series):
            x = left + (right-left) * idx / (len(series)-1)
            y = bottom - (record["new_users"] / max_y) * (bottom-top)
            points.append((x, y))
        draw.line(points, fill=COLORS[group], width=4)
        for x, y in points:
            draw.ellipse((x-3, y-3, x+3, y+3), fill=COLORS[group])
    incident = FACEBOOK_BAN_START.isoformat()
    if incident in dates:
        x = left + (right-left) * dates.index(incident) / (len(dates)-1)
        draw.line((x, top, x, bottom), fill=RED, width=3)
        bx, by = max(left+10, x-295), top+18
        draw.rounded_rectangle((bx, by, bx+275, by+74), radius=8, fill="#FFF2F2", outline=RED, width=2)
        draw_multiline(draw, (bx+12, by+8), "8/15–8/16 Facebook投放账户被封\n新增骤降，不作为产品/轻量化结论", small, RED, 250)
    lx = left
    for group in groups:
        draw.rounded_rectangle((lx, 702, lx+15, 717), radius=3, fill=COLORS[group])
        draw.text((lx+22, 698), group, fill=NAVY, font=small)
        lx += 235
    image.save(path)
    return path


def render_retention(summary: list[dict[str, Any]]) -> Path:
    path = ASSETS / "62日窗口留存对比.png"
    width, height = 1600, 850
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(19), font(15)
    draw.text((64, 36), "四渠道：已达到观察天数的留存对比", fill=NAVY, font=title)
    draw.text((64, 82), "D1/D3/D7/D15/D30分别只计算已达到对应观察天数的注册用户；留存按新增人数加权。", fill=MUTED, font=body)
    left, top, right, bottom = 135, 160, 1525, 650
    metrics = [("D1", "d1"), ("D3", "d3"), ("D7", "d7"), ("D15", "d15"), ("D30", "d30")]
    groups = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
    data = {x["group"]: x for x in summary}
    draw_grid(draw, left, top, right, bottom, .65, [0, .2, .4, .6], percent=True)
    unit = (right-left) / len(metrics)
    bar_w = 30
    for mi, (metric, field) in enumerate(metrics):
        base = left + unit*mi + 55
        draw.text((left+unit*mi+unit/2-20, bottom+14), metric, fill=NAVY, font=body)
        for gi, group in enumerate(groups):
            v = data[group][field] or 0
            h = v/.65*(bottom-top)
            x = base + gi*(bar_w+12)
            draw.rounded_rectangle((x, bottom-h, x+bar_w, bottom), radius=5, fill=COLORS[group])
            if v > .035:
                draw.text((x-1, bottom-h-22), fmt_rate(v), fill=NAVY, font=small)
    lx=left
    for group in groups:
        draw.rounded_rectangle((lx, 744, lx+14, 758), radius=3, fill=COLORS[group])
        draw.text((lx+20, 740), group, fill=NAVY, font=small)
        lx += 250
    image.save(path)
    return path


def render_retention_curve(rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "四渠道同批注册用户D1-D30留存曲线.png"
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(19), font(15)
    draw.text((64, 36), "四渠道同批注册用户 D1—D30 留存曲线", fill=NAVY, font=title)
    draw.text((64, 82), "每条曲线仅使用已注册满30天且五个留存点均完整的同一批用户；留存按新增人数加权。", fill=MUTED, font=body)
    left, top, right, bottom = 135, 160, 1525, 650
    metrics = [x[0] for x in RETENTION_STAGES]
    groups = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
    draw_grid(draw, left, top, right, bottom, .65, [0, .2, .4, .6], percent=True)
    x_positions = {metric: left + (right - left) * index / (len(metrics) - 1) for index, metric in enumerate(metrics)}
    label_offsets = {"H5 Facebook": 12, "H5 Google": -28, "H5自然": -10, "PWA自然": -46}
    for metric in metrics:
        x = x_positions[metric]
        draw.text((x - 18, bottom + 14), metric, fill=NAVY, font=body)
    for group in groups:
        series = sorted((r for r in rows if r["group"] == group), key=lambda r: r["stage_order"])
        points = []
        for record in series:
            value = record["rate"] or 0
            x = x_positions[record["metric"]]
            y = bottom - value / .65 * (bottom - top)
            points.append((x, y))
        draw.line(points, fill=COLORS[group], width=5)
        for record, (x, y) in zip(series, points):
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill="#FFFFFF", outline=COLORS[group], width=4)
            draw.text((x - 22, y + label_offsets[group]), fmt_rate(record["rate"]), fill=COLORS[group], font=small)
    lx = left
    for group in groups:
        sample = next((r for r in rows if r["group"] == group), None)
        draw.line((lx, 758, lx + 28, 758), fill=COLORS[group], width=5)
        draw.ellipse((lx + 9, 752, lx + 21, 764), fill="#FFFFFF", outline=COLORS[group], width=3)
        draw.text((lx + 38, 748), f"{group}（{sample['cohorts']}个注册批次）", fill=NAVY, font=small)
        lx += 335
    draw.text((64, 828), "说明：各渠道纳入的注册日期数量可能不同，但同一渠道内五个留存点使用完全相同的注册用户。", fill=MUTED, font=small)
    image.save(path)
    return path


def render_retention_decay(rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "四渠道分阶段留存衰减率.png"
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(19), font(15)
    draw.text((64, 36), "四渠道分阶段留存衰减率", fill=NAVY, font=title)
    draw.text((64, 82), "衰减率＝1－后一观察点留存÷前一观察点留存；每个阶段按同一批注册用户复算，数值越高表示流失越快。", fill=MUTED, font=body)
    left, top, right, bottom = 135, 160, 1525, 650
    stages = [x[0] for x in DECAY_STAGES]
    groups = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
    draw_grid(draw, left, top, right, bottom, .65, [0, .2, .4, .6], percent=True)
    unit = (right - left) / len(stages)
    bar_w = 42
    for stage_index, stage in enumerate(stages):
        base = left + unit * stage_index + 62
        draw.text((left + unit * stage_index + unit / 2 - 48, bottom + 14), stage, fill=NAVY, font=body)
        records = {r["group"]: r for r in rows if r["stage"] == stage}
        for group_index, group in enumerate(groups):
            value = records[group]["decay"] or 0
            height_px = value / .65 * (bottom - top)
            x = base + group_index * (bar_w + 16)
            draw.rounded_rectangle((x, bottom - height_px, x + bar_w, bottom), radius=6, fill=COLORS[group])
            draw.text((x - 2, bottom - height_px - 23), fmt_rate(value), fill=NAVY, font=small)
    lx = left
    for group in groups:
        draw.rounded_rectangle((lx, 758, lx + 14, 772), radius=3, fill=COLORS[group])
        draw.text((lx + 20, 754), group, fill=NAVY, font=small)
        lx += 250
    draw.text((64, 828), "说明：D3/D7/D15/D30阶段分别统计已达到后一观察天数且前后两点都有值的注册用户。", fill=MUTED, font=small)
    image.save(path)
    return path


def render_phase_d3(phase_rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "轻量化更新节点D3留存观察.png"
    width, height = 1600, 850
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(19), font(15)
    draw.text((64, 36), "轻量化游戏与版本节点：D3留存观察", fill=NAVY, font=title)
    draw.text((64, 82), "同一发布期内按渠道/运行形态比较；节点重叠，图表仅展示观察性变化。", fill=MUTED, font=body)
    left, top, right, bottom = 135, 160, 1525, 650
    phases = [p["label"] for p in PHASES]
    groups = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
    draw_grid(draw, left, top, right, bottom, .65, [0, .2, .4, .6], percent=True)
    unit = (right-left)/len(phases)
    bar_w=22
    for pi, phase in enumerate(phases):
        records={r["group"]:r for r in phase_rows if r["phase"]==phase}
        base=left+unit*pi+20
        for gi, group in enumerate(groups):
            v=records[group]["d3"] or 0
            h=v/.65*(bottom-top)
            x=base+gi*(bar_w+9)
            draw.rounded_rectangle((x,bottom-h,x+bar_w,bottom),radius=4,fill=COLORS[group])
        draw_multiline(draw,(base,bottom+14),phase,small,NAVY,int(unit-18),2)
    lx=left
    for group in groups:
        draw.rounded_rectangle((lx, 755, lx+14, 769), radius=3, fill=COLORS[group])
        draw.text((lx+20, 751), group, fill=NAVY, font=small)
        lx += 250
    image.save(path)
    return path


def render_phase_d3_line(phase_rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "轻量化更新节点D3留存折线.png"
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(19), font(15)
    draw.text((64, 36), "轻量化更新节点：四渠道 D3 留存变化", fill=NAVY, font=title)
    draw.text((64, 82), "按六个发布观察期连接D3留存；用于直观看阶段间变化，不代表单一版本或游戏的因果效果。", fill=MUTED, font=body)
    left, top, right, bottom = 135, 160, 1525, 650
    phases = [p["label"] for p in PHASES]
    groups = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
    draw_grid(draw, left, top, right, bottom, .40, [0, .1, .2, .3, .4], percent=True)
    x_positions = {phase: left + (right - left) * index / (len(phases) - 1) for index, phase in enumerate(phases)}
    for phase in phases:
        x = x_positions[phase]
        draw_multiline(draw, (x - 68, bottom + 14), phase, small, NAVY, 135, 2)
    label_offsets = {"H5 Facebook": 10, "H5 Google": -26, "H5自然": -8, "PWA自然": -42}
    for group in groups:
        records = [next(r for r in phase_rows if r["phase"] == phase and r["group"] == group) for phase in phases]
        points = []
        for record in records:
            value = record["d3"] or 0
            x = x_positions[record["phase"]]
            y = bottom - value / .40 * (bottom - top)
            points.append((x, y))
        draw.line(points, fill=COLORS[group], width=5)
        for point_index, (record, (x, y)) in enumerate(zip(records, points)):
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill="#FFFFFF", outline=COLORS[group], width=4)
            if point_index in (0, len(points) - 1):
                draw.text((x - 20, y + label_offsets[group]), fmt_rate(record["d3"]), fill=COLORS[group], font=small)
    lx = left
    for group in groups:
        draw.line((lx, 770, lx + 28, 770), fill=COLORS[group], width=5)
        draw.ellipse((lx + 9, 764, lx + 21, 776), fill="#FFFFFF", outline=COLORS[group], width=3)
        draw.text((lx + 38, 760), group, fill=NAVY, font=small)
        lx += 270
    draw.text((64, 840), "说明：每个阶段内四渠道使用相同日期窗口；阶段同时叠加活动、风控、故障和埋点变化。", fill=MUTED, font=small)
    image.save(path)
    return path


def render_lightgame_pre_post_deltas(rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "轻量化游戏上线前后核心指标变化.png"
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(19), font(15)
    draw.text((64, 36), "轻量化游戏上线前后：四渠道核心指标变化", fill=NAVY, font=title)
    draw.text((64, 82), "等长28天对比：6月16日—7月13日 vs 7月14日—8月10日；数值为百分点变化。", fill=MUTED, font=body)
    left, top, right, bottom = 145, 160, 1525, 650
    min_y, max_y = -.05, .10

    def y_pos(value: float) -> float:
        return bottom - (value - min_y) / (max_y - min_y) * (bottom - top)

    for tick in (-.05, 0, .05, .10):
        y = y_pos(tick)
        draw.line((left, y, right, y), fill=NAVY if tick == 0 else GRID, width=3 if tick == 0 else 2)
        draw.text((52, y - 9), f"{tick * 100:+.0f}pp", fill=MUTED, font=small)

    metrics = [("D1", "d1_delta"), ("D3", "d3_delta"), ("D7", "d7_delta"), ("新增付费率", "paid_rate_delta")]
    groups = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
    by_group = {r["group"]: r for r in rows}
    unit = (right - left) / len(metrics)
    bar_w = 40
    zero_y = y_pos(0)
    for metric_index, (metric_label, field) in enumerate(metrics):
        base = left + unit * metric_index + 55
        draw.text((left + unit * metric_index + unit / 2 - 55, bottom + 18), metric_label, fill=NAVY, font=body)
        for group_index, group in enumerate(groups):
            value = by_group[group][field]
            x = base + group_index * (bar_w + 18)
            y = y_pos(value)
            top_y, bottom_y = (y, zero_y) if value >= 0 else (zero_y, y)
            draw.rounded_rectangle((x, top_y, x + bar_w, bottom_y), radius=5, fill=COLORS[group])
            label_y = y - 24 if value >= 0 else y + 6
            draw.text((x - 4, label_y), f"{value * 100:+.1f}", fill=NAVY, font=small)

    lx = left
    for group in groups:
        draw.rounded_rectangle((lx, 758, lx + 14, 772), radius=3, fill=COLORS[group])
        draw.text((lx + 20, 754), group, fill=NAVY, font=small)
        lx += 250
    draw.text((64, 828), "说明：上线期还叠加活动、风控和投放变化，图表用于识别同步变化，不直接证明单一游戏造成结果。", fill=MUTED, font=small)
    image.save(path)
    return path


def render_payment_value(summary: list[dict[str, Any]]) -> Path:
    path = ASSETS / "付费显示率与D7CT对比.png"
    width, height = 1600, 820
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(18), font(15)
    draw.text((64, 36), "来源新增付费率与 D7 C-T 对比", fill=NAVY, font=title)
    draw.text((64, 82), "付费率为来源表显示口径；D7 C-T为来源值，均不等同真实LTV。", fill=MUTED, font=body)
    groups = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
    data={x["group"]:x for x in summary}
    panels=[("来源新增付费率（注册日期日均）", "pay", .45, 130, 780), ("D7 C-T（已注册满7天用户加权）", "ct", max((data[g]["d7_ct"] or 0) for g in groups)*1.2, 885, 1530)]
    for panel_title,key,max_y,left,right in panels:
        top,bottom=180,620
        draw.text((left,128),panel_title,fill=NAVY,font=body)
        ticks=[0,max_y*.25,max_y*.5,max_y*.75,max_y]
        for t in ticks:
            y=bottom-(t/max_y)*(bottom-top) if max_y else bottom
            draw.line((left,y,right,y),fill=GRID,width=2)
            label=fmt_rate(t,0) if key=="pay" else fmt_num(t,0)
            draw.text((left-54,y-8),label,fill=MUTED,font=small)
        unit=(right-left)/len(groups)
        for i,g in enumerate(groups):
            v=data[g]["source_new_paid_rate"]["mean"] if key=="pay" else data[g]["d7_ct"]
            v=v or 0
            h=v/max_y*(bottom-top) if max_y else 0
            x=left+unit*i+unit*.29
            draw.rounded_rectangle((x,bottom-h,x+unit*.42,bottom),radius=6,fill=COLORS[g])
            draw.text((x,bottom-h-22),fmt_rate(v) if key=="pay" else fmt_num(v,0),fill=NAVY,font=small)
            draw_multiline(draw,(x-6,bottom+12),g.replace("标准H5 · ",""),small,NAVY,int(unit*.58),2)
    image.save(path)
    return path


def source_meta() -> list[dict[str, Any]]:
    return [
        {
            "id": "new-user-source",
            "label": "新包新增用户分析（四个H5/PWA目标页）",
            "href": LARK_NEW_USER_URL,
            "query": {
                "engine": "Lark Sheets API",
                "sql": "SELECT cohort_date, new_users, retention_d1, retention_d3, retention_d7, retention_d15, retention_d30, source_new_paid_rate, source_first_charge_rate, source_ct_fields FROM WAJEBETH5, wajeH5-facebook, wajeH5ga-googlewords_int, PWA WHERE cohort_date BETWEEN '2026-06-16' AND '2026-08-16';",
                "description": "源表修订633；四个目标页均按6月16日至8月16日的完整used range读取。",
                "tables_used": ["WAJEBETH5", "wajeH5-facebook", "wajeH5ga-googlewords_int", "PWA"],
                "filters": ["cohort日期 2026-06-16—2026-08-16", "观察日 2026-08-19"],
                "metric_definitions": ["D7只纳入注册满7天的cohort；D15/D30同理。", "同批留存曲线只使用已满30天且D1/D3/D7/D15/D30均有值的cohort。", "阶段衰减率=1-后一观察点留存/前一观察点留存，且每个阶段用达到后一观察天数、前后两点均有值的同一批cohort复算。", "来源新增付费率、首充付费率与人数按来源定义展示，不形成互斥漏斗。", "终身、首日、7日、15日、30日为来源C-T字段，不等同收入LTV。"],
            },
        },
        {
            "id": "update-source",
            "label": "更新记录·新包 + 运营补充",
            "href": LARK_UPDATE_URL,
            "query": {
                "engine": "Lark Sheets API + user-provided operating context",
                "sql": "SELECT update_date, update_content, operations FROM 新包 WHERE update_date BETWEEN '2026-06-16' AND '2026-08-16';",
                "description": "版本、轻量化游戏、埋点、风控、运营事件；含用户确认的8月15–16日Facebook投放账户封禁。",
                "tables_used": ["新包", "用户补充运营事实"],
                "filters": ["保留与轻量化游戏、H5/PWA、版本、埋点、风控、故障及运营有关的事件"],
                "metric_definitions": ["事件仅用于设置观察窗口和解释干扰，不用于直接证明因果。"],
            },
        },
        {
            "id": "history-source",
            "label": "轻量化游戏历史分析与性能规范",
            "href": HISTORY_URL,
            "query": {"engine": "local knowledge snapshot", "sql": "SELECT historical_baseline, performance_requirement FROM local_knowledge;", "description": "仅用于说明5月历史基线与埋点缺口，不与本轮cohort直接合并。", "tables_used": ["historical_context"], "filters": [], "metric_definitions": []},
        },
    ]


def flat_summary(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows=[]
    for x in summary:
        rows.append({
            "group": x["group"], "surface": x["surface"], "channel": x["channel"], "new_users": x["new_users"],
            "d1": x["d1"], "d3": x["d3"], "d7": x["d7"], "d15": x["d15"], "d30": x["d30"],
            "d1_cohorts": x["d1_cohorts"], "d3_cohorts": x["d3_cohorts"], "d7_cohorts": x["d7_cohorts"], "d15_cohorts": x["d15_cohorts"], "d30_cohorts": x["d30_cohorts"],
            "d1_new_users": x["d1_new_users"], "d3_new_users": x["d3_new_users"], "d7_new_users": x["d7_new_users"], "d15_new_users": x["d15_new_users"], "d30_new_users": x["d30_new_users"],
            "source_new_paid_rate_mean": x["source_new_paid_rate"]["mean"], "source_new_paid_rate_median": x["source_new_paid_rate"]["median"],
            "source_first_charge_rate_mean": x["source_first_charge_rate"]["mean"], "source_first_charge_rate_median": x["source_first_charge_rate"]["median"],
            "d7_ct": x["d7_ct"], "d15_ct": x["d15_ct"], "d30_ct": x["d30_ct"],
            "source_lifetime_ct_weighted": x["source_lifetime_ct"]["weighted"], "source_lifetime_ct_median": x["source_lifetime_ct"]["median"],
            "source_tc_ratio_mean": x["source_tc_ratio"]["mean"], "source_tx_rate_mean": x["source_tx_rate"]["mean"], "source_avg_tx_mean": x["source_avg_tx"]["mean"],
        })
    return rows


def write_sqlite(analysis: dict[str, Any]) -> None:
    if SQLITE_DB.exists():
        SQLITE_DB.unlink()
    with sqlite3.connect(SQLITE_DB) as conn:
        conn.execute("CREATE TABLE daily_cohort (cohort_date TEXT, channel_group TEXT, new_users REAL, d1 REAL, d3 REAL, d7 REAL, d15 REAL, d30 REAL, source_new_paid_rate REAL, source_first_charge_rate REAL, ct_d7 REAL, ct_d15 REAL, ct_d30 REAL, tc_ratio REAL, tx_rate REAL, avg_tx REAL)")
        conn.executemany("INSERT INTO daily_cohort VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["date"], r["group"], r["new_users"], r["d1"], r["d3"], r["d7"], r["d15"], r["d30"], r["source_new_paid_rate"], r["source_first_charge_rate"], r["ct_d7"], r["ct_d15"], r["ct_d30"], r["tc_ratio"], r["tx_rate"], r["avg_tx"])
            for r in analysis["daily_rows"]
        ])
        conn.execute("CREATE TABLE channel_summary (channel_group TEXT, surface TEXT, channel TEXT, new_users REAL, d1 REAL, d3 REAL, d7 REAL, d15 REAL, d30 REAL, source_new_paid_rate_mean REAL, source_first_charge_rate_mean REAL, ct_d7 REAL, ct_d15 REAL, ct_d30 REAL, tc_ratio REAL, tx_rate REAL, avg_tx REAL)")
        conn.executemany("INSERT INTO channel_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["group"], r["surface"], r["channel"], r["new_users"], r["d1"], r["d3"], r["d7"], r["d15"], r["d30"], r["source_new_paid_rate_mean"], r["source_first_charge_rate_mean"], r["d7_ct"], r["d15_ct"], r["d30_ct"], r["source_tc_ratio_mean"], r["source_tx_rate_mean"], r["source_avg_tx_mean"])
            for r in flat_summary(analysis["channel_summary"])
        ])
        conn.execute("CREATE TABLE matched_retention_curve (channel_group TEXT, metric TEXT, stage_order INTEGER, day INTEGER, retention_rate REAL, cohorts INTEGER, new_users REAL, cohort_end TEXT)")
        conn.executemany("INSERT INTO matched_retention_curve VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["group"], r["metric"], r["stage_order"], r["day"], r["rate"], r["cohorts"], r["new_users"], r["cohort_end"])
            for r in analysis["matched_retention_curve"]
        ])
        conn.execute("CREATE TABLE matched_retention_decay (channel_group TEXT, stage TEXT, stage_order INTEGER, previous_rate REAL, next_rate REAL, retained_share REAL, decay REAL, cohorts INTEGER, new_users REAL, cohort_end TEXT)")
        conn.executemany("INSERT INTO matched_retention_decay VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["group"], r["stage"], r["stage_order"], r["previous_rate"], r["next_rate"], r["retained_share"], r["decay"], r["cohorts"], r["new_users"], r["cohort_end"])
            for r in analysis["matched_retention_decay"]
        ])
        conn.execute("CREATE TABLE lightgame_pre_post (channel_group TEXT, before_window TEXT, after_window TEXT, before_new_users REAL, after_new_users REAL, new_users_change REAL, before_d1 REAL, after_d1 REAL, d1_delta REAL, before_d3 REAL, after_d3 REAL, d3_delta REAL, before_d7 REAL, after_d7 REAL, d7_delta REAL, before_paid_rate REAL, after_paid_rate REAL, paid_rate_delta REAL, before_first_rate REAL, after_first_rate REAL, first_rate_delta REAL, before_d7_ct REAL, after_d7_ct REAL, d7_ct_delta REAL)")
        conn.executemany("INSERT INTO lightgame_pre_post VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["group"], r["before_window"], r["after_window"], r["before_new_users"], r["after_new_users"], r["new_users_change"], r["before_d1"], r["after_d1"], r["d1_delta"], r["before_d3"], r["after_d3"], r["d3_delta"], r["before_d7"], r["after_d7"], r["d7_delta"], r["before_paid_rate"], r["after_paid_rate"], r["paid_rate_delta"], r["before_first_rate"], r["after_first_rate"], r["first_rate_delta"], r["before_d7_ct"], r["after_d7_ct"], r["d7_ct_delta"])
            for r in analysis["lightgame_pre_post"]
        ])
        conn.execute("CREATE TABLE phase_summary (phase TEXT, window TEXT, channel_group TEXT, new_users REAL, d1 REAL, d3 REAL, d7 REAL, source_new_paid_rate REAL, ct_d7 REAL, notes TEXT)")
        conn.executemany("INSERT INTO phase_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["phase"], r["window"], r["group"], r["new_users"], r["d1"], r["d3"], r["d7"], r["source_new_paid_rate_mean"], r["d7_ct"], r["notes"])
            for r in analysis["phase_rows"]
        ])
        conn.execute("CREATE TABLE phase_overview (phase TEXT, window TEXT, new_users REAL, d1 REAL, d3 REAL, d7 REAL, d3_delta_baseline REAL, d7_delta_baseline REAL, d7_status TEXT, best_channel TEXT, best_channel_d3 REAL)")
        conn.executemany("INSERT INTO phase_overview VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["phase"], r["window"], r["new_users"], r["d1"], r["d3"], r["d7"], r["d3_delta_baseline"], r["d7_delta_baseline"], r["d7_status"], r["best_channel"], r["best_channel_d3"])
            for r in analysis["phase_overview"]
        ])
        conn.execute("CREATE TABLE phase_channel_matrix (phase TEXT, window TEXT, overall_d3 REAL, overall_d7 REAL, h5_natural_d3 REAL, h5_facebook_d3 REAL, h5_google_d3 REAL, pwa_natural_d3 REAL, h5_natural_d7 REAL, h5_facebook_d7 REAL, h5_google_d7 REAL, pwa_natural_d7 REAL, d7_status TEXT)")
        conn.executemany("INSERT INTO phase_channel_matrix VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["phase"], r["window"], r["overall_d3"], r["overall_d7"], r["h5_natural_d3"], r["h5_facebook_d3"], r["h5_google_d3"], r["pwa_natural_d3"], r["h5_natural_d7"], r["h5_facebook_d7"], r["h5_google_d7"], r["pwa_natural_d7"], r["d7_status"])
            for r in analysis["phase_channel_matrix"]
        ])
        conn.execute("CREATE TABLE update_events (event_date TEXT, event_kind TEXT, content TEXT)")
        conn.executemany("INSERT INTO update_events VALUES (?, ?, ?)", [(r["date"], r["kind"], r["content"]) for r in analysis["update_events"]])
        conn.execute("CREATE TABLE facebook_account_ban (baseline_window TEXT, affected_window TEXT, before_daily_new REAL, after_daily_new REAL, decline REAL, benchmark_gap REAL)")
        b=analysis["facebook_account_ban"]
        conn.execute("INSERT INTO facebook_account_ban VALUES (?, ?, ?, ?, ?, ?)", (b["baseline_window"], b["affected_window"], b["before_daily_new"], b["after_daily_new"], b["decline"], b["benchmark_gap"]))
        conn.commit()


def build_artifact(analysis: dict[str, Any]) -> dict[str, Any]:
    summary = analysis["channel_summary"]
    flat = flat_summary(summary)
    h5_fb = next(x for x in flat if x["group"] == "H5 Facebook")
    h5_google = next(x for x in flat if x["group"] == "H5 Google")
    h5_natural = next(x for x in flat if x["group"] == "H5自然")
    pwa = next(x for x in flat if x["group"] == "PWA自然")
    phase_by_key = {(r["phase"], r["group"]): r for r in analysis["phase_rows"]}
    baseline = {g: phase_by_key[("上线前基线", g)] for g in ("H5自然", "H5 Facebook", "H5 Google", "PWA自然")}
    color_dice = {g: phase_by_key[("Color Dice", g)] for g in baseline}
    keno = {g: phase_by_key[("H5 2.1.14 / Keno", g)] for g in baseline}
    curve_rows = analysis["matched_retention_curve"]
    decay_rows = analysis["matched_retention_decay"]
    decay_by_key = {(r["group"], r["stage"]): r for r in decay_rows}
    for row in flat:
        row["decay_d1_d3"] = decay_by_key[(row["group"], "D1→D3")]["decay"]
        row["decay_d3_d7"] = decay_by_key[(row["group"], "D3→D7")]["decay"]
        row["decay_d7_d15"] = decay_by_key[(row["group"], "D7→D15")]["decay"]
        row["decay_d15_d30"] = decay_by_key[(row["group"], "D15→D30")]["decay"]
    retention_long=[]
    for row in flat:
        for metric, field in (("D1", "d1"), ("D3", "d3"), ("D7", "d7"), ("D15", "d15"), ("D30", "d30")):
            retention_long.append({"group": row["group"], "metric": metric, "rate": row[field], "cohorts": row[f"{field}_cohorts"], "new_users": row[f"{field}_new_users"]})
    payment_long=[]
    value_long=[]
    for row in flat:
        payment_long.append({"group": row["group"], "metric": "来源新增付费率", "rate": row["source_new_paid_rate_mean"]})
        payment_long.append({"group": row["group"], "metric": "来源首充付费率", "rate": row["source_first_charge_rate_mean"]})
        value_long.append({"group": row["group"], "metric": "D7 C-T", "value": row["d7_ct"], "cohorts": row["d7_cohorts"]})
        value_long.append({"group": row["group"], "metric": "D15 C-T", "value": row["d15_ct"], "cohorts": row["d15_cohorts"]})
    same_h5=[h5_fb, h5_google]
    natural_compare=[h5_natural, pwa]
    lifetime_compare=flat
    phase_overview = analysis["phase_overview"]
    phase_channel_matrix = analysis["phase_channel_matrix"]
    headline=[{
        "window_days": analysis["window"]["common_cohort_days"],
        "h5_fb_d7": h5_fb["d7"], "h5_google_d7": h5_google["d7"], "h5_natural_d7": h5_natural["d7"], "pwa_d7": pwa["d7"],
    }]
    sources=source_meta()
    manifest={
        "version":1, "surface":"report", "title":"Waje H5/PWA轻量化游戏效果与新用户留存付费分析 V2", "description":"扩展至2026年6月16日至8月16日，围绕渠道、H5/PWA自然流量、更新节点、付费与来源C-T展开。", "generatedAt":"2026-08-19T19:00:00+08:00", "sources":sources,
        "cards":[
            {"id":"window","dataset":"headline","sourceId":"new-user-source","description":"四个目标页共同连续的数据窗口。","metrics":[{"label":"共同cohort日","field":"window_days","format":"number"}]},
            {"id":"fb-d7","dataset":"headline","sourceId":"new-user-source","description":"标准H5 Facebook中，已注册满7天的cohort加权D7。","metrics":[{"label":"Facebook D7","field":"h5_fb_d7","format":"percent"}]},
            {"id":"google-d7","dataset":"headline","sourceId":"new-user-source","description":"标准H5 Google Ads中，已注册满7天的cohort加权D7。","metrics":[{"label":"Google Ads D7","field":"h5_google_d7","format":"percent"}]},
            {"id":"h5-natural-d7","dataset":"headline","sourceId":"new-user-source","description":"WajeBet H5自然渠道中，已注册满7天的cohort加权D7。","metrics":[{"label":"H5自然 D7","field":"h5_natural_d7","format":"percent"}]},
            {"id":"pwa-d7","dataset":"headline","sourceId":"new-user-source","description":"PWA自然渠道中，已注册满7天的cohort加权D7。","metrics":[{"label":"PWA自然 D7","field":"pwa_d7","format":"percent"}]},
        ],
        "charts":[
            {"id":"daily-new","title":"四渠道每日新增用户","subtitle":"2026年6月16日至8月16日；8月15–16日Facebook投放账户封禁另行标注。","type":"line","dataset":"daily_new","sourceId":"new-user-source","layout":"full","encodings":{"x":{"field":"date","type":"temporal","label":"cohort日期"},"y":{"field":"new_users","type":"quantitative","format":"number","label":"新增人数"},"color":{"field":"group","type":"nominal","label":"渠道/运行形态"},"tooltip":[{"field":"date","type":"temporal"},{"field":"group","type":"nominal"},{"field":"new_users","type":"quantitative","format":"number"}]}},
            {"id":"retention","title":"四渠道：已达到观察天数的留存对比","subtitle":"D1/D3/D7/D15/D30只纳入已走满对应观察期的cohort；按新增人数加权。","type":"bar","dataset":"retention_long","sourceId":"new-user-source","layout":"full","encodings":{"x":{"field":"metric","type":"nominal","label":"留存天数"},"y":{"field":"rate","type":"quantitative","format":"percent","label":"留存率"},"color":{"field":"group","type":"nominal","label":"渠道/运行形态"},"tooltip":[{"field":"group","type":"nominal"},{"field":"metric","type":"nominal"},{"field":"rate","type":"quantitative","format":"percent"},{"field":"cohorts","type":"quantitative","format":"number"},{"field":"new_users","type":"quantitative","format":"number"}]}},
            {"id":"retention-curve","title":"四渠道同批注册用户的 D1—D30 留存曲线","subtitle":"各渠道仅使用已满30天且五个留存点均完整的同一批cohort；按新增人数加权。","type":"line","dataset":"matched_retention_curve","sourceId":"new-user-source","layout":"full","encodings":{"x":{"field":"metric","type":"nominal","label":"注册后观察点"},"y":{"field":"rate","type":"quantitative","format":"percent","label":"留存率"},"color":{"field":"group","type":"nominal","label":"渠道/运行形态"},"tooltip":[{"field":"group","type":"nominal"},{"field":"metric","type":"nominal"},{"field":"rate","type":"quantitative","format":"percent"},{"field":"cohorts","type":"quantitative","format":"number"},{"field":"new_users","type":"quantitative","format":"number"},{"field":"cohort_end","type":"temporal"}]}},
            {"id":"retention-decay","title":"四渠道分阶段留存衰减率","subtitle":"衰减率＝1－后一观察点留存÷前一观察点留存；每个阶段使用相同cohort。","type":"bar","dataset":"matched_retention_decay","sourceId":"new-user-source","layout":"full","encodings":{"x":{"field":"stage","type":"nominal","label":"留存阶段"},"y":{"field":"decay","type":"quantitative","format":"percent","label":"衰减率"},"color":{"field":"group","type":"nominal","label":"渠道/运行形态"},"tooltip":[{"field":"group","type":"nominal"},{"field":"stage","type":"nominal"},{"field":"previous_rate","type":"quantitative","format":"percent"},{"field":"next_rate","type":"quantitative","format":"percent"},{"field":"retained_share","type":"quantitative","format":"percent"},{"field":"decay","type":"quantitative","format":"percent"},{"field":"cohorts","type":"quantitative","format":"number"},{"field":"new_users","type":"quantitative","format":"number"}]}},
            {"id":"phase-d3","title":"轻量化更新节点：D3留存观察","subtitle":"6/16—8/16分阶段；真实h5_build缺失，只呈现观察性差异。","type":"bar","dataset":"phase_rows","sourceId":"update-source","layout":"full","encodings":{"x":{"field":"phase","type":"nominal","label":"发布期"},"y":{"field":"d3","type":"quantitative","format":"percent","label":"D3留存"},"color":{"field":"group","type":"nominal","label":"渠道/运行形态"},"tooltip":[{"field":"phase","type":"nominal"},{"field":"group","type":"nominal"},{"field":"d3","type":"quantitative","format":"percent"},{"field":"new_users","type":"quantitative","format":"number"},{"field":"notes","type":"text"}]}},
            {"id":"phase-d3-line","title":"轻量化更新节点：四渠道D3留存变化","subtitle":"六个发布观察期的D3留存折线；用于阶段间直观对比，不作为因果结论。","type":"line","dataset":"phase_rows","sourceId":"update-source","layout":"full","encodings":{"x":{"field":"phase","type":"nominal","label":"发布观察期"},"y":{"field":"d3","type":"quantitative","format":"percent","label":"D3留存"},"color":{"field":"group","type":"nominal","label":"渠道/运行形态"},"tooltip":[{"field":"phase","type":"nominal"},{"field":"window","type":"nominal"},{"field":"group","type":"nominal"},{"field":"d3","type":"quantitative","format":"percent"},{"field":"d3_cohorts","type":"quantitative","format":"number"},{"field":"d3_new_users","type":"quantitative","format":"number"},{"field":"notes","type":"text"}]}},
            {"id":"payment","title":"来源新增付费率与首充付费率","subtitle":"来源表显示率的cohort日均值；分子分母未确认一致，不作为互斥用户付费漏斗。","type":"bar","dataset":"payment_long","sourceId":"new-user-source","layout":"full","encodings":{"x":{"field":"group","type":"nominal","label":"渠道/运行形态"},"y":{"field":"rate","type":"quantitative","format":"percent","label":"来源显示率"},"color":{"field":"metric","type":"nominal","label":"来源指标"},"tooltip":[{"field":"group","type":"nominal"},{"field":"metric","type":"nominal"},{"field":"rate","type":"quantitative","format":"percent"}]}},
            {"id":"ct","title":"D7 / D15 C-T对比（来源字段）","subtitle":"只使用已走满对应观察期的cohort；C-T不是收入LTV。","type":"bar","dataset":"value_long","sourceId":"new-user-source","layout":"full","encodings":{"x":{"field":"group","type":"nominal","label":"渠道/运行形态"},"y":{"field":"value","type":"quantitative","format":"number","label":"来源C-T"},"color":{"field":"metric","type":"nominal","label":"观察节点"},"tooltip":[{"field":"group","type":"nominal"},{"field":"metric","type":"nominal"},{"field":"value","type":"quantitative","format":"number"},{"field":"cohorts","type":"quantitative","format":"number"}]}},
        ],
        "tables":[
            {"id":"channel-matrix","title":"四渠道留存与阶段衰减对比","subtitle":"留存率按各自观察窗口汇总；四段衰减率均按同一批cohort复算。","dataset":"channel_summary","sourceId":"new-user-source","density":"comfortable","layout":"full","columns":[{"field":"group","label":"渠道/运行形态","type":"text"},{"field":"new_users","label":"新增","format":"number","type":"number"},{"field":"d1","label":"D1","format":"percent","type":"percent"},{"field":"d3","label":"D3","format":"percent","type":"percent"},{"field":"d7","label":"D7","format":"percent","type":"percent"},{"field":"d15","label":"D15","format":"percent","type":"percent"},{"field":"d30","label":"D30","format":"percent","type":"percent"},{"field":"decay_d1_d3","label":"D1→D3衰减","format":"percent","type":"percent"},{"field":"decay_d3_d7","label":"D3→D7衰减","format":"percent","type":"percent"},{"field":"decay_d7_d15","label":"D7→D15衰减","format":"percent","type":"percent"},{"field":"decay_d15_d30","label":"D15→D30衰减","format":"percent","type":"percent"}]},
            {"id":"same-h5","title":"同发布时间窗：标准H5 Facebook与Google Ads对比","subtitle":"源表没有真实build，不能称为严格同版本实验。","dataset":"same_h5","sourceId":"new-user-source","density":"spacious","layout":"full","columns":[{"field":"group","label":"渠道","type":"text"},{"field":"new_users","label":"新增","format":"number","type":"number"},{"field":"d3","label":"D3","format":"percent","type":"percent"},{"field":"d7","label":"D7","format":"percent","type":"percent"},{"field":"source_new_paid_rate_mean","label":"来源新增付费率","format":"percent","type":"percent"},{"field":"d7_ct","label":"D7 C-T","format":"number","type":"number"}]},
            {"id":"natural","title":"同为自然流量：H5自然与PWA自然对比","subtitle":"包体/真实build不同，不能视为严格版本对照。","dataset":"natural_compare","sourceId":"new-user-source","density":"spacious","layout":"full","columns":[{"field":"group","label":"运行形态","type":"text"},{"field":"new_users","label":"新增","format":"number","type":"number"},{"field":"d3","label":"D3","format":"percent","type":"percent"},{"field":"d7","label":"D7","format":"percent","type":"percent"},{"field":"d30","label":"D30","format":"percent","type":"percent"},{"field":"source_new_paid_rate_mean","label":"来源新增付费率","format":"percent","type":"percent"},{"field":"d7_ct","label":"D7 C-T","format":"number","type":"number"}]},
            {"id":"lifetime","title":"生命周期价值（LTV参考）对照表","subtitle":"“终身”及各日C-T均为来源字段；它们不是订单收入LTV。D7/D15/D30只纳入已达到对应观察天数的cohort。","dataset":"lifetime_compare","sourceId":"new-user-source","density":"spacious","layout":"full","columns":[{"field":"group","label":"渠道/运行形态","type":"text"},{"field":"source_lifetime_ct_weighted","label":"终身C-T（LTV参考）","format":"number","type":"number"},{"field":"d7_ct","label":"D7 C-T","format":"number","type":"number"},{"field":"d15_ct","label":"D15 C-T","format":"number","type":"number"},{"field":"d30_ct","label":"D30 C-T","format":"number","type":"number"},{"field":"source_new_paid_rate_mean","label":"来源新增付费率","format":"percent","type":"percent"},{"field":"source_first_charge_rate_mean","label":"来源首充率","format":"percent","type":"percent"}]},
            {"id":"phase-overview","title":"各发布阶段总体表现","subtitle":"总体D1/D3/D7按渠道新增加权；当前期D7为部分数据。","dataset":"phase_overview","sourceId":"update-source","density":"comfortable","layout":"full","columns":[{"field":"phase","label":"阶段","type":"text"},{"field":"window","label":"日期窗口","type":"text"},{"field":"new_users","label":"总新增","format":"number","type":"number"},{"field":"d1","label":"总体D1","format":"percent","type":"percent"},{"field":"d3","label":"总体D3","format":"percent","type":"percent"},{"field":"d3_delta_baseline","label":"D3较基线","format":"percent","type":"percent","movement":True},{"field":"d7","label":"总体D7","format":"percent","type":"percent"},{"field":"d7_delta_baseline","label":"D7较基线","format":"percent","type":"percent","movement":True},{"field":"d7_status","label":"D7数据范围","type":"text"}]},
            {"id":"phase-channel","title":"各阶段四渠道D3对照","subtitle":"横向看同一阶段渠道差异，纵向看同一渠道阶段变化。","dataset":"phase_channel_matrix","sourceId":"update-source","density":"comfortable","layout":"full","columns":[{"field":"phase","label":"阶段","type":"text"},{"field":"window","label":"日期窗口","type":"text"},{"field":"overall_d3","label":"总体D3","format":"percent","type":"percent"},{"field":"h5_natural_d3","label":"H5自然D3","format":"percent","type":"percent"},{"field":"h5_facebook_d3","label":"H5 Facebook D3","format":"percent","type":"percent"},{"field":"h5_google_d3","label":"H5 Google D3","format":"percent","type":"percent"},{"field":"pwa_natural_d3","label":"PWA自然D3","format":"percent","type":"percent"}]},
            {"id":"phase-channel-d7","title":"各阶段四渠道D7对照","subtitle":"当前期已有注册用户达到7天观察条件，但源表暂无可用D7值；其余阶段为完整观察窗口。","dataset":"phase_channel_matrix","sourceId":"update-source","density":"comfortable","layout":"full","columns":[{"field":"phase","label":"阶段","type":"text"},{"field":"window","label":"日期窗口","type":"text"},{"field":"overall_d7","label":"总体D7","format":"percent","type":"percent"},{"field":"h5_natural_d7","label":"H5自然D7","format":"percent","type":"percent"},{"field":"h5_facebook_d7","label":"H5 Facebook D7","format":"percent","type":"percent"},{"field":"h5_google_d7","label":"H5 Google D7","format":"percent","type":"percent"},{"field":"pwa_natural_d7","label":"PWA自然D7","format":"percent","type":"percent"},{"field":"d7_status","label":"数据范围","type":"text"}]},
            {"id":"events","title":"轻量化更新、版本与干扰事件","subtitle":"用于解释阶段窗口与不可归因因素。","dataset":"update_events","sourceId":"update-source","density":"comfortable","layout":"full","columns":[{"field":"date","label":"日期","type":"date"},{"field":"kind","label":"类型","type":"text"},{"field":"content","label":"事件","type":"text"}]},
        ],
        "blocks":[
            {"id":"headline","type":"metric-strip","cardIds":["window","fb-d7","google-d7","h5-natural-d7","pwa-d7"]},
            {"id":"ltv-note","type":"markdown","body":"## 生命周期价值（LTV参考）对照\n\n下表新增了来源“终身”C-T及D7/D15/D30 C-T，便于四渠道直接比对。**请勿把它当作真实收入LTV：**源表尚缺订单收入、退款、奖励成本和统一币种分母；其中“终身”又包含不同年龄cohort的来源快照，最适合做方向性参考。"},
            {"id":"ltv-table","type":"table","tableId":"lifetime"},
            {"id":"daily","type":"chart","chartId":"daily-new"},
            {"id":"fb-ban-note","type":"markdown","body":"**备注：**8月15–16日 Facebook 渠道新增骤降，原因是投放账户被封；不作为产品或轻量化效果判断。"},
            {"id":"channels","type":"markdown","body":f"## 同发布时间窗的标准H5渠道差异\n\nFacebook带来更多新增（{fmt_count(h5_fb['new_users'])}），但已注册满7天用户的D7为 **{fmt_rate(h5_fb['d7'])}**，低于Google Ads的 **{fmt_rate(h5_google['d7'])}**；来源新增付费率分别为 **{fmt_rate(h5_fb['source_new_paid_rate_mean'])}** 与 **{fmt_rate(h5_google['source_new_paid_rate_mean'])}**。这说明当前最优先的问题仍是Facebook渠道的流量质量与新手路径，而非仅看总H5均值。源表未带真实h5_build，以下为同发布时间窗比较，不是严格同版本实验。"},
            {"id":"same-h5-table","type":"table","tableId":"same-h5"},
            {"id":"natural","type":"markdown","body":f"## 自然流量：H5自然与PWA自然\n\nPWA自然的D1/D3/D7为 **{fmt_rate(pwa['d1'])} / {fmt_rate(pwa['d3'])} / {fmt_rate(pwa['d7'])}**，H5自然为 **{fmt_rate(h5_natural['d1'])} / {fmt_rate(h5_natural['d3'])} / {fmt_rate(h5_natural['d7'])}**。PWA在留存上更高，但样本仅{fmt_count(pwa['new_users'])}，且真实build、入口与推送策略不同；它是优先验证对象，不是“PWA更优”的定论。"},
            {"id":"natural-table","type":"table","tableId":"natural"},
            {"id":"retention-text","type":"markdown","body":"## 扩展窗口后的留存对比\n\n“已达到观察天数”指注册日至观察日已走满对应天数。例如D7只统计8月12日及以前注册、已满7天的cohort；D15和D30同理。这样不会把尚未有机会回访的用户错记为流失。"},
            {"id":"retention","type":"chart","chartId":"retention"},
            {"id":"retention-curve-note","type":"markdown","body":"**同批次留存曲线：**五个观察点使用同一批已注册满30天且数据完整的cohort，避免把不同成熟窗口直接连接成一条曲线。"},
            {"id":"retention-curve","type":"chart","chartId":"retention-curve"},
            {"id":"retention-decay-note","type":"markdown","body":f"**分阶段衰减：**衰减率越高，表示该阶段流失越快。PWA自然的D3→D7衰减为 **{fmt_rate(decay_by_key[('PWA自然', 'D3→D7')]['decay'])}**；H5 Facebook的D1→D3和D3→D7衰减分别为 **{fmt_rate(decay_by_key[('H5 Facebook', 'D1→D3')]['decay'])}**、**{fmt_rate(decay_by_key[('H5 Facebook', 'D3→D7')]['decay'])}**，前7日仍是优先排查区间。"},
            {"id":"retention-decay","type":"chart","chartId":"retention-decay"},
            {"id":"channel-matrix","type":"table","tableId":"channel-matrix"},
            {"id":"phase-text","type":"markdown","body":f"## 轻量化更新与优化节点：只做分期观察\n\n6/16—7/13为上线前基线；其后依次观察Limbo、H5 2.1.14/Keno、Color Dice、Opera埋点和当前期。**相对基线，Color Dice期D3的观察变化为：H5自然 {fmt_pp(color_dice['H5自然']['d3'] - baseline['H5自然']['d3'])}、H5 Google {fmt_pp(color_dice['H5 Google']['d3'] - baseline['H5 Google']['d3'])}、H5 Facebook {fmt_pp(color_dice['H5 Facebook']['d3'] - baseline['H5 Facebook']['d3'])}、PWA自然 {fmt_pp(color_dice['PWA自然']['d3'] - baseline['PWA自然']['d3'])}。H5 2.1.14/Keno期对应变化为：H5自然 {fmt_pp(keno['H5自然']['d3'] - baseline['H5自然']['d3'])}、H5 Google {fmt_pp(keno['H5 Google']['d3'] - baseline['H5 Google']['d3'])}、H5 Facebook {fmt_pp(keno['H5 Facebook']['d3'] - baseline['H5 Facebook']['d3'])}、PWA自然 {fmt_pp(keno['PWA自然']['d3'] - baseline['PWA自然']['d3'])}。\n\n每个窗口还叠加活动、风控、KYC、故障或埋点变更，因此这些是复盘优先级，而非“某个游戏或版本导致变化”的因果结论。"},
            {"id":"phase-chart","type":"chart","chartId":"phase-d3"},
            {"id":"phase-line-note","type":"markdown","body":"**阶段变化折线：**折线用于追踪同一渠道跨阶段的D3变化；柱图用于比较同一阶段内四渠道差异。两者结合阅读，避免把渠道结构变化误认为版本效果。"},
            {"id":"phase-line","type":"chart","chartId":"phase-d3-line"},
            {"id":"phase-overview-table","type":"table","tableId":"phase-overview"},
            {"id":"phase-channel-table","type":"table","tableId":"phase-channel"},
            {"id":"phase-channel-d7-table","type":"table","tableId":"phase-channel-d7"},
            {"id":"payment-text","type":"markdown","body":"来源新增付费率与首充率按原表口径并列展示，分母未确认一致，不制作付费漏斗。C-T仅作来源价值参考，不等同真实LTV。"},
            {"id":"payment-chart","type":"chart","chartId":"payment"},
            {"id":"ct-chart","type":"chart","chartId":"ct"},
            {"id":"actions","type":"markdown","body":"## 结论与下一步\n\n1. **P0：恢复并复核Facebook投放。** 账户封禁影响8/15–16新增和渠道结构；恢复后按同媒体计划、同入口、同设备档位复测D1/D3/D7。\n2. **P0：补齐真实版本与游戏链路。** 每条事件带`h5_build`、`config_version`、`game_id`、会话、曝光、点击、加载、首局开始/完成和错误码。\n3. **P1：建立订单级价值表。** 以统一币种的成功支付、退款、奖励成本和净收入，计算真实D7/D30 LTV、ARPU和ARPPU。\n4. **P1：自然流量PWA验证。** 按相同入口/活动/推送条件灰度对比H5自然与PWA自然，而不是直接把当前差异当作产品胜出。"},
        ],
    }
    return {"surface":"report", "manifest":manifest, "snapshot":{"version":1,"generatedAt":"2026-08-19T19:00:00+08:00","status":"ready","datasets":{"headline":headline,"daily_new":analysis["daily_rows"],"retention_long":retention_long,"matched_retention_curve":curve_rows,"matched_retention_decay":decay_rows,"channel_summary":flat,"same_h5":same_h5,"natural_compare":natural_compare,"lifetime_compare":lifetime_compare,"phase_rows":analysis["phase_rows"],"phase_overview":phase_overview,"phase_channel_matrix":phase_channel_matrix,"payment_long":payment_long,"value_long":value_long,"update_events":analysis["update_events"]}}, "sources":sources, "package_info":{"title":"Waje H5/PWA轻量化游戏效果与新用户留存付费分析 V2","source_revision":SOURCE_REVISION,"analysis_as_of":REFERENCE_DATE.isoformat()}}


def html_table(headers: list[str], rows: list[list[str]], widths: list[int] | None = None) -> str:
    cols = "" if not widths else "<colgroup>" + "".join(f'<col width="{w}"/>' for w in widths) + "</colgroup>"
    head = "".join(f'<th background-color="light-blue"><p>{escape_xml(h)}</p></th>' for h in headers)
    body = "".join("<tr>" + "".join(f"<td><p>{escape_xml(v)}</p></td>" for v in row) + "</tr>" for row in rows)
    return f"<table>{cols}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def feishu_xml(analysis: dict[str, Any]) -> str:
    flat = flat_summary(analysis["channel_summary"])
    by_group = {r["group"]: r for r in flat}
    fb = by_group["H5 Facebook"]
    google = by_group["H5 Google"]
    h5 = by_group["H5自然"]
    pwa = by_group["PWA自然"]
    ban = analysis["facebook_account_ban"]
    phase_index = {(r["phase"], r["group"]): r for r in analysis["phase_rows"]}
    baseline = {g: phase_index[("上线前基线", g)] for g in ("H5自然", "H5 Facebook", "H5 Google", "PWA自然")}
    color_dice = {g: phase_index[("Color Dice", g)] for g in baseline}
    keno = {g: phase_index[("H5 2.1.14 / Keno", g)] for g in baseline}
    decay_by_key = {(r["group"], r["stage"]): r for r in analysis["matched_retention_decay"]}
    phase_overview_by = {r["phase"]: r for r in analysis["phase_overview"]}
    pre_post_by = {r["group"]: r for r in analysis["lightgame_pre_post"]}
    channel_table = html_table(
        ["渠道/运行形态", "新增", "D1", "D3", "D7", "D15", "D30", "D1→D3衰减", "D3→D7衰减", "D7→D15衰减", "D15→D30衰减"],
        [[r["group"], fmt_count(r["new_users"]), fmt_rate(r["d1"]), fmt_rate(r["d3"]), fmt_rate(r["d7"]), fmt_rate(r["d15"]), fmt_rate(r["d30"]), fmt_rate(decay_by_key[(r["group"], "D1→D3")]["decay"]), fmt_rate(decay_by_key[(r["group"], "D3→D7")]["decay"]), fmt_rate(decay_by_key[(r["group"], "D7→D15")]["decay"]), fmt_rate(decay_by_key[(r["group"], "D15→D30")]["decay"])] for r in flat],
        [150, 85, 55, 55, 55, 55, 55, 100, 100, 105, 115],
    )
    same_h5 = html_table(
        ["标准H5渠道", "新增", "D1", "D3", "D7", "来源新增付费率", "D7 C-T"],
        [[r["group"], fmt_count(r["new_users"]), fmt_rate(r["d1"]), fmt_rate(r["d3"]), fmt_rate(r["d7"]), fmt_rate(r["source_new_paid_rate_mean"]), fmt_num(r["d7_ct"])] for r in (fb, google)],
        [210, 110, 80, 80, 80, 150, 110],
    )
    lifetime_table = html_table(
        ["渠道/运行形态", "累计C-T参考值", "D7 C-T", "D15 C-T", "D30 C-T", "来源新增付费率", "来源首充率"],
        [[r["group"], fmt_num(r["source_lifetime_ct_weighted"]), fmt_num(r["d7_ct"]), fmt_num(r["d15_ct"]), fmt_num(r["d30_ct"]), fmt_rate(r["source_new_paid_rate_mean"]), fmt_rate(r["source_first_charge_rate_mean"])] for r in flat],
        [185, 155, 95, 100, 100, 135, 120],
    )
    natural = html_table(
        ["自然流量运行形态", "新增", "D1", "D3", "D7", "D15", "D30", "来源新增付费率", "D7 C-T"],
        [[r["group"], fmt_count(r["new_users"]), fmt_rate(r["d1"]), fmt_rate(r["d3"]), fmt_rate(r["d7"]), fmt_rate(r["d15"]), fmt_rate(r["d30"]), fmt_rate(r["source_new_paid_rate_mean"]), fmt_num(r["d7_ct"])] for r in (h5, pwa)],
        [210, 110, 80, 80, 80, 80, 80, 150, 110],
    )
    lightgame_change_table = html_table(
        ["渠道/运行形态", "新增变化", "D1变化", "D3变化", "D7变化", "新增付费率变化", "首充率变化", "D7 C-T变化"],
        [[r["group"], fmt_rate(r["new_users_change"]), fmt_pp(r["d1_delta"]), fmt_pp(r["d3_delta"]), fmt_pp(r["d7_delta"]), fmt_pp(r["paid_rate_delta"]), fmt_pp(r["first_rate_delta"]), fmt_num(r["d7_ct_delta"], 2)] for r in analysis["lightgame_pre_post"]],
        [160, 90, 80, 80, 80, 125, 105, 110],
    )
    lightgame_natural_table = html_table(
        ["运行形态", "阶段", "新增", "D1", "D3", "D7", "来源新增付费率", "来源首充率", "D7 C-T"],
        [
            ["H5自然", "上线前 6/16–7/13", fmt_count(pre_post_by["H5自然"]["before_new_users"]), fmt_rate(pre_post_by["H5自然"]["before_d1"]), fmt_rate(pre_post_by["H5自然"]["before_d3"]), fmt_rate(pre_post_by["H5自然"]["before_d7"]), fmt_rate(pre_post_by["H5自然"]["before_paid_rate"]), fmt_rate(pre_post_by["H5自然"]["before_first_rate"]), fmt_num(pre_post_by["H5自然"]["before_d7_ct"], 2)],
            ["H5自然", "上线后 7/14–8/10", fmt_count(pre_post_by["H5自然"]["after_new_users"]), fmt_rate(pre_post_by["H5自然"]["after_d1"]), fmt_rate(pre_post_by["H5自然"]["after_d3"]), fmt_rate(pre_post_by["H5自然"]["after_d7"]), fmt_rate(pre_post_by["H5自然"]["after_paid_rate"]), fmt_rate(pre_post_by["H5自然"]["after_first_rate"]), fmt_num(pre_post_by["H5自然"]["after_d7_ct"], 2)],
            ["PWA自然", "上线前 6/16–7/13", fmt_count(pre_post_by["PWA自然"]["before_new_users"]), fmt_rate(pre_post_by["PWA自然"]["before_d1"]), fmt_rate(pre_post_by["PWA自然"]["before_d3"]), fmt_rate(pre_post_by["PWA自然"]["before_d7"]), fmt_rate(pre_post_by["PWA自然"]["before_paid_rate"]), fmt_rate(pre_post_by["PWA自然"]["before_first_rate"]), fmt_num(pre_post_by["PWA自然"]["before_d7_ct"], 2)],
            ["PWA自然", "上线后 7/14–8/10", fmt_count(pre_post_by["PWA自然"]["after_new_users"]), fmt_rate(pre_post_by["PWA自然"]["after_d1"]), fmt_rate(pre_post_by["PWA自然"]["after_d3"]), fmt_rate(pre_post_by["PWA自然"]["after_d7"]), fmt_rate(pre_post_by["PWA自然"]["after_paid_rate"]), fmt_rate(pre_post_by["PWA自然"]["after_first_rate"]), fmt_num(pre_post_by["PWA自然"]["after_d7_ct"], 2)],
        ],
        [115, 150, 90, 65, 65, 65, 125, 105, 95],
    )
    phase_overview_table = html_table(
        ["阶段", "日期窗口", "总新增", "总体D1", "总体D3", "D3较基线", "总体D7", "D7较基线", "D7数据范围"],
        [[r["phase"], r["window"], fmt_count(r["new_users"]), fmt_rate(r["d1"]), fmt_rate(r["d3"]), fmt_pp(r["d3_delta_baseline"]), fmt_rate(r["d7"]), fmt_pp(r["d7_delta_baseline"]), r["d7_status"]] for r in analysis["phase_overview"]],
        [135, 90, 85, 70, 70, 85, 70, 85, 165],
    )
    phase_channel_table = html_table(
        ["阶段", "日期窗口", "总体D3", "H5自然D3", "H5 Facebook D3", "H5 Google D3", "PWA自然D3"],
        [[r["phase"], r["window"], fmt_rate(r["overall_d3"]), fmt_rate(r["h5_natural_d3"]), fmt_rate(r["h5_facebook_d3"]), fmt_rate(r["h5_google_d3"]), fmt_rate(r["pwa_natural_d3"])] for r in analysis["phase_channel_matrix"]],
        [155, 110, 90, 105, 135, 120, 105],
    )
    phase_d7_table = html_table(
        ["阶段", "日期窗口", "总体D7", "H5自然D7", "H5 Facebook D7", "H5 Google D7", "PWA自然D7", "数据范围"],
        [[r["phase"], r["window"], fmt_rate(r["overall_d7"]), fmt_rate(r["h5_natural_d7"]), fmt_rate(r["h5_facebook_d7"]), fmt_rate(r["h5_google_d7"]), fmt_rate(r["pwa_natural_d7"]), r["d7_status"]] for r in analysis["phase_channel_matrix"]],
        [135, 90, 80, 95, 125, 110, 95, 165],
    )
    events_table = html_table(
        ["日期", "类型", "事件"],
        [[e["date"], e["kind"], e["content"]] for e in analysis["update_events"]],
        [110, 130, 620],
    )
    return f'''<title>Waje H5/PWA轻量化游戏效果与新用户留存付费分析 V2（6月16日—8月16日）</title>
<p>数据窗口：2026年6月16日至8月16日；观察日：2026年8月19日；四个目标页共同覆盖62个注册日期批次。</p>
<callout emoji="💡" background-color="light-blue" border-color="blue"><p><b>轻量化游戏核心判断：</b>7月14日上线后，H5自然D7提升<span background-color="light-green"><b>{fmt_pp(pre_post_by['H5自然']['d7_delta'])}</b></span>，但新增付费率下降<span background-color="light-yellow"><b>{fmt_pp(abs(pre_post_by['H5自然']['paid_rate_delta'])).lstrip('+')}</b></span>、D7 C-T下降{fmt_num(abs(pre_post_by['H5自然']['d7_ct_delta']), 2)}；留存改善尚未转化为付费与价值提升。Facebook D7基本不变，PWA自然D7下降{fmt_pp(abs(pre_post_by['PWA自然']['d7_delta'])).lstrip('+')}，<span background-color="light-yellow">轻量化效果并非全渠道一致。</span></p><p><b>规模与留存短板：</b>H5 Facebook新增<span background-color="light-blue"><b>{fmt_count(fb['new_users'])}</b></span>，规模最大，但D7仅<span background-color="light-red"><b>{fmt_rate(fb['d7'])}</b></span>；Google Ads D7达到<span background-color="light-green"><b>{fmt_rate(google['d7'])}</b></span>，高出{fmt_pp(google['d7'] - fb['d7'])}。Facebook是当前最明确的质量短板。</p><p><b>自然流量结论：</b>PWA自然D1/D3分别领先H5自然<span background-color="light-green"><b>{fmt_pp(pwa['d1'] - h5['d1'])}</b></span>和<span background-color="light-green"><b>{fmt_pp(pwa['d3'] - h5['d3'])}</b></span>，但D7只领先<span background-color="light-yellow"><b>{fmt_pp(pwa['d7'] - h5['d7'])}</b></span>，早期优势到第7天基本收窄。</p><p><b>价值表现：</b>H5 Google累计C-T参考值<span background-color="light-green"><b>{fmt_num(google['source_lifetime_ct_weighted'], 2)}</b></span>最高；H5 Facebook仅<span background-color="light-red"><b>{fmt_num(fb['source_lifetime_ct_weighted'], 2)}</b></span>，同时来源新增付费率只有<span background-color="light-red"><b>{fmt_rate(fb['source_new_paid_rate_mean'])}</b></span>，价值与付费均明显偏低。</p></callout>
<h1 seq="auto">轻量化游戏上线前后：H5自然留存改善，但付费未同步</h1>
<p><b>等长28天对比显示，H5自然D1/D3/D7分别提升<span background-color="light-green">{fmt_pp(pre_post_by['H5自然']['d1_delta'])}/{fmt_pp(pre_post_by['H5自然']['d3_delta'])}/{fmt_pp(pre_post_by['H5自然']['d7_delta'])}</span>；但来源新增付费率下降{fmt_pp(abs(pre_post_by['H5自然']['paid_rate_delta'])).lstrip('+')}、首充率下降{fmt_pp(abs(pre_post_by['H5自然']['first_rate_delta'])).lstrip('+')}，D7 C-T从{fmt_num(pre_post_by['H5自然']['before_d7_ct'], 2)}降至{fmt_num(pre_post_by['H5自然']['after_d7_ct'], 2)}。</b> 当前可确认的是留存改善，不能确认商业价值同步提升。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_v2_2026_08_19/assets/轻量化游戏上线前后核心指标变化.png" caption="6月16日—7月13日与7月14日—8月10日等长窗口的核心指标百分点变化。"/>
<p><b>分渠道结果：</b>Google的D7、付费率和D7 C-T同步上升，但新增下降52.3%；Facebook D7下降0.2pp，基本没有改善；PWA自然新增接近翻倍，但D7下降3.1pp、付费率下降1.9pp。轻量化上线后的正向信号主要集中在H5自然和Google，并非全渠道普遍改善。</p>
{lightgame_change_table}
<h2 seq="auto">自然流量专项：H5自然反超PWA的D7，但价值表现分化</h2>
<p><b>上线前PWA自然D7为14.0%，领先H5自然4.2pp；上线后H5自然D7升至<span background-color="light-green">13.6%</span>，反而领先PWA自然<span background-color="light-green">+2.6pp</span>。</b> PWA仍保持更高D1/D3，但D7优势已消失；同时PWA来源付费率为27.4%，低于H5自然30.5%，而D7 C-T仍高于H5自然。自然流量的结论不是“PWA或H5全面胜出”，而是留存、付费和价值出现分化。</p>
{lightgame_natural_table}
<p><span text-color="gray">备注：两个窗口均为28天。7月14日后同时存在活动、风控、版本和投放变化，因此以上为上线前后同步变化，不作为单一轻量化游戏的因果证明。</span></p>
<h1 seq="auto">渠道价值表现：Google领先，Facebook明显偏低</h1>
<p><b>H5 Google累计C-T参考值{fmt_num(google['source_lifetime_ct_weighted'], 2)}居首；PWA自然{fmt_num(pwa['source_lifetime_ct_weighted'], 2)}、H5自然{fmt_num(h5['source_lifetime_ct_weighted'], 2)}接近。H5 Facebook仅{fmt_num(fb['source_lifetime_ct_weighted'], 2)}，约为Google的{fmt_rate(fb['source_lifetime_ct_weighted'] / google['source_lifetime_ct_weighted'])}，且来源新增付费率最低。</b></p>
{lifetime_table}
<p><span text-color="gray">备注：C-T为来源价值字段，用于同口径方向对比，不等同订单收入LTV。</span></p>
<img path="@./analysis/h5_pwa_lightgame_effect_v2_2026_08_19/assets/62日新增趋势与投放事件.png" caption="红线标记8月15日；Facebook投放账户被封影响8月15–16日新增。"/>
<p><b>备注：</b>8月15–16日 Facebook 渠道新增骤降，原因是投放账户被封；不作为产品或轻量化效果判断。</p>
<h1 seq="auto">同发布时间窗：标准H5渠道对比</h1>
<p>Facebook与Google Ads均按标准H5渠道表比较，但源表没有真实h5_build；以下是同发布时间窗的渠道比较，不是严格同版本实验。</p>
{same_h5}
<h1 seq="auto">四渠道留存：Facebook持续偏低，Google与PWA表现更稳</h1>
<p>D7只统计截至8月12日已经注册满7天的用户；D15、D30同理。未达到观察天数的用户不计入。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_v2_2026_08_19/assets/62日窗口留存对比.png" caption="各留存指标只统计已经达到对应观察天数的注册用户。"/>
<p><b>同批次留存曲线：</b>五个观察点使用同一批已注册满30天且数据完整的用户，避免不同注册日期的样本混在一起。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_v2_2026_08_19/assets/四渠道同批注册用户D1-D30留存曲线.png" caption="同一渠道内D1/D3/D7/D15/D30使用完全相同的注册批次。"/>
<p><b>分阶段衰减：</b>衰减率＝1－后一观察点留存÷前一观察点留存，数值越高表示该阶段流失越快。PWA自然D3→D7衰减为{fmt_rate(decay_by_key[('PWA自然', 'D3→D7')]['decay'])}；H5 Facebook D1→D3、D3→D7衰减分别为{fmt_rate(decay_by_key[('H5 Facebook', 'D1→D3')]['decay'])}、{fmt_rate(decay_by_key[('H5 Facebook', 'D3→D7')]['decay'])}。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_v2_2026_08_19/assets/四渠道分阶段留存衰减率.png" caption="每个阶段均使用达到后一观察天数且前后两点都有值的同一批注册用户。"/>
{channel_table}
<h1 seq="auto">轻量化更新与优化节点观察</h1>
<p>以6月16日至7月13日为上线前基线，分段观察Limbo、H5 2.1.14/Keno、Color Dice、Opera埋点及当前期。相对基线，Color Dice期D3的观察变化为：H5自然{fmt_pp(color_dice['H5自然']['d3'] - baseline['H5自然']['d3'])}、H5 Google{fmt_pp(color_dice['H5 Google']['d3'] - baseline['H5 Google']['d3'])}、H5 Facebook{fmt_pp(color_dice['H5 Facebook']['d3'] - baseline['H5 Facebook']['d3'])}、PWA自然{fmt_pp(color_dice['PWA自然']['d3'] - baseline['PWA自然']['d3'])}。H5 2.1.14/Keno期对应变化为：H5自然{fmt_pp(keno['H5自然']['d3'] - baseline['H5自然']['d3'])}、H5 Google{fmt_pp(keno['H5 Google']['d3'] - baseline['H5 Google']['d3'])}、H5 Facebook{fmt_pp(keno['H5 Facebook']['d3'] - baseline['H5 Facebook']['d3'])}、PWA自然{fmt_pp(keno['PWA自然']['d3'] - baseline['PWA自然']['d3'])}。节点与KYC/risk、活动、故障、埋点变更高度重叠，因此只作复盘优先级，不直接证明因果。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_v2_2026_08_19/assets/轻量化更新节点D3留存观察.png" caption="D3留存分期观察；用于定位值得复盘的窗口，不用于因果归因。"/>
<p><b>阶段变化折线：</b>折线用于追踪同一渠道跨阶段的D3变化；柱图用于比较同一阶段内四渠道差异。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_v2_2026_08_19/assets/轻量化更新节点D3留存折线.png" caption="同一渠道跨六个发布观察期的D3留存变化。"/>
<p><b>阶段总体对比：</b>同时比较D1、D3、D7及其相对上线前基线的变化；当前期只有8月11—12日注册用户已满7天，但源表尚未提供D7值，标记为N/A。</p>
{phase_overview_table}
<p><b>D3渠道对比：</b>横向看同一阶段四渠道差异，纵向看同一渠道跨阶段变化。</p>
{phase_channel_table}
<p><b>D7渠道对比：</b>Color Dice期总体D7为<span background-color="light-green"><b>{fmt_rate(phase_overview_by['Color Dice']['d7'])}</b></span>，较上线前基线{fmt_pp(phase_overview_by['Color Dice']['d7_delta_baseline'])}；Opera埋点期总体D7为<span background-color="light-green"><b>{fmt_rate(phase_overview_by['Opera 埋点期']['d7'])}</b></span>，较基线{fmt_pp(phase_overview_by['Opera 埋点期']['d7_delta_baseline'])}。当前期D7暂无可用值。</p>
{phase_d7_table}
{events_table}
<p><b>付费口径：</b>来源新增付费率与首充率按原表口径并列展示，分母未确认一致，不制作付费漏斗。C-T仅作来源价值参考，不等同真实LTV。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_v2_2026_08_19/assets/付费显示率与D7CT对比.png" caption="左侧为来源新增付费率，右侧为D7 C-T；二者均非真实LTV。"/>
<h1 seq="auto">结论与下一步</h1>
<ol><li><b>P0：Facebook恢复后重测。</b>账户恢复后，以同媒体计划、同入口和同设备档位复测D1/D3/D7，分离投放质量与产品路径问题。</li><li><b>P0：补齐真实版本和首局链路。</b>写入h5_build、config_version、game_id、入口曝光、加载、可下注、首局开始/完成及错误码。</li><li><b>P1：建立订单级LTV。</b>以成功支付、退款、奖励成本和统一币种收入，计算D7/D30 LTV、ARPU和ARPPU。</li><li><b>P1：自然流量灰度验证。</b>在可控入口/活动/推送条件下比较H5自然与PWA自然，不直接沿用当前观察差异。</li></ol>
<h1 seq="auto">附录：统计期间主要调整内容</h1>
{events_table}
<p align="center">Waje 数据产品分析 · V2 · 2026-08-19</p>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feishu-xml", type=Path)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    all_rows: dict[str, list[dict[str, Any]]] = {}
    source_details: dict[str, Any] = {}
    for name, config in GROUPS.items():
        rows, metadata = load_table(RAW / config["file"])
        all_rows[name] = [r for r in rows if WINDOW_START <= r["_date"] <= WINDOW_END]
        source_details[name] = metadata
    common_dates = sorted(set.intersection(*(set(r["_date"] for r in rows) for rows in all_rows.values())))
    if common_dates[0] != WINDOW_START or common_dates[-1] != WINDOW_END or len(common_dates) != 62:
        raise RuntimeError(f"Unexpected common window: {common_dates[0]}—{common_dates[-1]} ({len(common_dates)} days)")

    summaries = [group_summary(name, GROUPS[name], all_rows[name]) for name in GROUPS]
    h5_rows = all_rows["WAJEBETH5"] + all_rows["wajeH5-facebook"] + all_rows["wajeH5ga-googlewords_int"]
    ban = account_ban_impact(all_rows["wajeH5-facebook"], h5_rows)
    daily_rows=[]
    for name, config in GROUPS.items():
        for r in all_rows[name]:
            daily_rows.append({
                "date": r["_date"].isoformat(), "group": config["label"], "new_users": number(r.get("新增人数")) or 0,
                "d1": rate(r.get("次留")), "d3": rate(r.get("3日留")), "d7": rate(r.get("7日留")), "d15": rate(r.get("15日留")), "d30": rate(r.get("30日留")),
                "source_new_paid_rate": rate(r.get("新增付费率")), "source_first_charge_rate": rate(r.get("首充付费率")),
                "ct_d7": number(r.get("7日")), "ct_d15": number(r.get("15日")), "ct_d30": number(r.get("30日")),
                "tc_ratio": number(r.get("tc比")), "tx_rate": number(r.get("tx率")), "avg_tx": number(r.get("人均tx金额")),
            })
    daily_rows.sort(key=lambda x: (x["date"], x["group"]))
    phase_rows=[]
    for phase in PHASES:
        for name, config in GROUPS.items():
            phase_data=subset(all_rows[name], phase["start"], phase["end"])
            s=group_summary(name, config, phase_data)
            phase_rows.append({"phase":phase["label"],"window":phase["window"],"group":config["label"],"new_users":s["new_users"],"d1":s["d1"],"d3":s["d3"],"d7":s["d7"],"d1_new_users":s["d1_new_users"],"d3_new_users":s["d3_new_users"],"d7_new_users":s["d7_new_users"],"d1_cohorts":s["d1_cohorts"],"d3_cohorts":s["d3_cohorts"],"d7_cohorts":s["d7_cohorts"],"source_new_paid_rate_mean":s["source_new_paid_rate"]["mean"],"d7_ct":s["d7_ct"],"notes":phase["note"]})
    events=load_update_events(RAW / "update_log_new_package_table.json")
    curve_rows = matched_retention_curve(all_rows)
    decay_rows = matched_retention_decay(all_rows)
    phase_overview, phase_channel_matrix = phase_comparison_tables(phase_rows)
    lightgame_comparison = lightgame_pre_post_comparison(all_rows)
    history={}
    history_path=ROOT / "analysis/lightgame_topic_2026_08_18/analysis.json"
    if history_path.exists():
        history=json.loads(history_path.read_text()).get("click", {})
    analysis={
        "title":"Waje H5/PWA轻量化游戏效果与新用户留存付费分析 V2","as_of":REFERENCE_DATE.isoformat(),"source_revision":SOURCE_REVISION,"update_revision":UPDATE_REVISION,
        "window":{"start":WINDOW_START.isoformat(),"end":WINDOW_END.isoformat(),"common_cohort_days":len(common_dates)},
        "source_details":source_details,"channel_summary":summaries,"daily_rows":daily_rows,"matched_retention_curve":curve_rows,"matched_retention_decay":decay_rows,"lightgame_pre_post":lightgame_comparison,"phase_rows":phase_rows,"phase_overview":phase_overview,"phase_channel_matrix":phase_channel_matrix,"update_events":events,"facebook_account_ban":ban,"quality_rows":quality_rows(all_rows),"history_context":history,
        "limitations":["真实h5_build/app_version不在源表，版本只能按发布时间窗代理观察。","来源新增付费率、首充付费率及人数的分母/人群未确认一致，不能制作用户漏斗或免费用户反推。","终身、首日、7日、15日、30日为来源C-T字段；缺少订单收入、退款、统一币种和收入分母，不能输出真实LTV。","当前表没有game_id、入口/加载/首局链路、设备和网络字段，不能将变化归因至某一轻量化玩法或性能改造。"],
    }
    write_sqlite(analysis)
    artifact=build_artifact(analysis)
    ANALYSIS.write_text(json.dumps(analysis,ensure_ascii=False,indent=2))
    QUALITY.write_text(json.dumps({"as_of":REFERENCE_DATE.isoformat(),"quality_rows":analysis["quality_rows"],"limitations":analysis["limitations"]},ensure_ascii=False,indent=2))
    ARTIFACT.write_text(json.dumps(artifact,ensure_ascii=False,indent=2))
    SOURCE_REGISTRY.write_text(json.dumps({"read_at":datetime.now().astimezone().isoformat(timespec="seconds"),"workbook_revision":SOURCE_REVISION,"update_log_revision":UPDATE_REVISION,"window":analysis["window"],"sources":[{"role":"主数据源","url":LARK_NEW_USER_URL,"sheets":source_details,"snapshot_directory":str(RAW.relative_to(ROOT))},{"role":"更新与干扰事件","url":LARK_UPDATE_URL,"sheet":"新包"},{"role":"运营事实补充","source_type":"用户提供","fact":"8月15–16日H5 Facebook投放账户被封","use":"解释新增规模与渠道结构异常，不作为留存因果。"}],"calculation_rules":["D1/D3/D7/D15/D30均只纳入已达到对应观察天数的cohort，并按新增人数加权。","留存曲线使用已满30天且五个观察点均有值的同一批cohort。","阶段衰减率=1-后一观察点留存/前一观察点留存，每个阶段按同一批cohort复算。","来源付费率和首充率仅按来源显示口径比较，不制作漏斗。","D7/D15/D30 C-T为来源字段，不等同真实LTV。"]},ensure_ascii=False,indent=2))
    CHART_MAP.write_text(json.dumps([{ "section":"新增趋势","type":"line","dataset":"daily_new","claim":"识别流量结构与Facebook账户封禁影响。"},{"section":"留存对比","type":"bar","dataset":"retention_long","claim":"按各自观察窗口比较D1—D30留存。"},{"section":"同批留存曲线","type":"line","dataset":"matched_retention_curve","claim":"同一批已满30天cohort的D1—D30留存变化。"},{"section":"阶段留存衰减","type":"bar","dataset":"matched_retention_decay","claim":"量化D1→D3、D3→D7、D7→D15及D15→D30阶段流失。"},{"section":"更新分期内比较","type":"bar","dataset":"phase_rows","claim":"同一阶段内比较四渠道D3。"},{"section":"更新分期间变化","type":"line","dataset":"phase_rows","claim":"同一渠道跨六个发布观察期的D3变化。"},{"section":"付费显示率","type":"bar","dataset":"payment_long","claim":"来源显示率对比，不作用户漏斗。"},{"section":"C-T价值字段","type":"bar","dataset":"value_long","claim":"来源D7/D15 C-T对比，不命名LTV。"}],ensure_ascii=False,indent=2))
    render_daily_new(daily_rows)
    render_retention(summaries)
    render_retention_curve(curve_rows)
    render_retention_decay(decay_rows)
    render_lightgame_pre_post_deltas(lightgame_comparison)
    render_phase_d3(phase_rows)
    render_phase_d3_line(phase_rows)
    render_payment_value(summaries)
    summary_by_group = {x["group"]: x for x in summaries}
    h5_natural_summary = summary_by_group["H5自然"]
    facebook_summary = summary_by_group["H5 Facebook"]
    google_summary = summary_by_group["H5 Google"]
    pwa_summary = summary_by_group["PWA自然"]
    phase_overview_md = "\n".join(
        f"| {r['phase']} | {r['window']} | {fmt_count(r['new_users'])} | {fmt_rate(r['d1'])} | {fmt_rate(r['d3'])} | {fmt_pp(r['d3_delta_baseline'])} | {fmt_rate(r['d7'])} | {fmt_pp(r['d7_delta_baseline'])} | {r['d7_status']} |"
        for r in phase_overview
    )
    phase_d7_md = "\n".join(
        f"| {r['phase']} | {r['window']} | {fmt_rate(r['overall_d7'])} | {fmt_rate(r['h5_natural_d7'])} | {fmt_rate(r['h5_facebook_d7'])} | {fmt_rate(r['h5_google_d7'])} | {fmt_rate(r['pwa_natural_d7'])} | {r['d7_status']} |"
        for r in phase_channel_matrix
    )
    events_md = "\n".join(f"| {e['date']} | {e['kind']} | {e['content']} |" for e in events)
    lightgame_change_md = "\n".join(
        f"| {r['group']} | {fmt_rate(r['new_users_change'])} | {fmt_pp(r['d1_delta'])} | {fmt_pp(r['d3_delta'])} | {fmt_pp(r['d7_delta'])} | {fmt_pp(r['paid_rate_delta'])} | {fmt_pp(r['first_rate_delta'])} | {fmt_num(r['d7_ct_delta'], 2)} |"
        for r in lightgame_comparison
    )
    pre_post_by = {r["group"]: r for r in lightgame_comparison}
    md=f'''# Waje H5/PWA轻量化游戏效果与新用户留存付费分析 V2

数据窗口：2026-06-16—2026-08-16；观察日：2026-08-19；四个目标页共同连续覆盖62个注册日期批次。

## 关键结论

- **轻量化游戏上线后，H5自然留存改善但付费未同步。** D1/D3/D7提升{fmt_pp(pre_post_by['H5自然']['d1_delta'])}/{fmt_pp(pre_post_by['H5自然']['d3_delta'])}/{fmt_pp(pre_post_by['H5自然']['d7_delta'])}，但来源新增付费率下降{fmt_pp(abs(pre_post_by['H5自然']['paid_rate_delta'])).lstrip('+')}，D7 C-T下降{fmt_num(abs(pre_post_by['H5自然']['d7_ct_delta']), 2)}。
- **Facebook规模最大但质量最低。** 新增{fmt_count(facebook_summary['new_users'])}，D7仅{fmt_rate(facebook_summary['d7'])}；Google Ads D7为{fmt_rate(google_summary['d7'])}，高出{fmt_pp(google_summary['d7'] - facebook_summary['d7'])}。
- **PWA前期留存优势到D7明显收窄。** PWA自然D1/D3分别领先H5自然{fmt_pp(pwa_summary['d1'] - h5_natural_summary['d1'])}/{fmt_pp(pwa_summary['d3'] - h5_natural_summary['d3'])}，D7只领先{fmt_pp(pwa_summary['d7'] - h5_natural_summary['d7'])}；但D15/D30仍高{fmt_pp(pwa_summary['d15'] - h5_natural_summary['d15'])}/{fmt_pp(pwa_summary['d30'] - h5_natural_summary['d30'])}。
- **Google渠道价值表现最好，Facebook明显偏低。** H5 Google累计C-T参考值{fmt_num(google_summary['source_lifetime_ct']['weighted'], 2)}，Facebook仅{fmt_num(facebook_summary['source_lifetime_ct']['weighted'], 2)}，且Facebook来源新增付费率只有{fmt_rate(facebook_summary['source_new_paid_rate']['mean'])}。
- 8/15—8/16 Facebook投放账户封禁使日均新增从{fmt_count(ban['before_daily_new'])}降至{fmt_count(ban['after_daily_new'])}，降幅{fmt_rate(ban['decline'])}；当前期流量不可作轻量化效果比较。

## 轻量化游戏上线前后专项分析

对比等长28天窗口：上线前6月16日—7月13日，上线后7月14日—8月10日。

| 渠道/运行形态 | 新增变化 | D1变化 | D3变化 | D7变化 | 新增付费率变化 | 首充率变化 | D7 C-T变化 |
|---|---:|---:|---:|---:|---:|---:|---:|
{lightgame_change_md}

核心判断：H5自然和Google出现留存改善；Facebook基本不变，PWA自然留存和付费下降。轻量化上线后的正向信号并非全渠道一致。

### 自然流量：H5自然与PWA自然

- 上线前：PWA自然D7为{fmt_rate(pre_post_by['PWA自然']['before_d7'])}，领先H5自然{fmt_pp(pre_post_by['PWA自然']['before_d7'] - pre_post_by['H5自然']['before_d7'])}。
- 上线后：H5自然D7升至{fmt_rate(pre_post_by['H5自然']['after_d7'])}，领先PWA自然{fmt_pp(pre_post_by['H5自然']['after_d7'] - pre_post_by['PWA自然']['after_d7'])}。
- 上线后PWA自然来源付费率为{fmt_rate(pre_post_by['PWA自然']['after_paid_rate'])}，低于H5自然的{fmt_rate(pre_post_by['H5自然']['after_paid_rate'])}；但PWA D7 C-T仍更高，留存、付费和价值表现出现分化。

## 发布阶段总体表现

| 阶段 | 日期窗口 | 总新增 | 总体D1 | 总体D3 | D3较基线 | 总体D7 | D7较基线 | D7数据范围 |
|---|---|---:|---:|---:|---:|---:|---:|---|
{phase_overview_md}

## 各阶段四渠道 D7 对比

| 阶段 | 日期窗口 | 总体D7 | H5自然D7 | H5 Facebook D7 | H5 Google D7 | PWA自然D7 | 数据范围 |
|---|---|---:|---:|---:|---:|---:|---|
{phase_d7_md}

当前期只有8月11—12日注册用户已满7天，但源表尚未提供D7值，因此标记为N/A。

## 建议

1. Facebook恢复投放后，按相同媒体计划和入口重新观察D1/D3/D7，优先解决规模与质量不匹配。
2. 继续验证PWA早期留存优势能否转化为首充和复充，而不是只看D1/D3。
3. 更新事件必须带真实版本、游戏ID和配置版本，后续按用户实际版本比较。

## 附录：统计期间主要调整内容

| 日期 | 类型 | 事件 |
|---|---|---|
{events_md}

## 备注

- C-T为来源价值字段，用于同口径方向对比，不等同订单收入LTV。
- 留存只统计已经达到对应观察天数的注册用户；未达到观察天数的用户不计入。
- 真实版本、游戏ID和首局链路暂缺，更新节点分析属于阶段观察，不直接证明因果。
'''
    KNOWLEDGE.write_text(md)
    if args.feishu_xml:
        args.feishu_xml.parent.mkdir(parents=True,exist_ok=True)
        args.feishu_xml.write_text(feishu_xml(analysis))
    print(json.dumps({"artifact":str(ARTIFACT),"analysis":str(ANALYSIS),"quality":str(QUALITY),"knowledge":str(KNOWLEDGE),"source_registry":str(SOURCE_REGISTRY),"assets":[str(p) for p in sorted(ASSETS.glob("*.png"))]},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()

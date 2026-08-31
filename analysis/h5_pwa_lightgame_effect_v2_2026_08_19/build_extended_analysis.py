#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a source-backed H5/PWA lightweight-game effect analysis from Lark snapshots."""
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
RAW = ROOT / "data/raw/lark/2026-08-19/h5_pwa_lightgame"
OUT = ROOT / "analysis/h5_pwa_lightgame_effect_2026_08_19"
ASSETS = OUT / "assets"
KNOWLEDGE = ROOT / "knowledge/01-产品/Waje-H5-PWA轻量化游戏效果与新用户留存付费分析-2026-08-19.md"
ARTIFACT = OUT / "artifact.json"
ANALYSIS = OUT / "analysis.json"
QUALITY = OUT / "data_quality.json"
CHART_MAP = OUT / "chart_map.json"
SOURCE_REGISTRY = OUT / "source_registry.json"
SQLITE_DB = OUT / "analysis.sqlite"
REFERENCE_DATE = date(2026, 8, 19)
SOURCE_REVISION = 618
ANALYSIS_START = date(2026, 7, 14)
ANALYSIS_END = date(2026, 8, 16)
FACEBOOK_ACCOUNT_BAN_START = date(2026, 8, 15)
FACEBOOK_ACCOUNT_BAN_END = date(2026, 8, 16)

LARK_NEW_USER_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d?from=from_copylink&sheet=ef19NP"
LARK_UPDATE_URL = "https://ksg964l11fam.sg.larksuite.com/sheets/KmZcs6cdMhd6MQtHRDgl9jTNg5c?from=from_copylink&sheet=0owUxS"
HISTORY_URL = "https://ksg964l11fam.sg.larksuite.com/docx/Sk4XdrryEot7lcxmUW4l2vmSg2f"
PERFORMANCE_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/HpNOwkIqliWq6ckZE9clfeXdg4b"

GROUPS = {
    "WAJEBETH5": {"file": "wajebeth5.json", "label": "H5 自然", "surface": "H5", "channel": "自然"},
    "wajeH5-facebook": {"file": "waje_h5_facebook.json", "label": "H5 Facebook", "surface": "H5", "channel": "Facebook"},
    "wajeH5ga-googlewords_int": {"file": "waje_h5_google_ads.json", "label": "H5 Google Ads", "surface": "H5", "channel": "Google Ads"},
    "PWA": {"file": "pwa.json", "label": "PWA 自然", "surface": "PWA", "channel": "自然"},
}

RETENTION = {
    "D1": ("次留", 1),
    "D3": ("3日留", 3),
    "D7": ("7日留", 7),
    "D15": ("15日留", 15),
    "D30": ("30日留", 30),
    "D60": ("60日留", 60),
}

PHASES = [
    {
        "id": "limbo", "label": "Limbo 上线/恢复期", "window": "7/14–7/22",
        "start": date(2026, 7, 14), "end": date(2026, 7, 22),
        "note": "无上线前基线；7/20–7/21 Aviator 维护与触达为干扰项。",
        "sensitivity_exclude": [date(2026, 7, 20), date(2026, 7, 21)],
    },
    {
        "id": "keno", "label": "H5 2.1.14 / Keno 期", "window": "7/23–7/28",
        "start": date(2026, 7, 23), "end": date(2026, 7, 28),
        "note": "同日包含KYC、iOS注册回传修复；7/26–7/28有risk/KYC配置变更。",
        "sensitivity_exclude": [date(2026, 7, 26), date(2026, 7, 27), date(2026, 7, 28)],
    },
    {
        "id": "color", "label": "Color Dice 期", "window": "7/29–8/05",
        "start": date(2026, 7, 29), "end": date(2026, 8, 5),
        "note": "7/29 Color Dice 9003 上线；7/30 Tada 世界杯页面与Banner关闭。",
        "sensitivity_exclude": [date(2026, 7, 30)],
    },
    {
        "id": "opera", "label": "Opera 埋点期", "window": "8/06–8/10",
        "start": date(2026, 8, 6), "end": date(2026, 8, 10),
        "note": "Opera H5注册/埋点自动上报；主要用于覆盖和归因口径观察。",
        "sensitivity_exclude": [],
    },
    {
        "id": "current", "label": "当前期", "window": "8/11–8/16",
        "start": date(2026, 8, 11), "end": date(2026, 8, 16),
        "note": "App 2.17、iOS Firebase和Tada游戏上线并存；8/15–8/16 Facebook投放账户被封，新增规模与渠道结构不可作为产品比较；D7只使用已注册满7天的8/11–8/12 cohort。",
        "sensitivity_exclude": [],
    },
]

BLUE = "#2A7FBE"
GREEN = "#40A777"
GOLD = "#D9A02A"
PURPLE = "#7A6BC6"
RED = "#D85B66"
NAVY = "#183B5D"
MUTED = "#58718A"
GRID = "#DCEAF4"
GROUP_COLORS = {
    "H5 Facebook": BLUE,
    "H5 Google Ads": "#46A4B4",
    "H5 自然": GOLD,
    "PWA 自然": PURPLE,
}


def cell_value(cell: Any) -> Any:
    if isinstance(cell, dict):
        return cell.get("value")
    return cell


def parse_date(value: Any) -> date | None:
    if value is None:
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
    if value is None or value == "":
        return None
    text = str(value).strip().replace(",", "")
    try:
        if text.endswith("%"):
            return float(text[:-1]) / 100
        parsed = float(text)
        return parsed if 0 <= parsed <= 1 else parsed / 100
    except ValueError:
        return None


def fmt_rate(value: float | None, digits: int = 1) -> str:
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def fmt_num(value: float | int | None, digits: int = 0) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{digits}f}"


def fmt_count(value: float | int | None) -> str:
    """Round people counts with .5 upward rather than Python's banker rounding."""
    if value is None:
        return "N/A"
    return f"{math.floor(float(value) + 0.5):,}"


def fmt_pp(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:+.1f}pp"


def escape_xml(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|")


def load_rows(path: Path) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text())
    block = payload["ranges"][0]
    matrix = [[cell_value(cell) for cell in row] for row in block["cells"]]
    headers = [str(value or f"col{index+1}") for index, value in enumerate(matrix[0])]
    rows: list[dict[str, Any]] = []
    for index, values in enumerate(matrix[1:], start=2):
        row = {headers[i]: values[i] if i < len(values) else None for i in range(len(headers))}
        row["_row"] = index
        row["_date"] = parse_date(row.get("日期"))
        if row["_date"]:
            rows.append(row)
    return headers, rows, {"revision": payload.get("revision"), "range": block.get("actual_range"), "has_more": payload.get("has_more")}


def load_update_events(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    block = payload["ranges"][0]
    matrix = [[cell_value(cell) for cell in row] for row in block["cells"]]
    headers = [str(value or f"col{index+1}") for index, value in enumerate(matrix[0])]
    events: list[dict[str, Any]] = []
    for values in matrix[1:]:
        row = {headers[i]: values[i] if i < len(values) else None for i in range(len(headers))}
        event_date = parse_date(row.get("更新日期") or row.get("日期"))
        if not event_date:
            continue
        content = " ".join(str(row.get(key) or "") for key in ("更新内容", "运营活动"))
        low = content.lower()
        if not (date(2026, 7, 14) <= event_date <= date(2026, 8, 16)):
            continue
        if not any(term in low for term in ("limbo", "aviator", "keno", "color dice", "轻量", "h5", "opera", "risk", "kyc", "tada", "firebase")):
            continue
        kind = "context"
        if any(term in low for term in ("上线", "恢复上线", "下线", "维护")) and any(term in low for term in ("limbo", "aviator", "keno", "color dice", "轻量")):
            kind = "game"
        if any(term in low for term in ("打点", "opera", "版本", "firebase", "回传")):
            kind = "instrumentation"
        if any(term in low for term in ("risk", "kyc", "故障", "维护", "刷子", "关闭")):
            kind = "confounder"
        events.append({"date": event_date.isoformat(), "content": content.replace("\n", " / ").strip(), "kind": kind})
    return sorted(events, key=lambda item: item["date"])


def weighted_rate(rows: Iterable[dict[str, Any]], field: str, maturity_days: int) -> dict[str, Any]:
    cutoff = REFERENCE_DATE - timedelta(days=maturity_days)
    eligible = [r for r in rows if r["_date"] <= cutoff]
    observed = [r for r in eligible if rate(r.get(field)) is not None and number(r.get("新增人数")) not in (None, 0)]
    if not observed:
        return {"value": None, "cohorts": 0, "new_users": 0, "missing": len(eligible), "cutoff": cutoff.isoformat()}
    denominator = sum(number(r["新增人数"]) or 0 for r in observed)
    numerator = sum((rate(r[field]) or 0) * (number(r["新增人数"]) or 0) for r in observed)
    return {
        "value": numerator / denominator if denominator else None,
        "cohorts": len(observed),
        "new_users": denominator,
        "missing": len(eligible) - len(observed),
        "cutoff": cutoff.isoformat(),
    }


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def cohort_rate_distribution(rows: Iterable[dict[str, Any]], field: str, maturity_days: int | None = None) -> dict[str, Any]:
    selected = list(rows)
    if maturity_days is not None:
        selected = [r for r in selected if r["_date"] <= REFERENCE_DATE - timedelta(days=maturity_days)]
    values = [rate(r.get(field)) for r in selected if rate(r.get(field)) is not None]
    return {"mean": mean(values), "median": median(values), "days": len(values)}


def source_counts(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    new_users = sum(number(r.get("新增人数")) or 0 for r in rows)
    new_paid = sum(number(r.get("新增付费人数")) or 0 for r in rows)
    first_charge = sum(number(r.get("首充付费人数")) or 0 for r in rows)
    mismatch_paid = []
    mismatch_first = []
    for r in rows:
        base = number(r.get("新增人数"))
        if not base:
            continue
        for rate_field, count_field, target in [
            ("新增付费率", "新增付费人数", mismatch_paid),
            ("首充付费率", "首充付费人数", mismatch_first),
        ]:
            displayed = rate(r.get(rate_field))
            people = number(r.get(count_field))
            if displayed is not None and people is not None and abs(people / base - displayed) > 0.0005:
                target.append(r)
    return {
        "new_users": new_users,
        "source_new_paid_users": new_paid,
        "source_first_charge_users": first_charge,
        "new_paid_rate": cohort_rate_distribution(rows, "新增付费率"),
        "first_charge_rate": cohort_rate_distribution(rows, "首充付费率"),
        "first_charge_d1": cohort_rate_distribution(rows, "首充次留", 1),
        "first_charge_d3": cohort_rate_distribution(rows, "首充3日留", 3),
        "first_charge_d7": cohort_rate_distribution(rows, "首充7日留", 7),
        "new_paid_rate_mismatch_days": len(mismatch_paid),
        "first_charge_rate_mismatch_days": len(mismatch_first),
        "first_charge_gt_new_paid_days": sum(
            1 for r in rows
            if (number(r.get("首充付费人数")) or 0) > (number(r.get("新增付费人数")) or 0)
        ),
    }


def retention_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return {key: weighted_rate(rows, field, days) for key, (field, days) in RETENTION.items()}


def date_subset(rows: Iterable[dict[str, Any]], start: date, end: date, exclude: Iterable[date] = ()) -> list[dict[str, Any]]:
    excluded = set(exclude)
    return [r for r in rows if start <= r["_date"] <= end and r["_date"] not in excluded]


def facebook_account_ban_impact(facebook_rows: list[dict[str, Any]], h5_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Quantify the user-confirmed Facebook account suspension as a traffic/mix incident."""
    pre_start = date(2026, 8, 11)
    pre_end = FACEBOOK_ACCOUNT_BAN_START - timedelta(days=1)
    before = date_subset(facebook_rows, pre_start, pre_end)
    after = date_subset(facebook_rows, FACEBOOK_ACCOUNT_BAN_START, FACEBOOK_ACCOUNT_BAN_END)
    h5_before = date_subset(h5_rows, pre_start, pre_end)
    h5_after = date_subset(h5_rows, FACEBOOK_ACCOUNT_BAN_START, FACEBOOK_ACCOUNT_BAN_END)

    def new_total(items: list[dict[str, Any]]) -> float:
        return sum(number(r.get("新增人数")) or 0 for r in items)

    before_new = new_total(before)
    after_new = new_total(after)
    before_days = len(before)
    after_days = len(after)
    before_daily = before_new / before_days if before_days else None
    after_daily = after_new / after_days if after_days else None
    expected_after = (before_daily or 0) * after_days
    h5_before_new = new_total(h5_before)
    h5_after_new = new_total(h5_after)
    before_summary = group_summary("wajeH5-facebook", GROUPS["wajeH5-facebook"], before)
    after_summary = group_summary("wajeH5-facebook", GROUPS["wajeH5-facebook"], after)
    return {
        "fact_source": "用户补充：H5 Facebook投放账户被封",
        "affected_window": "2026-08-15—2026-08-16",
        "baseline_window": "2026-08-11—2026-08-14",
        "before": {
            "cohort_days": before_days,
            "new_users": before_new,
            "daily_new": before_daily,
            "d1": before_summary["d1"],
            "d3": before_summary["d3"],
            "facebook_share_of_h5_new": before_new / h5_before_new if h5_before_new else None,
        },
        "after": {
            "cohort_days": after_days,
            "new_users": after_new,
            "daily_new": after_daily,
            "d1": after_summary["d1"],
            "d3": after_summary["d3"],
            "facebook_share_of_h5_new": after_new / h5_after_new if h5_after_new else None,
        },
        "daily_new_decline": 1 - after_daily / before_daily if before_daily and after_daily is not None else None,
        "benchmark_new_gap": expected_after - after_new,
        "d7_interpretation": "当前期D7仅使用8月11日至12日cohort，早于账户封禁影响日；账户封禁用于解释新增规模和渠道结构，不作为D7变化原因。",
    }


def group_summary(name: str, config: dict[str, str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    retention = retention_summary(rows)
    counts = source_counts(rows)
    return {
        "group": config["label"],
        "sheet": name,
        "surface": config["surface"],
        "channel": config["channel"],
        "cohort_days": len(rows),
        "new_users": counts["new_users"],
        "d1": retention["D1"]["value"],
        "d3": retention["D3"]["value"],
        "d7": retention["D7"]["value"],
        "d7_cohorts": retention["D7"]["cohorts"],
        "d7_new_users": retention["D7"]["new_users"],
        "d15": retention["D15"]["value"],
        "d15_cohorts": retention["D15"]["cohorts"],
        "d15_missing": retention["D15"]["missing"],
        "d30": retention["D30"]["value"],
        "d30_cohorts": retention["D30"]["cohorts"],
        "d30_missing": retention["D30"]["missing"],
        "source_new_paid_users": counts["source_new_paid_users"],
        "source_new_paid_rate_mean": counts["new_paid_rate"]["mean"],
        "source_new_paid_rate_median": counts["new_paid_rate"]["median"],
        "source_first_charge_users": counts["source_first_charge_users"],
        "source_first_charge_rate_mean": counts["first_charge_rate"]["mean"],
        "source_first_charge_rate_median": counts["first_charge_rate"]["median"],
        "source_first_charge_d1_median": counts["first_charge_d1"]["median"],
        "source_first_charge_d3_median": counts["first_charge_d3"]["median"],
        "source_first_charge_d7_median": counts["first_charge_d7"]["median"],
        "paid_rate_mismatch_days": counts["new_paid_rate_mismatch_days"],
        "first_charge_rate_mismatch_days": counts["first_charge_rate_mismatch_days"],
        "first_charge_gt_new_paid_days": counts["first_charge_gt_new_paid_days"],
    }


def combine_rows(name: str, labels: list[str], group_rows: dict[str, list[dict[str, Any]]]) -> tuple[str, list[dict[str, Any]]]:
    merged: list[dict[str, Any]] = []
    for label in labels:
        merged.extend(group_rows[label])
    return name, merged


def make_quality(group_rows: dict[str, list[dict[str, Any]]], common_dates: list[date]) -> list[dict[str, Any]]:
    rows = []
    for name, config in GROUPS.items():
        data = group_rows[name]
        dates = [r["_date"] for r in data]
        result = {
            "group": config["label"],
            "cohort_days": len(data),
            "window": f"{min(dates).isoformat()}—{max(dates).isoformat()}",
            "duplicate_dates": len(dates) - len(set(dates)),
            "new_paid_rate_mismatch_days": source_counts(data)["new_paid_rate_mismatch_days"],
            "first_charge_rate_mismatch_days": source_counts(data)["first_charge_rate_mismatch_days"],
            "first_charge_gt_new_paid_days": source_counts(data)["first_charge_gt_new_paid_days"],
        }
        for metric, (field, days) in RETENTION.items():
            expected = [day for day in common_dates if day <= REFERENCE_DATE - timedelta(days=days)]
            observed = [r for r in data if r["_date"] in expected and rate(r.get(field)) is not None]
            result[f"{metric}_expected"] = len(expected)
            result[f"{metric}_observed"] = len(observed)
            result[f"{metric}_missing_dates"] = [r["_date"].isoformat() for r in data if r["_date"] in expected and rate(r.get(field)) is None]
        result["negative_lifecycle_days"] = sum(
            1 for r in data if any((number(r.get(k)) or 0) < 0 for k in ("终身", "首日", "次日", "3日", "7日", "15日"))
        )
        rows.append(result)
    return rows


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        try:
            return ImageFont.truetype(candidate, size, index=0)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_multiline(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font_obj: ImageFont.ImageFont, fill: str, width: int, leading: int = 5) -> None:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for char in paragraph:
            proposal = current + char
            if draw.textlength(proposal, font=font_obj) <= width:
                current = proposal
            else:
                lines.append(current)
                current = char
        if current:
            lines.append(current)
    y = xy[1]
    for line in lines:
        draw.text((xy[0], y), line, fill=fill, font=font_obj)
        y += font_obj.size + leading


def render_daily_new_chart(rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "34日新增趋势.png"
    width, height = 1520, 790
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(21), font(16)
    draw.text((64, 38), "H5/PWA 四渠道新增趋势", fill=NAVY, font=title)
    draw.text((64, 83), "2026年7月14日至8月16日；每个点为注册 cohort 新增人数；8/15起Facebook账户封禁影响已标注。", fill=MUTED, font=body)
    left, top, right, bottom = 130, 160, 1450, 620
    groups = sorted({r["group"] for r in rows})
    max_y = max(r["new_users"] for r in rows) * 1.12
    for part in range(5):
        value = max_y * part / 4
        y = bottom - (bottom-top)*part/4
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((24, y-8), fmt_num(value/1000, 1) + "k", fill=MUTED, font=small)
    dates = sorted({r["date"] for r in rows})
    for idx, day in enumerate(dates):
        if idx % 5 == 0 or idx == len(dates)-1:
            x = left+(right-left)*idx/(len(dates)-1)
            draw.text((x-17,bottom+12), datetime.strptime(day,"%Y-%m-%d").strftime("%m/%d"), fill=MUTED,font=small)
    for group in groups:
        series=[r for r in rows if r["group"]==group]
        points=[]
        for idx,r in enumerate(series):
            x=left+(right-left)*idx/(len(series)-1)
            y=bottom-(r["new_users"]/max_y)*(bottom-top)
            points.append((x,y))
        draw.line(points, fill=GROUP_COLORS[group], width=4)
        for x,y in points:
            draw.ellipse((x-3,y-3,x+3,y+3), fill=GROUP_COLORS[group])
    incident_day = FACEBOOK_ACCOUNT_BAN_START.isoformat()
    if incident_day in dates:
        incident_x = left + (right-left) * dates.index(incident_day) / (len(dates)-1)
        draw.line((incident_x, top, incident_x, bottom), fill=RED, width=3)
        box_x = max(left + 20, incident_x - 270)
        box_y = top + 18
        draw.rounded_rectangle((box_x, box_y, box_x + 250, box_y + 72), radius=8, fill="#FFF2F2", outline=RED, width=2)
        draw_multiline(draw, (box_x + 12, box_y + 9), "8/15–8/16 Facebook投放账户被封\n新增骤降，不作为产品/轻量化结论", small, RED, 226, leading=3)
    legend_x = left
    for group in groups:
        draw.rounded_rectangle((legend_x, 682, legend_x+14, 696), radius=3, fill=GROUP_COLORS[group])
        draw.text((legend_x+21, 678), group, fill=NAVY, font=small)
        legend_x += 180
    image.save(path)
    return path


def render_retention_chart(rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "H5_PWA成熟留存对比.png"
    width, height = 1520, 800
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(20), font(16)
    draw.text((64, 38), "H5 与 PWA：已达到观察天数的留存", fill=NAVY, font=title)
    draw.text((64, 83), "D1/D3使用34个已到对应观察日的cohort；D7使用30个已注册满7天的cohort。", fill=MUTED, font=body)
    left, top, right, bottom = 140, 155, 1440, 620
    selected=[r for r in rows if r["group"] in ("H5 汇总", "PWA 自然")]
    metrics=[("D1","d1"),("D3","d3"),("D7","d7")]
    max_y=0.75
    for tick in [0,0.2,0.4,0.6]:
        y=bottom-(tick/max_y)*(bottom-top)
        draw.line((left,y,right,y),fill=GRID,width=2)
        draw.text((55,y-8),fmt_rate(tick,0),fill=MUTED,font=small)
    colors={"H5 汇总":BLUE,"PWA 自然":PURPLE}
    for gi,r in enumerate(selected):
        for idx,(label,key) in enumerate(metrics):
            base_x=left+((right-left)/(len(metrics)))*idx+100
            x=base_x+gi*110
            v=r[key] or 0
            h=(v/max_y)*(bottom-top)
            draw.rounded_rectangle((x,bottom-h,x+72,bottom),radius=6,fill=colors[r["group"]])
            draw.text((x+1,bottom-h-25),fmt_rate(v),fill=NAVY,font=small)
            if gi==0: draw.text((base_x+28,bottom+12),label,fill=NAVY,font=body)
    legend_x=left
    for group,color in colors.items():
        draw.rounded_rectangle((legend_x,690,legend_x+14,704),radius=3,fill=color)
        draw.text((legend_x+20,686),group,fill=NAVY,font=small)
        legend_x+=160
    image.save(path)
    return path


def render_phase_chart(rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "发布期D3留存对比.png"
    width, height = 1520, 820
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(20), font(15)
    draw.text((64, 38), "发布期 D3 留存观察", fill=NAVY, font=title)
    draw.text((64, 83), "同一发布期内按渠道/运行形态比较；用于观察，不表达用户级版本因果。", fill=MUTED, font=body)
    rows=[r for r in rows if r["d3"] is not None]
    phases=[p["label"] for p in PHASES]
    groups=["H5 Facebook","H5 Google Ads","H5 自然","PWA 自然"]
    left,top,right,bottom=140,160,1450,620
    max_y=0.65
    for tick in [0,0.2,0.4,0.6]:
        y=bottom-(tick/max_y)*(bottom-top)
        draw.line((left,y,right,y),fill=GRID,width=2)
        draw.text((55,y-8),fmt_rate(tick,0),fill=MUTED,font=small)
    period_w=(right-left)/len(phases)
    bar_w=22
    for pi,label in enumerate(phases):
        base=left+period_w*pi+18
        group_rows={r["group"]:r for r in rows if r["phase"]==label}
        for gi,group in enumerate(groups):
            r=group_rows.get(group)
            if not r: continue
            v=r["d3"] or 0
            h=(v/max_y)*(bottom-top)
            x=base+gi*(bar_w+8)
            draw.rounded_rectangle((x,bottom-h,x+bar_w,bottom),radius=4,fill=GROUP_COLORS[group])
        draw_multiline(draw,(base,bottom+12),label,small,NAVY,int(period_w-22),leading=2)
    lx=left
    for group in groups:
        draw.rounded_rectangle((lx,724,lx+13,737),radius=3,fill=GROUP_COLORS[group])
        draw.text((lx+19,721),group,fill=NAVY,font=small)
        lx+=170
    image.save(path)
    return path


def render_quality_chart(rows: list[dict[str, Any]]) -> Path:
    path = ASSETS / "数据成熟与口径质量.png"
    width, height = 1520, 650
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title, body, small = font(32), font(20), font(16)
    draw.text((64, 38), "留存观察覆盖与口径质量", fill=NAVY, font=title)
    draw.text((64, 83), "绿色=已达到观察天数且有值；黄色=已达到观察天数但源数据缺失；红色=口径不对账。", fill=MUTED, font=body)
    cols=[("D1","D1_expected","D1_observed"),("D3","D3_expected","D3_observed"),("D7","D7_expected","D7_observed"),("D15","D15_expected","D15_observed"),("D30","D30_expected","D30_observed")]
    x0,y0,cellw,cellh=330,165,170,78
    for ci,(label,_,_) in enumerate(cols):
        draw.text((x0+ci*cellw+38,y0-36),label,fill=NAVY,font=body)
    for ri,row in enumerate(rows):
        y=y0+ri*cellh
        draw.text((65,y+22),row["group"],fill=NAVY,font=body)
        for ci,(_,expected,observed) in enumerate(cols):
            x=x0+ci*cellw
            exp,obs=row[expected],row[observed]
            color="#E5F5EB" if exp==obs else "#FFF1D6"
            draw.rounded_rectangle((x,y,x+145,y+52),radius=8,fill=color,outline="#D7E5EF")
            draw.text((x+18,y+16),f"{obs}/{exp}",fill=NAVY,font=body)
    qy=y0+len(rows)*cellh+25
    for i,row in enumerate(rows):
        text=f"{row['group']}：新增付费率不对账 {row['new_paid_rate_mismatch_days']}/{row['cohort_days']} 天；首充人数>新增付费人数 {row['first_charge_gt_new_paid_days']}/{row['cohort_days']} 天"
        draw.text((65,qy+i*30),text,fill=RED,font=small)
    image.save(path)
    return path


def source_meta() -> list[dict[str, Any]]:
    return [
        {
            "id": "new-user-source",
            "label": "新包新增用户分析（H5/PWA 四个目标页）",
            "href": LARK_NEW_USER_URL,
            "query": {
                "engine": "Lark Sheets API",
                "sql": "SELECT cohort_date AS date, channel_group AS group, new_users, d1_rate AS d1, d3_rate AS d3, d7_rate AS d7, source_new_paid_users, source_new_paid_rate, source_first_charge_users, source_first_charge_rate FROM daily_new WHERE cohort_date BETWEEN '2026-07-14' AND '2026-08-16';",
                "description": "读取 WAJEBETH5、wajeH5-facebook、wajeH5ga-googlewords_int、PWA 的 cohort 日聚合指标。",
                "executed_at": "2026-08-19T16:00:00+08:00",
                "tables_used": ["WAJEBETH5", "wajeH5-facebook", "wajeH5ga-googlewords_int", "PWA"],
                "filters": ["共同 cohort 窗口 2026-07-14 至 2026-08-16", "来源修订版 618"],
                "metric_definitions": ["D1/D3/D7 等留存仅纳入截至2026-08-19已达到对应观察天数的cohort，并按新增人数加权；例如D7只含已注册满7天的cohort。", "来源付费率与人数不对账，按独立来源字段展示。"],
            },
        },
        {
            "id": "update-source",
            "label": "更新记录·新包 + 运营补充",
            "href": LARK_UPDATE_URL,
            "query": {
                "engine": "Lark Sheets API",
                "sql": "SELECT event_date AS date, event_kind AS kind, content FROM update_events WHERE event_date BETWEEN '2026-07-14' AND '2026-08-16' ORDER BY event_date;",
                "description": "读取 2026-07-14 至 2026-08-16 的轻量化游戏、版本、埋点、风控和运营事件；包含用户补充的8/15–8/16 Facebook投放账户封禁事实。",
                "executed_at": "2026-08-19T16:00:00+08:00",
                "tables_used": ["新包", "用户补充运营事实"],
                "filters": ["只保留与轻量化游戏、H5/PWA、版本、埋点或干扰事件有关的记录"],
                "metric_definitions": ["更新记录只用作事件切点和干扰标注，不用于直接证明效果。"],
            },
        },
        {
            "id": "history-source",
            "label": "轻量化游戏历史数据盘点与近30天专题分析框架",
            "href": HISTORY_URL,
            "query": {"engine": "SQLite reproducibility snapshot", "sql": "SELECT metric, value FROM historical_context;", "description": "提供5月历史轻量化入口点击、0局和非0局基线及口径冲突说明。", "executed_at": "2026-08-18T16:00:00+08:00", "tables_used": ["historical_context"], "filters": [], "metric_definitions": ["历史数据不与本轮7/8月窗口直接合并。"]},
        },
        {
            "id": "performance-source",
            "label": "轻量化游戏标准 V1.2 与 H5/PWA性能监控方案",
            "href": PERFORMANCE_URL,
            "query": {"engine": "SQLite reproducibility snapshot", "sql": "SELECT requirement FROM performance_requirements;", "description": "定义 H5/PWA 的资源、性能、bet_ready 和低端机/弱网观测要求。", "executed_at": "2026-08-19T16:00:00+08:00", "tables_used": ["performance_requirements"], "filters": [], "metric_definitions": ["性能字段缺失时，不能将资源或加载问题归因于用户行为。"]},
        },
    ]


def write_sqlite(analysis: dict[str, Any], paid_rows: list[dict[str, Any]]) -> None:
    if SQLITE_DB.exists():
        SQLITE_DB.unlink()
    with sqlite3.connect(SQLITE_DB) as conn:
        conn.execute("CREATE TABLE daily_new (cohort_date TEXT, channel_group TEXT, new_users REAL, d1_rate REAL, d3_rate REAL, d7_rate REAL, source_new_paid_users REAL, source_new_paid_rate REAL, source_first_charge_users REAL, source_first_charge_rate REAL)")
        conn.executemany(
            "INSERT INTO daily_new VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (r["date"], r["group"], r["new_users"], r["d1"], r["d3"], r["d7"], r["source_new_paid_users"], r["source_new_paid_rate"], None, None)
                for r in analysis["daily_rows"]
            ],
        )
        conn.execute("CREATE TABLE channel_summary (channel_group TEXT, new_users REAL, d1_rate REAL, d3_rate REAL, d7_rate REAL, source_new_paid_users REAL, source_new_paid_rate_mean REAL, source_first_charge_users REAL, source_first_charge_rate_mean REAL)")
        conn.executemany(
            "INSERT INTO channel_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (r["group"], r["new_users"], r["d1"], r["d3"], r["d7"], r["source_new_paid_users"], r["source_new_paid_rate_mean"], r["source_first_charge_users"], r["source_first_charge_rate_mean"])
                for r in analysis["group_summary"]
            ],
        )
        conn.execute("CREATE TABLE phase_metrics (phase TEXT, channel_group TEXT, new_users REAL, d1_rate REAL, d3_rate REAL, d7_rate REAL, notes TEXT)")
        conn.executemany(
            "INSERT INTO phase_metrics VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(r["phase"], r["group"], r["new_users"], r["d1"], r["d3"], r["d7"], r["notes"]) for r in analysis["phase_rows"]],
        )
        conn.execute("CREATE TABLE quality (channel_group TEXT, cohort_days INTEGER, d7_coverage TEXT, d15_coverage TEXT, d30_coverage TEXT, new_paid_mismatch_days INTEGER, first_charge_gt_new_paid_days INTEGER)")
        conn.executemany(
            "INSERT INTO quality VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(r["group"], r["cohort_days"], r["D7_observed"], r["D15_observed"], r["D30_observed"], r["new_paid_rate_mismatch_days"], r["first_charge_gt_new_paid_days"]) for r in analysis["quality_rows"]],
        )
        conn.execute("CREATE TABLE update_events (event_date TEXT, event_kind TEXT, content TEXT)")
        conn.executemany("INSERT INTO update_events VALUES (?, ?, ?)", [(r["date"], r["kind"], r["content"]) for r in analysis["update_events"]])
        conn.execute("CREATE TABLE facebook_account_ban_impact (baseline_window TEXT, affected_window TEXT, baseline_daily_new REAL, affected_daily_new REAL, daily_new_decline REAL, benchmark_new_gap REAL, d7_interpretation TEXT)")
        incident = analysis["facebook_account_ban"]
        conn.execute(
            "INSERT INTO facebook_account_ban_impact VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                incident["baseline_window"], incident["affected_window"], incident["before"]["daily_new"],
                incident["after"]["daily_new"], incident["daily_new_decline"], incident["benchmark_new_gap"],
                incident["d7_interpretation"],
            ),
        )
        conn.execute("CREATE TABLE historical_context (metric TEXT, value TEXT)")
        for key, value in analysis.get("history_context", {}).items():
            conn.execute("INSERT INTO historical_context VALUES (?, ?)", (key, json.dumps(value, ensure_ascii=False)))
        conn.execute("CREATE TABLE performance_requirements (requirement TEXT)")
        conn.executemany("INSERT INTO performance_requirements VALUES (?)", [(item,) for item in analysis["limitations"]])
        conn.commit()


def build_artifact(analysis: dict[str, Any]) -> dict[str, Any]:
    groups = analysis["group_summary"]
    h5 = next(x for x in groups if x["group"] == "H5 汇总")
    pwa = next(x for x in groups if x["group"] == "PWA 自然")
    channel_groups = [x for x in groups if x["group"] not in ("H5 汇总",)]
    h5_fb = next(x for x in channel_groups if x["group"] == "H5 Facebook")
    h5_google = next(x for x in channel_groups if x["group"] == "H5 Google Ads")
    h5_natural = next(x for x in channel_groups if x["group"] == "H5 自然")
    account_ban = analysis["facebook_account_ban"]
    sources = source_meta()
    daily = analysis["daily_rows"]
    phase_rows = analysis["phase_rows"]
    paid_rows = [
        {
            "group": x["group"],
            "indicator": "来源新增付费率·cohort日均值",
            "rate": x["source_new_paid_rate_mean"],
            "users": x["source_new_paid_users"],
        }
        for x in channel_groups
    ] + [
        {
            "group": x["group"],
            "indicator": "来源首充付费率·cohort日均值",
            "rate": x["source_first_charge_rate_mean"],
            "users": x["source_first_charge_users"],
        }
        for x in channel_groups
    ]
    quality_display = [
        {
            "group": row["group"],
            "cohort_days": row["cohort_days"],
            "D7_observed": f"{row['D7_observed']}/{row['D7_expected']}",
            "D15_observed": f"{row['D15_observed']}/{row['D15_expected']}",
            "D30_observed": f"{row['D30_observed']}/{row['D30_expected']}",
            "new_paid_rate_mismatch_days": row["new_paid_rate_mismatch_days"],
            "first_charge_gt_new_paid_days": row["first_charge_gt_new_paid_days"],
        }
        for row in analysis["quality_rows"]
    ]
    headline = [{
        "common_cohort_days": analysis["window"]["common_cohort_days"],
        "d7_mature_cohort_days": analysis["window"]["d7_mature_cohort_days"],
        "h5_d7": h5["d7"],
        "pwa_d7": pwa["d7"],
        "rate_mismatch_days": sum(x["paid_rate_mismatch_days"] for x in channel_groups),
    }]
    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Waje H5/PWA 轻量化游戏效果与新用户留存付费分析",
        "description": "截至2026年8月19日的 H5/PWA 新用户 cohort、发布期观察与数据质量分析。",
        "generatedAt": "2026-08-19T16:00:00+08:00",
        "sources": sources,
        "cards": [
            {"id":"card-cohorts","dataset":"headline","sourceId":"new-user-source","description":"四个目标页共同有效 cohort 日数。","metrics":[{"label":"共同 cohort 日","field":"common_cohort_days","format":"number"}]},
            {"id":"card-d7","dataset":"headline","sourceId":"new-user-source","description":"四个目标页中，注册日至观察日已满7天、可计算D7的 cohort 日期数。","metrics":[{"label":"D7已满7天的cohort日","field":"d7_mature_cohort_days","format":"number"}]},
            {"id":"card-h5-d7","dataset":"headline","sourceId":"new-user-source","description":"H5 三渠道新增人数加权 D7 留存。","metrics":[{"label":"H5 汇总 D7","field":"h5_d7","format":"percent"}]},
            {"id":"card-pwa-d7","dataset":"headline","sourceId":"new-user-source","description":"PWA 自然渠道新增人数加权 D7 留存。","metrics":[{"label":"PWA D7","field":"pwa_d7","format":"percent"}]},
        ],
        "charts": [
            {
                "id":"daily-new","title":"四渠道每日新增用户","subtitle":"2026年7月14日至8月16日；8月15–16日H5 Facebook投放账户封禁影响已在图下注记，不作为产品或轻量化效果。","type":"line","dataset":"daily_new","sourceId":"new-user-source","layout":"full",
                "encodings":{"x":{"field":"date","type":"temporal","label":"cohort 日期"},"y":{"field":"new_users","type":"quantitative","format":"number","label":"新增人数"},"color":{"field":"group","type":"nominal","label":"渠道/运行形态"},"tooltip":[{"field":"date","type":"temporal"},{"field":"group","type":"nominal"},{"field":"new_users","type":"quantitative","format":"number"}]},
            },
            {
                "id":"retention-channel","title":"四渠道：已达到观察天数的留存对比","subtitle":"D1/D3使用34个已到对应观察日的cohort；D7使用30个已注册满7天的cohort；全部按新增人数加权。","type":"bar","dataset":"retention_long","sourceId":"new-user-source","layout":"full",
                "encodings":{"x":{"field":"group","type":"nominal","label":"渠道/运行形态"},"y":{"field":"rate","type":"quantitative","format":"percent","label":"留存率"},"color":{"field":"metric","type":"nominal","label":"留存天数"},"tooltip":[{"field":"group","type":"nominal"},{"field":"metric","type":"nominal"},{"field":"rate","type":"quantitative","format":"percent"},{"field":"cohort_days","type":"quantitative","format":"number"},{"field":"new_users","type":"quantitative","format":"number"}]},
            },
            {
                "id":"phase-d3","title":"发布期 D3 留存观察","subtitle":"按更新记录切分；真实版本字段缺失，展示的是发布期观察而非用户级版本效果。","type":"bar","dataset":"phase_metrics","sourceId":"new-user-source","layout":"full",
                "encodings":{"x":{"field":"phase","type":"nominal","label":"发布期"},"y":{"field":"d3","type":"quantitative","format":"percent","label":"D3 留存"},"color":{"field":"group","type":"nominal","label":"渠道/运行形态"},"tooltip":[{"field":"phase","type":"nominal"},{"field":"group","type":"nominal"},{"field":"d3","type":"quantitative","format":"percent"},{"field":"new_users","type":"quantitative","format":"number"},{"field":"notes","type":"text"}]},
            },
            {
                "id":"source-paid-rates","title":"来源新增付费与首充显示率","subtitle":"cohort 日均值；两类来源指标的分子分母未对账，不能理解为漏斗或免费用户的互补分组。","type":"bar","dataset":"paid_rates","sourceId":"new-user-source","layout":"full",
                "encodings":{"x":{"field":"group","type":"nominal","label":"渠道/运行形态"},"y":{"field":"rate","type":"quantitative","format":"percent","label":"来源显示率"},"color":{"field":"indicator","type":"nominal","label":"来源指标"},"tooltip":[{"field":"group","type":"nominal"},{"field":"indicator","type":"nominal"},{"field":"rate","type":"quantitative","format":"percent"},{"field":"users","type":"quantitative","format":"number"}]},
            },
        ],
        "tables": [
            {
                "id":"channel-matrix","title":"H5/PWA 渠道留存与来源付费指标","subtitle":"留存只使用已达到对应观察天数的cohort；付费人数和显示率并列，不合并为单一付费率。","dataset":"channel_summary","sourceId":"new-user-source","density":"spacious","layout":"full",
                "columns":[
                    {"field":"group","label":"渠道/运行形态","type":"text"},
                    {"field":"new_users","label":"新增用户","format":"number","type":"number"},
                    {"field":"d1","label":"D1","format":"percent","type":"percent"},
                    {"field":"d3","label":"D3","format":"percent","type":"percent"},
                    {"field":"d7","label":"D7","format":"percent","type":"percent"},
                    {"field":"d7_cohorts","label":"D7 cohort数","format":"number","type":"number"},
                    {"field":"source_new_paid_users","label":"来源新增付费人数","format":"number","type":"number"},
                    {"field":"source_new_paid_rate_mean","label":"来源新增付费率·日均","format":"percent","type":"percent"},
                    {"field":"source_first_charge_users","label":"来源首充人数","format":"number","type":"number"},
                    {"field":"source_first_charge_rate_mean","label":"来源首充率·日均","format":"percent","type":"percent"},
                ],
            },
            {
                "id":"release-matrix","title":"发布期渠道留存观察明细","subtitle":"D1/D3/D7只纳入已达到相应观察天数的cohort；仅用于发布期观察。","dataset":"phase_metrics","sourceId":"new-user-source","density":"comfortable","layout":"full",
                "columns":[
                    {"field":"phase","label":"发布期","type":"text"},
                    {"field":"group","label":"渠道/运行形态","type":"text"},
                    {"field":"new_users","label":"新增","format":"number","type":"number"},
                    {"field":"d1","label":"D1","format":"percent","type":"percent"},
                    {"field":"d3","label":"D3","format":"percent","type":"percent"},
                    {"field":"d7","label":"D7","format":"percent","type":"percent"},
                    {"field":"d7_cohorts","label":"D7 cohort日","format":"number","type":"number"},
                ],
            },
            {
                "id":"update-timeline","title":"发布期相关更新与干扰事件","subtitle":"事件表用于解释观察边界，不直接作为效果证据。","dataset":"update_events","sourceId":"update-source","density":"comfortable","layout":"full",
                "columns":[
                    {"field":"date","label":"日期","type":"date"},
                    {"field":"kind","label":"事件类型","type":"text"},
                    {"field":"content","label":"更新内容","type":"text"},
                ],
            },
        ],
        "blocks": [
            {"id":"headline-metrics","type":"metric-strip","cardIds":["card-cohorts","card-d7","card-h5-d7","card-pwa-d7"]},
            {"id":"new-finding","type":"markdown","body":"## 新增规模与渠道结构\n\n**新增曲线展示的是流量规模，不等于轻量化效果。** H5 Facebook、H5 Google、H5自然和PWA自然的每日新增在同一时间段受投放、自然流量、版本和活动共同影响。下图用于识别结构变化和异常日；游戏上线效果只在同渠道、同发布期并结合已达到观察天数的留存时观察。", "sourceId":"new-user-source"},
            {"id":"daily-new-block","type":"chart","chartId":"daily-new"},
            {"id":"facebook-account-ban","type":"markdown","body":f"### 8月15–16日Facebook投放账户事件\n\n**原因已确认：H5 Facebook投放账户被封。** 8月11–14日日均新增为 **{fmt_count(account_ban['before']['daily_new'])}** 人，8月15–16日降至 **{fmt_count(account_ban['after']['daily_new'])}** 人，降幅 **{fmt_rate(account_ban['daily_new_decline'])}**；按前四日日均作对照，两日少 **{fmt_count(account_ban['benchmark_new_gap'])}** 名新增。Facebook在H5新增中的占比也由 **{fmt_rate(account_ban['before']['facebook_share_of_h5_new'])}** 降至 **{fmt_rate(account_ban['after']['facebook_share_of_h5_new'])}**。\n\n这解释的是**新增规模和渠道结构突变**，不是轻量化游戏表现。当前期D7只使用8月11–12日cohort，早于账户封禁影响日，因此不能把该事件写成D7变化原因。"},
            {"id":"retention-finding","type":"markdown","body":"## 留存差异必须按已达到观察天数的 cohort 读取\n\n**“已达到观察天数”指注册日至观察日的间隔已走满对应天数。** 例如本报告观察日是8月19日：D7只统计8月12日及以前注册、已经有完整7天观察期的30个cohort；8月13日及以后注册的用户尚未走满7天，不进入D7分母。D15/D30同理；PWA还有部分已到观察日但源数据为空的日期，因此长周期只作为辅助观察。", "sourceId":"new-user-source"},
            {"id":"retention-chart-block","type":"chart","chartId":"retention-channel"},
            {"id":"channel-table-block","type":"table","tableId":"channel-matrix"},
            {"id":"release-finding","type":"markdown","body":"## 发布期观察：版本与游戏节点重叠\n\n**H5 2.1.14/Keno、Color Dice、Opera埋点等只作为时间切点。** 当前表缺少用户真实版本和游戏参与字段，因此图表可以提示哪些发布期需要复盘，但不支持“某版本造成留存变化”的结论。", "sourceId":"update-source"},
            {"id":"phase-chart-block","type":"chart","chartId":"phase-d3"},
            {"id":"release-table-block","type":"table","tableId":"release-matrix"},
            {"id":"timeline-finding","type":"markdown","body":"## 更新事件决定了归因边界\n\n**故障、风控、活动和埋点变化必须同时呈现。** 下表是本轮所有发布期判断的事件背景；任何与这些日期重叠的变化均只能被描述为观察性关联。", "sourceId":"update-source"},
            {"id":"timeline-table-block","type":"table","tableId":"update-timeline"},
            {"id":"payment-finding","type":"markdown","body":"## 付费与首充：保留来源指标，不制造免费用户分群\n\n**来源新增付费率、首充付费率、对应人数和首充留存必须并列阅读。** 它们的分母/用户范围尚未确认一致，因此付费分析仅描述来源指标的分布与变化，不把人数和率重算为新的“准确付费率”。", "sourceId":"new-user-source"},
            {"id":"payment-chart-block","type":"chart","chartId":"source-paid-rates"},
            {"id":"recommendations","type":"markdown","body":"## 建议的下一步\n\n1. **P0：补齐关联键。** 所有轻量化游戏与版本发布必须记录 `game_id`、`h5_build`、`config_version`、渠道、会话和用户类型。\n2. **P0：建立首局漏斗。** 覆盖入口曝光、点击、加载、可下注、首局开始、首局完成、异常与重试，并按设备/网络切片。\n3. **P1：补齐用户类型 cohort。** 输出免费、来源新增付费、首充、复充四类互斥/可追溯人群的D1/D3/D7与订单结果。\n4. **P1：将更新记录接入看板。** 每条上线、故障、活动和埋点变更自动形成前后7天观察窗口，并标明各留存指标是否已达到观察天数。\n\n## 口径与使用边界\n\n- `WAJEBETH5` 按既有映射作为 H5自然渠道。\n- H5版本使用发布期代理，非真实用户版本归因。\n- 终身、首日、TC、TX为来源定义字段，未命名为LTV，也不跨渠道直接汇总。\n- 5月历史轻量化结果仅作背景基线，不和本轮7/8月 cohort 合并。"},
        ],
    }
    return {
        "surface": "report",
        "manifest": manifest,
        "snapshot": {
            "version": 1,
            "generatedAt": "2026-08-19T16:00:00+08:00",
            "status": "ready",
            "datasets": {
                "headline": headline,
                "daily_new": daily,
                "retention_long": analysis["retention_long"],
                "phase_metrics": phase_rows,
                "paid_rates": paid_rows,
                "channel_summary": channel_groups,
                "quality": quality_display,
                "update_events": analysis["update_events"],
            },
        },
        "sources": sources,
        "package_info": {"title": "Waje H5/PWA轻量化游戏效果与新用户留存付费分析", "source_revision": SOURCE_REVISION, "analysis_as_of": REFERENCE_DATE.isoformat()},
    }


def feishu_xml(analysis: dict[str, Any]) -> str:
    groups = analysis["group_summary"]
    h5 = next(x for x in groups if x["group"] == "H5 汇总")
    pwa = next(x for x in groups if x["group"] == "PWA 自然")
    channels = [x for x in groups if x["group"] != "H5 汇总"]
    quality_rows = analysis["quality_rows"]
    h5_fb = next(x for x in groups if x["group"] == "H5 Facebook")
    account_ban = analysis["facebook_account_ban"]
    source_rows = "".join(
        f"<tr><td><p>{escape_xml(r['group'])}</p></td><td><p>{fmt_num(r['new_users'])}</p></td><td><p>{fmt_rate(r['d1'])}</p></td><td><p>{fmt_rate(r['d3'])}</p></td><td><p>{fmt_rate(r['d7'])}</p></td><td><p>{fmt_num(r['source_new_paid_users'])}</p></td><td><p>{fmt_rate(r['source_new_paid_rate_mean'])}</p></td></tr>"
        for r in channels
    )
    quality_xml = "".join(
        f"<tr><td><p>{escape_xml(r['group'])}</p></td><td><p>{r['D7_observed']}/{r['D7_expected']}</p></td><td><p>{r['D15_observed']}/{r['D15_expected']}</p></td><td><p>{r['new_paid_rate_mismatch_days']}/{r['cohort_days']}</p></td><td><p>{r['first_charge_gt_new_paid_days']}/{r['cohort_days']}</p></td></tr>"
        for r in quality_rows
    )
    events_xml = "".join(
        f"<tr><td><p>{escape_xml(item['date'])}</p></td><td><p>{escape_xml(item['kind'])}</p></td><td><p>{escape_xml(item['content'])}</p></td></tr>"
        for item in analysis["update_events"]
    )
    return f'''<title>Waje H5/PWA轻量化游戏效果与新用户留存付费分析（截至2026-08-19）</title>
<p>数据范围：新包新增用户分析四个H5/PWA目标页，cohort日期为2026年7月14日至8月16日；观察基准日为2026年8月19日。来源修订版：{SOURCE_REVISION}。</p>
<callout emoji="💡" background-color="light-blue" border-color="blue"><p><b>结论一：H5 Facebook 是当前最优先处理的渠道。</b>它带来H5三渠道<b>{fmt_rate(h5_fb['new_users']/h5['new_users'])}</b>的新增（{fmt_num(h5_fb['new_users'])}人），但已注册满7天用户的D7仅为<b>{fmt_rate(h5_fb['d7'])}</b>；因此H5三渠道加权D7只有<b>{fmt_rate(h5['d7'])}</b>。优先排查Facebook流量质量、入口加载与首局路径。</p><p><b>流量异常说明：</b>8月15–16日Facebook投放账户被封。日均新增由{fmt_count(account_ban['before']['daily_new'])}人降至{fmt_count(account_ban['after']['daily_new'])}人，降幅<b>{fmt_rate(account_ban['daily_new_decline'])}</b>；这只用于解释流量和渠道结构突变，不作为轻量化或D7留存变化原因。</p><p><b>结论二：PWA暂不能被认定为体验更优。</b>PWA自然渠道D7为<b>{fmt_rate(pwa['d7'])}</b>，但样本为{fmt_num(pwa['new_users'])}人，且渠道构成与H5不同；这只是需要继续验证的观察差异。</p><p><b>结论三：本轮不能证明某个轻量化游戏或版本带来留存变化。</b>发布节点、KYC/risk、活动与埋点改动重叠，且缺少真实版本、game_id和首局事实。</p></callout>
<h1 seq="auto">数据范围与统计口径</h1>
<p>仅纳入WAJEBETH5（H5自然）、wajeH5-facebook（标准H5 Facebook）、wajeH5ga-googlewords_int（标准H5 Google Ads）和PWA（PWA自然）四页的共同cohort窗口。<b>“已达到观察天数”指注册日至观察日的间隔已走满对应天数。</b>例如观察日为8月19日时，D7只计算8月12日及以前注册、已满7天的30个cohort；8月13日及以后注册的用户尚未走满7天，不进入D7分母。所有留存按新增人数加权；D15/D30同理。PWA已达到观察天数但来源为空的D15/D30显示为<b>N/A·源缺失</b>，不作为0值。</p>
<h1 seq="auto">四渠道新增趋势</h1>
<p>每个点为当日注册 cohort 新增人数，用于识别流量规模与结构变化，不能单独作为轻量化效果结论。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_2026_08_19/assets/34日新增趋势.png" caption="四个目标渠道，2026-07-14至2026-08-16；红色标记为8月15–16日Facebook投放账户被封影响。"/>
<callout emoji="⚠️" background-color="light-yellow" border-color="yellow"><p><b>8月15–16日Facebook新增骤降已确认是投放账户被封导致。</b>封禁前（8月11–14日）日均新增{fmt_count(account_ban['before']['daily_new'])}人，影响日降至{fmt_count(account_ban['after']['daily_new'])}人，降幅{fmt_rate(account_ban['daily_new_decline'])}。因此当前期新增量、渠道结构及D1/D3构成不适用于判断轻量化游戏效果；D7仅使用8月11–12日cohort，早于该事件。</p></callout>
<h1 seq="auto">H5与PWA：已达到观察天数的留存</h1>
<p>例如D7只统计已注册满7天的用户；截至8月19日，D7只含8月12日及以前注册的cohort。全部新增 cohort 按新增人数加权。H5与PWA的渠道结构不同，横向差异不等于体验因果。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_2026_08_19/assets/H5_PWA成熟留存对比.png" caption="D1/D3/D7均只计算已达到对应观察天数的cohort；例如D7只含已注册满7天的用户。"/>
<table><colgroup><col width="180"/><col width="130"/><col width="110"/><col width="110"/><col width="110"/><col width="150"/><col width="160"/></colgroup><thead><tr><th background-color="light-blue"><p>渠道/运行形态</p></th><th background-color="light-blue"><p>新增</p></th><th background-color="light-blue"><p>D1</p></th><th background-color="light-blue"><p>D3</p></th><th background-color="light-blue"><p>D7</p></th><th background-color="light-blue"><p>来源新增付费人数</p></th><th background-color="light-blue"><p>来源新增付费率日均</p></th></tr></thead><tbody>{source_rows}</tbody></table>
<h1 seq="auto">发布期观察</h1>
<p>下图按更新记录切分发布期。真实H5 build缺失，故仅可比较同渠道在不同发布时间窗的观察性变化。</p>
<img path="@./analysis/h5_pwa_lightgame_effect_2026_08_19/assets/发布期D3留存对比.png" caption="发布期D3留存；Limbo、Keno/2.1.14、Color Dice、Opera埋点和当前期。"/>
<callout emoji="⚠️" background-color="light-yellow" border-color="yellow"><p><b>干扰说明：</b>7月20–21日Aviator维护与触达、7月26–28日risk/KYC变化、7月30日页面调整、8月6日Opera埋点均已作为时间轴注记；不使用“版本导致”或“游戏带来”的因果表述。</p></callout>
<table><colgroup><col width="110"/><col width="130"/><col width="610"/></colgroup><thead><tr><th background-color="light-blue"><p>日期</p></th><th background-color="light-blue"><p>事件类型</p></th><th background-color="light-blue"><p>更新内容</p></th></tr></thead><tbody>{events_xml}</tbody></table>
<h1 seq="auto">建议的下一步</h1>
<ol><li><b>P0：补齐关联键。</b>发布事件必须带game_id、h5_build、config_version、渠道、会话和用户类型。</li><li><b>P0：补齐首局漏斗。</b>覆盖曝光、点击、加载、可下注、首局开始/完成及错误/重试。</li><li><b>P1：补齐免费/付费cohort。</b>输出互斥用户类型下D1/D3/D7、首充/复充和服务端订单结果。</li><li><b>P1：更新记录进入看板。</b>每条上线、故障、活动和埋点变更自动标注观察窗口，并标明各留存指标是否已达到观察天数。</li></ol>
<h1 seq="auto">来源与边界</h1>
<ul><li>新包新增用户分析：WAJEBETH5、wajeH5-facebook、wajeH5ga-googlewords_int、PWA。</li><li>更新记录·新包：游戏、版本、埋点、风控和运营事件。</li><li>轻量化历史分析与H5/PWA性能规范：仅作为机制、历史基线和待验证假设。</li><li>终身、首日、TC、TX沿用来源定义，不命名为LTV，也不跨渠道直接求和。</li></ul>
<p align="center">Waje 数据产品分析 · 2026-08-19</p>'''


def feishu_event_table_xml(analysis: dict[str, Any]) -> str:
    events_xml = "".join(
        f"<tr><td><p>{escape_xml(item['date'])}</p></td><td><p>{escape_xml(item['kind'])}</p></td><td><p>{escape_xml(item['content'])}</p></td></tr>"
        for item in analysis["update_events"]
    )
    return f'''<table><colgroup><col width="110"/><col width="130"/><col width="610"/></colgroup><thead><tr><th background-color="light-blue"><p>日期</p></th><th background-color="light-blue"><p>事件类型</p></th><th background-color="light-blue"><p>更新内容</p></th></tr></thead><tbody>{events_xml}</tbody></table>'''

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feishu-xml", type=Path)
    parser.add_argument("--feishu-event-table-xml", type=Path)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    group_rows: dict[str, list[dict[str, Any]]] = {}
    source_details = {}
    for name, config in GROUPS.items():
        _, rows, meta = load_rows(RAW / config["file"])
        group_rows[name] = rows
        source_details[name] = meta
    update_events = load_update_events(RAW / "update_log_new_package.json")
    update_events.append({
        "date": FACEBOOK_ACCOUNT_BAN_START.isoformat(),
        "kind": "投放异常",
        "content": "用户补充：H5 Facebook投放账户被封，影响8月15–16日新增投放；该流量骤降不作为轻量化游戏、产品体验或D7留存变化依据。",
    })
    update_events.sort(key=lambda item: item["date"])

    date_sets = [set(r["_date"] for r in rows) for rows in group_rows.values()]
    common_dates = sorted(
        day for day in set.intersection(*date_sets)
        if ANALYSIS_START <= day <= ANALYSIS_END
    )
    analysis_rows = {name: [r for r in rows if r["_date"] in common_dates] for name, rows in group_rows.items()}
    h5_name, h5_rows = combine_rows("H5 汇总", ["WAJEBETH5", "wajeH5-facebook", "wajeH5ga-googlewords_int"], analysis_rows)
    combined = {**analysis_rows, h5_name: h5_rows}

    summaries = [group_summary(name, GROUPS[name], analysis_rows[name]) for name in GROUPS]
    h5_config = {"label": "H5 汇总", "surface": "H5", "channel": "三渠道加权"}
    summaries.append(group_summary("H5 汇总", h5_config, h5_rows))
    account_ban = facebook_account_ban_impact(analysis_rows["wajeH5-facebook"], h5_rows)

    daily_rows = []
    for name, config in GROUPS.items():
        for r in analysis_rows[name]:
            daily_rows.append({
                "date": r["_date"].isoformat(), "group": config["label"],
                "new_users": number(r.get("新增人数")) or 0,
                "d1": rate(r.get("次留")), "d3": rate(r.get("3日留")), "d7": rate(r.get("7日留")),
                "source_new_paid_users": number(r.get("新增付费人数")) or 0,
                "source_new_paid_rate": rate(r.get("新增付费率")),
            })
    daily_rows.sort(key=lambda x: (x["date"], x["group"]))

    retention_long = []
    for s in summaries:
        if s["group"] == "H5 汇总":
            continue
        for metric, field in (("D1", "d1"), ("D3", "d3"), ("D7", "d7")):
            retention_long.append({
                "group": s["group"], "metric": metric, "rate": s[field],
                "cohort_days": s["d7_cohorts"] if metric == "D7" else len(common_dates),
                "new_users": s["d7_new_users"] if metric == "D7" else s["new_users"],
            })

    phase_rows = []
    sensitivity_rows = []
    for phase in PHASES:
        for name, config in GROUPS.items():
            phase_data = date_subset(analysis_rows[name], phase["start"], phase["end"])
            summary = group_summary(name, config, phase_data)
            phase_rows.append({
                "phase": phase["label"], "window": phase["window"], "group": config["label"],
                "new_users": summary["new_users"], "d1": summary["d1"], "d3": summary["d3"], "d7": summary["d7"],
                "d7_cohorts": summary["d7_cohorts"], "notes": phase["note"],
            })
        for label, data in (("H5 汇总", h5_rows), ("PWA 自然", analysis_rows["PWA"])):
            sensitivity_data = date_subset(data, phase["start"], phase["end"], phase["sensitivity_exclude"])
            summary = group_summary(label, h5_config if label == "H5 汇总" else GROUPS["PWA"], sensitivity_data)
            sensitivity_rows.append({"phase": phase["label"], "group": label, "days_excluded": len(phase["sensitivity_exclude"]), "new_users": summary["new_users"], "d1": summary["d1"], "d3": summary["d3"], "d7": summary["d7"]})

    quality_rows = make_quality(analysis_rows, common_dates)
    history = {}
    history_path = ROOT / "analysis/lightgame_topic_2026_08_18/analysis.json"
    if history_path.exists():
        history_data = json.loads(history_path.read_text())
        history = history_data.get("click", {})

    analysis = {
        "title": "Waje H5/PWA轻量化游戏效果与新用户留存付费分析",
        "as_of": REFERENCE_DATE.isoformat(),
        "source_revision": SOURCE_REVISION,
        "window": {
            "start": common_dates[0].isoformat(),
            "end": common_dates[-1].isoformat(),
            "common_cohort_days": len(common_dates),
            "d7_mature_cohort_days": sum(1 for day in common_dates if day <= REFERENCE_DATE - timedelta(days=7)),
        },
        "source_details": source_details,
        "maturity": {metric: {"cutoff": (REFERENCE_DATE-timedelta(days=days)).isoformat(), "field": field} for metric, (field, days) in RETENTION.items()},
        "group_summary": summaries,
        "daily_rows": daily_rows,
        "retention_long": retention_long,
        "phase_rows": phase_rows,
        "sensitivity_rows": sensitivity_rows,
        "quality_rows": quality_rows,
        "update_events": update_events,
        "facebook_account_ban": account_ban,
        "history_context": history,
        "limitations": [
            "真实 h5_build/app_version 不在最新 cohort 表中，版本比较只能作为发布期观察。",
            "新增付费率/人数与首充付费率/人数不能相互复算，不能推导免费用户或制作付费漏斗。",
            "当前 cohort 表不含 game_id、首局、加载、设备/网络和订单事实，不能归因至某一轻量化玩法。",
            "PWA 的部分已达到观察天数的 D15/D30 cohort 为空，显示为 N/A·源缺失。",
        ],
    }
    paid_rows = [
        {"group": x["group"], "indicator": "来源新增付费率·cohort日均值", "rate": x["source_new_paid_rate_mean"], "users": x["source_new_paid_users"]}
        for x in summaries if x["group"] != "H5 汇总"
    ] + [
        {"group": x["group"], "indicator": "来源首充付费率·cohort日均值", "rate": x["source_first_charge_rate_mean"], "users": x["source_first_charge_users"]}
        for x in summaries if x["group"] != "H5 汇总"
    ]
    write_sqlite(analysis, paid_rows)
    artifact = build_artifact(analysis)
    ANALYSIS.write_text(json.dumps(analysis, ensure_ascii=False, indent=2))
    QUALITY.write_text(json.dumps({"as_of": REFERENCE_DATE.isoformat(), "quality_rows": quality_rows, "limitations": analysis["limitations"]}, ensure_ascii=False, indent=2))
    ARTIFACT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2))
    SOURCE_REGISTRY.write_text(json.dumps({
        "read_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_observation_date": REFERENCE_DATE.isoformat(),
        "analysis_window": {"start": common_dates[0].isoformat(), "end": common_dates[-1].isoformat(), "cohort_days": len(common_dates)},
        "sources": [
            {
                "role": "主数据源",
                "title": "新包新增用户分析",
                "url": LARK_NEW_USER_URL,
                "wiki_node_revision": SOURCE_REVISION,
                "sheets": [
                    {"sheet": name, "mapping": GROUPS[name]["label"], "sheet_read_revision": source_details[name].get("revision"), "range": source_details[name].get("range")}
                    for name in GROUPS
                ],
                "snapshot_directory": str(RAW.relative_to(ROOT)),
            },
            {
                "role": "发布/干扰事件",
                "title": "更新记录·新包",
                "url": LARK_UPDATE_URL,
                "use": "仅用于发布期、故障、配置与埋点事件标注，不作为因果证据。",
            },
            {
                "role": "运营事实补充",
                "title": "H5 Facebook投放账户状态",
                "source_type": "用户提供",
                "affected_window": "2026-08-15—2026-08-16",
                "fact": "H5 Facebook投放账户被封，导致该渠道新增骤降。",
                "use": "用于解释新增规模与渠道结构异常；不作为轻量化游戏、产品体验或D7留存变化的因果依据。",
            },
            {
                "role": "历史基线",
                "title": "轻量化游戏历史分析",
                "url": HISTORY_URL,
                "use": "仅作为5月历史基线与待验证假设，不与本轮7/14—8/16 cohort汇总。",
            },
            {
                "role": "体验规范",
                "title": "H5/PWA性能规范",
                "url": PERFORMANCE_URL,
                "use": "用于补数与性能埋点需求，不参与本轮留存/付费计算。",
            },
        ],
        "calculation_rules": [
            "留存仅纳入达到观测日的 cohort，并按新增人数加权。",
            "已达到观察天数但来源为空的 PWA D15/D30 标为 N/A·源缺失，不作为未达到观察天数或0值处理。",
            "来源新增付费与首充字段按原定义并列展示；不制作伪漏斗或免费用户反推。",
            "真实 h5_build/app_version 缺失，发布期观察不做因果归因。",
            "8月15–16日Facebook投放账户被封，当前期新增规模和渠道结构比较需单独标注；当前期D7 cohort早于该事件。",
        ],
    }, ensure_ascii=False, indent=2))
    CHART_MAP.write_text(json.dumps([
        {"section": "新增规模与渠道结构", "question": "四渠道新增在34个cohort日内如何变化？", "type": "line", "dataset": "daily_new", "claim": "识别流量结构变化；8月15–16日Facebook投放账户被封导致的骤降已单独注记，不作为轻量化因果证据。"},
        {"section": "已达到观察天数的留存", "question": "H5与PWA各渠道的D1/D3/D7是否不同？", "type": "bar", "dataset": "retention_long", "claim": "仅纳入已达到对应观察天数的cohort并按新增人数加权。"},
        {"section": "发布期观察", "question": "不同发布期D3留存的渠道观察如何？", "type": "bar", "dataset": "phase_metrics", "claim": "仅观察，不做用户级版本因果。"},
        {"section": "来源付费口径", "question": "来源新增付费与首充显示率在各渠道如何分布？", "type": "bar", "dataset": "paid_rates", "claim": "独立来源指标，不形成漏斗。"},
    ], ensure_ascii=False, indent=2))

    render_daily_new_chart(daily_rows)
    render_retention_chart(summaries)
    render_phase_chart(phase_rows)
    render_quality_chart(quality_rows)

    h5 = next(x for x in summaries if x["group"] == "H5 汇总")
    pwa = next(x for x in summaries if x["group"] == "PWA 自然")
    md = f'''# Waje H5/PWA轻量化游戏效果与新用户留存付费分析

数据截至：{REFERENCE_DATE.isoformat()}；新用户 cohort 共同窗口：{common_dates[0].isoformat()} 至 {common_dates[-1].isoformat()}；源修订版：{SOURCE_REVISION}。

## 执行摘要

- H5汇总D7为 **{fmt_rate(h5['d7'])}**，PWA D7为 **{fmt_rate(pwa['d7'])}**；二者渠道结构不同，不能视为运行形态因果差异。
- 本轮可观察 Limbo、Keno、Color Dice、H5 2.1.14 和Opera埋点前后的发布期变化，但没有真实版本、game_id和首局事实，不输出因果结论。
- 付费/首充字段在来源层不对账，免费用户结果暂不支持；不构造新增→付费→首充漏斗。

## 口径

- D1/D3：34个已达到对应观察天数的 cohort；D7：30个已注册满7天的 cohort；D15：22个已注册满15天的 cohort（PWA 20个可用）；D30：7个已注册满30天的 cohort（PWA 6个可用）；D60：N/A。
- 所有新增留存按新增人数加权；已达到观察天数但为空的数据标为 `N/A·源缺失`。
- 终身、首日、TC、TX沿来源定义展示，不命名为LTV，不跨渠道直接汇总。

## Facebook投放账户事件

- 用户补充确认：H5 Facebook投放账户被封，影响2026年8月15日至8月16日的新增投放。
- 封禁前（8/11–8/14）日均新增 **{fmt_count(account_ban['before']['daily_new'])}** 人；影响日降至 **{fmt_count(account_ban['after']['daily_new'])}** 人，降幅 **{fmt_rate(account_ban['daily_new_decline'])}**。按封禁前日均作对照，两日少 **{fmt_count(account_ban['benchmark_new_gap'])}** 名新增。
- 该事件只解释新增规模和渠道结构突变；当前期D7只使用8/11–8/12 cohort，早于影响日，不能把账户封禁写成D7变化原因。

## 渠道结果

| 渠道/运行形态 | 新增 | D1 | D3 | D7 | 来源新增付费人数 | 来源新增付费率日均 | 来源首充人数 |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(f"| {x['group']} | {fmt_num(x['new_users'])} | {fmt_rate(x['d1'])} | {fmt_rate(x['d3'])} | {fmt_rate(x['d7'])} | {fmt_num(x['source_new_paid_users'])} | {fmt_rate(x['source_new_paid_rate_mean'])} | {fmt_num(x['source_first_charge_users'])} |" for x in summaries if x['group'] != 'H5 汇总')}

## 数据质量边界

{chr(10).join(f"- {x['group']}：新增付费率不对账 {x['new_paid_rate_mismatch_days']}/{x['cohort_days']} 天；首充人数大于新增付费人数 {x['first_charge_gt_new_paid_days']}/{x['cohort_days']} 天；D15 {x['D15_observed']}/{x['D15_expected']}、D30 {x['D30_observed']}/{x['D30_expected']}。" for x in quality_rows)}

## 行动建议

1. P0：补齐 `game_id + h5_build + config_version + user_type + session_id`。
2. P0：对Color Dice、Keno、Limbo补齐曝光→点击→加载→可下注→首局完成漏斗。
3. P1：输出免费、来源新增付费、首充、复充的互斥 cohort 事实表。
4. P1：将更新记录自动标注进H5/PWA效果看板，并按已达到观察天数的窗口复盘。
'''
    KNOWLEDGE.write_text(md)
    if args.feishu_xml:
        args.feishu_xml.parent.mkdir(parents=True, exist_ok=True)
        args.feishu_xml.write_text(feishu_xml(analysis))
    if args.feishu_event_table_xml:
        args.feishu_event_table_xml.parent.mkdir(parents=True, exist_ok=True)
        args.feishu_event_table_xml.write_text(feishu_event_table_xml(analysis))
    print(json.dumps({"artifact": str(ARTIFACT), "analysis": str(ANALYSIS), "quality": str(QUALITY), "source_registry": str(SOURCE_REGISTRY), "markdown": str(KNOWLEDGE), "assets": [str(p) for p in sorted(ASSETS.glob("*.png"))]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

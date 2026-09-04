#!/usr/bin/env python3
"""Recalculate H5/PWA retention from the latest Feishu new-user workbook.

Inputs are immutable aggregate-only Sheet snapshots captured from revision 754.
All reader-facing retention labels follow Waje's Dn Day convention:
Dn Day = registration date + (n - 1) natural days.
"""
from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"
AS_OF = date(2026, 8, 30)
SOURCE_REVISION = 754
SOURCE_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"

SOURCES = {
    "H5自然": ROOT / "source_revision754_wajebeth5_2026_09_01.json",
    "H5 Facebook": ROOT / "source_revision754_h5_facebook_2026_09_01.json",
    "H5 Google": ROOT / "source_revision754_h5_google_2026_09_01.json",
    "PWA自然": ROOT / "source_revision754_pwa_2026_09_01.json",
}
GROUPS = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
COLORS = {
    "H5 Facebook": "#4D8EC9",
    "H5 Google": "#3F9EAD",
    "H5自然": "#D89B1B",
    "PWA自然": "#8174C8",
}
PAPER, INK, MUTED, GRID = "#F7FBFD", "#18324B", "#60788E", "#DCE8F0"

# Source labels are mapped to the business convention rather than displayed raw.
METRICS = {
    "D2 Day": {"source": "次留", "first_pay_source": "首充次留", "offset": 1},
    "D3 Day": {"source": "3日留", "first_pay_source": "首充3日留", "offset": 2},
    "D7 Day": {"source": "7日留", "first_pay_source": "首充7日留", "offset": 6},
    "D15 Day": {"source": "15日留", "first_pay_source": "首充15日留", "offset": 14},
    "D30 Day": {"source": "30日留", "first_pay_source": "首充30日留", "offset": 29},
}


def get_font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT, size=size, index=1 if bold else 0)


def parse_date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace(".", "", 1).isdigit()):
        return date(1899, 12, 30) + timedelta(days=int(float(value)))
    text = str(value).strip().replace("/", "-")
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def as_number(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_rows(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sheet = payload["sheets"][0]
    return [dict(zip(sheet["columns"], values)) for values in sheet["data"]]


ROWS = {group: load_rows(path) for group, path in SOURCES.items()}


def aggregate(group: str, start: date, end: date, metric: str, *, first_pay: bool = False) -> dict:
    spec = METRICS[metric]
    rate_col = spec["first_pay_source"] if first_pay else spec["source"]
    weight_col = "首充付费人数" if first_pay else "新增人数"
    population = retained = 0.0
    cohorts = unavailable = 0
    last_available: date | None = None
    for row in ROWS[group]:
        cohort_date = parse_date(row.get("日期"))
        if cohort_date is None or not (start <= cohort_date <= min(end, AS_OF)):
            continue
        weight = as_number(row.get(weight_col))
        rate = as_number(row.get(rate_col))
        if weight is None or weight <= 0:
            continue
        if rate is None:
            unavailable += 1
            continue
        population += weight
        retained += weight * rate
        cohorts += 1
        last_available = max(last_available, cohort_date) if last_available else cohort_date
    return {
        "rate": (retained / population) if population else None,
        "population": int(round(population)),
        "cohorts": cohorts,
        "unavailable_in_source": unavailable,
        "mature_through": last_available.isoformat() if last_available else None,
        "theoretical_maturity_through": min(end, AS_OF - timedelta(days=spec["offset"])).isoformat(),
    }


def retention_matrix(start: date, end: date, *, first_pay: bool = False) -> dict:
    return {
        group: {metric: aggregate(group, start, end, metric, first_pay=first_pay) for metric in METRICS}
        for group in GROUPS
    }


def raw_new_scale(group: str, start: date, end: date) -> dict:
    values = []
    for row in ROWS[group]:
        cohort_date = parse_date(row.get("日期"))
        new_users = as_number(row.get("新增人数"))
        if cohort_date is not None and start <= cohort_date <= end and new_users is not None and new_users >= 0:
            values.append(new_users)
    return {"total": int(round(sum(values))), "days": len(values), "daily_avg": (sum(values) / len(values)) if values else None}


def pre_post() -> list[dict]:
    pre_start, pre_end = date(2026, 6, 16), date(2026, 7, 13)
    post_start, post_end = date(2026, 7, 14), AS_OF
    rows = []
    for group in GROUPS:
        pre_scale, post_scale = raw_new_scale(group, pre_start, pre_end), raw_new_scale(group, post_start, post_end)
        entry = {
            "group": group,
            "pre_daily_new": pre_scale["daily_avg"],
            "post_daily_new": post_scale["daily_avg"],
            "daily_new_change": ((post_scale["daily_avg"] / pre_scale["daily_avg"]) - 1)
            if pre_scale["daily_avg"] and post_scale["daily_avg"] is not None else None,
        }
        for metric in METRICS:
            before = aggregate(group, pre_start, pre_end, metric)
            after = aggregate(group, post_start, post_end, metric)
            entry[metric] = {"pre": before, "post": after, "delta": (after["rate"] - before["rate"]) if before["rate"] is not None and after["rate"] is not None else None}
        rows.append(entry)
    return rows


def all_groups_metric(start: date, end: date, metric: str) -> dict:
    pieces = [aggregate(group, start, end, metric) for group in GROUPS]
    population = sum(piece["population"] for piece in pieces)
    retained = sum((piece["rate"] or 0) * piece["population"] for piece in pieces)
    available_dates = [piece["mature_through"] for piece in pieces if piece["mature_through"]]
    return {
        "rate": (retained / population) if population else None,
        "population": population,
        "cohorts": sum(piece["cohorts"] for piece in pieces),
        "mature_through": min(available_dates) if available_dates else None,
    }


PHASES = [
    ("上线前基线", date(2026, 6, 16), date(2026, 7, 13)),
    ("Limbo上线/恢复", date(2026, 7, 14), date(2026, 7, 22)),
    ("H5 2.1.14 / Keno", date(2026, 7, 23), date(2026, 7, 28)),
    ("Color Dice", date(2026, 7, 29), date(2026, 8, 5)),
    ("Opera埋点期", date(2026, 8, 6), date(2026, 8, 10)),
    ("后续追踪", date(2026, 8, 11), AS_OF),
]


def phase_summary() -> list[dict]:
    result = []
    for label, start, end in PHASES:
        metrics = {metric: all_groups_metric(start, end, metric) for metric in METRICS}
        result.append({
            "phase": label,
            "window": f"{start:%-m/%-d}—{end:%-m/%-d}",
            "new_users": sum(raw_new_scale(group, start, end)["total"] for group in GROUPS),
            "metrics": metrics,
            "by_channel_d3": {group: aggregate(group, start, end, "D3 Day")["rate"] for group in GROUPS},
        })
    return result


def quality_audit() -> dict:
    source_quality = {}
    errors = []
    for group, rows in ROWS.items():
        valid_dates = [parse_date(row.get("日期")) for row in rows]
        valid_dates = [day for day in valid_dates if day]
        duplicate_dates = len(valid_dates) - len(set(valid_dates))
        source_quality[group] = {
            "rows": len(rows),
            "min_date": min(valid_dates).isoformat() if valid_dates else None,
            "max_date": max(valid_dates).isoformat() if valid_dates else None,
            "duplicate_dates": duplicate_dates,
        "target_cutoff_present": AS_OF in valid_dates,
            "required_columns_present": all(column in rows[0] for column in ["日期", "新增人数", "次留", "3日留", "7日留", "15日留", "30日留", "首充付费人数", "首充次留", "首充3日留", "首充7日留", "首充15日留", "首充30日留"]),
        }
        if source_quality[group]["max_date"] != AS_OF.isoformat() or duplicate_dates:
            errors.append(group)
    return {"source_revision": SOURCE_REVISION, "as_of": AS_OF.isoformat(), "channels": source_quality, "status": "passed" if not errors else "blocked", "error_channels": errors}


def draw_canvas(title: str, subtitle: str):
    image = Image.new("RGB", (1600, 900), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((70, 48), title, fill=INK, font=get_font(40, True))
    draw.text((70, 108), subtitle, fill=MUTED, font=get_font(20))
    return image, draw


def draw_legend(draw, y: int):
    x = 150
    for group in GROUPS:
        draw.rounded_rectangle((x, y, x + 20, y + 20), 4, fill=COLORS[group])
        draw.text((x + 30, y - 3), group, fill=INK, font=get_font(18))
        x += 290


def draw_grid(draw, left: int, right: int, top: int, bottom: int, maximum: float, ticks: int = 4):
    for index in range(ticks + 1):
        value = maximum * index / ticks
        y = bottom - int((bottom - top) * value / maximum)
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((left - 62, y - 10), f"{value:.0%}", fill=MUTED, font=get_font(17))


def render_retention(matrix: dict):
    image, draw = draw_canvas(
        "四渠道注册批次留存（截至8月30日）",
        "来源：飞书《新包新增用户分析》修订754｜每个观察点只纳入已达到对应Dn Day的注册批次；按新增人数加权",
    )
    labels = list(METRICS)
    left, right, top, bottom = 150, 1510, 190, 655
    draw_grid(draw, left, right, top, bottom, 0.60)
    gap = (right - left) / len(labels)
    for i, label in enumerate(labels):
        center = left + gap * (i + 0.5)
        draw.text((center - 38, bottom + 24), label, fill=INK, font=get_font(17, True))
        for j, group in enumerate(GROUPS):
            rate = matrix[group][label]["rate"] or 0
            x = center - 78 + 43 * j
            height = int((bottom - top) * rate / 0.60)
            draw.rounded_rectangle((x, bottom - height, x + 31, bottom), 6, fill=COLORS[group])
            draw.text((x - 2, bottom - height - 25), f"{rate:.1%}", fill=INK, font=get_font(14))
    draw_legend(draw, 770)
    draw.text((70, 842), "Dn Day：D1 Day为注册当天；D2 Day为次日；D3 Day为第3个自然日。", fill=MUTED, font=get_font(18))
    image.save(CHARTS / "01_起源四渠道DnDay留存对比.png", "PNG", optimize=True)


def render_pre_post(rows: list[dict]):
    metrics = ["D2 Day", "D3 Day", "D7 Day", "D15 Day"]
    image, draw = draw_canvas(
        "轻量化上线后累计留存变化",
        "来源：飞书《新包新增用户分析》修订754｜上线前6月16日—7月13日；上线后7月14日—8月30日；各指标仅纳入已达到观察天数的批次",
    )
    left, right, top, bottom = 150, 1510, 190, 650
    min_value, max_value = -0.08, 0.10
    for pct in [-0.08, -0.04, 0, 0.04, 0.08]:
        y = bottom - int((pct - min_value) / (max_value - min_value) * (bottom - top))
        draw.line((left, y, right, y), fill=INK if pct == 0 else GRID, width=3 if pct == 0 else 2)
        draw.text((55, y - 10), f"{pct:+.0%}", fill=MUTED, font=get_font(16))
    gap = (right - left) / len(metrics)
    for i, metric in enumerate(metrics):
        center = left + gap * (i + 0.5)
        draw.text((center - 37, bottom + 27), metric, fill=INK, font=get_font(18, True))
        for j, group in enumerate(GROUPS):
            delta = next(row for row in rows if row["group"] == group)[metric]["delta"] or 0
            x = center - 100 + 56 * j
            zero = bottom - int((0 - min_value) / (max_value - min_value) * (bottom - top))
            y = bottom - int((delta - min_value) / (max_value - min_value) * (bottom - top))
            draw.rounded_rectangle((x, min(y, zero), x + 44, max(y, zero)), 7, fill=COLORS[group])
            draw.text((x - 4, y - 25 if delta >= 0 else y + 5), f"{delta:+.1%}", fill=INK, font=get_font(14))
    draw_legend(draw, 770)
    image.save(CHARTS / "02_起源上线前后DnDay留存变化.png", "PNG", optimize=True)


def render_matched_curve():
    start, end = date(2026, 6, 16), AS_OF - timedelta(days=METRICS["D30 Day"]["offset"])
    matrix = retention_matrix(start, end)
    labels = list(METRICS)
    image, draw = draw_canvas(
        "四渠道同批注册用户留存曲线（Dn Day）",
        f"来源：飞书《新包新增用户分析》修订754｜同一批注册用户：{start:%Y年%m月%d日}—{end:%m月%d日}；避免不同观察期样本错位",
    )
    left, right, top, bottom = 150, 1510, 190, 650
    draw_grid(draw, left, right, top, bottom, 0.45)
    for group in GROUPS:
        points = []
        for i, metric in enumerate(labels):
            x = left + int((right - left) * i / (len(labels) - 1))
            rate = matrix[group][metric]["rate"] or 0
            y = bottom - int((bottom - top) * rate / 0.45)
            points.append((x, y))
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=COLORS[group])
        draw.line(points, fill=COLORS[group], width=4)
    for i, metric in enumerate(labels):
        x = left + int((right - left) * i / (len(labels) - 1))
        draw.text((x - 34, bottom + 26), metric, fill=INK, font=get_font(17, True))
    draw_legend(draw, 770)
    image.save(CHARTS / "03_起源同批注册DnDay留存曲线.png", "PNG", optimize=True)
    return matrix


def render_decay(matched: dict):
    pairs = [("D2 Day", "D3 Day"), ("D3 Day", "D7 Day"), ("D7 Day", "D15 Day"), ("D15 Day", "D30 Day")]
    image, draw = draw_canvas(
        "四渠道分阶段留存衰减（Dn Day）",
        "来源：飞书《新包新增用户分析》修订754｜衰减率=1－后一观察点留存÷前一观察点留存；使用与D30 Day一致的同一批注册用户",
    )
    left, right, top, bottom = 150, 1510, 190, 650
    draw_grid(draw, left, right, top, bottom, 0.65)
    gap = (right - left) / len(pairs)
    result = []
    for i, (before, after) in enumerate(pairs):
        center = left + gap * (i + 0.5)
        label = f"{before}→{after}"
        draw.text((center - 68, bottom + 25), label, fill=INK, font=get_font(16, True))
        stage = {"stage": label}
        for j, group in enumerate(GROUPS):
            base, next_value = matched[group][before]["rate"], matched[group][after]["rate"]
            decay = 1 - next_value / base if base and next_value is not None else None
            stage[group] = decay
            value = decay or 0
            x = center - 78 + 43 * j
            height = int((bottom - top) * value / 0.65)
            draw.rounded_rectangle((x, bottom - height, x + 31, bottom), 6, fill=COLORS[group])
            draw.text((x - 4, bottom - height - 25), f"{value:.1%}", fill=INK, font=get_font(14))
        result.append(stage)
    draw_legend(draw, 770)
    image.save(CHARTS / "04_起源DnDay留存衰减.png", "PNG", optimize=True)
    return result


def render_phase(phases: list[dict]):
    image, draw = draw_canvas(
        "轻量化更新节点：四渠道 D3 Day 留存变化",
        "来源：飞书《新包新增用户分析》修订754 + 更新记录｜D3 Day为第3个自然日；阶段存在版本、KYC、投放、埋点等同期干扰",
    )
    left, right, top, bottom = 150, 1510, 190, 650
    draw_grid(draw, left, right, top, bottom, 0.40)
    for group in GROUPS:
        points = []
        for i, phase in enumerate(phases):
            x = left + int((right - left) * i / (len(phases) - 1))
            value = phase["by_channel_d3"][group] or 0
            y = bottom - int((bottom - top) * value / 0.40)
            points.append((x, y))
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=COLORS[group])
        draw.line(points, fill=COLORS[group], width=4)
    for i, phase in enumerate(phases):
        x = left + int((right - left) * i / (len(phases) - 1))
        draw.text((x - 42, bottom + 25), phase["phase"], fill=INK, font=get_font(15, True))
    draw_legend(draw, 770)
    image.save(CHARTS / "05_起源轻量化节点D3Day留存.png", "PNG", optimize=True)


def render_first_pay(matrix: dict):
    labels = ["D2 Day", "D3 Day", "D7 Day", "D15 Day", "D30 Day"]
    image, draw = draw_canvas(
        "新增首充用户留存（截至8月30日）",
        "来源：飞书《新包新增用户分析》修订754｜按首充用户数加权；每个观察点只纳入已达到对应Dn Day的首充批次",
    )
    left, right, top, bottom = 150, 1510, 190, 655
    draw_grid(draw, left, right, top, bottom, 0.60)
    gap = (right - left) / len(labels)
    for i, label in enumerate(labels):
        center = left + gap * (i + 0.5)
        draw.text((center - 38, bottom + 24), label, fill=INK, font=get_font(17, True))
        for j, group in enumerate(GROUPS):
            rate = matrix[group][label]["rate"] or 0
            x = center - 78 + 43 * j
            height = int((bottom - top) * rate / 0.60)
            draw.rounded_rectangle((x, bottom - height, x + 31, bottom), 6, fill=COLORS[group])
            draw.text((x - 2, bottom - height - 25), f"{rate:.1%}", fill=INK, font=get_font(14))
    draw_legend(draw, 770)
    image.save(CHARTS / "06_新增首充用户DnDay留存_截止8月30日.png", "PNG", optimize=True)


def summary_rows(matrix: dict, *, first_pay: bool = False) -> list[dict]:
    output = []
    for group in GROUPS:
        row = {"channel": group}
        for metric in METRICS:
            point = matrix[group][metric]
            row[f"{metric}_rate"] = point["rate"]
            row[f"{metric}_population"] = point["population"]
            row[f"{metric}_cohorts"] = point["cohorts"]
        row["population_type"] = "新增首充用户" if first_pay else "新增注册用户"
        output.append(row)
    return output


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    audit = quality_audit()
    if audit["status"] != "passed":
        raise SystemExit(json.dumps(audit, ensure_ascii=False, indent=2))
    all_register = retention_matrix(date(2026, 6, 16), AS_OF)
    post_register = retention_matrix(date(2026, 7, 14), AS_OF)
    all_first_pay = retention_matrix(date(2026, 6, 16), AS_OF, first_pay=True)
    post_first_pay = retention_matrix(date(2026, 7, 14), AS_OF, first_pay=True)
    comparison = pre_post()
    phases = phase_summary()
    matched = render_matched_curve()
    decay = render_decay(matched)
    render_retention(all_register)
    render_pre_post(comparison)
    render_phase(phases)
    render_first_pay(post_first_pay)
    summary = {
        "status": "ok",
        "source": {"title": "新包新增用户分析", "url": SOURCE_URL, "revision": SOURCE_REVISION, "as_of": AS_OF.isoformat()},
        "quality": audit,
        "all_register": all_register,
        "post_register": post_register,
        "all_first_pay": all_first_pay,
        "post_first_pay": post_first_pay,
        "pre_post": comparison,
        "phase_summary": phases,
        "matched_curve": matched,
        "decay": decay,
    }
    (ROOT / "origin_retention_refresh_2026_08_30.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "origin_retention_quality_2026_08_30.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(ROOT / "origin_register_retention_2026_08_30.csv", summary_rows(all_register))
    write_csv(ROOT / "origin_firstpay_retention_2026_08_30.csv", summary_rows(all_first_pay, first_pay=True))
    write_csv(ROOT / "origin_post_firstpay_retention_2026_08_30.csv", summary_rows(post_first_pay, first_pay=True))
    write_csv(ROOT / "origin_prepost_retention_2026_08_30.csv", [
        {
            "channel": row["group"],
            "daily_new_change": row["daily_new_change"],
            **{f"{metric}_delta": row[metric]["delta"] for metric in METRICS},
        }
        for row in comparison
    ])
    print(json.dumps({"status": "ok", "as_of": AS_OF.isoformat(), "source_revision": SOURCE_REVISION}, ensure_ascii=False))


if __name__ == "__main__":
    main()

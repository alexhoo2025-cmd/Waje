#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
AS_OF = date(2026, 8, 29)

SOURCES = {
    "H5自然": ROOT / "source_v732_wajebeth5.json",
    "H5 Facebook": ROOT / "source_v732_h5_facebook.json",
    "H5 Google": ROOT / "source_v732_h5_google.json",
    "PWA自然": ROOT / "source_v732_pwa.json",
}
MATURITY = {"D1": 1, "D3": 3, "D7": 7, "D15": 15, "D30": 30}
COLUMNS = {"D1": "次留", "D3": "3日留", "D7": "7日留", "D15": "15日留", "D30": "30日留"}


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT, size=size, index=1 if bold else 0)


def parse_date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        return date(1899, 12, 30) + timedelta(days=int(float(value)))
    text = str(value).strip().replace("/", "-")
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def load_rows(path: Path) -> list[dict]:
    payload = json.loads(path.read_text("utf-8"))["sheets"][0]
    columns = payload["columns"]
    data = payload["data"]
    # New source extracts use --no-header because some pages have duplicate labels.
    # For these files the first physical row is the true business header.
    if columns and columns[0] == "col1" and data:
        columns = [str(value or "").strip() for value in data[0]]
        data = data[1:]
    return [dict(zip(columns, row)) for row in data]


rows_by_channel = {channel: load_rows(path) for channel, path in SOURCES.items()}


def weighted(channel: str, metric: str, start: date, end: date) -> dict:
    cutoff = min(end, AS_OF - timedelta(days=MATURITY[metric]))
    total_new = 0.0
    retained = 0.0
    cohorts = 0
    missing = 0
    for row in rows_by_channel[channel]:
        d = parse_date(row.get("日期"))
        if d is None or d < start or d > cutoff:
            continue
        new = row.get("新增人数")
        rate = row.get(COLUMNS[metric])
        if new in (None, "") or float(new) <= 0:
            continue
        if rate in (None, ""):
            missing += 1
            continue
        total_new += float(new)
        retained += float(new) * float(rate)
        cohorts += 1
    return {
        "value": retained / total_new if total_new else None,
        "new_users": int(total_new),
        "cohorts": cohorts,
        "missing": missing,
        "mature_through": cutoff.isoformat(),
    }


def period_summary(start: date, end: date) -> dict:
    return {
        channel: {metric: weighted(channel, metric, start, end) for metric in MATURITY}
        for channel in SOURCES
    }


pre = period_summary(date(2026, 6, 16), date(2026, 7, 13))
post_28 = period_summary(date(2026, 7, 14), date(2026, 8, 10))
post_latest = period_summary(date(2026, 7, 14), AS_OF)

stages = [
    ("上线前基线", date(2026, 6, 16), date(2026, 7, 13)),
    ("Limbo上线/恢复", date(2026, 7, 14), date(2026, 7, 22)),
    ("H5 2.1.14 / Keno", date(2026, 7, 23), date(2026, 7, 28)),
    ("Color Dice", date(2026, 7, 29), date(2026, 8, 5)),
    ("Opera埋点期", date(2026, 8, 6), date(2026, 8, 10)),
    ("当前期", date(2026, 8, 11), date(2026, 8, 16)),
]


def all_channel_metric(metric: str, start: date, end: date) -> dict:
    parts = [weighted(channel, metric, start, end) for channel in SOURCES]
    total = sum(p["new_users"] for p in parts)
    value = sum((p["value"] or 0) * p["new_users"] for p in parts) / total if total else None
    return {
        "value": value,
        "new_users": total,
        "cohorts": sum(p["cohorts"] for p in parts),
        "missing": sum(p["missing"] for p in parts),
        "mature_through": min(p["mature_through"] for p in parts),
    }


stage_rows = []
for label, start, end in stages:
    metrics = {metric: all_channel_metric(metric, start, end) for metric in ("D1", "D3", "D7", "D15")}
    stage_rows.append({"stage": label, "start": start.isoformat(), "end": end.isoformat(), "metrics": metrics})

top20 = [
    {"game_id": "6001", "game": "Whot", "new_visitors": 1109, "visitors": 2366, "page_views": 38447},
    {"game_id": "9008", "game": "Limbo", "new_visitors": 647, "visitors": 1353, "page_views": 3341},
    {"game_id": "9001", "game": "CoinFlip", "new_visitors": 425, "visitors": 1037, "page_views": 3732},
    {"game_id": "9010", "game": "Keno", "new_visitors": 270, "visitors": 709, "page_views": 1492},
    {"game_id": "9003", "game": "ColorDice", "new_visitors": 413, "visitors": 849, "page_views": 1658},
    {"game_id": "9011", "game": "Hilo", "new_visitors": 184, "visitors": 564, "page_views": 832},
    {"game_id": "9016", "game": "Plinko", "new_visitors": 365, "visitors": 1092, "page_views": 2287},
    {"game_id": "9013", "game": "Tower", "new_visitors": 122, "visitors": 501, "page_views": 843},
    {"game_id": "2003", "game": "Bottle spin", "new_visitors": 709, "visitors": 1585, "page_views": 5446},
]
for row in top20:
    row["page_views_per_new_visitor"] = row["page_views"] / row["new_visitors"]

top_game_returns = [
    {"game_id": "6001", "game": "Whot", "category": "非轻量化", "d1_num": 286, "d1_den": 935, "d3_num": 74, "d3_den": 529},
    {"game_id": "9008", "game": "Limbo", "category": "轻量化", "d1_num": 158, "d1_den": 544, "d3_num": 44, "d3_den": 316},
    {"game_id": "9001", "game": "CoinFlip", "category": "轻量化", "d1_num": 111, "d1_den": 351, "d3_num": 36, "d3_den": 204},
    {"game_id": "9010", "game": "Keno", "category": "轻量化", "d1_num": 84, "d1_den": 231, "d3_num": 19, "d3_den": 140},
    {"game_id": "9003", "game": "ColorDice", "category": "轻量化", "d1_num": 82, "d1_den": 325, "d3_num": 16, "d3_den": 102},
    {"game_id": "9011", "game": "Hilo", "category": "轻量化", "d1_num": 52, "d1_den": 151, "d3_num": 13, "d3_den": 78},
    {"game_id": "9016", "game": "Plinko", "category": "轻量化", "d1_num": 97, "d1_den": 310, "d3_num": 34, "d3_den": 196},
    {"game_id": "9013", "game": "Tower", "category": "轻量化", "d1_num": 32, "d1_den": 84, "d3_num": 0, "d3_den": 0},
    {"game_id": "2003", "game": "Bottle spin", "category": "非轻量化", "d1_num": 189, "d1_den": 601, "d3_num": 39, "d3_den": 353},
]
for row in top_game_returns:
    row["d1_rate"] = row["d1_num"] / row["d1_den"] if row["d1_den"] else None
    row["d3_rate"] = row["d3_num"] / row["d3_den"] if row["d3_den"] else None

payload = {
    "generated_at": "2026-08-31",
    "source_status": {
        "ga4_latest_complete_day": "2026-08-27",
        "origin_sheet_latest_day": "2026-08-29",
        "requested_yesterday": "2026-08-30",
        "missing_days": ["2026-08-30"],
        "status": "current_through_2026_08_29",
    },
    "pre_28d": pre,
    "post_28d": post_28,
    "post_latest_available": post_latest,
    "stage_rows": stage_rows,
    "top9_game_pages": top20,
    "top_games_d1_d3": top_game_returns,
}
(ROOT / "latest_extension_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

with (ROOT / "top9_game_pages.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(top20[0].keys()))
    writer.writeheader()
    writer.writerows(top20)
with (ROOT / "top_games_d1_d3.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(top_game_returns[0].keys()))
    writer.writeheader()
    writer.writerows(top_game_returns)

# Top9 comparison chart.
image = Image.new("RGB", (1600, 980), "#F7FBFD")
draw = ImageDraw.Draw(image)
draw.text((65, 45), "产品Top Games九款：新增访客触达", fill="#18324B", font=font(38, True))
draw.text((65, 105), "GA4 2026-08-21至08-27；按产品首页顺序展示，数值为进入游戏页的新访客", fill="#60788E", font=font(22))
max_value = max(row["new_visitors"] for row in top20)
left, right = 400, 1480
top, gap = 180, 78
for i, row in enumerate(top20):
    y = top + i * gap
    width = int((right - left) * row["new_visitors"] / max_value)
    color = "#8174C8" if row["game_id"] in {"9001", "9003", "9008", "9010", "9011", "9016", "9013"} else "#4D8EC9"
    draw.rounded_rectangle((left, y, left + width, y + 38), 8, fill=color)
    draw.text((65, y + 2), f"{row['game']}  ({row['game_id']})", fill="#18324B", font=font(22, row["game_id"] == "9008"))
    draw.text((left + width + 12, y + 3), f"{row['new_visitors']:,}人", fill="#18324B", font=font(21, True))
    draw.text((left, y + 42), f"页面浏览 {row['page_views']:,}｜人均 {row['page_views_per_new_visitor']:.2f}", fill="#60788E", font=font(17))
image.save(CHARTS / "06_GA4产品TopGames九款.png", "PNG", optimize=True)

# Top Games short-term return chart.
image = Image.new("RGB", (1600, 900), "#F7FBFD")
draw = ImageDraw.Draw(image)
draw.text((65, 45), "产品Top Games九款：D1/D3应用回访", fill="#18324B", font=font(38, True))
draw.text((65, 105), "GA4 2026-08-21至08-27；D1截至8/26，D3截至8/24；紫色标签=轻量化7款", fill="#60788E", font=font(22))
left, bottom, top = 100, 760, 200
plot_width = 1400
draw.line((left, bottom, left + plot_width, bottom), fill="#DCE8F0", width=2)
for tick in range(0, 51, 10):
    y = bottom - int((bottom - top) * tick / 50)
    draw.line((left, y, left + plot_width, y), fill="#DCE8F0", width=1)
    draw.text((35, y - 12), f"{tick}%", fill="#60788E", font=font(18))
gap = plot_width / len(top_game_returns)
bar_w = 28
for i, row in enumerate(top_game_returns):
    x = left + int(i * gap + 34)
    d1h = int((bottom - top) * (row["d1_rate"] or 0) / 0.5)
    draw.rounded_rectangle((x, bottom - d1h, x + bar_w, bottom), 5, fill="#4D8EC9")
    if row["d3_rate"] is not None:
        d3h = int((bottom - top) * row["d3_rate"] / 0.5)
        draw.rounded_rectangle((x + 36, bottom - d3h, x + 36 + bar_w, bottom), 5, fill="#55A982")
    label_color = "#8174C8" if row["category"] == "轻量化" else "#18324B"
    draw.text((x - 10, 790), row["game"], fill=label_color, font=font(18, row["category"] == "轻量化"))
    draw.text((x, bottom - d1h - 28), f"{row['d1_rate']:.0%}", fill="#18324B", font=font(15))
    if row["d3_rate"] is not None:
        draw.text((x + 36, bottom - d3h - 28), f"{row['d3_rate']:.0%}", fill="#18324B", font=font(15))
draw.rectangle((1160, 60, 1182, 82), fill="#4D8EC9")
draw.text((1190, 58), "D1", fill="#18324B", font=font(18))
draw.rectangle((1260, 60, 1282, 82), fill="#55A982")
draw.text((1290, 58), "D3", fill="#18324B", font=font(18))
image.save(CHARTS / "07_产品TopGames九款_D1D3回访.png", "PNG", optimize=True)

print(json.dumps({"status": "ok", "top9": len(top20), "stage_rows": len(stage_rows)}, ensure_ascii=False))

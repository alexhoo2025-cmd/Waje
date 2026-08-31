#!/usr/bin/env python3
"""Render the two report-only charts for D15 tracking and GA4 page activity."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "report_data.json").read_text(encoding="utf-8"))
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)

NAVY = "#173A63"
MUTED = "#5D7895"
GRID = "#D8E6F3"
BG = "#FFFFFF"
FB = "#2E7DCC"
GOOGLE = "#47A9B7"
NATURAL = "#D89B1B"
PWA = "#7867C9"
RED = "#D95D5D"
GREEN = "#20906C"
COLORS = {"H5 Facebook": FB, "H5 Google": GOOGLE, "H5自然": NATURAL, "PWA自然": PWA}


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def write(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill: str = NAVY) -> None:
    draw.text(xy, text, font=font(size), fill=fill)


def chart_d15() -> Path:
    image = Image.new("RGB", (1600, 900), BG)
    draw = ImageDraw.Draw(image)
    write(draw, (64, 42), "上线前后四渠道留存变化：补充D15", 34)
    write(draw, (64, 90), "D1/D3/D7使用完整28天窗口；D15仅使用已满15天的注册用户，后窗口截至8月4日。", 19, MUTED)
    left, right, top, bottom = 150, 1510, 175, 700
    min_y, max_y = -0.06, 0.09
    for tick in [-0.06, -0.03, 0, 0.03, 0.06, 0.09]:
        y = bottom - (tick - min_y) / (max_y - min_y) * (bottom - top)
        draw.line((left, y, right, y), fill=GRID, width=2)
        write(draw, (58, int(y - 10)), f"{tick * 100:+.0f}pp", 16, MUTED)
    zero_y = bottom - (0 - min_y) / (max_y - min_y) * (bottom - top)
    draw.line((left, zero_y, right, zero_y), fill=NAVY, width=3)
    metrics = [("D1", "d1_delta"), ("D3", "d3_delta"), ("D7", "d7_delta"), ("D15", "d15_delta")]
    groups = DATA["pre_post"]
    unit = (right - left) / len(metrics)
    bar_width = 44
    for mi, (label, key) in enumerate(metrics):
        center = left + unit * (mi + 0.5)
        write(draw, (int(center - 22), bottom + 22), label, 22)
        for gi, record in enumerate(groups):
            value = record[key]
            x = center - (len(groups) / 2 - 0.5) * (bar_width + 12) + gi * (bar_width + 12)
            y = bottom - (value - min_y) / (max_y - min_y) * (bottom - top)
            color = COLORS[record["group"]]
            draw.rounded_rectangle((int(x), min(y, zero_y), int(x + bar_width), max(y, zero_y)), radius=7, fill=color)
            label_y = int(y - 28) if value >= 0 else int(y + 7)
            write(draw, (int(x - 7), label_y), f"{value * 100:+.1f}", 15)
    legend_y = 770
    lx = 150
    for group in groups:
        draw.rounded_rectangle((lx, legend_y, lx + 20, legend_y + 20), radius=4, fill=COLORS[group["group"]])
        write(draw, (lx + 28, legend_y - 2), group["group"], 17)
        lx += 260
    write(draw, (64, 842), "D15样本：H5自然 28→20批次；Facebook 28→19；Google 28→19；PWA自然 23→17。", 16, MUTED)
    output = OUT / "上线前后D1-D15留存变化.png"
    image.save(output)
    return output


def chart_ga4() -> Path:
    activity = DATA["ga4_activity"]
    games = activity["games"]
    image = Image.new("RGB", (1600, 900), BG)
    draw = ImageDraw.Draw(image)
    write(draw, (64, 42), "GA4轻量化游戏页面活跃快照", 34)
    write(draw, (64, 90), "2026年7月23日—8月19日｜Africa/Lagos｜页面活跃与浏览不等于游戏开始、首局完成或结算。", 19, MUTED)
    panels = [(130, 170, 735, 660), (865, 170, 1470, 660)]
    titles = ["页面活跃用户", "人均页面浏览"]
    values = [[game["activeUsers"] for game in games], [game["views_per_active_user"] for game in games]]
    maxima = [max(values[0]) * 1.25, max(values[1]) * 1.35]
    colors = [FB, NATURAL]
    for pi, ((left, top, right, bottom), title, series, maximum) in enumerate(zip(panels, titles, values, maxima)):
        write(draw, (left, top - 48), title, 24)
        draw.line((left, bottom, right, bottom), fill=GRID, width=3)
        unit = (right - left) / len(games)
        bar_w = 120
        for i, (game, value) in enumerate(zip(games, series)):
            x = left + unit * (i + 0.5) - bar_w / 2
            height = value / maximum * (bottom - top)
            y = bottom - height
            draw.rounded_rectangle((int(x), int(y), int(x + bar_w), bottom), radius=9, fill=colors[i])
            label = f"{int(value):,}" if pi == 0 else f"{value:.2f}"
            write(draw, (int(x + 22), int(y - 35)), label, 20)
            write(draw, (int(x - 12), bottom + 20), game["name"], 18)
            write(draw, (int(x + 8), bottom + 52), game["page_path"], 15, MUTED)
    host = activity["host"]
    note = f"www.wajegame.com：{host['activeUsers']:,} 活跃用户、{host['sessions']:,} 会话、{host['eventCount']:,} 事件。"
    write(draw, (64, 740), note, 22)
    write(draw, (64, 790), "设备结构：移动端为主要访问形态；Android 32,641名活跃用户，iOS 6,084名。", 20, MUTED)
    write(draw, (64, 840), "Keno页面ID尚未确认；本图不用于游戏完成、局数或留存归因。", 17, RED)
    output = OUT / "GA4轻量化游戏页面活跃快照.png"
    image.save(output)
    return output


if __name__ == "__main__":
    print(chart_d15())
    print(chart_ga4())

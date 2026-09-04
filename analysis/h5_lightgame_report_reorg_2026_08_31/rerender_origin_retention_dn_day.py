#!/usr/bin/env python3
"""Render Origin retention charts using the Waje Dn Day display convention."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "h5_pwa_lightgame_effect_v2_2026_08_19" / "analysis.json"
CHARTS = ROOT / "charts"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
PAPER, INK, MUTED, GRID = "#F7FBFD", "#18324B", "#60788E", "#DCE8F0"
COLORS = {"H5 Facebook": "#4D8EC9", "H5 Google": "#3F9EAD", "H5自然": "#D89B1B", "PWA自然": "#8174C8"}
GROUPS = ["H5 Facebook", "H5 Google", "H5自然", "PWA自然"]
DISPLAY = {"D1": "D2 Day", "D3": "D3 Day", "D7": "D7 Day", "D15": "D15 Day", "D30": "D30 Day"}
STAGES = {"D1→D3": "D2 Day→D3 Day", "D3→D7": "D3 Day→D7 Day", "D7→D15": "D7 Day→D15 Day", "D15→D30": "D15 Day→D30 Day"}


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT, size=size, index=1 if bold else 0)


def canvas(title: str, subtitle: str):
    image = Image.new("RGB", (1600, 900), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((70, 48), title, fill=INK, font=font(40, True))
    draw.text((70, 108), subtitle, fill=MUTED, font=font(20))
    return image, draw


def legend(draw: ImageDraw.ImageDraw, y: int) -> None:
    x = 170
    for group in GROUPS:
        draw.rounded_rectangle((x, y, x + 20, y + 20), 4, fill=COLORS[group])
        draw.text((x + 28, y - 2), group, fill=INK, font=font(17))
        x += 260


def grid(draw, left, right, top, bottom, max_value: float):
    for tick in [0, max_value * .25, max_value * .5, max_value * .75, max_value]:
        y = bottom - int((bottom - top) * tick / max_value)
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((left - 58, y - 10), f"{tick:.0%}", fill=MUTED, font=font(17))


def retention(summary):
    image, draw = canvas(
        "四渠道留存对比（Dn Day）",
        "来源：起源 BQ-新增付费用户分析｜2026年6月16日至8月16日｜按新增人数加权；每个观察点仅纳入达到对应统计口径的注册批次",
    )
    labels = [("D2 Day", "d1"), ("D3 Day", "d3"), ("D7 Day", "d7"), ("D15 Day", "d15"), ("D30 Day", "d30")]
    left, right, top, bottom = 150, 1510, 190, 660
    grid(draw, left, right, top, bottom, .60)
    values = {x["group"]: x for x in summary}
    unit = (right - left) / len(labels)
    w = 30
    for i, (label, field) in enumerate(labels):
        center = left + unit * (i + .5)
        draw.text((center - 32, bottom + 24), label, fill=INK, font=font(18, True))
        for j, group in enumerate(GROUPS):
            value = values[group][field]
            x = center - 72 + j * 42
            h = int((bottom - top) * value / .60)
            draw.rounded_rectangle((x, bottom - h, x + w, bottom), 6, fill=COLORS[group])
            draw.text((x - 5, bottom - h - 25), f"{value:.1%}", fill=INK, font=font(14))
    legend(draw, 770)
    draw.text((70, 842), "Dn Day：D1 Day 为注册当天，D2 Day 为次日，D3 Day 为第3个自然日。", fill=MUTED, font=font(18))
    image.save(CHARTS / "01_起源四渠道DnDay留存对比.png", "PNG", optimize=True)


def pre_post(rows):
    image, draw = canvas(
        "轻量化上线前后：D2 Day / D3 Day / D7 Day 留存变化",
        "来源：起源 BQ-新增付费用户分析｜对照窗口：2026年6月16日至7月13日 vs 7月14日至8月10日｜数值为后窗口减前窗口（百分点）",
    )
    metrics = [("D2 Day", "d1_delta"), ("D3 Day", "d3_delta"), ("D7 Day", "d7_delta")]
    left, right, top, bottom = 150, 1510, 195, 650
    min_v, max_v = -.06, .09
    for tick in [-.06, -.03, 0, .03, .06, .09]:
        y = bottom - int((tick - min_v) / (max_v - min_v) * (bottom - top))
        draw.line((left, y, right, y), fill=INK if tick == 0 else GRID, width=3 if tick == 0 else 2)
        draw.text((58, y - 10), f"{tick:+.0%}", fill=MUTED, font=font(16))
    unit = (right - left) / len(metrics)
    w = 44
    by = {x["group"]: x for x in rows}
    for i, (label, field) in enumerate(metrics):
        center = left + unit * (i + .5)
        draw.text((center - 35, bottom + 28), label, fill=INK, font=font(19, True))
        for j, group in enumerate(GROUPS):
            value = by[group][field]
            x = center - 100 + j * 55
            zero = bottom - int((0 - min_v) / (max_v - min_v) * (bottom - top))
            y = bottom - int((value - min_v) / (max_v - min_v) * (bottom - top))
            draw.rounded_rectangle((x, min(y, zero), x + w, max(y, zero)), 7, fill=COLORS[group])
            draw.text((x - 4, y - 25 if value >= 0 else y + 6), f"{value:+.1%}", fill=INK, font=font(14))
    legend(draw, 770)
    image.save(CHARTS / "02_起源上线前后DnDay留存变化.png", "PNG", optimize=True)


def curve(rows):
    image, draw = canvas(
        "四渠道同批注册用户留存曲线（Dn Day）",
        "来源：起源 BQ-新增付费用户分析｜每条曲线仅使用D30 Day前已完整观察的同一批注册用户；按新增人数加权",
    )
    left, right, top, bottom = 150, 1510, 190, 650
    grid(draw, left, right, top, bottom, .40)
    order = ["D1", "D3", "D7", "D15", "D30"]
    grouped = {g: {r["metric"]: r["rate"] for r in rows if r["group"] == g} for g in GROUPS}
    for group in GROUPS:
        points = []
        for i, metric in enumerate(order):
            x = left + int((right - left) * i / (len(order) - 1))
            y = bottom - int((bottom - top) * grouped[group][metric] / .40)
            points.append((x, y))
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=COLORS[group])
        draw.line(points, fill=COLORS[group], width=4)
    for i, metric in enumerate(order):
        x = left + int((right - left) * i / (len(order) - 1))
        draw.text((x - 30, bottom + 25), DISPLAY[metric], fill=INK, font=font(18, True))
    legend(draw, 770)
    image.save(CHARTS / "03_起源同批注册DnDay留存曲线.png", "PNG", optimize=True)


def decay(rows):
    image, draw = canvas(
        "四渠道分阶段留存衰减（Dn Day）",
        "来源：起源 BQ-新增付费用户分析｜衰减率=1－后一观察点留存÷前一观察点留存；每阶段使用同一批注册用户",
    )
    stages = ["D1→D3", "D3→D7", "D7→D15", "D15→D30"]
    left, right, top, bottom = 150, 1510, 190, 650
    grid(draw, left, right, top, bottom, .65)
    by = {(r["group"], r["stage"]): r["decay"] for r in rows}
    unit = (right - left) / len(stages)
    for i, stage in enumerate(stages):
        center = left + unit * (i + .5)
        draw.text((center - 62, bottom + 25), STAGES[stage], fill=INK, font=font(17, True))
        for j, group in enumerate(GROUPS):
            value = by[(group, stage)]
            x = center - 72 + j * 42
            h = int((bottom - top) * value / .65)
            draw.rounded_rectangle((x, bottom - h, x + 30, bottom), 6, fill=COLORS[group])
            draw.text((x - 5, bottom - h - 25), f"{value:.1%}", fill=INK, font=font(14))
    legend(draw, 770)
    image.save(CHARTS / "04_起源DnDay留存衰减.png", "PNG", optimize=True)


def phase(rows):
    image, draw = canvas(
        "轻量化更新节点：四渠道 D3 Day 留存变化",
        "来源：起源 BQ-新增付费用户分析 + 飞书更新记录｜D3 Day 为第3个自然日；节点存在版本、KYC、投放和埋点等同期干扰",
    )
    left, right, top, bottom = 150, 1510, 190, 650
    grid(draw, left, right, top, bottom, .40)
    mapping = {"H5 Facebook": "h5_facebook_d3", "H5 Google": "h5_google_d3", "H5自然": "h5_natural_d3", "PWA自然": "pwa_natural_d3"}
    for group in GROUPS:
        points = []
        for i, row in enumerate(rows):
            x = left + int((right - left) * i / (len(rows) - 1))
            value = row[mapping[group]]
            y = bottom - int((bottom - top) * value / .40)
            points.append((x, y))
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=COLORS[group])
        draw.line(points, fill=COLORS[group], width=4)
    for i, row in enumerate(rows):
        x = left + int((right - left) * i / (len(rows) - 1))
        draw.text((x - 43, bottom + 25), row["phase"], fill=INK, font=font(15, True))
    legend(draw, 770)
    image.save(CHARTS / "05_起源轻量化节点D3Day留存.png", "PNG", optimize=True)


def main() -> None:
    analysis = json.loads(SOURCE.read_text(encoding="utf-8"))
    retention(analysis["channel_summary"])
    pre_post(analysis["lightgame_pre_post"])
    curve(analysis["matched_retention_curve"])
    decay(analysis["matched_retention_decay"])
    phase(analysis["phase_channel_matrix"])


if __name__ == "__main__":
    main()

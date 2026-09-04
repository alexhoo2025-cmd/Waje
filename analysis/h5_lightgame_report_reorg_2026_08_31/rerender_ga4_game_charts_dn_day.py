#!/usr/bin/env python3
"""Render corrected GA4 game charts with canonical GameId and Dn Day labels.

The retained GA4 return query has D0+1 and D0+3 results. Under the Waje
business-day convention these are D2 Day and D4 Day; D3 Day is intentionally
not fabricated here and requires the prepared D0+2 rerun.
"""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
PAPER = "#F7FBFD"
INK = "#18324B"
MUTED = "#60788E"
GRID = "#DCE8F0"
BLUE = "#4D8EC9"
PURPLE = "#8174C8"
GREEN = "#55A982"

TRACKED = ["9008", "9003", "9016", "9010", "9011"]
LIGHTWEIGHT = {"9001", "9003", "9008", "9010", "9011", "9016", "9013"}


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT, size=size, index=1 if bold else 0)


def canvas(title: str, subtitle: str):
    image = Image.new("RGB", (1600, 900), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((70, 48), title, fill=INK, font=font(40, True))
    draw.text((70, 108), subtitle, fill=MUTED, font=font(20))
    return image, draw


def load_page_data():
    with (ROOT / "top9_game_pages.csv").open() as fh:
        rows = {r["game_id"]: r for r in csv.DictReader(fh)}
    with (ROOT / "top_games_d1_d3.csv").open() as fh:
        returns = {r["game_id"]: r for r in csv.DictReader(fh)}
    return rows, returns


def draw_reach(rows: dict[str, dict[str, str]]) -> None:
    selected = [rows[k] for k in TRACKED]
    image, draw = canvas(
        "GA4 首次访问用户的近期五款游戏页面触达",
        "来源：GA4 BigQuery｜2026年8月21日至27日｜新访客=首次访问当天进入该游戏页的去重用户；页面进入不等于开局",
    )
    left, right, top, bottom = 420, 1490, 210, 770
    max_users = max(int(x["new_visitors"]) for x in selected)
    for tick in range(5):
        x = left + int((right - left) * tick / 4)
        draw.line((x, top, x, bottom), fill=GRID, width=2)
        draw.text((x - 20, 795), f"{int(max_users * tick / 4)}", fill=MUTED, font=font(18))
    for i, item in enumerate(selected):
        y = top + i * 105
        label = f"{item['game']} ({item['game_id']})"
        draw.text((70, y + 8), label, fill=INK, font=font(24, True))
        value = int(item["new_visitors"])
        end = left + int((right - left) * value / max_users)
        color = PURPLE if item["game_id"] in LIGHTWEIGHT else BLUE
        draw.rounded_rectangle((left, y, end, y + 38), 8, fill=color)
        draw.text((end + 12, y + 3), f"{value:,} 人", fill=INK, font=font(20, True))
        draw.text((left, y + 48), f"人均页面浏览 {float(item['page_views_per_new_visitor']):.2f}", fill=MUTED, font=font(19))
    draw.text((70, 845), "紫色=轻量化游戏；蓝色=其他 Top Games。数据使用单一 GA4 直接汇总，避免按日近似去重相加。", fill=MUTED, font=font(18))
    image.save(CHARTS / "02_新访客游戏页面触达_DnDay修正.png", "PNG", optimize=True)


def draw_returns(rows: dict[str, dict[str, str]], returns: dict[str, dict[str, str]], ids: list[str], name: str, title: str) -> None:
    image, draw = canvas(
        title,
        "来源：GA4 BigQuery｜D2 Day=首次访问后第1天；D4 Day=旧查询首次访问后第3天；Hilo、Plinko、Tower归入轻量化。",
    )
    draw.text((70, 140), "标准 D3 Day（首次访问后第2天）待重算；D4 Day 不是 D3 Day。", fill=MUTED, font=font(19))
    left, right, top, bottom = 240, 1490, 210, 720
    for tick in range(0, 51, 10):
        y = bottom - int((bottom - top) * tick / 50)
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((165, y - 10), f"{tick}%", fill=MUTED, font=font(18))
    group_w = 138 if len(ids) > 5 else 230
    bar_w = 48 if len(ids) > 5 else 70
    for i, game_id in enumerate(ids):
        item = rows[game_id]
        result = returns[game_id]
        cx = left + 70 + i * group_w
        d2 = int(result["d1_num"]) / int(result["d1_den"])
        d4 = int(result["d3_num"]) / int(result["d3_den"]) if int(result["d3_den"]) else None
        for offset, value, color in [(-30, d2, BLUE), (30, d4, GREEN)]:
            if value is None:
                draw.text((cx + offset - 18, bottom - 32), "N/A", fill=MUTED, font=font(16, True))
                continue
            height = int((bottom - top) * value / 0.5)
            draw.rounded_rectangle((cx + offset - bar_w // 2, bottom - height, cx + offset + bar_w // 2, bottom), 7, fill=color)
            draw.text((cx + offset - 28, bottom - height - 32), f"{value:.1%}", fill=INK, font=font(16, True))
        draw.text((cx - 46, 748), item["game"], fill=INK, font=font(17, True))
        draw.text((cx - 35, 776), item["game_id"], fill=MUTED, font=font(15))
    draw.rectangle((910, 165, 940, 187), fill=BLUE)
    draw.text((950, 159), "D2 Day（次日）", fill=INK, font=font(19))
    draw.rectangle((1165, 165, 1195, 187), fill=GREEN)
    draw.text((1205, 159), "D4 Day（旧 GA4 +3日）", fill=INK, font=font(19))
    draw.text((70, 842), "分母：D2 Day 仅纳入 8/26 及以前首次访问；D4 Day 仅纳入 8/24 及以前首次访问。", fill=MUTED, font=font(18))
    image.save(CHARTS / name, "PNG", optimize=True)


def main() -> None:
    rows, returns = load_page_data()
    draw_reach(rows)
    draw_returns(rows, returns, TRACKED, "03_游戏页新访客D2D4回访.png", "进入游戏页的新访客：D2 Day / D4 Day 应用回访")
    draw_returns(rows, returns, list(rows.keys()), "07_产品TopGames九款_D2D4回访.png", "产品 Top Games 九款：D2 Day / D4 Day 应用回访（轻量化7 / 非轻量化2）")


if __name__ == "__main__":
    main()

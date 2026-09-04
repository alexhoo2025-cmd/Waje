#!/usr/bin/env python3
"""Create aggregate-only daily RTP + all-product TC drilldowns for outlier games."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
ASSETS = ROOT / "assets"
DATA = json.loads((ROOT / "report_data.json").read_text(encoding="utf-8"))
TC = json.loads((ROOT / "metabase_tc_2026_09_01.json").read_text(encoding="utf-8"))
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
INK, MUTED, GRID, PAPER = "#17324D", "#637A90", "#DCE8F0", "#F6FBFE"
GAMES = ["EasyWin", "Blackjack", "Tower", "Plinko"]
REASONS = {
    "EasyWin": "近7日实际/预期偏离 +19.42pp，需核验有效局数与派奖。",
    "Blackjack": "近7日实际/预期偏离 -4.81pp，但下注额较小。",
    "Tower": "新游戏；近7日实际回报比高于全盘约3pp，需追踪玩法参数。",
    "Plinko": "新游戏；近7日实际/预期偏离 +2.57pp，且下注规模较大。",
}


def font(size, bold=False):
    return ImageFont.truetype(FONT, size=size, index=1 if bold else 0)


def pct(value, digits=2):
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def pp(value, digits=2):
    return "N/A" if value is None else f"{value:+.{digits}f}pp"


def amount(value):
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:.2f}亿"
    if abs(value) >= 10_000:
        return f"{value / 10_000:.2f}万"
    return f"{value:,.0f}"


def xml_table(headers, rows):
    head = "".join(f'<th background-color="light-gray"><p>{value}</p></th>' for value in headers)
    body = "".join("<tr>" + "".join(f"<td><p>{value}</p></td>" for value in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def load_builder():
    spec = importlib.util.spec_from_file_location("tracker", ROOT / "build_tracking_report.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main():
    ASSETS.mkdir(exist_ok=True)
    build = load_builder()
    tc_by_date = {row["date"]: row["tc"] for row in TC["daily"]}
    all_records = [build.game_row(row) for row in build.annotated_rows(build.GAME_SOURCE)]
    dates = [row["date"] for row in TC["daily"] if row["date"] >= "2026-08-26"]
    daily_rows = []
    for game in GAMES:
        for day in dates:
            records = [row for row in all_records if row["game"] == game and row["date"].isoformat() == day and row["complete_bet"] > 0]
            metric = build.aggregate(records)
            daily_rows.append({
                "game": game,
                "date": day,
                "all_product_tc": tc_by_date[day],
                "complete_bet": metric["complete_bet"],
                "actual_rtp": metric["actual_rtp"],
                "expected_rtp": metric["expected_rtp"],
                "rtp_gap_pp": metric["rtp_gap_pp"],
                "adjustment_pp": metric["adjustment_pp"],
                "profit_vs_expected": metric["profit_vs_expected"],
            })
    (ROOT / "deviation_game_daily_2026_08_26_09_01.json").write_text(json.dumps(daily_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "deviation_game_daily_2026_08_26_09_01.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(daily_rows[0])); writer.writeheader(); writer.writerows(daily_rows)

    # Four small multiples keep each RTP scale readable; captions give same-day full-product TC.
    path = ASSETS / "05_偏离游戏逐日RTP与全产品TC.png"
    image = Image.new("RGB", (1800, 1300), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((64, 42), "明显偏离游戏：逐日RTP与全产品TC", fill=INK, font=font(38, True))
    draw.text((64, 100), "每图：彩线=游戏完全实际回报比，黄线=完全预期回报比；下方标注同日全产品TC。仅用于定位优先级，不构成故障结论。", fill=MUTED, font=font(18))
    positions = [(70, 190), (930, 190), (70, 710), (930, 710)]
    colors = {"EasyWin": "#2D89C8", "Blackjack": "#D95E5E", "Tower": "#7C72C9", "Plinko": "#1FA187"}
    for game, (x0, y0) in zip(GAMES, positions):
        rows = [row for row in daily_rows if row["game"] == game]
        width, height = 720, 340
        left, right, top, bottom = x0 + 85, x0 + width - 20, y0 + 70, y0 + 270
        values = [x["actual_rtp"] for x in rows if x["actual_rtp"] is not None] + [x["expected_rtp"] for x in rows if x["expected_rtp"] is not None]
        low, high = max(0.70, min(values) - 0.02), max(values) + 0.02
        draw.rounded_rectangle((x0, y0, x0 + width, y0 + height), radius=14, outline=GRID, width=2, fill="#FBFDFF")
        draw.text((x0 + 20, y0 + 18), game, fill=colors[game], font=font(25, True))
        draw.text((x0 + 135, y0 + 22), REASONS[game], fill=MUTED, font=font(14))
        for tick in range(4):
            val = low + (high-low)*tick/3
            y = bottom - int((bottom-top)*(val-low)/(high-low))
            draw.line((left, y, right, y), fill=GRID, width=1)
            draw.text((x0+20, y-9), f"{val:.0%}", fill=MUTED, font=font(14))
        actual_pts, expected_pts = [], []
        for i, row in enumerate(rows):
            xx = left + int((right-left)*i/max(1, len(rows)-1))
            if row["actual_rtp"] is not None:
                actual_pts.append((xx, bottom-int((bottom-top)*(row["actual_rtp"]-low)/(high-low))))
            if row["expected_rtp"] is not None:
                expected_pts.append((xx, bottom-int((bottom-top)*(row["expected_rtp"]-low)/(high-low))))
            draw.text((xx-18, bottom+10), row["date"][5:].replace("-", "/"), fill=MUTED, font=font(12))
            draw.text((xx-20, bottom+30), f"TC{row['all_product_tc']:.0%}", fill=MUTED, font=font(11))
        if len(expected_pts) > 1:
            draw.line(expected_pts, fill="#D89B1B", width=3)
        if len(actual_pts) > 1:
            draw.line(actual_pts, fill=colors[game], width=4)
            for x, y in actual_pts:
                draw.ellipse((x-4, y-4, x+4, y+4), fill=colors[game])
    image.save(path, "PNG", optimize=True)

    summary = []
    overall = DATA["overall_7d"]["actual_rtp"]
    by_game = {row["game"]: row for row in DATA["all_games_7d"]}
    for game in GAMES:
        row = by_game[game]
        summary.append({
            "game": game,
            "reason": REASONS[game],
            "complete_bet": row["complete_bet"],
            "actual_rtp": row["actual_rtp"],
            "expected_rtp": row["expected_rtp"],
            "rtp_gap_pp": row["rtp_gap_pp"],
            "vs_all_product_pp": (row["actual_rtp"] - overall) * 100,
        })
    (ROOT / "deviation_game_summary_2026_08_26_09_01.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_rows = [[
        row["game"], row["reason"], amount(row["complete_bet"]), pct(row["actual_rtp"]),
        pct(row["expected_rtp"]), pp(row["rtp_gap_pp"]), pp(row["vs_all_product_pp"])
    ] for row in summary]
    detail_rows = [[
        row["date"], row["game"], pct(row["all_product_tc"]), amount(row["complete_bet"]),
        pct(row["actual_rtp"]), pct(row["expected_rtp"]), pp(row["rtp_gap_pp"])
    ] for row in daily_rows]
    xml = f"""<h1>明显偏离游戏：逐日下钻</h1><p>入选条件：近7日实际/预期偏离绝对值达到3pp，或新游戏实际回报比高于全盘约2pp。下表与图中的“全产品TC”是同日全站指标，<b>不是该游戏自身的TC</b>。</p>{xml_table(['游戏','入选原因','近7日完全下注额','实际回报比','预期回报比','实际-预期','较全盘RTP'], summary_rows)}<callout emoji="🔎" background-color="light-red" border-color="red"><p><b>优先定位：</b>EasyWin在8月31日的完全实际回报比为<b>204.70%</b>，完全下注额<b>64.48万</b>，同日全产品TC为<b>79.57%</b>。该单日高回报不等同于全站TC异常，但应优先核验有效局数、最终派奖、取消/退款和配置版本。</p></callout><img path="@./analysis/tc_game_rtp_tracking_2026_09_02/assets/05_偏离游戏逐日RTP与全产品TC.png" caption="明显偏离游戏：逐日RTP与全产品TC"/>{xml_table(['日期','游戏','同日全产品TC','完全下注额','实际回报比','预期回报比','RTP差异'], detail_rows)}"""
    (ROOT / "feishu_drilldown_insert.xml").write_text(xml, encoding="utf-8")
    print(json.dumps({"status": "ok", "games": GAMES, "chart": str(path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

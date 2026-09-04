#!/usr/bin/env python3
"""Render one evidence sheet per RTP deviation game; EasyWin uses a 30-day window."""
from __future__ import annotations

import csv
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
ASSETS = ROOT / "assets"
DATA = json.loads((ROOT / "report_data.json").read_text(encoding="utf-8"))
TC = json.loads((ROOT / "metabase_tc_2026_09_01.json").read_text(encoding="utf-8"))
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
INK, MUTED, GRID, PAPER = "#17324D", "#637A90", "#DCE8F0", "#F6FBFE"
AS_OF = date(2026, 9, 1)
WINDOWS = {
    "EasyWin": date(2026, 8, 3),
    "Blackjack": date(2026, 8, 26),
    "Tower": date(2026, 8, 26),
    "Plinko": date(2026, 8, 26),
}
COLORS = {"EasyWin": "#2D89C8", "Blackjack": "#D95E5E", "Tower": "#7C72C9", "Plinko": "#1FA187"}
REASONS = {
    "EasyWin": "彩票玩法；近7日实际/预期偏离 +19.42pp。",
    "Blackjack": "近7日实际/预期偏离 -4.81pp，但下注额较小。",
    "Tower": "新游戏；近7日实际回报比高于全盘约3pp。",
    "Plinko": "新游戏；近7日实际/预期偏离 +2.57pp，且下注规模较大。",
}


def font(size, bold=False):
    return ImageFont.truetype(FONT, size=size, index=1 if bold else 0)


def pct(value, digits=2):
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def pp(value, digits=2):
    return "N/A" if value is None else f"{value:+.{digits}f}pp"


def amount(value):
    if value is None:
        return "N/A"
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


def days(start):
    cursor = start
    while cursor <= AS_OF:
        yield cursor
        cursor += timedelta(days=1)


def draw_sheet(game, rows, period):
    width = 2400 if game == "EasyWin" else 1650
    path = ASSETS / f"06_{game}_逐日RTP观察.png"
    image = Image.new("RGB", (width, 860), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((60, 40), f"{game}｜逐日RTP观察", fill=COLORS[game], font=font(38, True))
    subtitle = f"{rows[0]['date'][5:]}—{rows[-1]['date'][5:]}；加权平均实际RTP {pct(period['actual_rtp'])}；预期基线 {pct(period['expected_rtp'])}；{REASONS[game]}"
    draw.text((60, 100), subtitle, fill=MUTED, font=font(18))
    left, right, top, bottom = 150, width - 80, 180, 620
    values = [r["actual_rtp"] for r in rows if r["actual_rtp"] is not None] + [period["expected_rtp"]]
    low = max(0.60, min(values) - 0.03)
    high = max(values) + 0.04
    for i in range(5):
        value = low + (high-low)*i/4
        y = bottom - int((bottom-top)*(value-low)/(high-low))
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((60, y-10), f"{value:.0%}", fill=MUTED, font=font(16))
    baseline_y = bottom - int((bottom-top)*(period["expected_rtp"]-low)/(high-low))
    draw.line((left, baseline_y, right, baseline_y), fill="#D89B1B", width=3)
    draw.text((right-270, baseline_y-30), f"预期基线 {pct(period['expected_rtp'])}", fill="#87620A", font=font(18, True))
    points = []
    for i, row in enumerate(rows):
        x = left + int((right-left)*i/max(1,len(rows)-1))
        y = bottom - int((bottom-top)*(row["actual_rtp"]-low)/(high-low))
        points.append((x,y))
        show_date = game != "EasyWin" or i % 2 == 0 or i == len(rows)-1
        if show_date:
            draw.text((x-22, bottom+18), row["date"][5:].replace("-", "/"), fill=MUTED, font=font(13))
        # Every node is numerically labeled; alternate labels to keep adjacent values legible.
        dy = -36 if i % 2 == 0 else 12
        draw.text((x-22, y+dy), f"{row['actual_rtp']*100:.1f}%", fill=COLORS[game], font=font(13, True))
        if row["all_product_tc"] is not None and show_date:
            draw.text((x-20, bottom+42), f"全站TC {row['all_product_tc']:.0%}", fill=MUTED, font=font(11))
    draw.line(points, fill=COLORS[game], width=4)
    for x,y in points:
        draw.ellipse((x-5,y-5,x+5,y+5), fill=COLORS[game])
    draw.text((150, 735), f"最高日：{max(rows,key=lambda r:r['actual_rtp'])['date']} {pct(max(r['actual_rtp'] for r in rows))}；最低日：{min(rows,key=lambda r:r['actual_rtp'])['date']} {pct(min(r['actual_rtp'] for r in rows))}。", fill=INK, font=font(20, True))
    draw.text((150, 780), "日期下方的全站TC仅用于观察是否同日变化；不表示该游戏导致全站TC变化。", fill=MUTED, font=font(16))
    image.save(path, "PNG", optimize=True)
    return path


def main():
    ASSETS.mkdir(exist_ok=True)
    build = load_builder()
    tc_by_date = {row["date"]: row["tc"] for row in TC["daily"]}
    all_records = [build.game_row(row) for row in build.annotated_rows(build.GAME_SOURCE)]
    all_games = {row["game"]: row for row in DATA["all_games_7d"]}
    summaries, sheets = [], {}
    for game, start in WINDOWS.items():
        rows = []
        for day in days(start):
            records = [r for r in all_records if r["game"] == game and r["date"] == day and r["complete_bet"] > 0]
            metric = build.aggregate(records)
            if metric["complete_bet"] <= 0:
                continue
            rows.append({"date": day.isoformat(), "game": game, "all_product_tc": tc_by_date.get(day.isoformat()), **metric})
        period = build.aggregate([r for r in all_records if r["game"] == game and start <= r["date"] <= AS_OF and r["complete_bet"] > 0])
        chart = draw_sheet(game, rows, period)
        sheets[game] = {"start": start.isoformat(), "rows": rows, "period": period, "chart": str(chart.relative_to(PROJECT))}
        seven = all_games[game]
        summaries.append({
            "game": game, "reason": REASONS[game], "window": f"{start.isoformat()}—{AS_OF.isoformat()}",
            "period_actual_rtp": period["actual_rtp"], "period_expected_rtp": period["expected_rtp"],
            "period_gap_pp": period["rtp_gap_pp"], "period_bet": period["complete_bet"],
            "seven_day_actual_rtp": seven["actual_rtp"], "seven_day_expected_rtp": seven["expected_rtp"],
            "seven_day_gap_pp": seven["rtp_gap_pp"], "seven_day_bet": seven["complete_bet"],
        })
    (ROOT / "deviation_game_sheets_2026_09_01.json").write_text(json.dumps({"sheets": sheets, "summary": summaries}, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "deviation_game_sheets_2026_09_01.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["date", "game", "all_product_tc", "complete_bet", "actual_rtp", "expected_rtp", "rtp_gap_pp", "adjustment_pp", "profit_vs_expected"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for sheet in sheets.values(): writer.writerows([{k: row.get(k) for k in fields} for row in sheet["rows"]])

    xml_parts = ["<h1>明显偏离游戏：逐日下钻</h1>", "<p>每款游戏单独展示。节点标注为实际RTP；黄色线为该统计窗口的加权预期RTP基线。日期下方的全站TC仅做同日对照，不代表游戏自身TC或因果关系。</p>"]
    for game in WINDOWS:
        item = sheets[game]
        rows = item["rows"]
        period = item["period"]
        table_rows = [[r["date"], pct(r["all_product_tc"]), amount(r["complete_bet"]), pct(r["actual_rtp"]), pct(r["expected_rtp"]), pp(r["rtp_gap_pp"])] for r in rows]
        window_label = "30日" if game == "EasyWin" else "近7日"
        xml_parts.append(f"<h2>{game}｜{window_label}独立观察</h2><p><b>加权平均实际RTP：</b>{pct(period['actual_rtp'])}；<b>预期基线：</b>{pct(period['expected_rtp'])}；<b>平均偏离：</b>{pp(period['rtp_gap_pp'])}；<b>完全下注额：</b>{amount(period['complete_bet'])}。{REASONS[game]}</p>")
        if game == "EasyWin":
            xml_parts.append("<callout emoji=\"🔎\" background-color=\"light-red\" border-color=\"red\"><p><b>优先核验：</b>8月31日实际RTP 204.70%，完全下注64.48万，较预期+107.74pp；同日全产品TC 79.57%。先核验最终派奖、有效局数、取消/退款与配置版本，再判断是否存在异常。</p></callout>")
        xml_parts.append(f"<img path=\"@./analysis/tc_game_rtp_tracking_2026_09_02/assets/06_{game}_逐日RTP观察.png\" caption=\"{game}逐日RTP：节点数值与预期基线\"/>")
        xml_parts.append(xml_table(["日期", "同日全产品TC", "完全下注额", "实际RTP", "预期RTP", "RTP差异"], table_rows))
    (ROOT / "feishu_drilldown_game_sheets.xml").write_text("".join(xml_parts), encoding="utf-8")
    print(json.dumps({"status": "ok", "games": list(WINDOWS), "easywin_days": len(sheets['EasyWin']['rows'])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

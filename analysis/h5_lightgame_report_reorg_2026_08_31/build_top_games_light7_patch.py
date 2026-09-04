#!/usr/bin/env python3
"""Build corrected Top Games 7-lightweight/2-other Feishu table and local note."""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LIGHTWEIGHT = {"9001", "9003", "9008", "9010", "9011", "9016", "9013"}


def pct(num: str, den: str) -> str:
    return "N/A" if not int(den) else f"{int(num) / int(den):.1%}（n={int(den)}）"


def main():
    with (ROOT / "top_games_d1_d3.csv").open(encoding="utf-8") as handle:
        raw = list(csv.DictReader(handle))
    with (ROOT / "top9_game_pages.csv").open(encoding="utf-8") as handle:
        page_rows = {row["game_id"]: row for row in csv.DictReader(handle)}
    by_id = {row["game_id"]: row for row in raw}
    order = ["6001", "9008", "9001", "9010", "9003", "9011", "9016", "9013", "2003"]
    rows = []
    for game_id in order:
        row = by_id[game_id]
        category = "轻量化" if game_id in LIGHTWEIGHT else "非轻量化"
        color = ' background-color="light-purple"' if category == "轻量化" else ""
        status = "未达到D4 Day统计口径" if not int(row["d3_den"]) else ("小样本" if int(row["d3_den"]) < 100 else "可观察")
        rows.append(
            f'<tr><td{color}><p>{category}</p></td><td><p>{row["game"]} / {game_id}</p></td>'
            f'<td><p>{int(page_rows[game_id]["new_visitors"]):,}</p></td><td><p>{pct(row["d1_num"], row["d1_den"])}</p></td>'
            f'<td><p>{pct(row["d3_num"], row["d3_den"])}</p></td><td><p>{status}</p></td></tr>'
        )
    xml = """<table><thead><tr><th background-color="light-gray"><p>分组</p></th><th background-color="light-gray"><p>游戏 / ID</p></th><th background-color="light-gray"><p>新访客</p></th><th background-color="light-gray"><p>D2 Day应用回访</p></th><th background-color="light-gray"><p>D4 Day应用回访（旧GA4+3日）</p></th><th background-color="light-gray"><p>观察状态</p></th></tr></thead><tbody>""" + "".join(rows) + "</tbody></table>"
    (ROOT / "top_games_light7_table.xml").write_text(xml, encoding="utf-8")
    (ROOT / "top_games_light7_grouping.md").write_text(
        "# Top Games 分类更正\n\n"
        "轻量化7款：CoinFlip、Limbo、Keno、ColorDice、Hilo、Plinko、Tower。\n\n"
        "非轻量化2款：Whot、Bottle spin。\n\n"
        "GA4 2026-08-21—27 的原始页面触达、D2 Day、D4 Day 数值不变；本次仅修正产品分类、表格着色、图例与分析表述。\n",
        encoding="utf-8",
    )
    print({"status": "ok", "lightweight": 7, "non_lightweight": 2})


if __name__ == "__main__":
    main()

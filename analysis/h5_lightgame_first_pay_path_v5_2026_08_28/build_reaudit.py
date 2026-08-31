#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
BLUE = "#4D8EC9"
GREEN = "#55A982"
YELLOW = "#E7B94C"
RED = "#D66B67"
INK = "#18324B"
MUTED = "#5F758A"
GRID = "#DCE8F0"
PAPER = "#F7FBFD"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size=size, index=1 if bold else 0)


def canvas(title: str, subtitle: str, width: int = 1600, height: int = 900):
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((70, 48), title, fill=INK, font=font(40, True))
    draw.text((70, 108), subtitle, fill=MUTED, font=font(22))
    return image, draw


master = pd.read_csv(RESULTS / "audit_07_first_pay_game_master.csv")
funnel = pd.read_csv(RESULTS / "audit_08_new_paid_free_funnel.csv")

master["played_by_pay_day_rate"] = master.played_by_first_pay_day / master.first_pay_users
master["first_game_d1_d7_rate"] = master.first_game_d1_d7 / master.first_pay_users
master["no_first_game_by_d7_rate"] = master.no_first_game_by_d7 / master.first_pay_users

funnel["first_game_d0_rate"] = funnel.first_game_d0_users / funnel.new_users
funnel["first_game_d7_rate"] = funnel.first_game_d7_users / funnel.new_users
funnel["no_first_game_by_d7_rate"] = funnel.no_first_game_by_d7 / funnel.new_users


def summarize_overall(frame: pd.DataFrame, period: str, group_col: str | None = None):
    part = frame[frame.period == period]
    if group_col is None:
        groups = [("全部H5/PWA", part)]
    else:
        groups = list(part.groupby(group_col, sort=False))
    rows = []
    for group, data in groups:
        n = int(data.iloc[:, data.columns.get_loc("first_pay_users")].sum()) if "first_pay_users" in data else int(data.new_users.sum())
        if "first_pay_users" in data:
            d0 = int(data.played_by_first_pay_day.sum())
            d7 = d0 + int(data.first_game_d1_d7.sum())
            no_d7 = int(data.no_first_game_by_d7.sum())
        else:
            d0 = int(data.first_game_d0_users.sum())
            d7 = int(data.first_game_d7_users.sum())
            no_d7 = int(data.no_first_game_by_d7.sum())
        rows.append({
            "period": period,
            "group": group,
            "users": n,
            "game_d0_users": d0,
            "game_d0_rate": d0 / n,
            "game_d7_users": d7,
            "game_d7_rate": d7 / n,
            "no_game_d7_users": no_d7,
            "no_game_d7_rate": no_d7 / n,
        })
    return rows


master_overall = summarize_overall(master, "pre") + summarize_overall(master, "post")
funnel_overall = []
for period in ["pre", "post"]:
    for user_group, part in funnel[funnel.period == period].groupby("user_group", sort=False):
        n = int(part.new_users.sum())
        d0 = int(part.first_game_d0_users.sum())
        d7 = int(part.first_game_d7_users.sum())
        no_d7 = int(part.no_first_game_by_d7.sum())
        funnel_overall.append({
            "period": period,
            "user_group": user_group,
            "new_users": n,
            "first_game_d0_users": d0,
            "first_game_d0_rate": d0 / n,
            "first_game_d7_users": d7,
            "first_game_d7_rate": d7 / n,
            "no_first_game_by_d7": no_d7,
            "no_first_game_by_d7_rate": no_d7 / n,
        })

master.to_csv(RESULTS / "reaudit_first_pay_game_by_segment.csv", index=False)
funnel.to_csv(RESULTS / "reaudit_new_paid_free_by_segment.csv", index=False)
(RESULTS / "reaudit_summary.json").write_text(json.dumps({
    "status": "reaudited_provisional",
    "controlling_game_participation_source": "origin_hfyl.user_xlid.first_game_date/last_game_date",
    "invalidated_source": "origin_hfyl.view_metaevent_gamestart for complete gameplay coverage",
    "master_overall": master_overall,
    "new_paid_free_overall": funnel_overall,
    "segment_rows": master.to_dict("records"),
    "funnel_segment_rows": funnel.to_dict("records"),
    "metabase_cross_check": {
        "status": "passed_coverage_only",
        "source": "external production Metabase stat_game_bet_gain",
        "evidence": "light-game IDs 9008, 9003, 9010, 9011 and 9016 have user and round aggregates; update_at is not a first-game timestamp",
    },
    "limitations": [
        "first_game_date is day-grain, so same-day pay-versus-game ordering cannot be determined",
        "PWA package mapping has much lower coverage than the existing workbook and remains provisional",
        "exact first-game time, game ID, rounds and bet amount require a certified event-level aggregate view",
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")


# Chart 10: first-pay users without a recorded first game by D7.
segments = ["H5自然", "H5 Facebook", "H5 Google", "PWA自然_映射待核验"]
pre = master[master.period == "pre"].set_index("segment")
post = master[master.period == "post"].set_index("segment")
image, draw = canvas(
    "首充用户：首充后7天仍无游戏记录",
    "完整用户主表口径；原71.9%为不完整GAMESTART视图的漏记，已撤回",
)
left, right, top, bottom = 390, 1490, 205, 760
max_value = 12.0
for tick in range(0, 13, 2):
    x = left + int((right - left) * tick / max_value)
    draw.line((x, top, x, bottom), fill=GRID, width=2)
    draw.text((x - 16, 790), f"{tick}%", fill=MUTED, font=font(18))
for idx, segment in enumerate(segments):
    y = top + idx * 132
    label = segment.replace("_映射待核验", "（映射待核验）")
    draw.text((65, y + 32), label, fill=INK, font=font(24, True))
    for offset, period, color in [(0, "pre", BLUE), (48, "post", GREEN)]:
        table = pre if period == "pre" else post
        value = float(table.loc[segment, "no_first_game_by_d7_rate"] * 100)
        end = left + int((right - left) * value / max_value)
        draw.rounded_rectangle((left, y + offset, end, y + offset + 34), radius=7, fill=color)
        draw.text((end + 10, y + offset + 2), f"{value:.1f}%", fill=INK, font=font(19, True))
draw.rectangle((1160, 112, 1190, 134), fill=BLUE)
draw.text((1200, 106), "上线前", fill=INK, font=font(20))
draw.rectangle((1320, 112, 1350, 134), fill=GREEN)
draw.text((1360, 106), "上线后", fill=INK, font=font(20))
image.save(CHARTS / "10_首充用户7天无游戏记录复核.png", optimize=True)


# Chart 11: post-launch same-day paid versus unpaid new users.
post_funnel = funnel[funnel.period == "post"].copy()
image, draw = canvas(
    "上线后新增用户：当日首充与当日未付费的游戏参与",
    "D0=注册当日首次游戏；D7=注册后7天内首次游戏；用户主表日粒度",
)
left, right, top, bottom = 390, 1490, 205, 760
max_value = 100.0
for tick in range(0, 101, 20):
    x = left + int((right - left) * tick / max_value)
    draw.line((x, top, x, bottom), fill=GRID, width=2)
    draw.text((x - 20, 790), f"{tick}%", fill=MUTED, font=font(18))
plot_segments = ["H5自然", "H5 Facebook", "H5 Google", "H5其他"]
for idx, segment in enumerate(plot_segments):
    y = top + idx * 132
    draw.text((65, y + 32), segment, fill=INK, font=font(24, True))
    for offset, group, color in [(0, "当日新增首充", GREEN), (48, "当日新增未付费", YELLOW)]:
        row = post_funnel[(post_funnel.segment == segment) & (post_funnel.user_group == group)].iloc[0]
        value = float(row.first_game_d7_rate * 100)
        end = left + int((right - left) * value / max_value)
        draw.rounded_rectangle((left, y + offset, end, y + offset + 34), radius=7, fill=color)
        draw.text((end + 10, y + offset + 2), f"{value:.1f}%", fill=INK, font=font(19, True))
draw.rectangle((1080, 112, 1110, 134), fill=GREEN)
draw.text((1120, 106), "当日新增首充", fill=INK, font=font(20))
draw.rectangle((1320, 112, 1350, 134), fill=YELLOW)
draw.text((1360, 106), "当日新增未付费", fill=INK, font=font(20))
image.save(CHARTS / "11_新增首充与新增未付费7天游戏参与.png", optimize=True)

print(json.dumps({"status": "ok", "charts": 2, "summary": "results/reaudit_summary.json"}, ensure_ascii=False))

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
BLUE, GREEN, YELLOW, PURPLE = "#4D8EC9", "#55A982", "#E7B94C", "#8174C8"
INK, GRID, PAPER = "#18324B", "#DCE8F0", "#F7FBFD"


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype(FONT_PATH, size=size, index=1 if bold else 0)
    except OSError:
        return ImageFont.truetype(FONT_PATH, size=size, index=0)


def canvas(title: str, subtitle: str, width=1600, height=900):
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((70, 48), title, fill=INK, font=font(40, True))
    draw.text((70, 108), subtitle, fill="#5F758A", font=font(22))
    return image, draw


pre = pd.read_csv(RESULTS / "02_bq_replay_pre.csv")
post = pd.concat([
    pd.read_csv(RESULTS / "02_bq_replay_post_a.csv"),
    pd.read_csv(RESULTS / "02_bq_replay_post_b.csv"),
], ignore_index=True)

post_combined = (
    post.groupby(["path_group", "day_since_first_pay"], as_index=False)
    .agg(first_pay_users=("first_pay_users", "sum"), replay_users=("replay_users", "sum"))
)
post_combined["replay_rate"] = post_combined.replay_users / post_combined.first_pay_users
post_combined.insert(0, "period", "post")

pre_combined = pre[["path_group", "day_since_first_pay", "first_pay_users", "replay_users", "replay_rate"]].copy()
pre_combined.insert(0, "period", "pre")
combined = pd.concat([pre_combined, post_combined], ignore_index=True)
combined["previous_replay_rate"] = combined.sort_values("day_since_first_pay").groupby(["period", "path_group"])["replay_rate"].shift(1)
combined["day_decay"] = 1 - combined.replay_rate / combined.previous_replay_rate
combined.to_csv(RESULTS / "02_replay_combined.csv", index=False)

overall = (
    combined.groupby(["period", "day_since_first_pay"], as_index=False)
    .agg(first_pay_users=("first_pay_users", "sum"), replay_users=("replay_users", "sum"))
)
overall["replay_rate"] = overall.replay_users / overall.first_pay_users
overall["previous_replay_rate"] = overall.groupby("period")["replay_rate"].shift(1)
overall["day_decay"] = 1 - overall.replay_rate / overall.previous_replay_rate
overall.to_csv(RESULTS / "02_replay_overall.csv", index=False)

key_days = [0, 1, 3, 7, 15]
key = overall[overall.day_since_first_pay.isin(key_days)].pivot(index="day_since_first_pay", columns="period", values="replay_rate")
key["change_pp"] = (key["post"] - key["pre"]) * 100

summary_path = RESULTS / "provisional_summary.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary["replay_overall"] = [
    {
        "day": int(day),
        "pre": float(row["pre"]),
        "post": float(row["post"]),
        "change_pp": float(row["change_pp"]),
    }
    for day, row in key.iterrows()
]
summary["limits"] = [item for item in summary["limits"] if not item.startswith("D0-D15 replay")]
summary["limits"].append("D0-D15 replay is now computed; general login retention and repeat-pay remain pending.")
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


# Overall replay line chart
image, draw = canvas(
    "首充用户T0—D15游戏复玩率",
    "分母为已完成观察的首充用户；上线后两段按人数合并，不平均比例",
)
left, right, top, bottom = 150, 1510, 190, 760
max_y = max(overall.replay_rate.max() * 100, 10)
max_y = ((int(max_y) // 10) + 1) * 10
for tick in range(0, max_y + 1, 10):
    y = bottom - int((bottom - top) * tick / max_y)
    draw.line((left, y, right, y), fill=GRID, width=2)
    draw.text((70, y - 12), f"{tick}%", fill="#71869A", font=font(18))
for period, color, label in [("pre", BLUE, "上线前"), ("post", GREEN, "上线后")]:
    part = overall[overall.period == period].sort_values("day_since_first_pay")
    points = []
    for _, row in part.iterrows():
        x = left + int((right - left) * int(row.day_since_first_pay) / 15)
        y = bottom - int((bottom - top) * float(row.replay_rate) * 100 / max_y)
        points.append((x, y))
    draw.line(points, fill=color, width=5)
    for x, y in points:
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
    draw.rectangle((1160 if period == "pre" else 1320, 108, 1190 if period == "pre" else 1350, 130), fill=color)
    draw.text((1200 if period == "pre" else 1360, 102), label, fill=INK, font=font(20))
for day in key_days:
    x = left + int((right - left) * day / 15)
    draw.text((x - 18, 790), f"D{day}", fill=INK, font=font(20, True))
draw.text((left, 835), "注：D0为首充当日；该指标为GAMESTART复玩，不等同登录留存。", fill="#5F758A", font=font(19))
image.save(CHARTS / "04_T0-D15游戏复玩率.png", format="PNG", optimize=True)


# Key-day delta chart
image, draw = canvas(
    "上线前后关键日复玩率变化",
    "柱值为上线后减上线前，单位：百分点；正值表示上线后更高",
)
left, right, center_y = 170, 1510, 500
max_abs = max(abs(key.change_pp).max(), 1)
draw.line((left, center_y, right, center_y), fill=INK, width=3)
bar_width = 130
for idx, day in enumerate(key_days):
    value = float(key.loc[day, "change_pp"])
    x = 250 + idx * 260
    h = int(260 * abs(value) / max_abs)
    color = GREEN if value >= 0 else PURPLE
    if value >= 0:
        box = (x, center_y - h, x + bar_width, center_y)
        label_y = center_y - h - 42
    else:
        box = (x, center_y, x + bar_width, center_y + h)
        label_y = center_y + h + 8
    draw.rounded_rectangle(box, radius=10, fill=color)
    draw.text((x + 12, label_y), f"{value:+.2f}pp", fill=INK, font=font(21, True))
    draw.text((x + 40, 790), f"D{day}", fill=INK, font=font(24, True))
draw.text((left, 835), "注意：路径自选择与事件覆盖仍会影响差异，不能写成轻量化的因果效应。", fill="#5F758A", font=font(19))
image.save(CHARTS / "05_关键日复玩率变化.png", format="PNG", optimize=True)

print(json.dumps(summary["replay_overall"], ensure_ascii=False, indent=2))


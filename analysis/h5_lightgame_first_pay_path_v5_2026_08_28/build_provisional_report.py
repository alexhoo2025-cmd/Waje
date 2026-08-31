#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)

BLUE = "#4D8EC9"
GREEN = "#55A982"
YELLOW = "#E7B94C"
RED = "#D66B67"
PURPLE = "#8174C8"
GRID = "#DCE8F0"
INK = "#18324B"
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    index = 1 if bold else 0
    try:
        return ImageFont.truetype(FONT_PATH, size=size, index=index)
    except OSError:
        return ImageFont.truetype(FONT_PATH, size=size, index=0)


def canvas(title: str, subtitle: str, width: int = 1600, height: int = 900):
    image = Image.new("RGB", (width, height), "#F7FBFD")
    draw = ImageDraw.Draw(image)
    draw.text((70, 48), title, fill=INK, font=font(40, True))
    draw.text((70, 108), subtitle, fill="#5F758A", font=font(22))
    return image, draw


def save(image: Image.Image, name: str) -> None:
    image.save(CHARTS / name, format="PNG", optimize=True)


def pct(x: float) -> float:
    return round(float(x) * 100, 2)


pre = pd.read_csv(RESULTS / "01_bq_first_pay_game_path_pre.csv")
post = pd.read_csv(RESULTS / "01_bq_first_pay_game_path_post.csv")
order_pre = pd.read_csv(RESULTS / "00_bq_origin_order_pre.csv")
order_post = pd.read_csv(RESULTS / "00_bq_origin_order_post.csv")
game_pre = pd.read_csv(RESULTS / "00_bq_origin_game_pre.csv")
game_post_a = pd.read_csv(RESULTS / "00_bq_origin_game_post_1.csv")
game_post_b = pd.read_csv(RESULTS / "00_bq_origin_game_post_2.csv")

order = ["付费前7日已玩", "付费后30分钟内玩", "付费后24小时内玩", "付费后第2至7天玩", "付费后7天未玩"]
pre_map = pre.set_index("path_group")
post_map = post.set_index("path_group")

path_rows = []
for group in order:
    path_rows.append({
        "path_group": group,
        "pre_users": int(pre_map.loc[group, "first_pay_users"]),
        "post_users": int(post_map.loc[group, "first_pay_users"]),
        "pre_share": float(pre_map.loc[group, "user_share"]),
        "post_share": float(post_map.loc[group, "user_share"]),
        "change_pp": (float(post_map.loc[group, "user_share"]) - float(pre_map.loc[group, "user_share"])) * 100,
    })

pre_total = int(pre.first_pay_users.sum())
post_total = int(post.first_pay_users.sum())
pre_post30 = float(pre_map.loc["付费后30分钟内玩", "user_share"])
post_post30 = float(post_map.loc["付费后30分钟内玩", "user_share"])
pre_post24 = pre_post30 + float(pre_map.loc["付费后24小时内玩", "user_share"])
post_post24 = post_post30 + float(post_map.loc["付费后24小时内玩", "user_share"])
pre_post7 = pre_post24 + float(pre_map.loc["付费后第2至7天玩", "user_share"])
post_post7 = post_post24 + float(post_map.loc["付费后第2至7天玩", "user_share"])

fp_pre = order_pre[(order_pre.is_first_buy == True) & (order_pre.is_success == "pay_success")]
fp_post = order_post[(order_post.is_first_buy == True) & (order_post.is_success == "pay_success")]
first_pay_events_pre = int(fp_pre.events.sum())
first_pay_events_post = int(fp_post.events.sum())

game_events_pre = int(game_pre.game_start_events.sum())
game_events_post = int(game_post_a.game_start_events.sum() + game_post_b.game_start_events.sum())

summary = {
    "status": "provisional_partial",
    "primary_scope": {
        "pre": "2026-06-16 to 2026-06-30",
        "post": "2026-07-14 to 2026-07-28",
        "population": "device_type=Others first-pay users; H5/PWA combined proxy",
    },
    "pre_first_pay_users": pre_total,
    "post_first_pay_users": post_total,
    "no_game_7d_pre": float(pre_map.loc["付费后7天未玩", "user_share"]),
    "no_game_7d_post": float(post_map.loc["付费后7天未玩", "user_share"]),
    "no_game_7d_change_pp": (float(post_map.loc["付费后7天未玩", "user_share"]) - float(pre_map.loc["付费后7天未玩", "user_share"])) * 100,
    "postpay_game_30m_pre": pre_post30,
    "postpay_game_30m_post": post_post30,
    "postpay_game_24h_pre": pre_post24,
    "postpay_game_24h_post": post_post24,
    "postpay_game_7d_pre": pre_post7,
    "postpay_game_7d_post": post_post7,
    "first_pay_success_events_pre_28d": first_pay_events_pre,
    "first_pay_success_events_post_28d": first_pay_events_post,
    "game_start_events_pre_28d": game_events_pre,
    "game_start_events_post_28d": game_events_post,
    "path_rows": path_rows,
    "limits": [
        "Path result covers all server GAMESTART, not light games only.",
        "device_type=Others combines standard H5 and PWA and has no channel mapping.",
        "Pre/post path windows are matched 15-day windows because the profile sources have different coverage.",
        "D0-D15 replay, retention and repeat-pay queries are prepared but not executed in this audit after the 25 GiB scan gate.",
    ],
}
(RESULTS / "provisional_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


# Chart 1: path shares
image, draw = canvas(
    "H5/PWA首充用户付费前后游戏路径",
    "等长15天首充批次；设备类型Others作为H5/PWA合并代理；横轴为首充用户占比",
)
left, right, top = 420, 1500, 190
max_value = 80.0
for tick in range(0, 81, 20):
    x = left + int((right - left) * tick / max_value)
    draw.line((x, top, x, 785), fill=GRID, width=2)
    draw.text((x - 16, 800), f"{tick}%", fill="#71869A", font=font(18))
draw.rectangle((1140, 108, 1170, 130), fill=BLUE)
draw.text((1180, 102), "上线前", fill=INK, font=font(20))
draw.rectangle((1290, 108, 1320, 130), fill=GREEN)
draw.text((1330, 102), "上线后", fill=INK, font=font(20))
for idx, label in enumerate(order):
    y = top + idx * 112
    draw.text((70, y + 25), label, fill=INK, font=font(24, True))
    pre_value = pct(pre_map.loc[label, "user_share"])
    post_value = pct(post_map.loc[label, "user_share"])
    pre_end = left + int((right - left) * pre_value / max_value)
    post_end = left + int((right - left) * post_value / max_value)
    draw.rounded_rectangle((left, y + 5, pre_end, y + 42), radius=8, fill=BLUE)
    draw.rounded_rectangle((left, y + 53, post_end, y + 90), radius=8, fill=GREEN)
    draw.text((pre_end + 10, y + 8), f"{pre_value:.1f}%", fill=INK, font=font(19, True))
    draw.text((post_end + 10, y + 56), f"{post_value:.1f}%", fill=INK, font=font(19, True))
save(image, "01_首充用户路径结构.png")


# Chart 2: cumulative post-pay activation
stages = ["30分钟内", "24小时内", "7天内"]
pre_values = [pct(pre_post30), pct(pre_post24), pct(pre_post7)]
post_values = [pct(post_post30), pct(post_post24), pct(post_post7)]
image, draw = canvas(
    "首充后首次GAMESTART累计转化",
    "分母为首充用户；同一用户只计首次首充后的第一条GAMESTART",
)
base_y, chart_top, max_value = 760, 190, 20.0
for tick in range(0, 21, 5):
    y = base_y - int((base_y - chart_top) * tick / max_value)
    draw.line((130, y, 1500, y), fill=GRID, width=2)
    draw.text((60, y - 12), f"{tick}%", fill="#71869A", font=font(18))
for idx, stage in enumerate(stages):
    center = 380 + idx * 430
    for offset, value, color in [(-70, pre_values[idx], BLUE), (20, post_values[idx], GREEN)]:
        h = int((base_y - chart_top) * value / max_value)
        draw.rounded_rectangle((center + offset, base_y - h, center + offset + 65, base_y), radius=8, fill=color)
        draw.text((center + offset - 5, base_y - h - 38), f"{value:.1f}%", fill=INK, font=font(21, True))
    draw.text((center - 55, 790), stage, fill=INK, font=font(24, True))
draw.rectangle((1170, 108, 1200, 130), fill=BLUE)
draw.text((1210, 102), "上线前", fill=INK, font=font(20))
draw.rectangle((1320, 108, 1350, 130), fill=GREEN)
draw.text((1360, 102), "上线后", fill=INK, font=font(20))
save(image, "02_首充后首次开局累计转化.png")


# Chart 3: 28-day scale indexed to pre=100
metrics = ["首充成功事件", "GAMESTART事件"]
post_index = [first_pay_events_post / first_pay_events_pre * 100, game_events_post / game_events_pre * 100]
image, draw = canvas(
    "28天窗口首充与开局事件规模变化",
    "上线前=100；事件规模用于判断总体变化，不等同渠道内用户质量",
)
base_y, chart_top = 750, 190
for tick in range(0, 121, 20):
    y = base_y - int((base_y - chart_top) * tick / 120)
    draw.line((180, y, 1480, y), fill=GRID, width=2)
    draw.text((90, y - 12), str(tick), fill="#71869A", font=font(18))
ref_y = base_y - int((base_y - chart_top) * 100 / 120)
draw.line((180, ref_y, 1480, ref_y), fill=INK, width=3)
for idx, (metric, value, color) in enumerate(zip(metrics, post_index, [YELLOW, PURPLE])):
    x = 470 + idx * 520
    h = int((base_y - chart_top) * value / 120)
    draw.rounded_rectangle((x, base_y - h, x + 180, base_y), radius=12, fill=color)
    draw.text((x + 45, base_y - h - 45), f"{value:.1f}", fill=INK, font=font(25, True))
    draw.text((x - 10, 790), metric, fill=INK, font=font(25, True))
save(image, "03_首充与开局事件规模指数.png")

print(json.dumps(summary, ensure_ascii=False, indent=2))

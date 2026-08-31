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


pre = pd.concat([
    pd.read_csv(RESULTS / "03_bq_repeat_pre_a.csv"),
    pd.read_csv(RESULTS / "03_bq_repeat_pre_b.csv"),
], ignore_index=True)
post = pd.concat([
    pd.read_csv(RESULTS / "03_bq_repeat_post_a1.csv"),
    pd.read_csv(RESULTS / "03_bq_repeat_post_a2.csv"),
    pd.read_csv(RESULTS / "03_bq_repeat_post_b1.csv"),
    pd.read_csv(RESULTS / "03_bq_repeat_post_b2.csv"),
], ignore_index=True)

sum_cols = ["first_pay_users", "repeat_pay_users_d1", "repeat_pay_users_d3", "repeat_pay_users_d7", "repeat_orders_7d"]


def combine(frame: pd.DataFrame, period: str) -> pd.DataFrame:
    out = frame.groupby("path_group", as_index=False)[sum_cols].sum()
    for day in (1, 3, 7):
        out[f"repeat_pay_rate_d{day}"] = out[f"repeat_pay_users_d{day}"] / out["first_pay_users"]
    out.insert(0, "period", period)
    return out


pre_c = combine(pre, "pre")
post_c = combine(post, "post")
combined = pd.concat([pre_c, post_c], ignore_index=True)
combined.to_csv(RESULTS / "03_repeat_pay_combined.csv", index=False)


def overall(frame: pd.DataFrame, period: str) -> dict:
    total = int(frame.first_pay_users.sum())
    return {
        "period": period,
        "first_pay_users": total,
        "repeat_pay_rate_d1": float(frame.repeat_pay_users_d1.sum() / total),
        "repeat_pay_rate_d3": float(frame.repeat_pay_users_d3.sum() / total),
        "repeat_pay_rate_d7": float(frame.repeat_pay_users_d7.sum() / total),
        "repeat_orders_7d": int(frame.repeat_orders_7d.sum()),
    }


d15_pre = pd.read_csv(RESULTS / "05_bq_repeat_d15_pre.csv").iloc[0]
d15_post = pd.read_csv(RESULTS / "05_bq_repeat_d15_post.csv").iloc[0]
overall_rows = []
for row in (d15_pre, d15_post):
    overall_rows.append({
        "period": str(row["period"]),
        "first_pay_users": int(row["first_pay_users"]),
        "repeat_pay_rate_d1": float(row["repeat_pay_rate_d1"]),
        "repeat_pay_rate_d3": float(row["repeat_pay_rate_d3"]),
        "repeat_pay_rate_d7": float(row["repeat_pay_rate_d7"]),
        "repeat_pay_rate_d15": float(row["repeat_pay_rate_d15"]),
        "repeat_pay_users_d15": int(row["repeat_pay_users_d15"]),
    })
pd.DataFrame(overall_rows).to_csv(RESULTS / "03_repeat_pay_overall.csv", index=False)

summary_path = RESULTS / "provisional_summary.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary["repeat_pay_overall"] = overall_rows
summary["repeat_pay_by_path"] = combined.to_dict("records")
summary["limits"] = [item for item in summary["limits"] if not item.startswith("D0-D15 replay") and "repeat-pay remain pending" not in item]
summary["limits"].append("D1/D3/D7/D15 repeat-pay is computed from one consistent cohort query; path-level repeat-pay remains D1/D3/D7.")
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


order = ["付费前7日已玩", "付费后30分钟内玩", "付费后24小时内玩", "付费后第2至7天玩", "付费后7天未玩"]
pre_map = pre_c.set_index("path_group")
post_map = post_c.set_index("path_group")

# Chart 6: D7 repeat pay by path
image, draw = canvas(
    "不同游戏路径的D7复充率",
    "分母为各路径首充用户；上线前后分段按人数合并，不平均比例",
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
    pre_value = float(pre_map.loc[label, "repeat_pay_rate_d7"]) * 100
    post_value = float(post_map.loc[label, "repeat_pay_rate_d7"]) * 100
    pre_end = left + int((right - left) * pre_value / max_value)
    post_end = left + int((right - left) * post_value / max_value)
    draw.rounded_rectangle((left, y + 5, pre_end, y + 42), radius=8, fill=BLUE)
    draw.rounded_rectangle((left, y + 53, post_end, y + 90), radius=8, fill=GREEN)
    draw.text((pre_end + 10, y + 8), f"{pre_value:.1f}%", fill=INK, font=font(19, True))
    draw.text((post_end + 10, y + 56), f"{post_value:.1f}%", fill=INK, font=font(19, True))
image.save(CHARTS / "06_不同路径D7复充率.png", format="PNG", optimize=True)


# Chart 7: overall repeat pay
pre_o, post_o = overall_rows
days = [1, 3, 7, 15]
pre_values = [pre_o[f"repeat_pay_rate_d{d}"] * 100 for d in days]
post_values = [post_o[f"repeat_pay_rate_d{d}"] * 100 for d in days]
image, draw = canvas(
    "首充用户累计复充率",
    "同一首充批次累计至D1、D3、D7、D15；不包含失败、处理中或首充订单本身",
)
base_y, chart_top, max_value = 760, 190, max(max(post_values), max(pre_values)) * 1.25
max_value = max(max_value, 40)
for tick in range(0, int(max_value) + 1, 10):
    y = base_y - int((base_y - chart_top) * tick / max_value)
    draw.line((130, y, 1500, y), fill=GRID, width=2)
    draw.text((60, y - 12), f"{tick}%", fill="#71869A", font=font(18))
for idx, day in enumerate(days):
    center = 300 + idx * 330
    for offset, value, color in [(-70, pre_values[idx], BLUE), (20, post_values[idx], GREEN)]:
        h = int((base_y - chart_top) * value / max_value)
        draw.rounded_rectangle((center + offset, base_y - h, center + offset + 65, base_y), radius=8, fill=color)
        draw.text((center + offset - 5, base_y - h - 38), f"{value:.1f}%", fill=INK, font=font(21, True))
    draw.text((center - 15, 790), f"D{day}", fill=INK, font=font(24, True))
draw.rectangle((1170, 108, 1200, 130), fill=BLUE)
draw.text((1210, 102), "上线前", fill=INK, font=font(20))
draw.rectangle((1320, 108, 1350, 130), fill=GREEN)
draw.text((1360, 102), "上线后", fill=INK, font=font(20))
image.save(CHARTS / "07_首充用户累计复充率.png", format="PNG", optimize=True)

print(json.dumps({"overall": overall_rows, "by_path": combined.to_dict("records")}, ensure_ascii=False, indent=2))

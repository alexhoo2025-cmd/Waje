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
BLUE, GREEN, YELLOW = "#4D8EC9", "#55A982", "#E7B94C"
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


pre_files = sorted(RESULTS.glob("04_bq_timing_strict7_pre_*.csv"))
post_files = sorted(RESULTS.glob("04_bq_timing_strict7_post_*.csv"))
if len(pre_files) != 2 or len(post_files) != 4:
    raise SystemExit("blocked_missing_strict7_timing_files")

pre = pd.concat([pd.read_csv(p) for p in pre_files], ignore_index=True)
post = pd.concat([pd.read_csv(p) for p in post_files], ignore_index=True)

count_cols = [
    "first_pay_users",
    "repeat_pay_users_d7",
    "repeat_before_first_game_users",
    "repeat_after_first_game_users",
    "repeat_without_post_game_users",
]


def combine(frame: pd.DataFrame, period: str) -> pd.DataFrame:
    out = frame.groupby("path_group", as_index=False)[count_cols].sum()
    out["timing_sum"] = (
        out.repeat_before_first_game_users
        + out.repeat_after_first_game_users
        + out.repeat_without_post_game_users
    )
    out["timing_reconciliation_error"] = out.timing_sum - out.repeat_pay_users_d7
    if not (out.timing_reconciliation_error == 0).all():
        raise SystemExit(f"timing_reconciliation_failed:{period}")
    for col in ["repeat_before_first_game_users", "repeat_after_first_game_users", "repeat_without_post_game_users"]:
        out[col.replace("_users", "_share")] = out[col] / out.repeat_pay_users_d7
    out.insert(0, "period", period)
    return out


pre_c = combine(pre, "pre")
post_c = combine(post, "post")
combined = pd.concat([pre_c, post_c], ignore_index=True)
combined.to_csv(RESULTS / "04_repeat_game_timing_combined.csv", index=False)


def overall(frame: pd.DataFrame, period: str) -> dict:
    repeat_users = int(frame.repeat_pay_users_d7.sum())
    before = int(frame.repeat_before_first_game_users.sum())
    after = int(frame.repeat_after_first_game_users.sum())
    without = int(frame.repeat_without_post_game_users.sum())
    if before + after + without != repeat_users:
        raise SystemExit(f"overall_timing_reconciliation_failed:{period}")
    return {
        "period": period,
        "repeat_pay_users_d7": repeat_users,
        "repeat_before_first_game_users": before,
        "repeat_after_first_game_users": after,
        "repeat_without_post_game_users": without,
        "repeat_before_first_game_share": before / repeat_users,
        "repeat_after_first_game_share": after / repeat_users,
        "repeat_without_post_game_share": without / repeat_users,
    }


overall_rows = [overall(pre_c, "pre"), overall(post_c, "post")]
pd.DataFrame(overall_rows).to_csv(RESULTS / "04_repeat_game_timing_overall.csv", index=False)

summary_path = RESULTS / "provisional_summary.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary["repeat_game_timing_overall"] = overall_rows
summary["repeat_game_timing_by_path"] = combined.to_dict("records")
summary["limits"] = [item for item in summary["limits"] if "direct ordering" not in item]
summary["limits"].append("Strict 7-day repeat-pay versus first GAMESTART ordering is reconciled; light-game-only ordering remains unavailable.")
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


categories = [
    ("repeat_before_first_game_share", "复充早于首次开局", YELLOW),
    ("repeat_after_first_game_share", "复充晚于/等于首次开局", GREEN),
    ("repeat_without_post_game_share", "复充后7天仍未开局", BLUE),
]

# Chart 8: overall timing composition
image, draw = canvas(
    "D7复充用户的复充与首次开局顺序",
    "分母为7天内已复充用户；三类人数之和与D7复充人数完全一致",
)
left, right = 180, 1480
for idx, row in enumerate(overall_rows):
    y = 300 + idx * 230
    draw.text((70, y + 18), "上线前" if row["period"] == "pre" else "上线后", fill=INK, font=font(28, True))
    cursor = left
    for key, label, color in categories:
        share = float(row[key])
        width = int((right - left) * share)
        draw.rectangle((cursor, y, cursor + width, y + 92), fill=color)
        if width > 110:
            draw.text((cursor + 12, y + 28), f"{share*100:.1f}%", fill=INK, font=font(22, True))
        cursor += width
draw.rectangle((250, 730, 280, 752), fill=YELLOW)
draw.text((290, 722), "复充早于首次开局", fill=INK, font=font(20))
draw.rectangle((650, 730, 680, 752), fill=GREEN)
draw.text((690, 722), "复充晚于/等于首次开局", fill=INK, font=font(20))
draw.rectangle((1130, 730, 1160, 752), fill=BLUE)
draw.text((1170, 722), "复充后7天仍未开局", fill=INK, font=font(20))
image.save(CHARTS / "08_D7复充与首次开局顺序.png", format="PNG", optimize=True)


# Chart 9: post timing by path
post_map = post_c.set_index("path_group")
order = ["付费前7日已玩", "付费后30分钟内玩", "付费后24小时内玩", "付费后第2至7天玩", "付费后7天未玩"]
image, draw = canvas(
    "上线后不同路径的复充与开局顺序",
    "分母为各路径D7复充用户；用于识别先复充后游戏结构",
)
left, right, top = 460, 1500, 200
for idx, path in enumerate(order):
    y = top + idx * 112
    draw.text((70, y + 22), path, fill=INK, font=font(23, True))
    cursor = left
    for key, label, color in categories:
        share = float(post_map.loc[path, key])
        width = int((right - left) * share)
        draw.rectangle((cursor, y, cursor + width, y + 70), fill=color)
        if width > 85:
            draw.text((cursor + 8, y + 20), f"{share*100:.0f}%", fill=INK, font=font(18, True))
        cursor += width
draw.rectangle((320, 790, 350, 812), fill=YELLOW)
draw.text((360, 782), "开局前复充", fill=INK, font=font(19))
draw.rectangle((670, 790, 700, 812), fill=GREEN)
draw.text((710, 782), "开局后复充", fill=INK, font=font(19))
draw.rectangle((1010, 790, 1040, 812), fill=BLUE)
draw.text((1050, 782), "复充后仍未开局", fill=INK, font=font(19))
image.save(CHARTS / "09_上线后各路径复充开局顺序.png", format="PNG", optimize=True)

print(json.dumps({"overall": overall_rows, "by_path": combined.to_dict("records")}, ensure_ascii=False, indent=2))


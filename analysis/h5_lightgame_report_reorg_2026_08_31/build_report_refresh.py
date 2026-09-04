#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"
PROJECT = ROOT.parent.parent
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"

BLUE = "#4D8EC9"
GREEN = "#55A982"
YELLOW = "#E7B94C"
RED = "#D66B67"
PURPLE = "#8174C8"
TEAL = "#3F9EAD"
INK = "#18324B"
MUTED = "#60788E"
GRID = "#DCE8F0"
PAPER = "#F7FBFD"

GAME_NAMES = {
    "9003": "Color Dice",
    "9008": "Keno",
    "9010": "Limbo",
    "9011": "Hilo",
    "9016": "Plinko",
}


def load_json(name: str):
    return json.loads((RESULTS / name).read_text("utf-8"))


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype(FONT_PATH, size=size, index=1 if bold else 0)
    except OSError:
        return ImageFont.truetype(FONT_PATH, size=size, index=0)


def canvas(title: str, subtitle: str):
    image = Image.new("RGB", (1600, 900), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((70, 48), title, fill=INK, font=font(40, True))
    draw.text((70, 108), subtitle, fill=MUTED, font=font(22))
    return image, draw


daily = load_json("01_ga4_daily_integrity.json")
event_mix = load_json("02_ga4_event_mix.json")
device_rows = load_json("03_ga4_new_visitor_game_pages.json")
return_rows = load_json("04_ga4_game_page_return.json")
observability = load_json("05_ga4_id_and_observability.json")[0]
new_summary = load_json("06_ga4_new_visitor_summary.json")
game_totals = load_json("07_ga4_game_page_totals.json")
reach_rows = load_json("08_ga4_new_visitor_lightgame_reach.json")

ga4_total_events = sum(int(r["event_rows"]) for r in daily)
ga4_users = max(int(r["users"]) for r in daily)
ga4_first_visitors = next(int(r["users"]) for r in event_mix if r["event_name"] == "first_visit")
user_id_event_coverage = int(observability["events_with_user_id"]) / int(observability["total_events"])

game_agg = defaultdict(lambda: {
    "new_visitors": 0,
    "all_visitors": 0,
    "page_views": 0,
    "d1_den": 0,
    "d1_num": 0,
    "d3_den": 0,
    "d3_num": 0,
})
for row in game_totals:
    item = game_agg[row["game_id"]]
    item["new_visitors"] += int(row["new_visitors"])
    item["all_visitors"] += int(row["all_visitors"])
    item["page_views"] += int(row["page_views"])
for row in return_rows:
    item = game_agg[row["game_id"]]
    entry_date = row["entry_date"]
    users = int(row["new_game_users"])
    if entry_date <= "2026-08-26":
        item["d1_den"] += users
        item["d1_num"] += int(row["return_d1_users"])
    if entry_date <= "2026-08-24":
        item["d3_den"] += users
        item["d3_num"] += int(row["return_d3_users"])

game_summary = []
for game_id, item in sorted(game_agg.items()):
    item = dict(item)
    item["game_id"] = game_id
    item["game"] = GAME_NAMES[game_id]
    item["page_views_per_new_visitor"] = item["page_views"] / item["new_visitors"]
    item["d1_return_rate"] = item["d1_num"] / item["d1_den"] if item["d1_den"] else None
    item["d3_return_rate"] = item["d3_num"] / item["d3_den"] if item["d3_den"] else None
    item["d7_return_rate"] = None
    game_summary.append(item)

source_rollup = defaultdict(lambda: {"new": 0, "light": 0, "d1_den": 0, "d1_num": 0, "d3_den": 0, "d3_num": 0})
for row in reach_rows:
    item = source_rollup[row["source_group"]]
    item["new"] += int(row["new_visitors"])
    item["light"] += int(row["lightgame_page_users"])
for row in new_summary:
    item = source_rollup[row["source_group"]]
    cohort = row["first_visit_date"]
    users = int(row["new_visitors"])
    if cohort <= "2026-08-26":
        item["d1_den"] += users
        item["d1_num"] += int(row["return_d1_users"])
    if cohort <= "2026-08-24":
        item["d3_den"] += users
        item["d3_num"] += int(row["return_d3_users"])
source_summary = []
for source, item in sorted(source_rollup.items()):
    source_summary.append({
        "source_group": source,
        **item,
        "lightgame_reach_rate": item["light"] / item["new"] if item["new"] else None,
        "d1_return_rate": item["d1_num"] / item["d1_den"] if item["d1_den"] else None,
        "d3_return_rate": item["d3_num"] / item["d3_den"] if item["d3_den"] else None,
    })

metabase_rows = []
with (PROJECT / "analysis/h5_lightgame_first_pay_path_v5_2026_08_28/results/00_current_first_pay_game_summary.csv").open() as fh:
    for row in csv.DictReader(fh):
        if row["game_id"] in GAME_NAMES:
            users = int(row["users"])
            rounds = int(row["round_count"])
            metabase_rows.append({
                "game_id": row["game_id"],
                "game": GAME_NAMES[row["game_id"]],
                "users": users,
                "rounds": rounds,
                "rounds_per_user": rounds / users,
                "bet_amount": float(row["bet_amount"]),
                "status": "first_pay_cumulative_snapshot",
            })
metabase_rows.sort(key=lambda x: x["users"], reverse=True)

origin_source = json.loads(
    (PROJECT / "data/outputs/origin_new_user/2026-08-28-30d/source-data.json").read_text("utf-8")
)
recent_channels = []
channel_map = {
    "wajebetH5-facebook": "H5自然",
    "wajeH5-fb": "H5 Facebook",
    "wajeH5ga-googlewors_int": "H5 Google",
    "pww": "PWA/PWW",
}
for sheet, label in channel_map.items():
    payload = origin_source["sheets"][sheet]
    headers = payload["headers"]
    idx = {name: i for i, name in enumerate(headers)}
    row = next(r for r in payload["rows"] if r[0] == "2026-08-25")
    recent_channels.append({
        "channel": label,
        "cohort_date": row[0],
        "new_users": int(row[idx["新增人数"]]),
        "d1": float(row[idx["次留"]].strip("%")) / 100,
        "d3": float(row[idx["3日留"]].strip("%")) / 100,
        "d7": None,
        "status": "D1_D3_mature_D7_immature",
    })

v5_summary = json.loads(
    (PROJECT / "analysis/h5_lightgame_first_pay_path_v5_2026_08_28/results/reaudit_summary.json").read_text("utf-8")
)
paid_free = {
    (r["period"], r["user_group"]): r for r in v5_summary["new_paid_free_overall"]
}
segment_comparison = {
    "post_paid_d7_game_rate": paid_free[("post", "当日新增首充")]["first_game_d7_rate"],
    "post_unpaid_d7_game_rate": paid_free[("post", "当日新增未付费")]["first_game_d7_rate"],
}

quality_matrix = [
    {"item": "GA4日表连续性", "status": "provisional", "evidence": "2026-08-21至08-27连续7日；每日24类事件；全部WEB"},
    {"item": "GA4游戏页面", "status": "provisional", "evidence": "5个目标game_id页面路径可识别；表示页面进入，不表示游戏开始"},
    {"item": "GA4用户关联", "status": "blocked", "evidence": f"user_id事件覆盖仅{user_id_event_coverage:.2%}，不能与服务端做用户级关联"},
    {"item": "GA4前端性能", "status": "blocked", "evidence": "game/performance命名事件均为0；无Web Vitals和错误事件"},
    {"item": "Firebase Web App", "status": "blocked", "evidence": "应用已注册，但未关联Google Analytics数据流；Performance无Web应用数据"},
    {"item": "Ares曝光/点击", "status": "blocked", "evidence": "H5 js来源及game_id/入口关联未通过"},
    {"item": "Origin GAMESTART", "status": "blocked", "evidence": "仅覆盖4个统一play_id，不能用未命中判断未玩"},
    {"item": "Origin GAMEEND", "status": "blocked", "evidence": "最近7日异常率约6.13%，未通过<1%门禁"},
    {"item": "Metabase游戏深度", "status": "provisional", "evidence": "真实game_id、用户、局数、下注可用；仅近期首充用户累计快照，update_at非首次开局"},
    {"item": "新增留存", "status": "certified_partial", "evidence": "Origin已验收到8月26；8月25批次D1/D3可用，D7尚未成熟"},
]

summary = {
    "generated_at": "2026-08-31",
    "status": "provisional_with_blocked_funnel_stages",
    "joint_cutoff": "2026-08-26",
    "ga4": {
        "window": ["2026-08-21", "2026-08-27"],
        "event_rows": ga4_total_events,
        "first_visitors": ga4_first_visitors,
        "event_types": 24,
        "user_id_event_coverage": user_id_event_coverage,
        "game_process_named_events": int(observability["game_process_named_events"]),
        "performance_named_events": int(observability["performance_named_events"]),
    },
    "games": game_summary,
    "source_groups": source_summary,
    "metabase_first_pay_snapshot": metabase_rows,
    "recent_origin_channels": recent_channels,
    "paid_unpaid_segment": segment_comparison,
    "quality_matrix": quality_matrix,
}
(ROOT / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "quality_matrix.json").write_text(json.dumps(quality_matrix, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "source_register.json").write_text(json.dumps({
    "ga4_bigquery": {"project": "waje-analytics-readonly", "dataset": "analytics_504208609", "cutoff": "2026-08-27", "status": "provisional"},
    "firebase_web": {"project": "waje-special", "status": "registered_unlinked_no_performance"},
    "origin_new_user": {"source": "BQ-新增付费用户分析", "cutoff": "2026-08-26", "status": "validated"},
    "origin_tracking": {"window": "2026-08-21 to 2026-08-27", "status": "partial_with_gameend_errors"},
    "external_metabase": {"host": "35.181.27.61:3001", "status": "existing_aggregate_snapshot_only"},
}, ensure_ascii=False, indent=2), encoding="utf-8")


def save_chart(image: Image.Image, name: str):
    image.save(CHARTS / name, "PNG", optimize=True)


# Chart 1: release timeline
image, draw = canvas("轻量化游戏发布与分析节点", "发布日期用于观察窗口定位；同期版本、KYC、投放和埋点变化属于干扰项")
y = 440
draw.line((120, y, 1480, y), fill=GRID, width=8)
events = [
    ("7/17", "Limbo\n稳定恢复", BLUE),
    ("7/23", "Keno / H5 2.1.14", TEAL),
    ("7/29", "Color Dice", GREEN),
    ("8/06", "Opera埋点期", YELLOW),
    ("8/15", "Facebook\n投放封禁", RED),
    ("8/21", "Hilo / Plinko", PURPLE),
]
for idx, (when, label, color) in enumerate(events):
    x = 150 + idx * 255
    draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=color)
    draw.text((x - 35, y + 45), when, fill=INK, font=font(24, True))
    lines = label.split("\n")
    for j, line in enumerate(lines):
        draw.text((x - 85, y - 105 + j * 30), line, fill=INK, font=font(21, j == 0))
draw.rounded_rectangle((95, 710, 1505, 805), 16, fill="#EDF4FA")
draw.text((125, 735), "跨源共同完整日：2026-08-26｜GA4行为数据至8月27日｜Hilo/Plinko D7显示N/A", fill=INK, font=font(25, True))
save_chart(image, "01_轻量化游戏发布与分析节点.png")


# Chart 2: game page reach and intensity
image, draw = canvas("GA4首次访问用户的轻量化游戏页面触达", "2026-08-21至08-27；页面进入不是游戏开始，用户可能进入多款游戏")
ordered = sorted(game_summary, key=lambda x: x["new_visitors"], reverse=True)
left, right, top, bottom = 420, 1490, 210, 770
max_users = max(x["new_visitors"] for x in ordered)
for tick in range(0, 5):
    x = left + int((right-left) * tick / 4)
    draw.line((x, top, x, bottom), fill=GRID, width=2)
    draw.text((x-20, 795), f"{int(max_users*tick/4)}", fill=MUTED, font=font(18))
for i, item in enumerate(ordered):
    y = top + i * 105
    draw.text((70, y + 8), item["game"], fill=INK, font=font(25, True))
    end = left + int((right-left) * item["new_visitors"] / max_users)
    draw.rounded_rectangle((left, y, end, y+38), 8, fill=BLUE)
    draw.text((end+12, y+3), f"{item['new_visitors']:,}人", fill=INK, font=font(20, True))
    draw.text((left, y+48), f"人均页面浏览 {item['page_views_per_new_visitor']:.2f}", fill=MUTED, font=font(19))
save_chart(image, "02_新访客游戏页面触达.png")


# Chart 3: D1/D3 return
image, draw = canvas("进入轻量化游戏页的新访客：D1/D3应用回访", "同一GA4首次访问批次；D1截至8/26、D3截至8/24；D7尚未成熟")
left, right, top, bottom = 240, 1490, 210, 760
for tick in range(0, 51, 10):
    y = bottom - int((bottom-top)*tick/50)
    draw.line((left, y, right, y), fill=GRID, width=2)
    draw.text((170, y-10), f"{tick}%", fill=MUTED, font=font(18))
bar_w = 70
group_w = 230
for i, item in enumerate(sorted(game_summary, key=lambda x: x["game"])):
    cx = left + 85 + i * group_w
    for off, val, color, label in [
        (-42, item["d1_return_rate"], BLUE, "D1"),
        (42, item["d3_return_rate"], GREEN, "D3"),
    ]:
        h = int((bottom-top) * (val or 0) / 0.5)
        draw.rounded_rectangle((cx+off-bar_w//2, bottom-h, cx+off+bar_w//2, bottom), 8, fill=color)
        draw.text((cx+off-32, bottom-h-34), f"{val:.1%}", fill=INK, font=font(18, True))
    draw.text((cx-62, 790), item["game"], fill=INK, font=font(21, True))
draw.rectangle((1190, 110, 1220, 132), fill=BLUE)
draw.text((1230, 104), "D1", fill=INK, font=font(20))
draw.rectangle((1300, 110, 1330, 132), fill=GREEN)
draw.text((1340, 104), "D3", fill=INK, font=font(20))
save_chart(image, "03_游戏页新访客D1D3回访.png")


# Chart 4: Metabase first-pay game depth
image, draw = canvas("近期首充用户的轻量化游戏累计深度", "外部生产Metabase累计快照；只作首充分群，不代表全体新增用户或首次开局时点")
ordered_mb = sorted(metabase_rows, key=lambda x: x["rounds_per_user"], reverse=True)
left, right, top, bottom = 420, 1490, 210, 770
max_rounds = max(x["rounds_per_user"] for x in ordered_mb)
for i, item in enumerate(ordered_mb):
    y = top + i * 105
    draw.text((70, y + 8), item["game"], fill=INK, font=font(25, True))
    end = left + int((right-left) * item["rounds_per_user"] / max_rounds)
    draw.rounded_rectangle((left, y, end, y+38), 8, fill=PURPLE)
    draw.text((end+12, y+3), f"{item['rounds_per_user']:.1f}局/人", fill=INK, font=font(20, True))
    draw.text((left, y+48), f"首充样本 {item['users']:,}人｜累计局数 {item['rounds']:,}", fill=MUTED, font=font(18))
save_chart(image, "04_首充用户游戏深度横向比较.png")


# Chart 5: data availability
image, draw = canvas("新增用户全链路：当前可验证范围", "绿色=可用；黄色=部分可用；红色=blocked，缺失环节不计为用户流失")
stages = [
    ("新增注册", "可用", GREEN),
    ("H5访问", "可用", GREEN),
    ("游戏页进入", "部分可用", YELLOW),
    ("入口曝光/点击", "blocked", RED),
    ("GAME_LOAD/READY", "blocked", RED),
    ("GAMESTART", "覆盖不全", YELLOW),
    ("有效下注", "首充样本", YELLOW),
    ("首局结算", "blocked", RED),
    ("D1/D3回访", "GA4可用", GREEN),
    ("D7/D15留存", "未成熟/分源", YELLOW),
]
for i, (label, status, color) in enumerate(stages):
    row, col = divmod(i, 5)
    x = 75 + col * 300
    y = 210 + row * 260
    draw.rounded_rectangle((x, y, x+250, y+135), 18, fill=color)
    draw.text((x+20, y+24), label, fill="#FFFFFF" if color != YELLOW else INK, font=font(22, True))
    draw.text((x+20, y+78), status, fill="#FFFFFF" if color != YELLOW else INK, font=font(19))
    if col < 4:
        draw.line((x+255, y+68, x+292, y+68), fill=MUTED, width=4)
save_chart(image, "05_新增用户全链路数据可用性.png")


print(json.dumps({"status": "ok", "games": len(game_summary), "charts": 5}, ensure_ascii=False))

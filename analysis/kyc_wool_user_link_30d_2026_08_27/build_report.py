#!/usr/bin/env python3
"""Build privacy-safe aggregates and visual assets for the 30-day KYC / risk report.

All input values come from aggregate-only Metabase queries. User identifiers are
only used inside controlled database joins and are never saved by this script.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent
ARCHIVE = (
    OUT.parents[1]
    / "knowledge"
    / "02-数据"
    / "Waje-KYC人脸与羊毛风险综合分析-近30天与用户关联-2026-08-27.md"
)

W, H = 1600, 1050
BG = "#F7FBFF"
PANEL = "#FFFFFF"
INK = "#17324D"
MUTED = "#5E7891"
GRID = "#D7E5F0"
BLUE = "#2F80C8"
TEAL = "#35A988"
GOLD = "#E6A824"
RED = "#D96A65"
PURPLE = "#7264CE"


FACE_PHASES = [
    {"phase": "7月28日—8月3日", "days": 7, "users": 10527, "success": 5590, "fail": 4937, "avg_verify": 1.00},
    {"phase": "8月4日—8月10日", "days": 7, "users": 10661, "success": 5645, "fail": 5016, "avg_verify": 1.01},
    {"phase": "8月11日—8月17日", "days": 7, "users": 11378, "success": 5765, "fail": 5613, "avg_verify": 1.01},
    {"phase": "8月18日—8月26日", "days": 9, "users": 14631, "success": 7062, "fail": 7569, "avg_verify": 1.01},
]

LINK_GROUPS = [
    {
        "label": "当前未查到\n人脸状态记录",
        "short": "未查到人脸记录",
        "users": 13240,
        "first_pay": 13327607.56,
        "cash_recharge_7d": 16008086.00,
        "withdraw": 6913735.10,
        "ratio_to_first_pay": 0.52,
        "tc7": 0.43,
        "first_pay_match_rate": 1.00,
        "repeat_recharge_rate": 0.18,
        "positive_pre_first_pay_asset_rate": 1.00,
        "avg_pre_first_pay_asset": 75998.07,
        "withdraw_rate": 0.37,
        "fast_rate": 0.36,
        "withdraw_gt_first": 0.13,
        "game_rate": 0.893,
        "zero_round_rate": 0.107,
        "rounds_per_gamer": 75.8,
        "identity_link_rate": 0.49,
        "risk_rule_match_rate": 0.00,
    },
    {
        "label": "当前人脸状态\n= 通过",
        "short": "人脸通过",
        "users": 4396,
        "first_pay": 4404765.24,
        "cash_recharge_7d": 5258810.00,
        "withdraw": 7218978.10,
        "ratio_to_first_pay": 1.64,
        "tc7": 1.37,
        "first_pay_match_rate": 1.00,
        "repeat_recharge_rate": 0.19,
        "positive_pre_first_pay_asset_rate": 1.00,
        "avg_pre_first_pay_asset": 98859.83,
        "withdraw_rate": 0.96,
        "fast_rate": 0.92,
        "withdraw_gt_first": 0.46,
        "game_rate": 0.921,
        "zero_round_rate": 0.079,
        "rounds_per_gamer": 77.3,
        "identity_link_rate": 1.00,
        "risk_rule_match_rate": 0.00,
    },
    {
        "label": "当前人脸状态\n= 未通过",
        "short": "人脸未通过",
        "users": 3085,
        "first_pay": 3119638.60,
        "cash_recharge_7d": 3443783.00,
        "withdraw": 731763.72,
        "ratio_to_first_pay": 0.23,
        "tc7": 0.21,
        "first_pay_match_rate": 1.00,
        "repeat_recharge_rate": 0.11,
        "positive_pre_first_pay_asset_rate": 1.00,
        "avg_pre_first_pay_asset": 94813.10,
        "withdraw_rate": 0.30,
        "fast_rate": 0.28,
        "withdraw_gt_first": 0.041,
        "game_rate": 0.842,
        "zero_round_rate": 0.158,
        "rounds_per_gamer": 104.3,
        "identity_link_rate": 0.93,
        "risk_rule_match_rate": 0.00,
    },
]

STABILITY = [
    {"period": "8月12日—8月15日", "人脸通过": (2210, 1.39, 0.95, 0.91), "人脸未通过": (1505, 0.22, 0.30, 0.28), "未查到人脸记录": (6550, 0.43, 0.37, 0.36)},
    {"period": "8月16日—8月19日", "人脸通过": (2186, 1.36, 0.97, 0.93), "人脸未通过": (1580, 0.21, 0.29, 0.27), "未查到人脸记录": (6690, 0.44, 0.37, 0.35)},
]


def pct(value: float, precision: int = 1) -> str:
    return f"{value * 100:.{precision}f}%"


def comma(value: float) -> str:
    return f"{value:,.0f}"


def num(value: float) -> str:
    return f"{value:,.2f}"


def fnt(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size, index=0)
    return ImageFont.load_default()


FONT_S = fnt(26)
FONT_M = fnt(32)
FONT_L = fnt(42, True)
FONT_XL = fnt(50, True)


def new_canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 24, W - 28, H - 28), radius=28, fill=PANEL, outline="#D6E5F0", width=2)
    draw.text((72, 64), title, font=FONT_L, fill=INK)
    draw.text((74, 122), subtitle, font=FONT_S, fill=MUTED)
    return image, draw


def save(image: Image.Image, name: str) -> None:
    image.save(OUT / name, "PNG", optimize=True)


def draw_bar(draw: ImageDraw.ImageDraw, x: float, y: float, width: float, height: float, value: float, max_value: float, color: str) -> None:
    bar_h = height * value / max_value if max_value else 0
    draw.rounded_rectangle((x, y + height - bar_h, x + width, y + height), radius=9, fill=color)


def draw_phase_trend() -> None:
    image, draw = new_canvas(
        "KYC 项目节点后的状态变化",
        "项目节点：7月27日23:20，H5首充带币触发门槛由900降至500；本图覆盖调整后的30个完整自然日。",
    )
    # Left panel: daily new face-status records
    x0, y0, cw, ch = 100, 245, 660, 470
    draw.text((x0, 190), "每日新增人脸状态记录", font=FONT_M, fill=INK)
    max_day = 1750
    for p in [0, 500, 1000, 1500]:
        y = y0 + ch - ch * p / max_day
        draw.line((x0, y, x0 + cw, y), fill=GRID, width=2)
        draw.text((x0 - 72, y - 14), f"{p:,}", font=FONT_S, fill=MUTED)
    bar_w = 86
    for i, r in enumerate(FACE_PHASES):
        value = r["users"] / r["days"]
        x = x0 + 76 + i * 150
        draw_bar(draw, x, y0, bar_w, ch, value, max_day, BLUE)
        draw.text((x - 8, y0 + ch - ch * value / max_day - 42), f"{value:,.0f}", font=FONT_S, fill=INK)
        draw.multiline_text((x - 36, y0 + ch + 24), r["phase"].replace("—", "\n"), font=FONT_S, fill=MUTED, align="center", spacing=2)
    # Right panel: status success share
    x1, y1, cw1, ch1 = 910, 245, 580, 470
    draw.text((x1, 190), "人脸状态为“通过”的占比", font=FONT_M, fill=INK)
    low, high = 44, 56
    for p in [44, 47, 50, 53, 56]:
        y = y1 + ch1 - ch1 * (p - low) / (high - low)
        draw.line((x1, y, x1 + cw1, y), fill=GRID, width=2)
        draw.text((x1 - 74, y - 14), f"{p}%", font=FONT_S, fill=MUTED)
    pts = []
    for i, r in enumerate(FACE_PHASES):
        value = 100 * r["success"] / r["users"]
        x = x1 + 75 + i * 150
        y = y1 + ch1 - ch1 * (value - low) / (high - low)
        pts.append((x, y, value))
        draw.text((x - 40, y1 + ch1 + 24), r["phase"].replace("—", "\n"), font=FONT_S, fill=MUTED, align="center", spacing=2)
    draw.line([(x, y) for x, y, _ in pts], fill=TEAL, width=6)
    for x, y, value in pts:
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=TEAL)
        draw.text((x - 44, y - 44), f"{value:.1f}%", font=FONT_S, fill=INK)
    draw.rounded_rectangle((90, 830, W - 90, 990), radius=12, fill="#FFF8E5")
    draw.multiline_text(
        (116, 850),
        "解读：后段的日均状态记录量比首周高8.1%，但“通过”占比由53.1%降至48.3%。\n"
        "已知记录中未见7月27日后的新配置切点，因此只能作为待核查的结构变化。",
        font=FONT_S,
        fill=INK,
        spacing=12,
    )
    save(image, "01_KYC项目节点后的状态变化.png")


def draw_tc_comparison() -> None:
    image, draw = new_canvas(
        "首充用户的7日现金提充审计",
        "审计口径：实际首笔成功充值起7天内成功提现 ÷ 同7天内全部成功现金充值；旧“提现÷首充”只作分母完整性核验。",
    )
    x0, y0, cw, ch = 320, 230, 1010, 450
    xmax = 1.8
    for t in [0, 0.5, 1.0, 1.5]:
        x = x0 + cw * t / xmax
        draw.line((x, y0, x, y0 + ch), fill=GRID, width=2)
        draw.text((x - 18, y0 + ch + 24), f"{t:.1f}", font=FONT_S, fill=MUTED)
    ref_x = x0 + cw / xmax
    draw.line((ref_x, y0 - 10, ref_x, y0 + ch + 8), fill=RED, width=3)
    draw.text((ref_x + 10, y0 - 40), "100%（提现额=现金充值额）", font=FONT_S, fill=RED)
    row_h = 145
    for i, r in enumerate(LINK_GROUPS):
        y = y0 + 8 + i * row_h
        draw.multiline_text((84, y + 10), r["label"], font=FONT_M, fill=INK, spacing=2)
        old_width = cw * r["ratio_to_first_pay"] / xmax
        audit_width = cw * r["tc7"] / xmax
        draw.rounded_rectangle((x0, y + 16, x0 + old_width, y + 56), radius=10, fill="#A9C8E3")
        draw.rounded_rectangle((x0, y + 70, x0 + audit_width, y + 116), radius=10, fill=GOLD if r["tc7"] >= 1 else TEAL)
        draw.text((x0 + old_width + 20, y + 15), f"首充金额口径 {pct(r['ratio_to_first_pay'])}", font=FONT_S, fill=MUTED)
        draw.text((x0 + audit_width + 20, y + 72), f"7日现金口径 {pct(r['tc7'])}", font=FONT_M, fill=INK)
    draw.rounded_rectangle((86, 780, W - 86, 980), radius=12, fill="#EAF5FF")
    draw.multiline_text(
        (112, 805),
        "审计修正：人脸通过组原“提现÷首充”为164%，但首充后存在重复充值。\n"
        "使用同7天全部成功现金充值做分母后，7日现金提充比为137%，仍高于其他两组。\n"
        "这不是自动判定羊毛的依据：所有样本首充前均有非零资产，资产来源和可提现性仍待核验。",
        font=FONT_S,
        fill=INK,
        spacing=12,
    )
    save(image, "02_首充用户七日提充结构.png")


def draw_withdraw_speed() -> None:
    image, draw = new_canvas(
        "首充用户的提现速度",
        "同一批完成7天观察的首充用户；百分比的分母均为对应人脸状态组的首充用户数。",
    )
    x0, y0, cw, ch = 160, 220, 1260, 430
    for p in range(0, 101, 20):
        y = y0 + ch - ch * p / 100
        draw.line((x0, y, x0 + cw, y), fill=GRID, width=2)
        draw.text((86, y - 14), f"{p}%", font=FONT_S, fill=MUTED)
    group_w = cw / len(LINK_GROUPS)
    labels = [("7日内成功提现", BLUE), ("24小时内成功提现", GOLD)]
    for i, r in enumerate(LINK_GROUPS):
        cx = x0 + group_w * (i + 0.5)
        for j, (metric, color) in enumerate(labels):
            value = r["withdraw_rate"] if j == 0 else r["fast_rate"]
            bx = cx - 46 + j * 50
            bh = ch * value
            draw.rounded_rectangle((bx, y0 + ch - bh, bx + 34, y0 + ch), radius=8, fill=color)
            draw.text((bx - 8, y0 + ch - bh - 38), pct(value), font=FONT_S, fill=INK)
        draw.multiline_text((cx - 80, y0 + ch + 26), r["label"], font=FONT_S, fill=MUTED, align="center", spacing=2)
    lx, ly = 160, 738
    for text, color in labels:
        draw.rectangle((lx, ly, lx + 26, ly + 22), fill=color)
        draw.text((lx + 38, ly - 4), text, font=FONT_S, fill=INK)
        lx += 310
    draw.rounded_rectangle((84, 805, W - 84, 980), radius=12, fill="#FFF0EF")
    draw.multiline_text(
        (110, 830),
        "人脸通过组有96%在7天内成功提现，其中92%在首充后24小时内已成功提现。\n"
        "该模式在8月12—15日与8月16—19日两个首充阶段均重复出现。",
        font=FONT_S,
        fill=INK,
        spacing=12,
    )
    save(image, "03_首充用户提现速度.png")


def draw_game_activity() -> None:
    image, draw = new_canvas(
        "首充后7日游戏参与：未发现“低参与”信号",
        "游戏数据来自用户级聚合；仅用于判断资金异常是否同时伴随低真实游戏参与。",
    )
    x0, y0, cw, ch = 150, 220, 790, 440
    for p in range(0, 101, 20):
        y = y0 + ch - ch * p / 100
        draw.line((x0, y, x0 + cw, y), fill=GRID, width=2)
        draw.text((76, y - 14), f"{p}%", font=FONT_S, fill=MUTED)
    group_w = cw / len(LINK_GROUPS)
    for i, r in enumerate(LINK_GROUPS):
        cx = x0 + group_w * (i + 0.5)
        for j, (value, color) in enumerate([(r["game_rate"], TEAL), (r["zero_round_rate"], RED)]):
            bx = cx - 42 + j * 48
            bh = ch * value
            draw.rounded_rectangle((bx, y0 + ch - bh, bx + 32, y0 + ch), radius=8, fill=color)
            draw.text((bx - 9, y0 + ch - bh - 38), pct(value), font=FONT_S, fill=INK)
        draw.multiline_text((cx - 84, y0 + ch + 26), r["label"], font=FONT_S, fill=MUTED, align="center", spacing=2)
    draw.rectangle((164, 745, 190, 767), fill=TEAL)
    draw.text((202, 739), "有游戏参与", font=FONT_S, fill=INK)
    draw.rectangle((410, 745, 436, 767), fill=RED)
    draw.text((448, 739), "0局用户", font=FONT_S, fill=INK)
    # right side table
    tx, ty = 1050, 235
    draw.text((tx, ty), "人均局数（仅游戏用户）", font=FONT_M, fill=INK)
    for i, r in enumerate(LINK_GROUPS):
        y = ty + 90 + i * 120
        draw.multiline_text((tx, y), r["label"], font=FONT_S, fill=INK, spacing=2)
        draw.text((tx + 300, y + 16), f"{r['rounds_per_gamer']:.1f} 局", font=FONT_L, fill=PURPLE)
    draw.rounded_rectangle((1000, 650, 1500, 850), radius=16, fill="#EAF7F0")
    draw.multiline_text(
        (1030, 678),
        "人脸通过组的游戏参与率为92.1%，\n0局比例仅7.9%，与未查到人脸记录组接近。\n\n“高提充”并未同时呈现低游戏参与，\n不能据此直接判断为羊毛行为。",
        font=FONT_S,
        fill=INK,
        spacing=10,
    )
    save(image, "04_首充用户游戏参与.png")


def draw_stability() -> None:
    image, draw = new_canvas(
        "高现金流出结构在两个首充阶段均出现",
        "8月12—15日与8月16—19日的首充用户均已观察满7天；柱高为7日成功提现 ÷ 同7天成功现金充值。",
    )
    x0, y0, cw, ch = 175, 225, 1220, 430
    ymax = 1.8
    for p in [0, 0.5, 1.0, 1.5]:
        y = y0 + ch - ch * p / ymax
        draw.line((x0, y, x0 + cw, y), fill=GRID, width=2)
        draw.text((96, y - 14), f"{p:.1f}", font=FONT_S, fill=MUTED)
    y_ref = y0 + ch - ch * 1.0 / ymax
    draw.line((x0, y_ref, x0 + cw, y_ref), fill=RED, width=3)
    draw.text((x0 + cw - 190, y_ref - 38), "100% 参考线", font=FONT_S, fill=RED)
    colors = {"人脸通过": GOLD, "人脸未通过": TEAL, "未查到人脸记录": BLUE}
    group_x = [420, 960]
    for phase, cx in zip(STABILITY, group_x):
        draw.text((cx - 120, y0 + ch + 28), phase["period"], font=FONT_M, fill=INK)
        for j, name in enumerate(["人脸通过", "人脸未通过", "未查到人脸记录"]):
            users, tc, _, _ = phase[name]
            bx = cx - 105 + j * 75
            bh = ch * tc / ymax
            draw.rounded_rectangle((bx, y0 + ch - bh, bx + 48, y0 + ch), radius=8, fill=colors[name])
            draw.text((bx - 2, y0 + ch - bh - 40), pct(tc), font=FONT_S, fill=INK)
    lx = 320
    for name in ["人脸通过", "人脸未通过", "未查到人脸记录"]:
        draw.rectangle((lx, 760, lx + 24, 782), fill=colors[name])
        draw.text((lx + 36, 755), name, font=FONT_S, fill=INK)
        lx += 270
    draw.rounded_rectangle((100, 820, W - 100, 980), radius=12, fill="#FFF8E5")
    draw.multiline_text(
        (126, 842),
        "人脸通过组在两个阶段的7日现金提充比均为136%—139%，不是由单个日期造成的尖点。\n"
        "下一步需要拆解首充前资产、Bonus、派奖和提现审核状态。",
        font=FONT_S,
        fill=INK,
        spacing=12,
    )
    save(image, "05_分阶段首充提充比.png")


def markdown() -> str:
    total_face = sum(r["users"] for r in FACE_PHASES)
    total_success = sum(r["success"] for r in FACE_PHASES)
    return f"""---
type: kyc-wool-risk-user-link-report
status: audited_with_caveats
period: 2026-07-28 至 2026-08-26
user_link_period: 2026-08-12 至 2026-08-19（首充后完整观察7天）
privacy: user_linked_in_query_aggregate_only
---

# Waje KYC人脸与羊毛风险｜30天关联分析

> KYC状态趋势：2026年7月28日至8月26日（30个完整自然日）。
> 
> 用户级关联：仅纳入2026年8月12日至19日首充、且已经观察满7天至8月26日的 **{comma(sum(r['users'] for r in LINK_GROUPS))} 名用户**。用户标识只在受控查询内关联，报告不保存或展示任何个人明细。

## 核心结论

1. **KYC 后段状态呈现变弱迹象。** 已知项目节点为 **7月27日23:20，H5触发门槛由900降至500**；30天窗口均处于调整后。新增人脸状态记录的日均量由 **1,504** 增至 **1,626**，但状态为“通过”的占比从 **53.1%** 降至 **48.3%**。已知记录中未见后续配置切点，因此这是需要继续核查的结构变化，不能直接归因于门槛调整。
2. **164% 已被审计修正。** 旧值的分母只有首充金额，不是正确的提充比。以实际首笔成功充值为起点、统计同7天内全部成功现金充值后，人脸通过组的 **7日提现/现金充值为137%**；未查到人脸状态记录组为 **43%**，人脸未通过组为 **21%**。资金流出偏高仍存在，但不能再用164%作为提充比。
3. **高值不只由重复充值造成。** 人脸通过组的7日现金充值是首充金额的 **119%**，有 **19%** 用户发生重复充值；分母补全后仍高于100%。同时所有样本在首充前都有非零资产，资产来源和可提现性尚未核验，因此不能直接归因于羊毛或故障。
4. **当前证据不能把这组用户直接称为刷子。** 人脸通过组的游戏参与率为 **92.1%**，0局比例仅 **7.9%**，没有出现“高提现同时低游戏参与”的典型组合；现有风险规则表也未匹配到已记录的规则命中。
5. **下一步重点是补齐资金解释链路。** 需要把“首充前资产、首充/复充、Bonus、有效下注、派奖、最终提现和审核结果”用稳定的匿名用户键和订单/流程键连接，才能分清真实赢利、奖励套利、重复充值和风控漏检。

## 1. 30天 KYC 项目进展：状态记录增加，但通过占比下降

![KYC项目节点后的状态变化](01_KYC项目节点后的状态变化.png)

| 阶段 | 天数 | 人脸状态记录用户 | 日均记录数 | 状态为“通过” | 状态为“未通过” | 通过占比 |
|---|---:|---:|---:|---:|---:|---:|
""" + "\n".join(
        f"| {r['phase']} | {r['days']} | {comma(r['users'])} | {r['users']/r['days']:,.0f} | {comma(r['success'])} | {comma(r['fail'])} | {pct(r['success']/r['users'])} |"
        for r in FACE_PHASES
    ) + f"""

**怎么读：** 这张表的“通过占比”是 `人脸状态为通过的人数 ÷ 当期产生人脸状态记录的人数`，不是完整认证漏斗成功率。30天共产生 {comma(total_face)} 条人脸状态记录，其中 {comma(total_success)} 条为通过。它能发现结构变化，不能替代“触发 → 身份认证 → 人脸 → 提现”的完整漏斗。

## 2. 完成7天观察的首充用户：7日现金提充审计

![首充用户七日提充结构](02_首充用户七日提充结构.png)

| 人脸状态（查询时点） | 首充用户 | 提现÷首充金额（旧口径） | 7日现金充值 | 7日成功提现 | **7日提现÷现金充值** | 首充订单匹配 | 重复充值用户 | 24小时内成功提现 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
""" + "\n".join(
        f"| {r['short']} | {comma(r['users'])} | {pct(r['ratio_to_first_pay'])} | {num(r['cash_recharge_7d'])} | {num(r['withdraw'])} | **{pct(r['tc7'])}** | {pct(r['first_pay_match_rate'])} | {pct(r['repeat_recharge_rate'])} | {pct(r['fast_rate'])} |"
        for r in LINK_GROUPS
    ) + """

**审计结果：** 旧“提现÷首充金额”不是提充比，原因是它遗漏首充后的成功现金充值。首充时间与成功充值订单的24小时匹配覆盖率为 **100%**，因此改用“实际首笔成功充值起7天内成功提现 ÷ 同7天内全部成功现金充值”。

**为什么仍会高于100%：** 现金提现可以来自游戏赢利、首充前已有资产或奖励。审计中，三个分组的首充前非零资产覆盖率均为 **100%**；该资产的来源、资产类型与可提现性尚未核验。因此 **137% 是需要解释的现金流出信号，不是羊毛结论，也不是游戏故障结论。**

## 3. 高提现没有同时表现为低游戏参与

![首充用户游戏参与](04_首充用户游戏参与.png)

| 人脸状态（查询时点） | 有游戏参与 | 0局用户 | 仅游戏用户人均局数 |
|---|---:|---:|---:|
""" + "\n".join(
        f"| {r['short']} | **{pct(r['game_rate'])}** | {pct(r['zero_round_rate'])} | {r['rounds_per_gamer']:.1f} 局 |"
        for r in LINK_GROUPS
    ) + """

**判断：** 人脸通过组的游戏参与率最高，且0局比例最低。按当前可见的“有效局数/参与”维度，它不符合“充值后几乎不玩、立即提现”的低参与特征。需要继续核验的是：这些局数对应的真实现金下注、Bonus下注、结算/派奖和现金资产变化。

## 4. 7日现金提充比不是单个日期造成的尖点

![分阶段首充提充比](05_分阶段首充提充比.png)

| 首充阶段 | 人脸状态 | 首充用户 | **7日提现÷现金充值** | 7日有成功提现 | 24小时内有成功提现 |
|---|---|---:|---:|---:|---:|
""" + "\n".join(
        f"| {phase['period']} | {name} | {users:,} | **{pct(tc)}** | {pct(wr)} | {pct(fr)} |"
        for phase in STABILITY
        for name, (users, tc, wr, fr) in [("人脸通过", phase["人脸通过"]), ("人脸未通过", phase["人脸未通过"]), ("未查到人脸记录", phase["未查到人脸记录"])]
    ) + """

**判断：** 人脸通过组在8月12—15日和8月16—19日两段的7日现金提充比分别为 **139%**、**136%**，不是单日波动。下一步的目标是解释首充前资产、Bonus、游戏结算和提现审核构成，而不是先给用户打标签。

## 5. 风险关联：目前没有看到已匹配的规则命中，但这不是“无风险”证明

| 人脸状态 | 有身份关联记录 | 两类及以上关联标识 | 已匹配风险规则 |
|---|---:|---:|---:|
""" + "\n".join(
        f"| {r['short']} | {pct(r['identity_link_rate'])} | 0.0% | 0.0% |"
        for r in LINK_GROUPS
    ) + """

身份关联记录是 KYC/风控流程的正常副产物，不能直接视作风险命中。当前的规则匹配结果为0，只能说明本次可读规则表没有匹配记录；它不能证明用户没有其他风险，也不能替代审核结果、关联账号数或提款拒绝原因。

## 6. 下一步：先解释“高现金流出”，再调整 KYC 策略

1. **P0｜重建资金解释链路。** 对人脸通过且7日现金提充比偏高的分组，按“首充前资产、首充后总现金充值、Bonus、有效真金下注、结算、派奖、成功提现、提现审核结果”拆分。先确认是正常赢利、奖励资产还是流程问题。
2. **P0｜补齐 KYC 成功时点和流程键。** 服务端落地 `kyc_flow_id`、`withdraw_id`、匿名用户键、人脸最终成功时间、配置/规则版本；否则只能按当前状态做描述性关联，无法判断 KYC 在提现前还是提现后完成。
3. **P1｜建立固定的7日首充风险观察。** 每日新增一批完成7天观察的首充用户，按人脸状态输出7日现金提充比、24小时提现、有效局数、首充前资产、Bonus和规则匹配；只有多项异常同时出现，才进入人工核查。
4. **P1｜继续观察KYC状态通过占比。** 8月18日后的状态通过占比下降需要按端、包体、BVN/NIN、H5构建版本和错误码进一步拆分；现有30天表缺少这些稳定维度。

## 数据范围与限制

- KYC趋势窗口为 **7月28日至8月26日**；该窗口全部位于7月27日H5门槛调整之后，因此不能单凭本报告证明门槛调整的因果效果。
- 用户级关联的首充事实表从 **8月12日** 才有可用记录；为保证7日观察完整，只使用 **8月12日至19日** 的首充用户。
- 人脸状态来自当前状态表；“未查到人脸状态记录”不等同于“从未进行人脸认证”。
- 首充前非零资产在本样本中覆盖率为100%，但资产来源、类型和可提现性未完成核验；这会影响对高现金提充比的解释。
- Bonus金额、最终提现审核结论及真实人脸成功时间尚未形成可核验统一链路，不纳入本次定性。
- 本次审计过程中，首充事实表的样本量发生少量实时变化；因此结论标记为 `provisional`，后续以稳定日终快照复核。
- 企业 BigQuery MCP 仍处于认证阻断状态；本次不以未验证的替代数据补造结论。
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    draw_phase_trend()
    draw_tc_comparison()
    draw_withdraw_speed()
    draw_game_activity()
    draw_stability()

    snapshot = {
        "report_period": "2026-07-28 至 2026-08-26",
        "first_pay_link_period": "2026-08-12 至 2026-08-19，观察至2026-08-26",
        "source_status": {
            "metabase_kyc_state": "provisional_aggregate_available",
            "metabase_user_link": "provisional_aggregate_available",
            "tc_metric": "corrected_to_7d_cash_withdraw_over_7d_cash_recharge_provisional",
            "bonus_link": "blocked_unit_and_settlement_mapping_unverified",
            "bigquery_mcp": "blocked_auth_required",
        },
        "project_node": {
            "effective_at": "2026-07-27 23:20",
            "change": "H5首充带币触发门槛 900 → 500",
            "post_change_adjustments_observed": "none_in_known_configuration_record",
        },
        "face_phases": FACE_PHASES,
        "first_pay_user_link": LINK_GROUPS,
        "stability": STABILITY,
        "privacy": "No user identifiers, KYC identifiers, payment identifiers, device IDs, IPs, bank data, biometric data, or transaction detail rows stored.",
    }
    (OUT / "source_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "report.md").write_text(markdown(), encoding="utf-8")
    ARCHIVE.write_text(markdown(), encoding="utf-8")
    chart_map = [
        {"file": "01_KYC项目节点后的状态变化.png", "question": "调整后30天KYC状态记录的量和通过占比是否变化", "type": "bar + line", "takeaway": "日均量小幅增加，但通过占比下降4.8pp"},
        {"file": "02_首充用户七日提充结构.png", "question": "不同人脸状态组的7日现金提现/充值是否不同，以及旧分母缺失会造成多大偏差", "type": "paired horizontal bar", "takeaway": "人脸通过组旧164%经分母审计后为137%"},
        {"file": "03_首充用户提现速度.png", "question": "高提充是否由更快提现带动", "type": "grouped bar", "takeaway": "人脸通过组96%在7天内、92%在24小时内成功提现"},
        {"file": "04_首充用户游戏参与.png", "question": "高提现是否同时伴随低游戏参与", "type": "grouped bar + exact values", "takeaway": "人脸通过组游戏参与率高，未出现低参与组合"},
        {"file": "05_分阶段首充提充比.png", "question": "高7日现金提现/充值是否仅由单日尖点造成", "type": "grouped bar", "takeaway": "两个首充阶段均复现136%—139%"},
    ]
    (OUT / "chart_map.json").write_text(json.dumps(chart_map, ensure_ascii=False, indent=2), encoding="utf-8")
    quality = {
        "status": "share_with_caveats",
        "checks": [
            {"check": "KYC状态键唯一性", "result": "54,797行与54,797个gid一致", "status": "passed"},
            {"check": "首充用户关联粒度", "result": "审计时点8月12—19日共20,721名唯一首充用户；源表查询中存在少量实时变化", "status": "provisional"},
            {"check": "订单状态映射", "result": "8月26日充值(type=1,status=3)与提现(type=2,status=103)金额和起源TC详情同日汇总近似一致", "status": "provisional"},
            {"check": "首充订单匹配", "result": "首充时间与成功充值订单在24小时内的匹配覆盖率为100%", "status": "passed"},
            {"check": "首充后7日观察", "result": "最后一批首充为8月19日，观察截止8月26日，均已满7天", "status": "passed"},
            {"check": "现金提充比公式", "result": "改为实际首笔成功充值起7天内成功提现 ÷ 同7天内全部成功现金充值；人脸通过组为137%", "status": "provisional"},
            {"check": "首充前资产与Bonus解释", "result": "所有样本首充前均有非零资产；资产来源、类型、可提现性、Bonus和结算链路未完成核验", "status": "blocked"},
            {"check": "BigQuery企业关联", "result": "MCP返回Auth required", "status": "blocked"},
        ],
    }
    (OUT / "quality_checks.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

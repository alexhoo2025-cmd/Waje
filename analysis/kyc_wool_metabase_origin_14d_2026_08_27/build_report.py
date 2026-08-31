#!/usr/bin/env python3
"""Build a privacy-safe KYC / anti-abuse 14-day analytical snapshot.

Inputs were read from visible aggregate-only Metabase and Origin report rows.
No user, payment-account, device, IP, identity, or biometric-level rows are
stored in this artifact.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent
WIDTH = 1400
HEIGHT = 760
BG = "#F7FBFF"
INK = "#17324D"
MUTED = "#5D7894"
GRID = "#D8E6F1"
BLUE = "#2E82C8"
GREEN = "#3DAA7A"
YELLOW = "#F2B94B"
RED = "#E46C67"
PURPLE = "#7867D7"


KYC_SUMMARY = {
    "overall": {
        "trigger": 20065,
        "called": 17085,
        "bvn_called": 8116,
        "nin_called": 11844,
        "bvn_pass": 5311,
        "nin_pass": 10154,
        "face_request": 13366,
        "face_request_times": 33997,
        "face_success": 9539,
        "face_failure": 1467,
        "face_historical_failure_times": 8403,
    },
    "app": {
        "trigger": 14966,
        "called": 12694,
        "bvn_called": 5685,
        "nin_called": 8793,
        "bvn_pass": 3989,
        "nin_pass": 7659,
        "face_request": 9624,
        "face_request_times": 23434,
        "face_success": 7009,
        "face_failure": 1033,
    },
    "h5": {
        "trigger": 5099,
        "called": 4391,
        "bvn_called": 2431,
        "nin_called": 3051,
        "bvn_pass": 1322,
        "nin_pass": 2495,
        "face_request": 3742,
        "face_request_times": 10563,
        "face_success": 2530,
        "face_failure": 434,
    },
    "early_7d": {
        "trigger": 10117,
        "called": 8620,
        "bvn_called": 4096,
        "nin_called": 5971,
        "bvn_pass": 2677,
        "nin_pass": 5145,
        "face_request": 6775,
        "face_success": 4833,
        "face_failure": 751,
    },
    "late_7d": {
        "trigger": 9948,
        "called": 8465,
        "bvn_called": 4020,
        "nin_called": 5873,
        "bvn_pass": 2634,
        "nin_pass": 5009,
        "face_request": 6591,
        "face_success": 4706,
        "face_failure": 716,
    },
}

KYC_DAILY = [
    ("08/13", 1052, 487, 471, 238),
    ("08/14", 1061, 511, 400, 191),
    ("08/15", 1031, 489, 327, 162),
    ("08/16", 1011, 490, 306, 152),
    ("08/17", 1076, 502, 355, 166),
    ("08/18", 1119, 514, 327, 160),
    ("08/19", 1130, 541, 451, 230),
    ("08/20", 1132, 516, 421, 229),
    ("08/21", 1034, 472, 362, 196),
    ("08/22", 1037, 497, 332, 150),
    ("08/23", 1079, 516, 332, 169),
    ("08/24", 1007, 497, 330, 152),
    ("08/25", 1057, 491, 326, 154),
    ("08/26", 1140, 486, 359, 181),
]

ORIGIN_DAILY = [
    ("08/13", 80.99, 15.34, 29.97, 359_507_766.00, 291_182_626.25),
    ("08/14", 76.13, 15.52, 30.22, 366_302_821.00, 278_848_816.32),
    ("08/15", 76.71, 15.67, 30.55, 372_578_684.00, 285_802_902.59),
    ("08/16", 79.70, 15.27, 30.09, 349_192_337.00, 278_290_832.67),
    ("08/17", 79.38, 14.93, 29.55, 338_771_417.00, 268_926_496.77),
    ("08/18", 78.09, 14.78, 29.31, 366_031_973.00, 285_848_681.67),
    ("08/19", 78.39, 14.33, 28.33, 365_495_638.00, 286_527_388.64),
    ("08/20", 77.72, 14.58, 28.97, 375_479_803.00, 291_838_734.20),
    ("08/21", 79.07, 14.94, 29.38, 362_897_477.00, 286_926_666.02),
    ("08/22", 79.98, 14.86, 29.43, 366_166_736.00, 292_876_478.30),
    ("08/23", 79.17, 14.59, 29.01, 349_400_597.00, 276_620_390.40),
    ("08/24", 77.53, 14.59, 29.36, 352_617_328.00, 273_372_500.92),
    ("08/25", 75.28, 14.72, 29.43, 357_865_207.00, 269_402_699.55),
    ("08/26", 79.48, 14.40, 28.66, 367_372_777.00, 291_991_360.49),
]


def rate(numerator: float, denominator: float) -> float:
    return 100 * numerator / denominator if denominator else 0.0


def pct(value: float) -> str:
    return f"{value:.2f}%"


def comma(value: float) -> str:
    return f"{value:,.0f}"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size, index=0)
    return ImageFont.load_default()


FONT_S = font(24)
FONT_M = font(30)
FONT_L = font(42, bold=True)
FONT_XL = font(52, bold=True)


def canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, WIDTH - 28, HEIGHT - 28), radius=28, fill="#FFFFFF", outline="#D6E6F2", width=2)
    draw.text((70, 70), title, font=FONT_L, fill=INK)
    draw.text((72, 128), subtitle, font=FONT_S, fill=MUTED)
    return image, draw


def save(image: Image.Image, name: str) -> None:
    image.save(OUT / name, "PNG", optimize=True)


def draw_funnel() -> None:
    all_ = KYC_SUMMARY["overall"]
    stages = [
        ("风险提现触发", all_["trigger"], BLUE),
        ("实际调用 BVN/NIN", all_["called"], "#4697D3"),
        ("请求人脸识别", all_["face_request"], GREEN),
        ("形成人脸最终结果", all_["face_success"] + all_["face_failure"], YELLOW),
        ("最终人脸成功", all_["face_success"], "#2C8C6B"),
    ]
    image, draw = canvas("提现触发人脸认证漏斗", "2026年8月13日至26日；单位：触发/认证人数；无最终结果不当作失败")
    max_value = stages[0][1]
    top = 205
    for i, (label, value, color) in enumerate(stages):
        y = top + i * 92
        width = int(850 * value / max_value)
        draw.rounded_rectangle((335, y, 335 + width, y + 56), radius=12, fill=color)
        draw.text((82, y + 10), label, font=FONT_M, fill=INK)
        draw.text((356, y + 9), comma(value), font=FONT_M, fill="#FFFFFF")
        if i:
            prev = stages[i - 1][1]
            draw.text((1020, y + 10), f"保留 {pct(rate(value, prev))}", font=FONT_S, fill=MUTED)
    unresolved = all_["face_request"] - all_["face_success"] - all_["face_failure"]
    draw.rounded_rectangle((72, 676, WIDTH - 72, 716), radius=10, fill="#FFF8E6")
    draw.text((92, 683), f"人脸请求后未形成最终结果：{comma(unresolved)} 人，占请求人数 {pct(rate(unresolved, all_['face_request']))}。", font=FONT_S, fill=INK)
    save(image, "01_提现触发人脸认证漏斗.png")


def draw_platform_quality() -> None:
    app = KYC_SUMMARY["app"]
    h5 = KYC_SUMMARY["h5"]
    metrics = [
        ("认证启动率", rate(app["called"], app["trigger"]), rate(h5["called"], h5["trigger"])),
        ("BVN通过率", rate(app["bvn_pass"], app["bvn_called"]), rate(h5["bvn_pass"], h5["bvn_called"])),
        ("NIN通过率", rate(app["nin_pass"], app["nin_called"]), rate(h5["nin_pass"], h5["nin_called"])),
        ("人脸成功率", rate(app["face_success"], app["face_request"]), rate(h5["face_success"], h5["face_request"])),
        ("无最终结果率", rate(app["face_request"] - app["face_success"] - app["face_failure"], app["face_request"]), rate(h5["face_request"] - h5["face_success"] - h5["face_failure"], h5["face_request"])),
    ]
    image, draw = canvas("App 与 H5：人脸认证质量对比", "同一提现触发流程；H5 在人脸请求后形成最终结果的能力弱于 App")
    x0, y0, chart_w, chart_h = 150, 220, 1120, 390
    for p in range(0, 101, 20):
        y = y0 + chart_h - chart_h * p / 100
        draw.line((x0, y, x0 + chart_w, y), fill=GRID, width=2)
        draw.text((88, y - 12), f"{p}%", font=FONT_S, fill=MUTED)
    group_w = chart_w / len(metrics)
    for i, (label, app_value, h5_value) in enumerate(metrics):
        cx = x0 + group_w * (i + 0.5)
        for shift, value, color, name in [(-36, app_value, BLUE, "App"), (12, h5_value, GREEN, "H5")]:
            bar_h = chart_h * value / 100
            draw.rounded_rectangle((cx + shift, y0 + chart_h - bar_h, cx + shift + 30, y0 + chart_h), radius=7, fill=color)
            draw.text((cx + shift - 8, y0 + chart_h - bar_h - 36), pct(value), font=FONT_S, fill=INK)
        draw.multiline_text((cx - 65, y0 + chart_h + 22), label, font=FONT_S, fill=INK, align="center", spacing=2)
    draw.rounded_rectangle((128, 650, 610, 704), radius=10, fill="#EAF5FF")
    draw.text((150, 662), "App", font=FONT_S, fill=INK)
    draw.rectangle((215, 669, 239, 693), fill=BLUE)
    draw.text((258, 662), "H5", font=FONT_S, fill=INK)
    draw.rectangle((310, 669, 334, 693), fill=GREEN)
    draw.text((650, 662), "说明：无最终结果率越低越好。", font=FONT_S, fill=MUTED)
    save(image, "02_App与H5认证质量对比.png")


def draw_kyc_daily() -> None:
    image, draw = canvas("人脸认证端到端成功率：14日趋势", "成功人数 ÷ 风险提现触发人数；H5的端到端表现不代表其人脸体验更优")
    x0, y0, chart_w, chart_h = 130, 210, 1150, 410
    for p in range(40, 61, 5):
        y = y0 + chart_h - chart_h * (p - 40) / 20
        draw.line((x0, y, x0 + chart_w, y), fill=GRID, width=2)
        draw.text((55, y - 12), f"{p}%", font=FONT_S, fill=MUTED)
    points = []
    for idx, (date, app_t, app_s, h5_t, h5_s) in enumerate(KYC_DAILY):
        x = x0 + chart_w * idx / (len(KYC_DAILY) - 1)
        app = rate(app_s, app_t)
        h5 = rate(h5_s, h5_t)
        points.append((date, x, app, h5))
        draw.text((x - 18, y0 + chart_h + 20), date, font=FONT_S, fill=MUTED)
    for field, color, label in [(2, BLUE, "App"), (3, GREEN, "H5")]:
        line = []
        for date, x, app, h5 in points:
            value = app if field == 2 else h5
            y = y0 + chart_h - chart_h * (value - 40) / 20
            line.append((x, y))
        draw.line(line, fill=color, width=5)
        for x, y in line:
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)
    for x, y, text, color in [(160, 675, "App", BLUE), (295, 675, "H5", GREEN)]:
        draw.rectangle((x, y, x + 26, y + 22), fill=color)
        draw.text((x + 38, y - 3), text, font=FONT_S, fill=INK)
    draw.rounded_rectangle((715, 655, 1270, 708), radius=10, fill="#FFF8E6")
    draw.text((735, 666), "H5 请求率更高；不能只看端到端率判断体验。", font=FONT_S, fill=INK)
    save(image, "03_端到端成功率趋势.png")


def draw_tc_trend() -> None:
    image, draw = canvas("全站提充比（TC）趋势", "起源 BQ-TC详情，2026年8月13日至26日；TC＝提款金额÷充值金额")
    x0, y0, chart_w, chart_h = 130, 215, 1150, 395
    low, high = 72, 84
    for p in range(72, 85, 2):
        y = y0 + chart_h - chart_h * (p - low) / (high - low)
        draw.line((x0, y, x0 + chart_w, y), fill=GRID, width=2)
        draw.text((62, y - 12), f"{p}%", font=FONT_S, fill=MUTED)
    line = []
    for idx, (date, tc, _, _, _, _) in enumerate(ORIGIN_DAILY):
        x = x0 + chart_w * idx / (len(ORIGIN_DAILY) - 1)
        y = y0 + chart_h - chart_h * (tc - low) / (high - low)
        line.append((x, y))
        draw.text((x - 18, y0 + chart_h + 18), date, font=FONT_S, fill=MUTED)
    draw.line(line, fill=PURPLE, width=5)
    for idx, (x, y) in enumerate(line):
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=PURPLE)
        if idx in (0, 11, 12, 13):
            draw.text((x - 24, y - 38), pct(ORIGIN_DAILY[idx][1]), font=FONT_S, fill=INK)
    draw.rounded_rectangle((95, 660, 1280, 712), radius=10, fill="#F1EDFF")
    draw.text((120, 672), "14日加权 TC 为 78.39%；后7日较前7日下降 0.13 个百分点，未出现整体 TC 上升信号。", font=FONT_S, fill=INK)
    save(image, "04_全站提充比趋势.png")


def derived() -> dict:
    all_ = KYC_SUMMARY["overall"]
    app = KYC_SUMMARY["app"]
    h5 = KYC_SUMMARY["h5"]
    early = KYC_SUMMARY["early_7d"]
    late = KYC_SUMMARY["late_7d"]
    total_pay = sum(row[4] for row in ORIGIN_DAILY)
    total_tx = sum(row[5] for row in ORIGIN_DAILY)
    return {
        "period": "2026-08-13 至 2026-08-26",
        "kyc": {
            "trigger": all_["trigger"],
            "called": all_["called"],
            "face_request": all_["face_request"],
            "face_success": all_["face_success"],
            "face_failure": all_["face_failure"],
            "face_unresolved": all_["face_request"] - all_["face_success"] - all_["face_failure"],
            "start_rate": rate(all_["called"], all_["trigger"]),
            "bvn_pass_rate": rate(all_["bvn_pass"], all_["bvn_called"]),
            "nin_pass_rate": rate(all_["nin_pass"], all_["nin_called"]),
            "face_success_request_rate": rate(all_["face_success"], all_["face_request"]),
            "face_unresolved_rate": rate(all_["face_request"] - all_["face_success"] - all_["face_failure"], all_["face_request"]),
            "e2e_rate": rate(all_["face_success"], all_["trigger"]),
            "app": {
                "face_success_request_rate": rate(app["face_success"], app["face_request"]),
                "unresolved_rate": rate(app["face_request"] - app["face_success"] - app["face_failure"], app["face_request"]),
                "bvn_pass_rate": rate(app["bvn_pass"], app["bvn_called"]),
                "nin_pass_rate": rate(app["nin_pass"], app["nin_called"]),
                "e2e_rate": rate(app["face_success"], app["trigger"]),
                "request_per_requester": app["face_request_times"] / app["face_request"],
            },
            "h5": {
                "face_success_request_rate": rate(h5["face_success"], h5["face_request"]),
                "unresolved_rate": rate(h5["face_request"] - h5["face_success"] - h5["face_failure"], h5["face_request"]),
                "bvn_pass_rate": rate(h5["bvn_pass"], h5["bvn_called"]),
                "nin_pass_rate": rate(h5["nin_pass"], h5["nin_called"]),
                "e2e_rate": rate(h5["face_success"], h5["trigger"]),
                "request_per_requester": h5["face_request_times"] / h5["face_request"],
            },
            "early_e2e": rate(early["face_success"], early["trigger"]),
            "late_e2e": rate(late["face_success"], late["trigger"]),
            "early_face_success": rate(early["face_success"], early["face_request"]),
            "late_face_success": rate(late["face_success"], late["face_request"]),
            "early_unresolved": rate(early["face_request"] - early["face_success"] - early["face_failure"], early["face_request"]),
            "late_unresolved": rate(late["face_request"] - late["face_success"] - late["face_failure"], late["face_request"]),
        },
        "origin": {
            "payment_amount": total_pay,
            "withdraw_amount": total_tx,
            "weighted_tc": rate(total_tx, total_pay),
            "early_tc": 78.46,
            "late_tc": 78.32,
            "early_tx_rate": 15.12,
            "late_tx_rate": 14.67,
            "early_payment_rate": 29.72,
            "late_payment_rate": 29.18,
            "early_arppu": 8463.37,
            "late_arppu": 8582.65,
        },
        "source_status": {
            "metabase_kyc_withdraw": "provisional_aggregate_available",
            "origin_tc_detail": "provisional_filter_display_mismatch",
            "origin_tx_analysis": "blocked_14d_filter_not_effective",
            "origin_tc_summary": "blocked_14d_filter_not_effective",
            "origin_wool_analysis": "restricted_user_level_sensitive_fields",
            "kyc_to_cashflow_link": "blocked_not_observed",
        },
    }


def report_markdown(data: dict) -> str:
    k = data["kyc"]
    a, h = k["app"], k["h5"]
    o = data["origin"]
    return f"""---
type: kyc-wool-risk-report
status: partial_evidence
period: {data['period']}
sources: [Metabase 提现触发人脸认证统计, 起源 BQ-TC详情]
privacy: aggregate_only
---

# Waje KYC 人脸与羊毛风险综合分析｜近 14 天

> 数据范围：{data['period']}。本报告仅使用可见的聚合数据；不包含用户、银行卡、BVN/NIN、人脸、设备或 IP 明细。

## 核心结论

1. **KYC 认证链路整体稳定，但人脸阶段仍有明显损失。** 14 日内共触发 {comma(k['trigger'])} 人，最终人脸成功 {comma(k['face_success'])} 人，端到端成功率为 **{pct(k['e2e_rate'])}**。请求人脸后有 {comma(k['face_unresolved'])} 人未形成最终结果，占 **{pct(k['face_unresolved_rate'])}**。
2. **H5 的人脸阶段质量弱于 App。** H5 请求口径的人脸成功率为 **{pct(h['face_success_request_rate'])}**，低于 App 的 **{pct(a['face_success_request_rate'])}**；H5 无最终结果率为 **{pct(h['unresolved_rate'])}**，高于 App 的 **{pct(a['unresolved_rate'])}**。H5 端到端成功率较高主要来自更高的人脸请求率，不能解读为 H5 人脸体验更好。
3. **NIN 明显优于 BVN。** 整体 NIN 通过率为 **{pct(k['nin_pass_rate'])}**，比 BVN 的 **{pct(k['bvn_pass_rate'])}** 高 {k['nin_pass_rate']-k['bvn_pass_rate']:.2f} 个百分点；H5 BVN 通过率仅 **{pct(h['bvn_pass_rate'])}**，是当前最值得优先核查的身份认证短板。
4. **全站资金面未出现近 14 日整体恶化信号。** 起源汇总的累计充值金额为 **{comma(o['payment_amount'])}**，累计提现金额为 **{comma(o['withdraw_amount'])}**，加权 TC 为 **{pct(o['weighted_tc'])}**。后 7 日 TC 较前 7 日下降 {o['early_tc']-o['late_tc']:.2f} 个百分点，未见全站提现占充值持续抬升。
5. **本轮不能判断“人脸 KYC 用户是否混入刷子”。** 当前 Metabase 人脸表与起源资金表没有可验证的 KYC 状态—充值—最终提现关联键；起源羊毛分析报表含用户级敏感字段且未纳入读取。结论应保持为 `blocked`，不能用同期趋势替代人群关联。

## 1. 提现触发人脸认证表现

### 漏斗结果

![提现触发人脸认证漏斗](01_提现触发人脸认证漏斗.png)

| 阶段 | 人数 | 相对上一阶段 |
|---|---:|---:|
| 风险提现触发 | {comma(k['trigger'])} | — |
| 实际调用 BVN/NIN | {comma(k['called'])} | {pct(k['start_rate'])} |
| 请求人脸识别 | {comma(k['face_request'])} | {pct(rate(k['face_request'], k['called']))} |
| 形成人脸最终结果 | {comma(k['face_success'] + k['face_failure'])} | {pct(rate(k['face_success'] + k['face_failure'], k['face_request']))} |
| 最终人脸成功 | {comma(k['face_success'])} | {pct(k['face_success_request_rate'])} |

人脸请求次数为 {comma(KYC_SUMMARY['overall']['face_request_times'])} 次，平均每位请求人脸用户约 {KYC_SUMMARY['overall']['face_request_times']/KYC_SUMMARY['overall']['face_request']:.2f} 次。该指标只反映请求次数，不等于失败用户数。

## 2. App 与 H5：问题集中在人脸请求后的链路

![App与H5认证质量对比](02_App与H5认证质量对比.png)

| 指标 | App | H5 | 差异（H5-App） |
|---|---:|---:|---:|
| 认证启动率 | {pct(rate(KYC_SUMMARY['app']['called'], KYC_SUMMARY['app']['trigger']))} | {pct(rate(KYC_SUMMARY['h5']['called'], KYC_SUMMARY['h5']['trigger']))} | {rate(KYC_SUMMARY['h5']['called'], KYC_SUMMARY['h5']['trigger'])-rate(KYC_SUMMARY['app']['called'], KYC_SUMMARY['app']['trigger']):+.2f}pp |
| BVN 通过率 | {pct(a['bvn_pass_rate'])} | {pct(h['bvn_pass_rate'])} | {h['bvn_pass_rate']-a['bvn_pass_rate']:.2f}pp |
| NIN 通过率 | {pct(a['nin_pass_rate'])} | {pct(h['nin_pass_rate'])} | {h['nin_pass_rate']-a['nin_pass_rate']:.2f}pp |
| 人脸成功率（请求口径） | {pct(a['face_success_request_rate'])} | {pct(h['face_success_request_rate'])} | {h['face_success_request_rate']-a['face_success_request_rate']:.2f}pp |
| 无最终结果率 | {pct(a['unresolved_rate'])} | {pct(h['unresolved_rate'])} | +{h['unresolved_rate']-a['unresolved_rate']:.2f}pp |
| 每位请求用户的人脸请求次数 | {a['request_per_requester']:.2f} | {h['request_per_requester']:.2f} | +{h['request_per_requester']-a['request_per_requester']:.2f} |

端到端成功率为 App {pct(a['e2e_rate'])}、H5 {pct(h['e2e_rate'])}。H5 的人脸请求率更高，因此不能用端到端结果覆盖其后段质量问题。

![端到端成功率趋势](03_端到端成功率趋势.png)

近两周整体端到端成功率从 {pct(k['early_e2e'])} 变为 {pct(k['late_e2e'])}，仅下降 {k['late_e2e']-k['early_e2e']:.2f} 个百分点；人脸请求成功率基本持平（{pct(k['early_face_success'])} → {pct(k['late_face_success'])}）。当前不是全链路突然恶化，优先应定位 H5 的 BVN、请求后无结果和重复请求。

## 3. 同期资金与提现背景

![全站提充比趋势](04_全站提充比趋势.png)

| 指标 | 8月13—19日 | 8月20—26日 | 变化 |
|---|---:|---:|---:|
| 加权 TC | {o['early_tc']:.2f}% | {o['late_tc']:.2f}% | {o['late_tc']-o['early_tc']:.2f}pp |
| 日均 TX 率 | {o['early_tx_rate']:.2f}% | {o['late_tx_rate']:.2f}% | {o['late_tx_rate']-o['early_tx_rate']:.2f}pp |
| 日均付费率 | {o['early_payment_rate']:.2f}% | {o['late_payment_rate']:.2f}% | {o['late_payment_rate']-o['early_payment_rate']:.2f}pp |
| 日均 ARPPU | {o['early_arppu']:.2f} | {o['late_arppu']:.2f} | {o['late_arppu']-o['early_arppu']:.2f} |

**观察结论：** 全站 TC、TX 率和付费率均轻微下降或基本稳定；本窗口没有支持“全站羊毛风险正在抬升”的证据。但该表是全站汇总，不能映射到人脸 KYC 成功用户。

## 4. 数据限制与风险判断边界

| 数据项 | 状态 | 本轮处理 |
|---|---|---|
| Metabase 提现触发人脸认证统计 | 可用（聚合） | 用于 KYC 漏斗、App/H5 对比和趋势 |
| 起源 BQ-TC详情 | 可用但筛选控件显示异常 | 仅按实际返回的 8月13—26 日行汇总，标记 `provisional` |
| 起源 BQ-TX分析 | 阻断 | 选择 14 日后仍返回 7 日窗口，不用于结论 |
| 起源 BQ-tc汇总请求 | 阻断 | 同样未按选定 14 日窗口返回，不用于结论 |
| 起源 BQ-羊毛分析 | 受限 | 包含用户、设备、IP、邮箱等敏感标识，本轮不读取或导出 |
| KYC 状态—充值—提现关联 | 阻断 | 无可验证关联键，不判断 KYC 用户是否混入刷子 |

## 5. 可执行优化建议

1. **P0：修复 H5 的人脸后段链路。** 按 BVN/NIN、相机授权、SDK 拉起、活体、人像比对、超时和退出拆分；优先核查 H5 BVN 通过率低、无最终结果率高、请求次数偏高的问题。
2. **P0：建立 KYC 与资金的受限聚合关联。** 最小链路为“人脸成功状态 → 成功现金充值 → 最终到账提现 → 有效真金下注 → 风控命中”，仅返回分组结果，不输出个人信息。
3. **P1：修复起源经济体系报表筛选。** `BQ-TX分析` 与 `tc汇总` 必须实际按所选日期返回结果；在筛选验收通过前，不允许进入羊毛专题报告。
4. **P1：把羊毛判断从单一 TC 升级为组合信号。** 仅当高 TC 同时伴随快速提现、低真实游戏参与、Bonus 依赖或规则命中时，才进入“待核查异常结构”。
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = derived()
    (OUT / "source_snapshot.json").write_text(
        json.dumps(
            {
                "period": data["period"],
                "sources": {
                    "metabase": "提现触发人脸认证统计（Question 233，可见聚合行）",
                    "origin": "BQ-TC详情（报表ID 99，可见聚合行）",
                },
                "data": data,
                "kyc_daily": KYC_DAILY,
                "origin_daily": ORIGIN_DAILY,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    draw_funnel()
    draw_platform_quality()
    draw_kyc_daily()
    draw_tc_trend()
    report = report_markdown(data)
    (OUT / "report.md").write_text(report, encoding="utf-8")
    archive = OUT.parents[1] / "knowledge" / "02-数据" / "Waje-KYC人脸与羊毛风险综合分析-2026-08-27.md"
    archive.write_text(report, encoding="utf-8")
    (OUT / "source_checks.json").write_text(
        json.dumps(
            {
                "period": data["period"],
                "metabase": {
                    "question": "提现触发人脸认证统计（Question 233）",
                    "returned_rows": 28,
                    "grain": "日期×包体",
                    "status": "provisional_aggregate_available",
                },
                "origin": {
                    "report": "BQ-TC详情（ID 99）",
                    "returned_rows": 14,
                    "grain": "日期×区服",
                    "status": "provisional_filter_display_mismatch",
                },
                "blocked": [
                    "BQ-TX分析：14日筛选未生效",
                    "BQ-tc汇总请求：14日筛选未生效",
                    "BQ-羊毛分析：用户级敏感字段，未读取",
                    "KYC状态—充值—最终提现：缺少可验证关联键",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

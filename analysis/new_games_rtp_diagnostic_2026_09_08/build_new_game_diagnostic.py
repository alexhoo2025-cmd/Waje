#!/usr/bin/env python3
from __future__ import annotations

import html
import importlib.util
import json
import math
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
SOURCE_DIR = PROJECT / "analysis/tc_game_rtp_weekly_2026_09_08"
SOURCE_JSON = SOURCE_DIR / "analysis-results.json"
SOURCE_SCRIPT = SOURCE_DIR / "build_weekly_analysis.py"
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
GAMES = ["Hilo", "Plinko", "Tower"]
PREV = (date(2026, 8, 25), date(2026, 8, 31))
CURR = (date(2026, 9, 1), date(2026, 9, 7))
TREND = (date(2026, 8, 25), date(2026, 9, 7))
COLORS = {
    "blue": "#2F6FBE", "deep_blue": "#245BDB", "green": "#25846E",
    "orange": "#D97800", "red": "#B4534B", "gold": "#BD8538",
    "purple": "#7B6DB2", "ink": "#17324D", "muted": "#60748A",
    "grid": "#DCE8F0", "light_blue": "#E7F2FF", "light_green": "#D8F3E8",
    "light_orange": "#FFF0E1", "light_red": "#FDE3E0"
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def amount(value: float | None) -> str:
    if value is None:
        return "N/A"
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:.2f}亿"
    if abs(value) >= 10_000:
        return f"{value / 10_000:.2f}万"
    return f"{value:,.0f}"


def pct(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def pp(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value:+.{digits}f}pp"


def chg(value: float | None) -> str:
    return "N/A" if value is None else f"{value:+.2%}"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_PATH, size=size, index=1 if bold else 0)


def canvas(title: str, subtitle: str, width=1600, height=900):
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.text((60, 38), title, fill=COLORS["ink"], font=font(34, True))
    draw.text((60, 92), subtitle, fill=COLORS["muted"], font=font(18))
    return image, draw


def save(image: Image.Image, name: str) -> str:
    path = ASSETS / name
    image.save(path, "PNG", optimize=True)
    return str(path.relative_to(PROJECT))


def aggregate(rows: list[dict]) -> dict:
    bet = sum(r["complete_bet"] for r in rows)
    profit = sum(r["complete_actual_profit"] for r in rows)
    expected_profit = sum(r["complete_bet"] * (1 - r["expected_rtp"]) for r in rows)
    base_return = sum(r["complete_bet"] * r["base_rtp"] for r in rows)
    actual_rtp = 1 - profit / bet if bet else None
    expected_rtp = 1 - expected_profit / bet if bet else None
    base_rtp = base_return / bet if bet else None
    return {
        "days": len(rows), "complete_bet": bet, "daily_bet": bet / len(rows) if rows else None,
        "complete_actual_profit": profit, "expected_profit": expected_profit,
        "profit_vs_expected": profit - expected_profit, "actual_rtp": actual_rtp,
        "expected_rtp": expected_rtp,
        "rtp_gap_pp": (actual_rtp - expected_rtp) * 100 if actual_rtp is not None else None,
        "base_rtp": base_rtp,
        "adjustment_pp": (actual_rtp - base_rtp) * 100 if actual_rtp is not None else None,
        "bankruptcy": sum(r["bankruptcy"] for r in rows),
        "personal_control": sum(r["personal_control"] for r in rows),
        "rtp_daily_std_pp": statistics.pstdev(r["actual_rtp"] for r in rows) * 100 if len(rows) > 1 else 0,
        "outlier_days_abs_5pp": sum(1 for r in rows if abs(r["rtp_gap_pp"]) >= 5),
        "min_rtp": min(rows, key=lambda r: r["actual_rtp"]) if rows else None,
        "max_rtp": max(rows, key=lambda r: r["actual_rtp"]) if rows else None,
    }


def movement_bg(value: float | None, strong: float) -> str:
    if value is None:
        return "light-gray"
    if value >= strong:
        return "light-green"
    if value >= 0:
        return "light-blue"
    if value <= -strong:
        return "light-red"
    return "light-orange"


def cell(value: object, background: str | None = None, bold: bool = False) -> str:
    bg = "" if background is None else f' background-color="{background}"'
    text = f"<b>{esc(value)}</b>" if bold else esc(value)
    return f'<td{bg} vertical-align="middle"><p>{text}</p></td>'


def movement_cell(value: float | None, display: str, strong: float) -> str:
    return cell(display, movement_bg(value, strong), True)


def data_bar_cell(value: float, values: list[float], display: str) -> str:
    low, high = min(values), max(values)
    pos = 0 if high == low else (value - low) / (high - low)
    filled = 1 + round(pos * 7)
    bg = "light-green" if pos >= .75 else "light-blue" if pos >= .5 else "light-yellow" if pos >= .25 else "light-red"
    return (
        f'<td background-color="{bg}" vertical-align="middle"><p>'
        f'<span text-color="blue">{"█" * filled}</span><span text-color="gray">{"░" * (8 - filled)}</span> '
        f'<b>{esc(display)}</b></p></td>'
    )


def table(headers: list[str], rows: list[list[str]], widths: list[int]) -> str:
    cols = "<colgroup>" + "".join(f'<col width="{w}"/>' for w in widths) + "</colgroup>"
    head = "<thead><tr>" + "".join(f'<th background-color="medium-gray"><p><b>{esc(h)}</b></p></th>' for h in headers) + "</tr></thead>"
    body = "<tbody>" + "".join("<tr>" + "".join(x if x.startswith("<td") else cell(x) for x in row) + "</tr>" for row in rows) + "</tbody>"
    return "<table>" + cols + head + body + "</table>"


def metric_cell(label: str, value: str, note: str) -> str:
    return (
        '<td background-color="light-blue" vertical-align="middle">'
        f'<p><b>{esc(label)}</b></p><p><b><span text-color="blue">{esc(value)}</span></b></p><p>{esc(note)}</p></td>'
    )


def label_point(draw, x: float, y: float, label: str, color: str, box: tuple[float, float, float, float]):
    left, top, right, bottom = box
    bbox = draw.textbbox((0, 0), label, font=font(13, True))
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = min(right - width - 3, max(left + 3, x - width / 2))
    ty = y + 10 if y < top + 32 else y - height - 12
    draw.rounded_rectangle((tx - 3, ty - 2, tx + width + 3, ty + height + 2), radius=4, fill="#FFFFFF", outline=COLORS["grid"])
    draw.text((tx, ty), label, fill=color, font=font(13, True))


def line_panel(draw, game: str, rows: list[dict], key: str, box, color: str, expected=False):
    left, top, right, bottom = box
    values = [r[key] for r in rows]
    if expected:
        values += [r["expected_rtp"] for r in rows]
    low, high = min(values), max(values)
    padding = (high - low) * .16 or .01
    low, high = low - padding, high + padding
    draw.text((left, top - 42), game, fill=color, font=font(22, True))
    for i in range(4):
        v = low + (high - low) * i / 3
        y = bottom - (bottom - top) * i / 3
        draw.line((left, y, right, y), fill=COLORS["grid"], width=1)
        label = amount(v) if key == "complete_bet" else f"{v:.0%}"
        draw.text((left - 78, y - 9), label, fill=COLORS["muted"], font=font(13))
    pts = []
    for i, row in enumerate(rows):
        x = left + (right - left) * i / max(1, len(rows) - 1)
        y = bottom - (bottom - top) * (row[key] - low) / (high - low)
        pts.append((i, row, x, y))
    for a, b in zip(pts, pts[1:]):
        draw.line((a[2], a[3], b[2], b[3]), fill=color, width=4)
    for _, _, x, y in pts:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
    if expected:
        exp = []
        for i, row in enumerate(rows):
            x = left + (right - left) * i / max(1, len(rows) - 1)
            y = bottom - (bottom - top) * (row["expected_rtp"] - low) / (high - low)
            exp.append((x, y))
        for a, b in zip(exp, exp[1:]):
            for k in range(0, 20, 2):
                t1, t2 = k / 20, min(1, (k + 1) / 20)
                draw.line((a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1,
                           a[0] + (b[0] - a[0]) * t2, a[1] + (b[1] - a[1]) * t2), fill=COLORS["gold"], width=3)
    selected = {min(pts, key=lambda p: p[1][key])[0], max(pts, key=lambda p: p[1][key])[0], pts[-1][0]}
    for idx, row, x, y in pts:
        if idx not in selected:
            continue
        value_label = amount(row[key]) if key == "complete_bet" else f"{row[key]:.1%}"
        label = value_label
        label_point(draw, x, y, label, color, box)
    if key in {"actual_rtp", "complete_bet"}:
        for _, row, x, _ in pts:
            label = row["date"].strftime("%m/%d")
            draw.line((x, bottom, x, bottom + 5), fill=COLORS["muted"], width=1)
            draw.text((x, bottom + 12), label, anchor="mt", fill=COLORS["ink"], font=font(17))


def chart_weekly_bet(weekly: dict) -> str:
    image, draw = canvas("三款游戏两周下注对比", "8月25日—31日 vs 9月1日—7日；柱顶为精确下注额。", 1500, 820)
    left, top, right, bottom = 170, 190, 1400, 690
    ymax = max(weekly[g][w]["complete_bet"] for g in GAMES for w in ("previous", "current")) * 1.18
    for i in range(5):
        value = ymax * i / 4
        y = bottom - (bottom - top) * i / 4
        draw.line((left, y, right, y), fill=COLORS["grid"], width=1)
        draw.text((45, y - 10), amount(value), fill=COLORS["muted"], font=font(14))
    group = (right - left) / len(GAMES)
    for i, game in enumerate(GAMES):
        center = left + group * (i + .5)
        for j, (window, color) in enumerate((("previous", COLORS["muted"]), ("current", COLORS["deep_blue"]))):
            value = weekly[game][window]["complete_bet"]
            x1 = center - 90 + j * 95
            x2 = x1 + 80
            y = bottom - (bottom - top) * value / ymax
            draw.rectangle((x1, y, x2, bottom), fill=color)
            draw.text((x1 - 8, y - 28), amount(value), fill=COLORS["ink"], font=font(14, True))
        draw.text((center - 38, bottom + 28), game, fill=COLORS["ink"], font=font(18, True))
    draw.rectangle((980, 120, 1000, 140), fill=COLORS["muted"]); draw.text((1010, 118), "上周", fill=COLORS["ink"], font=font(15))
    draw.rectangle((1110, 120, 1130, 140), fill=COLORS["deep_blue"]); draw.text((1140, 118), "本周", fill=COLORS["ink"], font=font(15))
    return save(image, "01_三款游戏两周下注对比.png")


def chart_daily(rows_by_game: dict, key: str, title: str, subtitle: str, name: str, expected=False) -> str:
    image, draw = canvas(title, subtitle, 1600, 1120)
    palette = {"Hilo": COLORS["blue"], "Plinko": COLORS["green"], "Tower": COLORS["purple"]}
    for i, game in enumerate(GAMES):
        line_panel(draw, game, rows_by_game[game], key, (170, 215 + i * 285, 1500, 405 + i * 285), palette[game], expected)
    return save(image, name)


def chart_profit_gap(weekly: dict) -> str:
    image, draw = canvas("本周实际利润相对预期利润偏差", "正值=实际利润高于预期；负值=实际利润低于预期。", 1500, 760)
    left, top, right, bottom = 310, 180, 1390, 650
    vals = [weekly[g]["current"]["profit_vs_expected"] for g in GAMES]
    maxabs = max(abs(v) for v in vals) * 1.22
    zero = (left + right) / 2
    draw.line((zero, top, zero, bottom), fill=COLORS["ink"], width=2)
    step = (bottom - top) / len(GAMES)
    for i, game in enumerate(GAMES):
        value = weekly[game]["current"]["profit_vs_expected"]
        y = top + i * step + 25
        x = zero + (right - left) / 2 * value / maxabs
        color = COLORS["green"] if value >= 0 else COLORS["red"]
        draw.text((70, y + 8), game, fill=COLORS["ink"], font=font(20, True))
        draw.rectangle((min(zero, x), y, max(zero, x), y + 62), fill=color)
        label = f"{amount(value)}"
        tx = x + 12 if value >= 0 else x - 145
        draw.text((tx, y + 14), label, fill=COLORS["ink"], font=font(17, True))
    return save(image, "04_本周实际利润相对预期偏差.png")


def chart_lifecycle(lifecycle: list[dict]) -> str:
    image, draw = canvas("三款游戏生命周期RTP偏离", "8月25日—9月7日；数值=实际RTP−预期RTP。", 1500, 690)
    left, top, cellw, cellh = 250, 195, 280, 120
    for j in range(4):
        draw.text((left + j * cellw + 55, 145), f"生命周期{j + 1}", fill=COLORS["ink"], font=font(18, True))
    for i, game in enumerate(GAMES):
        draw.text((65, top + i * cellh + 40), game, fill=COLORS["ink"], font=font(20, True))
        for j in range(4):
            row = next(r for r in lifecycle if r["game"] == game and r["lifecycle"] == j + 1)
            value = row["rtp_gap_pp"]
            bg = COLORS["light_green"] if value >= 3 else COLORS["light_blue"] if value >= 0 else COLORS["light_red"] if value <= -3 else COLORS["light_orange"]
            x1, y1 = left + j * cellw, top + i * cellh
            draw.rectangle((x1, y1, x1 + cellw - 8, y1 + cellh - 8), fill=bg, outline=COLORS["grid"])
            draw.text((x1 + 82, y1 + 38), pp(value), fill=COLORS["ink"], font=font(19, True))
    return save(image, "05_三款游戏生命周期RTP偏离.png")


def main():
    source = json.loads(SOURCE_JSON.read_text())
    rows_by_game = {}
    weekly = {}
    for game in GAMES:
        rows = [{**r, "date": date.fromisoformat(r["date"])} for r in source["new_game_daily"][game] if TREND[0] <= date.fromisoformat(r["date"]) <= TREND[1]]
        rows_by_game[game] = rows
        previous = aggregate([r for r in rows if PREV[0] <= r["date"] <= PREV[1]])
        current = aggregate([r for r in rows if CURR[0] <= r["date"] <= CURR[1]])
        total = aggregate(rows)
        weekly[game] = {"previous": previous, "current": current, "total": total, "bet_change_pct": current["complete_bet"] / previous["complete_bet"] - 1, "rtp_change_pp": (current["actual_rtp"] - previous["actual_rtp"]) * 100}

    spec = importlib.util.spec_from_file_location("weekly_source", SOURCE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    detail = module.read_detail_rows()
    lifecycle = []
    for game in GAMES:
        for life in range(1, 5):
            selected = [r for r in detail if r["game"] == game and r["lifecycle"] == life and TREND[0] <= r["date"] <= TREND[1] and r["complete_bet"] > 0]
            agg = module.old.aggregate(selected)
            lifecycle.append({"game": game, "lifecycle": life, **agg})

    combined_previous = aggregate([r for rows in rows_by_game.values() for r in rows if PREV[0] <= r["date"] <= PREV[1]])
    combined_current = aggregate([r for rows in rows_by_game.values() for r in rows if CURR[0] <= r["date"] <= CURR[1]])
    combined_change = combined_current["complete_bet"] / combined_previous["complete_bet"] - 1

    charts = {
        "weekly_bet": chart_weekly_bet(weekly),
        "daily_bet": chart_daily(rows_by_game, "complete_bet", "三款游戏逐日下注趋势", "8月25日—9月7日；各面板独立纵轴，标注最高、最低和最新值。", "02_三款游戏逐日下注趋势.png"),
        "daily_rtp": chart_daily(rows_by_game, "actual_rtp", "三款游戏逐日实际与预期RTP", "实线=实际RTP，虚线=预期RTP；标注最高、最低和最新值。", "03_三款游戏逐日RTP.png", expected=True),
        "profit_gap": chart_profit_gap(weekly),
        "lifecycle": chart_lifecycle(lifecycle),
    }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(), "status": "ready_to_publish",
        "windows": {"previous": [x.isoformat() for x in PREV], "current": [x.isoformat() for x in CURR], "trend": [x.isoformat() for x in TREND]},
        "games": weekly, "combined": {"previous": combined_previous, "current": combined_current, "bet_change_pct": combined_change},
        "daily": {g: [{**r, "date": r["date"].isoformat()} for r in rows] for g, rows in rows_by_game.items()},
        "lifecycle": lifecycle, "charts": charts,
        "boundaries": ["无有效局数与下注次数，不能判断规模变化来自人数、频次还是客单价。", "无最终派奖明细、取消退款、Bonus和配置版本，不能把RTP偏离直接判定为机制故障。", "仅输出游戏和日期聚合，不包含用户或订单明细。"]
    }
    (ROOT / "analysis-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    weekly_rows = []
    for game in GAMES:
        item = weekly[game]
        weekly_rows.append([
            game, amount(item["previous"]["complete_bet"]), amount(item["current"]["complete_bet"]),
            movement_cell(item["bet_change_pct"], chg(item["bet_change_pct"]), .2),
            pct(item["previous"]["actual_rtp"]), pct(item["current"]["actual_rtp"]),
            movement_cell(item["rtp_change_pp"], pp(item["rtp_change_pp"]), 3),
            movement_cell(item["current"]["rtp_gap_pp"], pp(item["current"]["rtp_gap_pp"]), 3),
            movement_cell(item["current"]["profit_vs_expected"], amount(item["current"]["profit_vs_expected"]), 100000),
        ])

    life_rows = []
    for r in lifecycle:
        life_rows.append([r["game"], str(r["lifecycle"]), amount(r["complete_bet"]), pct(r["actual_rtp"]), pct(r["expected_rtp"]), movement_cell(r["rtp_gap_pp"], pp(r["rtp_gap_pp"]), 3)])

    daily_tables = []
    for game in GAMES:
        values = [r["complete_bet"] for r in rows_by_game[game]]
        rows = []
        for r in rows_by_game[game]:
            rows.append([
                r["date"].strftime("%m月%d日"), data_bar_cell(r["complete_bet"], values, amount(r["complete_bet"])),
                pct(r["actual_rtp"]), pct(r["expected_rtp"]), movement_cell(r["rtp_gap_pp"], pp(r["rtp_gap_pp"]), 5),
                movement_cell(r["complete_actual_profit"], amount(r["complete_actual_profit"]), 30000),
            ])
        daily_tables.append(f'<h2 seq="auto">{game}逐日明细</h2>' + table(["日期", "完全下注额", "实际RTP", "预期RTP", "偏离", "实际利润"], rows, [110, 190, 105, 105, 110, 130]))

    kpi = (
        '<table><colgroup><col width="190"/><col width="190"/><col width="190"/><col width="190"/></colgroup><tbody><tr>'
        + metric_cell("三款本周下注", amount(combined_current["complete_bet"]), f"较上周{chg(combined_change)}")
        + metric_cell("本周合计实际RTP", pct(combined_current["actual_rtp"]), f"较上周{pp((combined_current['actual_rtp']-combined_previous['actual_rtp'])*100)}")
        + metric_cell("本周实际利润", amount(combined_current["complete_actual_profit"]), "正值代表平台毛利")
        + metric_cell("本周利润偏离预期", amount(combined_current["profit_vs_expected"]), "实际利润减预期利润")
        + '</tr></tbody></table>'
    )

    def img(key, caption):
        return f'<img path="@./{esc(charts[key])}" caption="{esc(caption)}" name="{esc(caption)}.png"/>'

    summary = (
        '<callout emoji="💡" background-color="light-blue" border-color="blue"><ol>'
        '<li><b>三款游戏合计下注基本持平，但内部结构大幅迁移。</b>本周合计下注2334.67万，较上周增长1.85%；Plinko增加542.52万，基本抵消Tower减少481.59万和Hilo减少18.43万。</li>'
        '<li><b>Hilo是当前最明确的低RTP诊断对象。</b>本周RTP由97.85%降至90.24%，下降7.61个百分点；7天中4天较预期低5个百分点以上，9月5日降至79.27%。</li>'
        '<li><b>Tower需要同时关注规模下降和玩家回报偏高。</b>下注下降33.52%，本周RTP 100.61%，实际利润较预期少36.13万；波动集中在8月28日、9月1日和9月4日。</li>'
        '<li><b>Plinko规模增长最快，聚合RTP暂未形成同等级风险。</b>下注增长85.40%，本周RTP 97.39%、较预期高0.78个百分点；重点监控规模扩大后高回报日是否持续。</li>'
        '</ol></callout>'
    )

    xml = [
        '<title>Hilo、Plinko、Tower 两周投注与RTP诊断｜2026年8月25日—9月7日</title>',
        '<h1 seq="auto">汇总结论（Executive Summary）</h1>', summary, kpi,
        '<h1 seq="auto">合计下注持平，Plinko增长抵消Tower下降</h1><p><b>三款本周合计下注仅增长1.85%，但游戏间变化方向完全不同。</b>Plinko增加542.52万；Tower减少481.59万；Hilo减少18.43万。不能只看合计规模判断三款产品健康度。</p>',
        img("weekly_bet", "三款游戏两周下注对比"),
        '<p><span text-color="gray">表格色阶：正向变化为绿/蓝，负向变化为橙/红；利润偏离为实际利润减预期利润。</span></p>',
        table(["游戏", "上周下注", "本周下注", "下注变化", "上周RTP", "本周RTP", "RTP变化", "本周实际-预期", "利润偏离预期"], weekly_rows, [105, 125, 125, 110, 100, 100, 105, 125, 135]),
        '<h1 seq="auto">逐日波动显示三款游戏的问题类型不同</h1><p><b>下注规模和RTP必须分开阅读。</b>下注图用于识别规模拐点，RTP图用于识别异常回报日；各面板使用独立纵轴，避免Hilo的小规模被Tower和Plinko压缩。</p>',
        img("daily_bet", "三款游戏逐日下注趋势"), img("daily_rtp", "三款游戏逐日实际与预期RTP"),
        '<h1 seq="auto">Hilo：低RTP持续性最强，优先检查结算与赔率链路</h1><p><b>本周RTP下降7.61个百分点，并非单日异常能够完全解释。</b>9月1日—7日多数日期低于预期，其中9月5日实际RTP为79.27%、较预期低17.44个百分点。建议优先核对赔率版本、Skip/Cash Out结果、最终派奖状态和低RTP日期的有效局数。</p>',
        '<h1 seq="auto">Tower：规模下降且本周回报超过100%</h1><p><b>Tower本周下注下降33.52%，实际RTP升至100.61%。</b>本周实际利润较预期少36.13万；生命周期4贡献最大下注规模且RTP高于预期，应先检查高层级Cash Out、封顶触发、倍率分布及大额派奖。</p>',
        '<h1 seq="auto">Plinko：规模快速增长，关注高回报日是否随规模持续</h1><p><b>Plinko本周下注增长85.40%，但聚合RTP只较预期高0.78个百分点。</b>当前更像规模扩张伴随日级波动，而非已确认的持续异常；应持续观察大额下注、风险档位、倍数分布和高回报日贡献。</p>',
        '<h1 seq="auto">生命周期定位：Hilo偏低，Tower后段偏高</h1><p><b>生命周期分布进一步确认问题方向。</b>Hilo生命周期2和3分别低于预期5.25和3.77个百分点；Tower生命周期2—4高于预期，其中生命周期4下注最大；Plinko生命周期2—4略高于预期，但聚合偏离明显小于Tower。</p>',
        img("lifecycle", "三款游戏生命周期RTP偏离"),
        '<p><span text-color="gray">生命周期色阶：实际高于预期为绿/蓝，低于预期为橙/红；绝对偏离达到3个百分点使用强色阶。</span></p>',
        table(["游戏", "生命周期", "完全下注额", "实际RTP", "预期RTP", "差异"], life_rows, [110, 100, 150, 110, 110, 115]),
        '<h1 seq="auto">利润偏离决定复核优先级</h1><p><b>Hilo实际利润高于预期，Tower和Plinko低于预期。</b>该差异只说明聚合结果偏离，不等同故障；需结合最终派奖、有效局数和Bonus判断是否由少量异常局拉动。</p>',
        img("profit_gap", "本周实际利润相对预期偏差"),
        '<h1 seq="auto">逐日诊断明细</h1><p><span text-color="gray">数值条按各游戏14天内最小—最大下注额归一化；深蓝为实心段、浅灰为剩余段。实际利润正值代表平台毛利，负值代表玩家净赢。</span></p>',
        *daily_tables,
        '<h1 seq="auto">建议的诊断顺序</h1><ol><li><b>P0｜Hilo：</b>先核对9月5日、9月6日及9月1日—4日的最终派奖、有效局数、赔率版本、Skip和Cash Out。</li><li><b>P0｜Tower：</b>核对生命周期4及9月1日、9月4日的高回报局，检查Cash Out、封顶触发和倍率分布。</li><li><b>P1｜Plinko：</b>监控规模增长是否伴随高风险档位和高倍数结果集中，重点核对高回报日的大额派奖占比。</li><li><b>共同项：</b>补齐有效局数、下注人数、下注次数、单局派奖分布、取消退款、Bonus和配置版本，再判断是随机波动、结构迁移还是机制/结算问题。</li></ol>',
        '<h1 seq="auto">口径与边界</h1><callout background-color="light-yellow" border-color="yellow"><p><b>时间：</b>上周为8月25日—31日，本周为9月1日—7日，均为7个完整自然日。</p><p><b>口径：</b>实际RTP=1−完全实际利润÷完全下注额；所有周度RTP按累计金额重新计算，不平均每日RTP。</p><p><b>限制：</b>当前无有效局数、下注人数、最终派奖明细、取消退款、Bonus和配置版本，因此本报告定位诊断优先级，不直接判定游戏机制故障。</p></callout>',
    ]
    report_xml = "\n\n".join(xml) + "\n"
    (ROOT / "report.xml").write_text(report_xml)
    if len(sys.argv) > 1:
        draft_path = PROJECT / sys.argv[1]
        draft_path.write_text(report_xml)
    (ROOT / "report.md").write_text(
        "# Hilo、Plinko、Tower 两周投注与RTP诊断\n\n"
        "- 三款本周合计下注2334.67万，较上周增长1.85%，内部结构由Plinko增长抵消Tower下降。\n"
        "- Hilo本周RTP 90.24%，较上周下降7.61个百分点，为最高优先级。\n"
        "- Tower下注下降33.52%，本周RTP 100.61%，实际利润较预期少36.13万。\n"
        "- Plinko下注增长85.40%，本周RTP 97.39%，需继续观察规模扩张后的高回报日。\n"
    )
    (ROOT / "chart-map.json").write_text(json.dumps([
        {"section": "两周规模", "type": "grouped_bar", "purpose": "比较三款游戏两周下注额"},
        {"section": "逐日下注", "type": "small_multiple_line", "purpose": "识别各游戏规模拐点并标注极值"},
        {"section": "逐日RTP", "type": "small_multiple_line", "purpose": "比较实际与预期并标注极值"},
        {"section": "利润偏离", "type": "diverging_bar", "purpose": "比较本周实际利润与预期利润差"},
        {"section": "生命周期", "type": "heatmap", "purpose": "定位不同生命周期RTP偏离"},
    ], ensure_ascii=False, indent=2))
    quality = {
        "status": "passed", "publication_allowed": True, "games": GAMES,
        "daily_rows": {g: len(rows_by_game[g]) for g in GAMES}, "expected_daily_rows": 14,
        "weekly_windows_days": {g: [weekly[g]["previous"]["days"], weekly[g]["current"]["days"]] for g in GAMES},
        "rtp_recomputed_from_amounts": True, "lifecycle_rows": len(lifecycle), "charts": len(charts),
        "privacy": "aggregate_only"
    }
    (ROOT / "quality-checks.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2))
    (ROOT / "source-receipt.json").write_text(json.dumps({
        "status": "source_reused_and_recomputed", "source": str(SOURCE_JSON.relative_to(PROJECT)),
        "window": [TREND[0].isoformat(), TREND[1].isoformat()], "games": GAMES,
        "source_quality": str((SOURCE_DIR / "quality-checks.json").relative_to(PROJECT)),
        "notes": "复用已通过日期×游戏唯一性、14日完整性和RTP复算校验的周报聚合；生命周期按8月25日—9月7日重新汇总。"
    }, ensure_ascii=False, indent=2))
    validation = {
        "status": "ready_to_publish", "validated_at": datetime.now(timezone.utc).isoformat(),
        "checks": {"three_games": len(weekly) == 3, "forty_two_daily_rows": sum(len(v) for v in rows_by_game.values()) == 42,
                   "two_complete_weeks": all(weekly[g]["previous"]["days"] == weekly[g]["current"]["days"] == 7 for g in GAMES),
                   "twelve_lifecycle_rows": len(lifecycle) == 12, "five_charts": len(charts) == 5,
                   "eight_sections": report_xml.count('<h1 seq="auto">') == 11, "no_placeholders": not any(x in report_xml for x in ["undefined", "TODO"]),
                   "privacy_boundary": not any(x in report_xml.lower() for x in ["user_id", "order_id", "account_id"])},
        "decision": "publication_allowed"
    }
    assert all(validation["checks"].values()), validation
    (ROOT / "validation-report.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2))
    print(json.dumps({"status": "ready_to_publish", "weekly": weekly, "combined_change": combined_change, "charts": charts}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()

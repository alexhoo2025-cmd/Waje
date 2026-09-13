#!/usr/bin/env python3
"""Build a concise self-contained EasyWin 30-day RTP HTML report."""

from __future__ import annotations

import csv
import datetime as dt
import html
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TITLE = "EasyWin 30日累计RTP 111.41%，高回报集中在少数日期"


def number(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def load_rows() -> list[dict[str, Any]]:
    with (OUT / "easywin-daily.csv").open(encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append({
                "date": row["date"],
                "base_bet": number(row["base_bet"]),
                "actual_profit": number(row["actual_profit"]),
                "actual_rtp": number(row["actual_rtp"]),
                "status": row["status"],
            })
    return rows


def compact(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    sign = "-" if value < 0 else ""
    absolute = abs(value)
    if absolute >= 1e6:
        return f"{sign}{absolute / 1e6:.2f}M"
    if absolute >= 1e3:
        return f"{sign}{absolute / 1e3:.1f}k"
    return f"{value:,.2f}"


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def date_label(value: str) -> str:
    return value[5:].replace("-", "/")


def svg_rtp(rows: list[dict[str, Any]]) -> str:
    width, height = 1120, 370
    left, right, top, bottom = 70, 24, 36, 68
    plot_w, plot_h = width - left - right, height - top - bottom
    values = [row["actual_rtp"] * 100 for row in rows if row["actual_rtp"] is not None]
    low = math.floor(min(values) / 20) * 20
    high = math.ceil(max(values) / 20) * 20
    low = min(low, 80)
    high = max(high, 120)
    x = lambda index: left + plot_w * index / (len(rows) - 1)
    y = lambda value: top + plot_h * (high - value) / (high - low)
    parts = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="EasyWin每日实际RTP趋势"><title>EasyWin每日实际RTP趋势</title>']
    for index in range(6):
        tick = low + (high - low) * index / 5
        yy = y(tick)
        parts.append(f'<line class="grid" x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}"/><text class="axis" x="{left-10}" y="{yy+4:.1f}" text-anchor="end">{tick:.0f}%</text>')
    if low <= 100 <= high:
        yy = y(100)
        parts.append(f'<line class="reference" x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}"/><text class="reference-label" x="{width-right-4}" y="{yy-7:.1f}" text-anchor="end">100%</text>')
    segments: list[list[tuple[float, float, dict[str, Any]]]] = []
    current: list[tuple[float, float, dict[str, Any]]] = []
    for index, row in enumerate(rows):
        if row["actual_rtp"] is None:
            if current:
                segments.append(current)
                current = []
            parts.append(f'<line class="missing" x1="{x(index):.1f}" y1="{top}" x2="{x(index):.1f}" y2="{top+plot_h}"/><text class="missing-label" x="{x(index):.1f}" y="{top+14}" text-anchor="middle">缺失</text>')
            continue
        current.append((x(index), y(row["actual_rtp"] * 100), row))
    if current:
        segments.append(current)
    for segment in segments:
        path = " ".join(("M" if index == 0 else "L") + f"{px:.1f},{py:.1f}" for index, (px, py, _) in enumerate(segment))
        parts.append(f'<path class="rtp-line" d="{path}"/>')
        for px, py, row in segment:
            parts.append(f'<circle class="rtp-point" cx="{px:.1f}" cy="{py:.1f}" r="4"><title>{row["date"]}：RTP {pct(row["actual_rtp"])}；下注 {row["base_bet"]:,.2f}；盈利 {row["actual_profit"]:,.2f}</title></circle>')
    complete = [row for row in rows if row["actual_rtp"] is not None]
    annotations = [
        (max(complete, key=lambda row: row["actual_rtp"]), "最高"),
        (min(complete, key=lambda row: row["actual_rtp"]), "最低"),
        (complete[-1], "最新"),
    ]
    for row, label in annotations:
        index = rows.index(row)
        parts.append(f'<text class="point-label" x="{x(index):.1f}" y="{y(row["actual_rtp"]*100)-12:.1f}" text-anchor="middle">{label} {pct(row["actual_rtp"])}</text>')
    tick_indices = sorted({0, len(rows)-1, *range(2, len(rows), 4)})
    for index in tick_indices:
        parts.append(f'<text class="axis" x="{x(index):.1f}" y="{height-27}" text-anchor="middle">{date_label(rows[index]["date"])}</text>')
    parts.append('<text class="axis-title" x="18" y="190" transform="rotate(-90 18 190)" text-anchor="middle">实际RTP</text></svg>')
    return "".join(parts)


def svg_amounts(rows: list[dict[str, Any]]) -> str:
    width, height = 1120, 560
    left, right = 70, 24
    plot_w = width - left - right
    x = lambda index: left + plot_w * index / len(rows)
    bar_w = plot_w / len(rows) * .66
    bet_top, bet_height = 44, 180
    profit_top, profit_height = 320, 170
    complete = [row for row in rows if row["status"] == "complete"]
    max_bet = max(row["base_bet"] for row in complete)
    max_profit = max(abs(row["actual_profit"]) for row in complete)
    zero_y = profit_top + profit_height / 2
    parts = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="EasyWin每日下注额和实际盈利"><title>EasyWin每日下注额和实际盈利</title>']
    parts.append(f'<text class="panel-title" x="{left}" y="22">每日基础下注额</text><line class="grid" x1="{left}" y1="{bet_top+bet_height}" x2="{width-right}" y2="{bet_top+bet_height}"/>')
    for index, row in enumerate(rows):
        if row["base_bet"] is None:
            continue
        bar_h = row["base_bet"] / max_bet * bet_height
        xx = x(index) + (plot_w / len(rows) - bar_w) / 2
        yy = bet_top + bet_height - bar_h
        parts.append(f'<rect class="bet-bar" x="{xx:.1f}" y="{yy:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3"><title>{row["date"]}：下注 {row["base_bet"]:,.2f}</title></rect>')
    peak = max(complete, key=lambda row: row["base_bet"])
    peak_index = rows.index(peak)
    parts.append(f'<text class="point-label" x="{x(peak_index)+plot_w/len(rows)/2:.1f}" y="{bet_top+bet_height-peak["base_bet"]/max_bet*bet_height-10:.1f}" text-anchor="middle">最高 {compact(peak["base_bet"])}</text>')
    parts.append(f'<text class="panel-title" x="{left}" y="{profit_top-24}">每日基础实际盈利</text><line class="zero" x1="{left}" y1="{zero_y}" x2="{width-right}" y2="{zero_y}"/><text class="zero-label" x="{width-right}" y="{zero_y-7}" text-anchor="end">0</text>')
    for index, row in enumerate(rows):
        if row["actual_profit"] is None:
            continue
        magnitude = abs(row["actual_profit"]) / max_profit * (profit_height / 2 - 8)
        xx = x(index) + (plot_w / len(rows) - bar_w) / 2
        yy = zero_y - magnitude if row["actual_profit"] >= 0 else zero_y
        cls = "profit-positive" if row["actual_profit"] >= 0 else "profit-negative"
        parts.append(f'<rect class="{cls}" x="{xx:.1f}" y="{yy:.1f}" width="{bar_w:.1f}" height="{magnitude:.1f}" rx="3"><title>{row["date"]}：盈利 {row["actual_profit"]:,.2f}；RTP {pct(row["actual_rtp"])}</title></rect>')
    tick_indices = sorted({0, len(rows)-1, *range(2, len(rows), 4)})
    for index in tick_indices:
        parts.append(f'<text class="axis" x="{x(index)+plot_w/len(rows)/2:.1f}" y="{height-22}" text-anchor="middle">{date_label(rows[index]["date"])}</text>')
    parts.append('</svg>')
    return "".join(parts)


def table_rows(rows: list[dict[str, Any]]) -> str:
    output = []
    for row in rows:
        if row["status"] != "complete":
            output.append(f'<tr class="missing-row"><td>{row["date"]}</td><td colspan="3">缺失</td></tr>')
            continue
        profit_class = "negative" if row["actual_profit"] < 0 else "positive"
        rtp_class = "rtp-high" if row["actual_rtp"] > 1 else ""
        output.append(
            f'<tr><td>{row["date"]}</td><td>{row["base_bet"]:,.2f}</td>'
            f'<td class="{profit_class}">{row["actual_profit"]:,.2f}</td>'
            f'<td class="{rtp_class}">{pct(row["actual_rtp"])}</td></tr>'
        )
    return "".join(output)


def build_artifact(rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    complete = [row for row in rows if row["status"] == "complete"]
    datasets = {
        "daily": [{**row, "payout": None if row["base_bet"] is None else row["base_bet"] - row["actual_profit"]} for row in rows],
        "daily_valid": [{**row, "payout": row["base_bet"] - row["actual_profit"]} for row in complete],
        "summary": [{
            "total_base_bet": summary["metrics"]["total_base_bet"],
            "total_actual_profit": summary["metrics"]["total_actual_profit"],
            "total_payout": summary["metrics"]["total_base_bet"] - summary["metrics"]["total_actual_profit"],
            "cumulative_actual_rtp": summary["metrics"]["cumulative_actual_rtp"],
            "complete_days": summary["coverage"]["complete_days"],
        }],
    }
    source = {
        "id": "lifecycle-game-summary",
        "label": "生命周期价值飞书文档回读 revision 1608",
        "path": summary["source"]["path"],
        "query": {"engine": "Lark Sheets readback", "description": "EasyWin分游戏日汇总；17个日期与本地原始快照交叉一致。", "tables_used": ["生命周期奖池分游戏汇总"]},
    }
    contract = {
        "type": "business",
        "language": "zh",
        "population": "EasyWin分游戏日汇总",
        "period": "2026-08-12—2026-09-10（香港时间），29/30日有效",
        "timezone": "Asia/Hong_Kong",
        "metrics": [
            {"dataset": "daily_valid", "field": "base_bet", "kind": "sum", "unit": "源表单位", "scale": "native", "definition": "每日基础下注额。"},
            {"dataset": "daily_valid", "field": "actual_profit", "kind": "sum", "unit": "源表单位", "scale": "native", "definition": "每日基础实际盈利。"},
            {"dataset": "daily_valid", "field": "actual_rtp", "kind": "ratio", "unit": "%", "scale": "fraction", "definition": "每日基础返奖额除以基础下注额。", "denominator": "当日基础下注额"},
            {"dataset": "summary", "field": "cumulative_actual_rtp", "kind": "ratio", "unit": "%", "scale": "fraction", "definition": "窗口累计基础返奖额除以累计基础下注额。", "denominator": "29个有效日累计基础下注额"},
        ],
        "assertions": [
            {"kind": "ratio", "dataset": "daily_valid", "numerator": "payout", "denominator": "base_bet", "actual": "actual_rtp", "tolerance": 1e-10},
            {"kind": "ratio", "dataset": "summary", "numerator": "total_payout", "denominator": "total_base_bet", "actual": "cumulative_actual_rtp", "tolerance": 1e-10},
        ],
        "decisions": {"missing_date": {"status": "confirmed", "value": "2026-09-03保留为空"}, "amount_unit": {"status": "confirmed", "value": "沿用源表单位"}},
        "openQuestions": [{"parameter": "high_return_dates", "question": "高RTP日期的大额派奖、有效局数及Bonus结构如何？"}],
    }
    tables = [{"id": "daily", "title": "EasyWin每日明细", "subtitle": "基础口径；金额沿用源表单位。", "dataset": "daily", "sourceId": source["id"], "defaultSort": {"field": "date", "direction": "asc"}, "columns": [{"field": "date", "label": "日期", "type": "text"}, {"field": "base_bet", "label": "基础下注额", "type": "number"}, {"field": "actual_profit", "label": "基础实际盈利", "type": "number"}, {"field": "actual_rtp", "label": "实际RTP", "type": "number", "format": "percent"}, {"field": "status", "label": "状态", "type": "text"}]}]
    charts = [
        {"id": "rtp-trend", "title": "EasyWin每日实际RTP", "subtitle": "9月3日保留为空；参考线为100%。", "type": "line", "dataset": "daily", "sourceId": source["id"], "encodings": {"x": {"field": "date", "type": "temporal"}, "y": {"field": "actual_rtp", "type": "quantitative", "format": "percent"}, "tooltip": [{"field": "base_bet", "type": "quantitative"}, {"field": "actual_profit", "type": "quantitative"}]}, "xAxisTitle": "业务日期", "yAxisTitle": "实际RTP", "annotations": [{"type": "reference", "value": 1, "label": "100%"}, {"type": "extrema", "field": "actual_rtp", "labels": ["最高", "最低", "最新"]}]},
        {"id": "bet-profit", "title": "EasyWin每日下注与实际盈利", "subtitle": "上图为下注额，下图为实际盈利。", "type": "bar", "dataset": "daily", "sourceId": source["id"], "unit": "源表单位", "encodings": {"x": {"field": "date", "type": "temporal"}, "y": {"fields": ["base_bet", "actual_profit"], "type": "quantitative", "unit": "源表单位"}}, "xAxisTitle": "业务日期", "yAxisTitle": "基础下注额/实际盈利（源表单位）"},
    ]
    blocks = [
        {"id": "title", "type": "markdown", "body": f"# {TITLE}\n\n2026-08-12—2026-09-10（香港时间）；29/30日有效。"},
        {"id": "summary", "type": "markdown", "body": "## 执行摘要\n\n**30日窗口累计RTP为111.41%。** 累计下注20.01M，实际盈利-2.28M。\n\n**结果集中在少数日期。** 9月9日、9月4日、9月8日三天合计实际盈利-3.64M。"},
        {"id": "rtp-intro", "type": "markdown", "body": "## 每日RTP趋势\n\n最高值为9月9日300.27%，最低值为8月16日46.15%，最新值为9月10日72.29%。"},
        {"id": "rtp", "type": "chart", "chartId": "rtp-trend"},
        {"id": "amounts-intro", "type": "markdown", "body": "## 每日下注与盈利\n\n9月9日、9月4日、9月8日三天合计实际盈利-3.64M，构成本窗口主要负向贡献。"},
        {"id": "amounts", "type": "chart", "chartId": "bet-profit"},
        {"id": "daily", "type": "table", "tableId": "daily"},
    ]
    return {"surface": "report", "manifest": {"version": 1, "surface": "report", "title": TITLE, "description": "EasyWin过去30日投注、盈利与RTP汇总。", "generatedAt": summary["generated_at"], "sources": [source], "charts": charts, "tables": tables, "blocks": blocks, "reportContract": contract}, "snapshot": {"generatedAt": summary["generated_at"], "datasets": datasets, "quality": {"status": summary["status"], "complete_days": 29, "requested_days": 30, "missing_dates": ["2026-09-03"], "raw_overlap_days_checked": 17, "raw_overlap_status": "passed"}}, "sources": [source]}


def build_html(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    complete = [row for row in rows if row["status"] == "complete"]
    total_bet = summary["metrics"]["total_base_bet"]
    total_profit = summary["metrics"]["total_actual_profit"]
    cumulative_rtp = summary["metrics"]["cumulative_actual_rtp"]
    loss_days = sorted(complete, key=lambda row: row["actual_profit"])
    focus = loss_days[:3]
    focus_profit = sum(row["actual_profit"] for row in focus)
    remaining_profit = total_profit - focus_profit
    days_over_100 = sum(1 for row in complete if row["actual_rtp"] > 1)
    focus_rows = "".join(f'<tr><td>{row["date"]}</td><td>{row["base_bet"]:,.2f}</td><td class="negative">{row["actual_profit"]:,.2f}</td><td class="rtp-high">{pct(row["actual_rtp"])}</td></tr>' for row in focus)
    project_css = (ROOT / "config/report_readability.css").read_text(encoding="utf-8") if (ROOT / "config/report_readability.css").exists() else ""
    css = """
    :root{color-scheme:light dark;--bg:#eef3f8;--paper:#fff;--ink:#172033;--muted:#66758a;--line:#d6e0ea;--blue:#2563eb;--blue-soft:#eaf2ff;--orange:#ea580c;--red:#b91c1c;--green:#15803d;--shadow:0 16px 44px rgba(28,55,88,.09)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif;font-size:16px;line-height:1.76}.page{width:min(1120px,calc(100% - 32px));margin:0 auto 56px}.hero{padding:48px 0 26px}.eyebrow{color:var(--blue);font-size:12px;letter-spacing:.15em;font-weight:800}.hero h1{max-width:900px;margin:12px 0 8px;font-size:clamp(32px,5vw,52px);line-height:1.12;letter-spacing:-.04em}.dek{margin:0;color:var(--muted);font-size:18px}.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.meta span{padding:6px 10px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:12px}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.kpi,.section,.summary{background:var(--paper);border:1px solid var(--line);border-radius:17px;box-shadow:var(--shadow)}.kpi{padding:18px}.kpi .label{color:var(--muted);font-size:12px;font-weight:750}.kpi .value{margin:7px 0 4px;font-size:30px;line-height:1.15;font-weight:850}.blue{color:var(--blue)}.orange{color:var(--orange)}.red{color:var(--red)}.green{color:var(--green)}.kpi .note{color:var(--muted);font-size:12px}.summary{margin-top:16px;padding:21px 24px;border-left:5px solid var(--blue);background:linear-gradient(100deg,#fff,#f3f7ff)}.summary h2{margin:0 0 7px;font-size:19px}.summary p{margin:5px 0}.section{margin-top:18px;padding:27px 29px}.section h2{margin:0 0 8px;font-size:25px;line-height:1.3}.section h3{margin:24px 0 8px;font-size:18px}.intro{margin:0 0 14px;color:var(--muted)}.conclusion{margin:14px 0 11px;padding:11px 14px;border-left:4px solid var(--blue);border-radius:0 10px 10px 0;background:var(--blue-soft)}.chart-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px;background:#fbfdff;padding:8px}.chart-svg{display:block;width:100%;min-width:820px;height:auto}.grid{stroke:#dce5ef;stroke-width:1}.reference{stroke:#7c8ba1;stroke-width:1.5;stroke-dasharray:5 5}.reference-label,.zero-label{fill:#64748b;font-size:12px}.missing{stroke:#f59e0b;stroke-width:2;stroke-dasharray:3 4}.missing-label{fill:#b45309;font-size:11px;font-weight:700}.rtp-line{fill:none;stroke:var(--blue);stroke-width:3;stroke-linecap:round;stroke-linejoin:round}.rtp-point{fill:var(--blue);stroke:#fff;stroke-width:2}.axis,.axis-title{fill:#64748b;font-size:12px}.point-label,.panel-title{fill:#334155;font-size:12px;font-weight:750}.bet-bar{fill:#2563eb;opacity:.82}.zero{stroke:#7c8ba1;stroke-width:1.5}.profit-positive{fill:#64748b;opacity:.82}.profit-negative{fill:#dc2626;opacity:.82}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px;margin-top:15px}table{width:100%;border-collapse:collapse;min-width:660px;font-size:14px}th,td{padding:11px 13px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}th{position:sticky;top:0;background:#eaf1f8;color:#334155;font-size:12px}th:first-child,td:first-child{text-align:left}tbody tr:nth-child(even){background:rgba(232,240,248,.25)}.negative{color:var(--red);font-weight:720}.positive{color:#475569}.rtp-high{color:var(--orange);font-weight:720}.missing-row{background:#fff8e8!important;color:#92400e}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.detail{padding:15px;border:1px solid var(--line);border-radius:12px}.detail strong{display:block;font-size:22px;margin-bottom:2px}.small{color:var(--muted);font-size:13px}details{margin-top:14px}summary{cursor:pointer;color:#1d4ed8;font-weight:750}@media(max-width:820px){.page{width:calc(100% - 20px)}.hero{padding:31px 0 21px}.hero h1{font-size:32px}.dek{font-size:15px}.kpis{grid-template-columns:1fr 1fr}.section{padding:21px 14px}.summary{padding:18px}.two{grid-template-columns:1fr}.chart-svg{min-width:760px}}@media(max-width:480px){.page{width:calc(100% - 14px)}.hero h1{font-size:29px}.kpi{padding:14px 11px}.kpi .value{font-size:22px}.section{padding:18px 10px}.summary{padding:16px}}@media(prefers-color-scheme:dark){:root{--bg:#0b1220;--paper:#111b2d;--ink:#e6edf7;--muted:#9aabc0;--line:#26364c;--blue-soft:#142747;--shadow:0 16px 44px rgba(0,0,0,.25)}.summary{background:#122342}.chart-wrap{background:#0e1726}th{background:#142238;color:#dbeafe}tbody tr:nth-child(even){background:rgba(38,54,76,.18)}.point-label,.panel-title{fill:#dbeafe}.axis,.axis-title,.reference-label,.zero-label{fill:#9aabc0}.rtp-point{stroke:#111b2d}.missing-row{background:#211d16!important;color:#fbbf24}.detail{background:#0e1726}}
    """
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="report-type" content="business"><meta name="report-status" content="partial"><title>{html.escape(TITLE)}</title><style>{project_css}\n{css}</style></head>
<body><main class="page">
<header class="hero"><div class="eyebrow">WAJE ANALYST · EASYWIN RTP</div><h1>{html.escape(TITLE)}</h1><p class="dek">2026-08-12—2026-09-10 · 香港时间 · 基础口径</p><div class="meta"><span>覆盖29/30日</span><span>缺口：2026-09-03</span><span>金额沿用源表单位</span></div></header>
<section class="kpis"><div class="kpi"><div class="label">累计实际RTP</div><div class="value orange">{pct(cumulative_rtp)}</div><div class="note">累计返奖 ÷ 累计下注</div></div><div class="kpi"><div class="label">累计基础下注额</div><div class="value blue">{compact(total_bet)}</div><div class="note">精确值 {total_bet:,.2f}</div></div><div class="kpi"><div class="label">累计基础实际盈利</div><div class="value red">{compact(total_profit)}</div><div class="note">精确值 {total_profit:,.2f}</div></div><div class="kpi"><div class="label">RTP高于100%的日期</div><div class="value blue">{days_over_100}日</div><div class="note">29个有效日</div></div></section>
<section class="summary"><h2>执行摘要</h2><p><strong>EasyWin 30日窗口累计RTP为111.41%，累计实际盈利为-2.28M。</strong></p><p><strong>结果集中在少数日期。</strong> 9月9日、9月4日、9月8日三天合计实际盈利 {compact(focus_profit)}；其余26个有效日合计 {compact(remaining_profit)}。</p></section>
<section class="section"><h2>01｜每日RTP波动较大，9月上旬出现集中高点</h2><p class="intro">实际RTP在46.15%—300.27%之间波动；100%参考线用于区分当日盈利方向。</p><div class="conclusion"><strong>最高值：</strong>9月9日300.27%；<strong>最低值：</strong>8月16日46.15%；<strong>最新值：</strong>9月10日72.29%。</div><div class="chart-wrap">{svg_rtp(rows)}</div></section>
<section class="section"><h2>02｜累计亏损主要集中在三个日期</h2><p class="intro">每日下注规模与实际盈利结合查看，可区分高RTP来自下注规模还是派奖结果。</p><div class="conclusion"><strong>9月9日、9月4日、9月8日合计盈利 {compact(focus_profit)}，</strong>占据本窗口主要负向贡献；9月4日下注额最高，为2.33M。</div><div class="chart-wrap">{svg_amounts(rows)}</div><h3>重点日期</h3><div class="table-wrap"><table><thead><tr><th>日期</th><th>基础下注额</th><th>基础实际盈利</th><th>实际RTP</th></tr></thead><tbody>{focus_rows}</tbody></table></div></section>
<section class="section"><h2>03｜每日明细</h2><p class="intro">正盈利表示当日平台盈利，负盈利表示当日平台亏损；累计RTP采用累计下注额加权。</p><div class="table-wrap"><table><thead><tr><th>日期</th><th>基础下注额</th><th>基础实际盈利</th><th>实际RTP</th></tr></thead><tbody>{table_rows(rows)}<tr><td><strong>汇总</strong></td><td><strong>{total_bet:,.2f}</strong></td><td class="negative"><strong>{total_profit:,.2f}</strong></td><td class="rtp-high"><strong>{pct(cumulative_rtp)}</strong></td></tr></tbody></table></div></section>
<section class="section"><h2>04｜结论与核查重点</h2><div class="two"><div class="detail"><strong>结果集中</strong><span>9月9日、9月4日、9月8日贡献主要亏损。</span></div><div class="detail"><strong>优先核查</strong><span>有效局数、最终派奖、Bonus、取消/退款及大额单局分布。</span></div></div><details><summary>口径与来源</summary><p class="small">累计实际RTP = 1 − Σ基础实际盈利 ÷ Σ基础下注额。来源为生命周期价值飞书文档回读 revision 1608；17个日期与本地原始快照交叉一致。2026-09-03保留为空。</p></details></section>
</main></body></html>"""


def main() -> None:
    rows = load_rows()
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    complete = [row for row in rows if row["status"] == "complete"]
    if len(rows) != 30 or len(complete) != 29:
        raise ValueError("unexpected date coverage")
    total_bet = sum(row["base_bet"] for row in complete)
    total_profit = sum(row["actual_profit"] for row in complete)
    cumulative_rtp = 1 - total_profit / total_bet
    if abs(total_bet - summary["metrics"]["total_base_bet"]) > .01 or abs(total_profit - summary["metrics"]["total_actual_profit"]) > .01 or abs(cumulative_rtp - summary["metrics"]["cumulative_actual_rtp"]) > 1e-12:
        raise ValueError("summary reconciliation failed")
    artifact = build_artifact(rows, summary)
    report_html = build_html(rows, summary)
    (OUT / "artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.html").write_text(report_html, encoding="utf-8")
    receipt = {
        "schema_version": 1,
        "status": "built_pending_visual_qa",
        "generated_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds"),
        "window": summary["window"],
        "coverage": summary["coverage"],
        "metrics": summary["metrics"],
        "source_revision": 1608,
        "validation": summary["validation"],
        "artifacts": {"html": str((OUT / "report.html").resolve()), "artifact": str((OUT / "artifact.json").resolve()), "markdown": str((OUT / "report.md").resolve()), "csv": str((OUT / "easywin-daily.csv").resolve())},
        "visual_qa": {"status": "pending", "viewports": [1280, 390]},
        "security": {"credentials_embedded": False, "user_level_detail_embedded": False},
    }
    (OUT / "report-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "html": receipt["artifacts"]["html"], "cumulative_rtp": pct(cumulative_rtp), "total_bet": total_bet, "total_profit": total_profit}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

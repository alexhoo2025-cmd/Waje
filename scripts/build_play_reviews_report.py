#!/usr/bin/env python3
"""Build self-contained daily and weekly Google Play review reports.

The report is deliberately local-only: all chart marks are inline SVG and
every chart has a visible data table fallback.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import math
import os
import statistics
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(os.environ.get("WAJE_ANALYST_ROOT", str(Path(__file__).resolve().parents[1]))).resolve()
SOURCE_URL = "https://play.google.com/store/apps/details?id=com.hfhy.waje.special&hl=en-gb&gl=ng&pli=1"
TOPIC_LABELS = {
    "payment_and_withdrawal": "充值/扣款/余额/提现",
    "stability_and_verification": "网络/加载/验证",
    "fairness_and_game_rules": "公平性/规则/输赢",
    "customer_support": "客服与投诉",
    "promotion_and_referral": "Bonus/推荐/活动",
    "gameplay_and_feature_request": "玩法与功能",
    "trust_and_responsible_gambling": "信任/监管/负责任博彩",
    "general_product_feedback": "其他产品反馈",
}
ACTION_LABELS = {
    "payment_and_withdrawal": "核查充值、余额、提现和扣款闭环，建立高风险客服跟进清单",
    "stability_and_verification": "优先复核加载、网络和身份验证失败链路，按版本和设备补充内部监控",
    "fairness_and_game_rules": "补充玩法、RNG、限额和输赢规则解释，避免用模板回复替代核查",
    "customer_support": "检查客服响应时延、转人工成功率和公开回复后的解决结果",
    "promotion_and_referral": "复核 Bonus、注册送、推荐活动的规则展示、领取和提现条件",
    "gameplay_and_feature_request": "将高频玩法和功能建议进入产品需求池，并按 Helpful 数排序验证",
    "trust_and_responsible_gambling": "将信任、监管和负责任博彩线索交由合规与客服联合复核",
    "general_product_feedback": "人工复核其他产品反馈，补充分类词表",
}


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def read_json(path: Path, fallback: Any = None) -> Any:
    if not path.exists():
        return {} if fallback is None else fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {} if fallback is None else fallback


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    return [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]


def week_window(report_date: dt.date) -> tuple[dt.date, dt.date]:
    end = report_date - dt.timedelta(days=1)
    return end - dt.timedelta(days=6), end


def load_day(root: Path, day: dt.date) -> dict[str, Any]:
    analysis_path = root / "data/outputs/play_reviews" / day.isoformat() / "analysis.json"
    quality_path = root / "data/outputs/play_reviews" / day.isoformat() / "quality.json"
    summary_path = root / "data/processed/play_reviews" / day.isoformat() / "summary.json"
    analysis = read_json(analysis_path, {"items": []})
    quality = read_json(quality_path, {})
    summary = read_json(summary_path, {})
    items = analysis.get("items", []) if isinstance(analysis, dict) else []
    legacy_baseline = bool(items) and not any("record_state" in item for item in items)
    return {
        "date": day.isoformat(),
        "available": analysis_path.exists(),
        "analysis": analysis,
        "quality": quality,
        "summary": summary,
        "items": items,
        "new_items": items if legacy_baseline else [item for item in items if item.get("record_state") == "new"],
        "updated_items": [item for item in items if item.get("record_state") == "updated"],
    }


def latest_raw_manifest(root: Path, day: dt.date) -> dict[str, Any]:
    paths = sorted((root / "data/raw/play_reviews" / day.isoformat()).glob("manifest-*.json"))
    return read_json(paths[-1], {}) if paths else {}


def rating_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {str(i): 0 for i in range(1, 6)}
    for item in items:
        rating = item.get("rating")
        if rating in range(1, 6):
            counts[str(rating)] += 1
    total = len(items)
    ratings = [item.get("rating") for item in items if item.get("rating") in range(1, 6)]
    good = counts["4"] + counts["5"]
    bad = counts["1"] + counts["2"]
    neutral = counts["3"]
    return {
        "counts": counts,
        "total": total,
        "rated_count": len(ratings),
        "average": round(statistics.mean(ratings), 2) if ratings else None,
        "median": statistics.median(ratings) if ratings else None,
        "good_count": good,
        "bad_count": bad,
        "neutral_count": neutral,
        "good_rate": good / total if total else None,
        "bad_rate": bad / total if total else None,
        "neutral_rate": neutral / total if total else None,
    }


def counts_for(items: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(collections.Counter(str(item.get(field)) for item in items if item.get(field)))


def topic_counts(items: Iterable[dict[str, Any]]) -> collections.Counter[str]:
    return collections.Counter(topic for item in items for topic in item.get("topics", []))


def top_topics(items: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    total = len(items)
    return [
        {"topic": topic, "label": TOPIC_LABELS.get(topic, topic), "count": count, "rate": count / total if total else 0}
        for topic, count in topic_counts(items).most_common(limit)
    ]


def reply_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    replied = [item for item in items if item.get("has_developer_reply")]
    lags = [item.get("reply_lag_days") for item in replied if isinstance(item.get("reply_lag_days"), (int, float)) and item.get("reply_lag_days") >= 0]
    return {
        "reply_count": len(replied),
        "reply_rate": len(replied) / len(items) if items else None,
        "average_lag_days": round(statistics.mean(lags), 1) if lags else None,
        "median_lag_days": statistics.median(lags) if lags else None,
        "template_counts": counts_for(replied, "reply_template"),
        "resolution_signal_count": sum(1 for item in replied if item.get("is_resolution_signal")),
    }


def quality_summary(days: list[dict[str, Any]]) -> dict[str, Any]:
    available = [day for day in days if day["available"]]
    qualities = [day["quality"] for day in available]
    return {
        "expected_days": len(days),
        "available_days": len(available),
        "missing_dates": [day["date"] for day in days if not day["available"]],
        "statuses": dict(collections.Counter(str(q.get("status", "unknown")) for q in qualities)),
        "shortfall_days": [day["date"] for day in available if day["quality"].get("source_health", {}).get("stop_reason") == "shortfall" or day["quality"].get("collection", {}).get("status") == "shortfall"],
    }


def truncate(value: str, length: int = 190) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"


def quote_rows(items: list[dict[str, Any]], limit: int = 8, negative: bool = False) -> list[dict[str, Any]]:
    selected = [item for item in items if (item.get("rating_bucket") == ("negative" if negative else "positive"))]
    selected.sort(key=lambda item: (-(item.get("helpful_count") or 0), item.get("rating") or 0))
    return [
        {
            "rating": item.get("rating") or "-",
            "helpful": item.get("helpful_count") or 0,
            "severity": item.get("severity") or "-",
            "topics": ", ".join(TOPIC_LABELS.get(t, t) for t in item.get("topics", [])[:3]),
            "text": truncate(item.get("review_text") or item.get("summary") or "", 240),
        }
        for item in selected[:limit]
    ]


def action_rows(items: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    negative = [item for item in items if item.get("rating_bucket") == "negative"]
    rows = []
    for topic, count in topic_counts(negative).most_common(limit):
        topic_items = [item for item in negative if topic in item.get("topics", [])]
        p0 = sum(1 for item in topic_items if item.get("severity") == "P0")
        rows.append({"priority": "P0" if p0 else "P1", "topic": TOPIC_LABELS.get(topic, topic), "count": count, "p0": p0, "action": ACTION_LABELS.get(topic, "人工复核并补充运营动作")})
    return rows


def daily_series(root: Path, end: dt.date, days_count: int = 7) -> list[dict[str, Any]]:
    rows = []
    for day in date_range(end - dt.timedelta(days=days_count - 1), end):
        batch = load_day(root, day)
        items = batch["new_items"]
        stats = rating_stats(items)
        rows.append({
            "date": day.isoformat(),
            "label": day.strftime("%m-%d"),
            "available": batch["available"],
            "new_count": len(items),
            "average": stats["average"],
            "good_rate": stats["good_rate"],
            "bad_rate": stats["bad_rate"],
        })
    return rows


def svg_bar(values: list[tuple[str, float]], width: int = 680, height: int = 230, suffix: str = "") -> str:
    if not values:
        return '<div class="empty-chart">暂无数据</div>'
    max_value = max((value for _, value in values), default=1) or 1
    left, bottom, top = 120, 36, 20
    chart_h = height - bottom - top
    bar_h = min(30, max(14, chart_h / max(len(values), 1) - 8))
    pieces = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="横向柱状图">']
    for index, (label, value) in enumerate(values):
        y = top + index * (chart_h / len(values)) + 4
        bar_w = (width - left - 28) * value / max_value
        pieces.append(f'<text class="axis-label" x="0" y="{y + bar_h * 0.72:.1f}">{esc(label)}</text>')
        pieces.append(f'<rect class="series-{index % 3 + 1}" x="{left}" y="{y:.1f}" width="{max(bar_w, 1):.1f}" height="{bar_h:.1f}" rx="4"></rect>')
        pieces.append(f'<text class="value-label" x="{min(left + bar_w + 8, width - 58):.1f}" y="{y + bar_h * 0.72:.1f}">{esc(f"{value:g}{suffix}")}</text>')
    pieces.append("</svg>")
    return "".join(pieces)


def svg_stacked(stats: dict[str, Any], width: int = 680, height: int = 110) -> str:
    total = stats.get("total") or 0
    if not total:
        return '<div class="empty-chart">暂无数据</div>'
    pieces = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="好评价、中性评价和差评价占比">']
    x = 12
    y = 24
    h = 34
    colors = [("good_count", "series-1", "好评价"), ("neutral_count", "series-2", "中性评价"), ("bad_count", "series-3", "差评价")]
    for key, cls, label in colors:
        value = stats.get(key, 0)
        w = (width - 24) * value / total
        if w > 0:
            pieces.append(f'<rect class="{cls}" x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="4"></rect>')
            if w > 58:
                pieces.append(f'<text class="stack-label" x="{x + w / 2:.1f}" y="{y + 22}" text-anchor="middle">{esc(label)} {value}</text>')
        x += w
    pieces.append(f'<text class="axis-label" x="12" y="88">总样本 {total} 条；好评价=4–5星，差评价=1–2星</text>')
    pieces.append("</svg>")
    return "".join(pieces)


def svg_line(series: list[dict[str, Any]], field: str, label: str, width: int = 680, height: int = 230, percent: bool = False) -> str:
    valid = [row for row in series if isinstance(row.get(field), (int, float))]
    if not valid:
        return '<div class="empty-chart">暂无足够趋势数据</div>'
    values = [float(row[field]) for row in valid]
    minimum = 0 if percent else min(values) - 0.2
    maximum = 1 if percent else max(values) + 0.2
    if maximum <= minimum:
        maximum = minimum + 1
    left, right, top, bottom = 44, 16, 18, 42
    chart_w, chart_h = width - left - right, height - top - bottom
    points = []
    for index, row in enumerate(valid):
        x = left + (chart_w * index / max(len(valid) - 1, 1))
        y = top + chart_h * (maximum - float(row[field])) / (maximum - minimum)
        points.append((x, y, row))
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
    pieces = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}趋势图">', '<line class="grid-line" x1="44" y1="18" x2="664" y2="18"></line>', '<line class="grid-line" x1="44" y1="188" x2="664" y2="188"></line>', f'<polyline class="trend-line" points="{polyline}"></polyline>']
    for x, y, row in points:
        value = float(row[field])
        display = f"{value:.0%}" if percent else f"{value:.2f}"
        pieces.append(f'<circle class="trend-dot" cx="{x:.1f}" cy="{y:.1f}" r="4"><title>{esc(row["label"])} {esc(display)}</title></circle>')
        pieces.append(f'<text class="axis-label" x="{x:.1f}" y="210" text-anchor="middle">{esc(row["label"])}</text>')
    pieces.append(f'<text class="axis-label" x="44" y="14">{esc(label)}</text></svg>')
    return "".join(pieces)


def table(title: str, headers: list[str], rows: list[list[Any]], empty: str = "暂无数据") -> str:
    head = "".join(f"<th scope=\"col\">{esc(value)}</th>" for value in headers)
    if rows:
        body = "".join("<tr>" + "".join(f"<td>{esc(value)}</td>" for value in row) + "</tr>" for row in rows)
    else:
        body = f"<tr><td colspan=\"{len(headers)}\" class=\"empty\">{esc(empty)}</td></tr>"
    return f'<div class="table-wrap"><table><caption>{esc(title)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def metric_cards(stats: dict[str, Any], reply: dict[str, Any], quality: dict[str, Any], target: int) -> str:
    total = stats.get("total", 0)
    completion = min(1, total / target) if target else 1
    cards = [
        ("新增评价", f"{total:,}", f"目标 {target:,}，完成 {completion:.0%}"),
        ("平均星级", f"{stats.get('average'):.2f}" if stats.get("average") is not None else "—", f"中位数 {stats.get('median') or '—'}"),
        ("好评价率", f"{stats.get('good_rate'):.1%}" if stats.get("good_rate") is not None else "—", f"4–5星，共 {stats.get('good_count', 0)} 条"),
        ("差评价率", f"{stats.get('bad_rate'):.1%}" if stats.get("bad_rate") is not None else "—", f"1–2星，共 {stats.get('bad_count', 0)} 条"),
        ("开发者回复率", f"{reply.get('reply_rate'):.1%}" if reply.get("reply_rate") is not None else "—", f"{reply.get('reply_count', 0)} 条已回复"),
        ("数据状态", str(quality.get("status", "unknown")), f"短缺 {quality.get('shortfall', 0)} 条"),
    ]
    return "<div class=\"metric-grid\">" + "".join(f'<div class="metric-card"><span>{esc(label)}</span><strong>{esc(value)}</strong><small>{esc(note)}</small></div>' for label, value, note in cards) + "</div>"


def build_css() -> str:
    return """
    :root{color-scheme:light dark;--bg:#f6f7f9;--surface:#fff;--ink:#17202a;--muted:#5f6b76;--border:#dfe4e8;--accent:#2b6cb0;--good:#2f855a;--warn:#b7791f;--bad:#c53030;--series-1:#2f855a;--series-2:#b7791f;--series-3:#c53030;--series-4:#2b6cb0;--grid:#d8dee4;--shadow:0 8px 28px rgba(18,32,45,.08);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    @media(prefers-color-scheme:dark){:root{--bg:#11171d;--surface:#1a222b;--ink:#e7edf2;--muted:#aab6c0;--border:#35414c;--accent:#7db2e8;--good:#69c18c;--warn:#e5b65c;--bad:#f17b7b;--series-1:#69c18c;--series-2:#e5b65c;--series-3:#f17b7b;--series-4:#7db2e8;--grid:#40505d;--shadow:0 8px 28px rgba(0,0,0,.28)}}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-size:14px;line-height:1.55}main{max-width:1180px;margin:0 auto;padding:28px 22px 60px}h1,h2,h3{line-height:1.2;margin:0 0 10px;font-weight:500}h1{font-size:30px;letter-spacing:-.02em}h2{font-size:20px;margin-top:30px}h3{font-size:16px;margin-top:20px}.subtitle,.meta,.note{color:var(--muted)}.meta{font-size:12px}.hero{border-bottom:1px solid var(--border);padding-bottom:22px}.status{display:inline-flex;align-items:center;border:1px solid var(--border);border-radius:999px;padding:3px 9px;font-size:12px;margin:8px 0}.status.ok{color:var(--good)}.status.shortfall,.status.degraded{color:var(--warn)}.status.blocked,.status.error{color:var(--bad)}.metric-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin:22px 0}.metric-card,.panel{background:var(--surface);border:1px solid var(--border);border-radius:12px;box-shadow:var(--shadow)}.metric-card{padding:14px;min-height:112px}.metric-card span,.metric-card small{display:block;color:var(--muted);font-size:12px}.metric-card strong{display:block;font-size:25px;font-weight:500;margin:10px 0 4px}.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.panel{padding:18px;margin-top:16px}.panel h2,.panel h3{margin-top:0}.chart-svg{display:block;width:100%;height:auto;min-height:100px}.chart-svg text{font-family:inherit;fill:var(--ink);font-size:12px}.axis-label{fill:var(--muted)!important}.value-label{font-variant-numeric:tabular-nums}.series-1{fill:var(--series-1)}.series-2{fill:var(--series-2)}.series-3{fill:var(--series-3)}.series-4{fill:var(--series-4)}.stack-label{fill:var(--surface)!important;font-size:11px!important}.grid-line{stroke:var(--grid);stroke-width:1}.trend-line{fill:none;stroke:var(--series-4);stroke-width:3;stroke-linecap:round;stroke-linejoin:round}.trend-dot{fill:var(--series-4);stroke:var(--surface);stroke-width:2}.empty-chart{padding:35px 0;color:var(--muted);text-align:center;border:1px dashed var(--border);border-radius:8px}.table-wrap{overflow-x:auto;margin-top:12px}table{border-collapse:collapse;width:100%;font-size:13px}caption{text-align:left;color:var(--muted);font-size:12px;margin-bottom:7px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}th{font-weight:500;color:var(--muted);white-space:nowrap}td:first-child{color:var(--ink)}.empty{text-align:center;color:var(--muted)}.callout{border-left:3px solid var(--accent);padding:10px 13px;background:color-mix(in srgb,var(--accent) 8%,var(--surface));margin-top:12px}.small{font-size:12px;color:var(--muted)}.footer{margin-top:28px;padding-top:16px;border-top:1px solid var(--border);color:var(--muted);font-size:12px}.danger{color:var(--bad)}.good{color:var(--good)}@media(max-width:900px){.metric-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:600px){main{padding:20px 14px 40px}h1{font-size:24px}.metric-grid,.grid-2{grid-template-columns:1fr 1fr;gap:8px}.metric-card{padding:11px;min-height:100px}.metric-card strong{font-size:21px}.panel{padding:13px}th,td{padding:7px 6px}}@media(max-width:380px){.metric-grid{grid-template-columns:1fr}.metric-card{min-height:auto}.metric-card strong{margin:5px 0 2px}}
    """


def section_satisfaction(items: list[dict[str, Any]]) -> str:
    positive = [item for item in items if item.get("rating_bucket") == "positive"]
    negative = [item for item in items if item.get("rating_bucket") == "negative"]
    pos_topics = top_topics(positive)
    neg_topics = top_topics(negative)
    pos_rows = [[row["label"], row["count"], f"{row['rate']:.1%}"] for row in pos_topics]
    neg_rows = [[row["label"], row["count"], f"{row['rate']:.1%}"] for row in neg_topics]
    return f"""
    <h2>满意点与不满意点</h2>
    <div class="grid-2">
      <section class="panel"><h3 class="good">满意层面（4–5星）</h3><p class="small">按正向评价中的主题命中次数统计；一条评价可命中多个主题。</p>{svg_bar([(row['label'], row['count']) for row in pos_topics])}{table('正向主题统计',['主题','评价数','占正向评价'],pos_rows)}</section>
      <section class="panel"><h3 class="danger">不满意层面（1–2星）</h3><p class="small">按差评价中的主题命中次数统计；资金和信任相关线索需内部核查。</p>{svg_bar([(row['label'], row['count']) for row in neg_topics])}{table('负向主题统计',['主题','评价数','占差评价'],neg_rows)}</section>
    </div>
    """


def build_payload(root: Path, report_date: dt.date, period: str, batch: bool = False) -> dict[str, Any]:
    if period == "weekly":
        start, end = week_window(report_date)
        days = [load_day(root, report_date)] if batch else [load_day(root, day) for day in date_range(start, end)]
        title = f"Waje Google Play 用户评价周报｜{report_date.isoformat()}"
        period_label = f"{start.isoformat()} 至 {end.isoformat()}" + ("（周五批次采集）" if batch else "")
    else:
        start = end = report_date
        days = [load_day(root, report_date)]
        title = f"Waje Google Play 用户评价日报｜{report_date.isoformat()}"
        period_label = report_date.isoformat()
    new_items = [item for day in days for item in day["new_items"]]
    updated_items = [item for day in days for item in day["updated_items"]]
    all_items = [item for day in days for item in day["items"]]
    stats = rating_stats(new_items)
    reply = reply_stats(new_items)
    quality = quality_summary(days)
    manifests = [latest_raw_manifest(root, dt.date.fromisoformat(day["date"])) for day in days]
    manifests = [manifest for manifest in manifests if manifest]
    statuses = [manifest.get("status") for manifest in manifests]
    status = "blocked" if "blocked" in statuses else "error" if "error" in statuses else "shortfall" if quality["missing_dates"] or quality["shortfall_days"] or any(status == "shortfall" for status in statuses) else "ok"
    if not new_items and not all_items:
        status = "degraded"
    target = 200 if period == "daily" or batch else 200 * len(days)
    series = daily_series(root, end, 7) if period == "daily" else [
        {
            "date": day["date"],
            "label": day["date"][5:],
            "available": day["available"],
            "new_count": len(day["new_items"]),
            "average": rating_stats(day["new_items"])["average"],
            "good_rate": rating_stats(day["new_items"])["good_rate"],
            "bad_rate": rating_stats(day["new_items"])["bad_rate"],
        }
        for day in days
    ]
    daily_rows = [[day["date"], len(day["new_items"]), rating_stats(day["new_items"])["average"] or "—", rating_stats(day["new_items"])["bad_rate"] if rating_stats(day["new_items"])["bad_rate"] is not None else "—", "是" if day["available"] else "否"] for day in days]
    topic_rows = [[row["label"], row["count"], f"{row['rate']:.1%}"] for row in top_topics(new_items)]
    rating_rows = [[f"{i} 星", stats["counts"][str(i)], f"{stats['counts'][str(i)] / stats['total']:.1%}" if stats["total"] else "—"] for i in range(1, 6)]
    sentiment_rows = [[label, count] for label, count in (("正向", counts_for(new_items, "sentiment").get("positive", 0)), ("中性", counts_for(new_items, "sentiment").get("neutral", 0)), ("负向", counts_for(new_items, "sentiment").get("negative", 0)))]
    manifest = manifests[-1] if manifests else {}
    latest_quality = days[-1]["quality"] if days else {}
    index_health = latest_quality.get("index_health", {}) if isinstance(latest_quality, dict) else {}
    return {
        "title": title,
        "period": period,
        "report_date": report_date.isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat(), "label": period_label},
        "status": status,
        "target_new_count": target,
        "new_items": new_items,
        "updated_items": updated_items,
        "all_items": all_items,
        "stats": stats,
        "reply": reply,
        "quality": {**quality, "shortfall": sum(int(day["quality"].get("source_health", {}).get("shortfall", 0) or 0) for day in days), "index_review_count": index_health.get("review_count", 0), "index_version_count": index_health.get("version_count", 0)},
        "manifest": manifest,
        "series": series,
        "tables": {"daily": daily_rows, "ratings": rating_rows, "sentiment": sentiment_rows, "topics": topic_rows},
        "actions": action_rows(new_items),
        "positive_quotes": quote_rows(new_items, negative=False),
        "negative_quotes": quote_rows(new_items, negative=True),
        "updated_count": len(updated_items),
        "all_observed_count": len(all_items),
    }


def build_html(payload: dict[str, Any]) -> str:
    stats = payload["stats"]
    reply = payload["reply"]
    quality = payload["quality"]
    period = payload["period"]
    status = payload["status"]
    status_label = {"ok": "完成", "shortfall": "未达到200条，已降级", "blocked": "页面被阻断", "error": "采集失败", "degraded": "数据不足"}.get(status, status)
    topic_rows = payload["tables"]["topics"]
    rating_rows = payload["tables"]["ratings"]
    sentiment_rows = payload["tables"]["sentiment"]
    daily_rows = payload["tables"]["daily"]
    source_summary = payload["manifest"].get("visible_review_summaries", []) if isinstance(payload["manifest"], dict) else []
    target = payload["target_new_count"]
    actions = [[row["priority"], row["topic"], row["count"], row["p0"], row["action"]] for row in payload["actions"]]
    positive_quotes = [[row["rating"], row["helpful"], row["topics"], row["text"]] for row in payload["positive_quotes"]]
    negative_quotes = [[row["rating"], row["helpful"], row["severity"], row["topics"], row["text"]] for row in payload["negative_quotes"]]
    reply_rows = [[label, count] for label, count in sorted(reply.get("template_counts", {}).items(), key=lambda pair: -pair[1])]
    reply_rows = [[label.replace("_", " "), count] for label, count in reply_rows]
    trend = payload["series"]
    html_doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(payload['title'])}</title><style>{build_css()}</style></head><body><main>
    <header class="hero"><div class="meta">GOOGLE PLAY 用户评价 · {esc(period.upper())}</div><h1>{esc(payload['title'])}</h1><p class="subtitle">统计窗口：{esc(payload['window']['label'])}；主统计口径为本窗口首次入库的用户评价。</p><span class="status {esc(status)}">状态：{esc(status_label)}</span><p class="small">来源：<a href="{esc(SOURCE_URL)}">Waje Google Play 公开评价页面</a> · 过滤：Newest / Phone / en-gb / ng · 生成时间：{esc(dt.datetime.now().astimezone().isoformat(timespec='seconds'))}</p></header>
    {metric_cards(stats, reply, {'status': status, 'shortfall': max(0, target - stats['total'])}, target)}
    <section class="panel"><h2>一页结论</h2><div class="callout">本窗口新增 <strong>{stats['total']}</strong> 条评价，目标完成率 <strong>{min(1, stats['total'] / target) if target else 1:.0%}</strong>；好评价 {stats['good_count']} 条，差评价 {stats['bad_count']} 条。{('当前未达到 200 条，原因：' + ', '.join(quality['missing_dates'] + quality['shortfall_days'])) if quality['missing_dates'] or quality['shortfall_days'] else '当前采集达到目标。'}</div><p class="small">评价编辑、开发者回复变化：{payload['updated_count']} 条；本次观察卡片总数：{payload['all_observed_count']} 条。公开评价属于 D 级证据，P0/P1 线索需结合客服、订单和资金流水核查。</p></section>
    <h2>评分统计与分布</h2><div class="grid-2"><section class="panel"><h3>1–5 星分布</h3>{svg_bar([(row[0], row[1]) for row in rating_rows])}{table('星级统计',['星级','评价数','占比'],rating_rows)}</section><section class="panel"><h3>好 / 中 / 差评价</h3>{svg_stacked(stats)}{table('评价分组',['分组','评价数'],[['好评价（4–5星）',stats['good_count']],['中性（3星）',stats['neutral_count']],['差评价（1–2星）',stats['bad_count']]])}</section></div>
    <section class="panel"><h3>文本情感与星级交叉参考</h3>{table('文本情感统计',['文本情感','评价数'],sentiment_rows)}<p class="small">文本情感为规则分析结果，不能替代星级；两者不一致时保留差异供人工复核。</p></section>
    {section_satisfaction(payload['new_items'])}
    <h2>主题与优化需求</h2><div class="grid-2"><section class="panel"><h3>主题 Pareto</h3>{svg_bar([(row[0], row[1]) for row in topic_rows])}{table('主题统计',['主题','评价数','占新增评价'],topic_rows)}</section><section class="panel"><h3>运营行动清单</h3>{table('按负向主题排序',['优先级','主题','差评价数','P0数','建议动作'],actions, '当前没有可生成的负向行动项')}</section></div>
    <h2>{'本周每日完成情况' if period == 'weekly' else '近 7 日趋势'}</h2><section class="panel">{svg_line(trend,'average','平均星级')}{svg_line(trend,'bad_rate','差评价率',percent=True)}{table('每日采集与质量',['日期','新增评价','平均星级','差评价率','数据可用'],daily_rows)}</section>
    <h2>开发者回复运营</h2><div class="grid-2"><section class="panel"><h3>回复覆盖与时延</h3>{table('回复指标',['指标','数值'],[['已回复',reply['reply_count']],['回复率',f"{reply['reply_rate']:.1%}" if reply['reply_rate'] is not None else '—'],['平均回复时延（天）',reply['average_lag_days'] or '—'],['回复时延中位数（天）',reply['median_lag_days'] or '—'],['问题已解决信号',reply['resolution_signal_count']]])}</section><section class="panel"><h3>回复模板类型</h3>{svg_bar(reply_rows)}{table('模板统计',['模板','数量'],reply_rows)}</section></div>
    <h2>重点评价</h2><div class="grid-2"><section class="panel"><h3 class="good">高 Helpful 正向评价</h3>{table('正向评价摘要',['星级','Helpful','主题','评价摘要'],positive_quotes,'暂无好评价')}</section><section class="panel"><h3 class="danger">高 Helpful 负向评价</h3>{table('负向评价摘要',['星级','Helpful','严重度','主题','评价摘要'],negative_quotes,'暂无差评价')}</section></div>
    <h2>数据质量与可追溯性</h2><section class="panel">{table('采集质量',['字段','值'],[['状态',status_label],['缺失日期',', '.join(quality['missing_dates']) or '无'],['shortfall 日期',', '.join(quality['shortfall_days']) or '无'],['停止原因',payload['manifest'].get('stop_reason') or '—'],['页面可见评价摘要','；'.join(source_summary) or '未提取'],['原始快照目录',payload['manifest'].get('raw_path') or '—'],['采集时间',payload['manifest'].get('fetched_at') or '—'],['索引评价数',payload['quality'].get('index_review_count') or '—'],['版本记录数',payload['quality'].get('index_version_count') or '—'],['页面 URL',payload['manifest'].get('url') or SOURCE_URL]])}<p class="small">不保存作者真实展示名；原始页面快照仅用于审计。评论中的 Scam、扣款、提现失败和故障描述是用户线索，不直接认定为事实。</p></section>
    <footer class="footer">本报告由本地 Google Play 公开评价管道生成。报告主统计按首次入库评价计数；历史回填、评价更新和开发者回复变化单独记录。生成脚本与 JSON 分析产物位于项目本地 data/outputs/play_reviews/。</footer>
    </main></body></html>"""
    return html_doc


def build_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    stats = payload["stats"]
    return {
        "schema_version": 1,
        "surface": "google_play_review_report",
        "title": payload["title"],
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": payload["status"],
        "period": payload["period"],
        "window": payload["window"],
        "metrics": {
            "new_count": stats["total"],
            "target_new_count": payload["target_new_count"],
            "average_rating": stats["average"],
            "good_count": stats["good_count"],
            "bad_count": stats["bad_count"],
            "neutral_count": stats["neutral_count"],
            "reply_rate": payload["reply"]["reply_rate"],
            "updated_count": payload["updated_count"],
        },
        "datasets": payload["tables"],
        "sources": [{"id": "google_play_public_reviews", "label": "Waje Google Play 公开评价", "href": SOURCE_URL, "evidence_grade": "D"}],
        "quality": payload["quality"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--period", choices=("daily", "weekly"), default="daily")
    parser.add_argument("--batch", action="store_true", help="Use the single collection batch at --date as the weekly observation input")
    args = parser.parse_args()
    report_date = dt.date.fromisoformat(args.date)
    payload = build_payload(ROOT, report_date, args.period, args.batch)
    if args.period == "weekly":
        out_dir = ROOT / "data/outputs/play_reviews/weekly" / args.date
        target = ROOT / "knowledge/01-产品/Google Play用户评价/周报" / f"{args.date}-Google Play用户评价周报.html"
        alias = ROOT / "output/html/Waje-google-play-reviews-weekly.html"
    else:
        out_dir = ROOT / "data/outputs/play_reviews" / args.date
        target = ROOT / "knowledge/01-产品/Google Play用户评价/日报" / f"{args.date}-Google Play用户评价日报.html"
        alias = ROOT / "output/html/Waje-google-play-reviews-daily.html"
    out_dir.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    alias.parent.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / "report-artifact.json"
    receipt_path = out_dir / "report-receipt.json"
    html_path = target
    artifact = build_artifact(payload)
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(build_html(payload), encoding="utf-8")
    alias.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")
    html_text = html_path.read_text(encoding="utf-8")
    required_markers = ["评分统计与分布", "满意点与不满意点", "主题与优化需求", "数据质量与可追溯性"]
    receipt = {
        "schema_version": 1,
        "report_date": args.date,
        "period": args.period,
        "status": payload["status"],
        "artifact": str(artifact_path.relative_to(ROOT)),
        "html": str(html_path.relative_to(ROOT)),
        "preview_html": str(alias.relative_to(ROOT)),
        "validation": {"passed": all(marker in html_text for marker in required_markers), "required_markers": required_markers, "html_bytes": len(html_text.encode("utf-8"))},
        "summary": artifact["metrics"],
        "quality": payload["quality"],
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "html": str(html_path.relative_to(ROOT)), "artifact": str(artifact_path.relative_to(ROOT)), "new_count": payload["stats"]["total"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the Friday authorized public-account article weekly report."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path

from render_analysis_report_html import render_markdown_file
from wechat_common import now_iso, project_root


def week_dates(end_date: dt.date) -> list[dt.date]:
    monday = end_date - dt.timedelta(days=end_date.weekday())
    return [monday + dt.timedelta(days=offset) for offset in range((end_date - monday).days + 1)]


def batch_window(end_date: dt.date) -> tuple[dt.date, dt.date]:
    return end_date - dt.timedelta(days=7), end_date - dt.timedelta(days=1)


def load_articles(root: Path, dates: list[dt.date]) -> tuple[list[dict], list[str]]:
    articles: list[dict] = []
    missing: list[str] = []
    for day in dates:
        path = root / "data/processed/wechat" / day.isoformat() / "articles.json"
        if not path.exists():
            missing.append(day.isoformat())
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            articles.extend(payload.get("articles", []))
        except (OSError, json.JSONDecodeError):
            missing.append(day.isoformat())
    unique: list[dict] = []
    seen: set[str] = set()
    for article in articles:
        identity = str(article.get("article_id") or article.get("content_hash") or article.get("canonical_url") or article.get("title"))
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(article)
    return unique, missing


def article_row(article: dict) -> str:
    title = str(article.get("title") or "未命名文章").replace("|", "\\|")
    published = article.get("published_at") or "未提供"
    source_status = article.get("source_access_status") or "未提供"
    metrics = ", ".join(article.get("analysis", {}).get("metrics", [])[:6]) or "待解析"
    return f"| {title} | {published} | {source_status} | {metrics} |"


def render_report(root: Path, end_date: dt.date, articles: list[dict], missing: list[str], batch: bool = False) -> Path:
    out_dir = root / "knowledge/03-竞品/周报"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{end_date.isoformat()}-博彩社交游戏公众号周报.md"
    metric_counts = Counter(metric for article in articles for metric in article.get("analysis", {}).get("metrics", []))
    chart_counts = Counter(chart for article in articles for chart in article.get("analysis", {}).get("chart_types", {}).keys())
    layout_counts = Counter(pattern for article in articles for pattern in article.get("analysis", {}).get("layout_patterns", []))
    focus = sorted(articles, key=lambda item: (len(item.get("analysis", {}).get("metrics", [])), len(item.get("structure", {}).get("headings", []))), reverse=True)[:5]
    lines = [
        "---",
        "type: weekly-intelligence",
        "domain: competitor",
        "status: generated",
        "owner: analyst",
        f"updated: {end_date.isoformat()}",
        "tags: [wechat, social-casino, product-analysis, data-analysis, weekly-report]",
        "source_access: authorized_read_only_api_or_export",
        "---",
        "",
        f"# 博彩/社交游戏公众号周报｜{end_date.isoformat()}",
        "",
        "> 本周报只纳入授权只读 API 或授权导出文件；未获得正文的文章不做内容推断。启发性结论需结合 Waje 自有数据二次验证。",
        "",
        "## 1. 本周摘要",
        "",
        f"- 采集文章：{len(articles)} 篇。",
        f"- 高频指标主题：{', '.join(f'{key}（{value}）' for key, value in metric_counts.most_common(8)) or '暂无可用文章'}。",
        f"- 识别图表/证据形式：{', '.join(f'{key}（{value}）' for key, value in chart_counts.most_common(8)) or '暂无可用图表'}。",
        f"- 结构/排版信号：{', '.join(f'{key}（{value}）' for key, value in layout_counts.most_common(8)) or '暂无可用结构'}。",
        "",
        "## 2. 本周新增文章",
        "",
        "| 标题 | 发布时间 | 来源状态 | 指标主题 |",
        "|---|---|---|---|",
    ]
    lines.extend(article_row(article) for article in articles)
    if not articles:
        lines.append("| 暂无可访问文章 | - | 待接入授权 API/导出 | - |")
    lines.extend(["", "## 3. 重点文章逻辑与框架拆解", ""])
    if focus:
        for index, article in enumerate(focus, 1):
            analysis = article.get("analysis", {})
            structure = article.get("structure", {})
            lines.extend([
                f"### 3.{index} {article.get('title') or '未命名文章'}",
                "",
                f"- 文章 ID：`{article.get('article_id', '')}`；内容哈希：`{article.get('content_hash', '')}`。",
                f"- 导语/问题线索：{structure.get('intro') or '待人工确认'}",
                f"- 章节结构：{' → '.join(item.get('text', '') for item in structure.get('headings', [])) or '未识别标题层级'}。",
                f"- 指标主题：{', '.join(analysis.get('metrics', [])) or '未识别'}。",
                f"- 证据类型：{', '.join(analysis.get('evidence_types', [])) or '未识别'}。",
                f"- 可迁移分析链：{' → '.join(analysis.get('analysis_framework', []))}。",
                f"- 当前判断：{analysis.get('confidence', '待人工复核')}。",
                "",
            ])
    else:
        lines.extend(["本周没有可用于拆解的正文；待研发提供授权 API 或把文章导出到 `data/incoming/wechat/YYYY-MM-DD/`。", ""])
    lines.extend([
        "## 4. 内容组织、排版与图表样式",
        "",
        "- 解析字段包括：标题/导语、章节层级、段落长度、引用、分隔线、表格、图片位置、宽高比和图表类型提示。",
        f"- 本周观察到的排版模式：{', '.join(f'{key}（{value}）' for key, value in layout_counts.most_common()) or '暂无'}。",
        f"- 本周观察到的图表模式：{', '.join(f'{key}（{value}）' for key, value in chart_counts.most_common()) or '暂无'}。",
        "- Waje 报告可复用模板：结论标题 → 指标口径 → 分群/漏斗/队列/对比 → 机制解释 → 产品/运营动作 → 验证指标。",
        "",
        "## 5. 对 Waje 的可迁移建议",
        "",
        "### 产品与运营",
        "",
        "- 用注册→首局→首次下注→首充→D1/D3/D7 的新手漏斗连接任务、福利和玩法入口，避免只看单点转化。",
        "- Fish、Slots、Whot、Roulette 等玩法按入口、难度、复玩率、有效下注和 RTP 分层，不把规模直接当成体验质量。",
        "### 数据与研发",
        "",
        "- 报告中的 RTP、LTV、留存、支付、提现必须带游戏、版本、包/渠道、币种、时间窗、样本量和分母口径。",
        "- 公众号文章的启发仅作为假设来源；上线前应在 Ares/BigQuery 数据中完成口径校验和灰度验证。",
        "",
        "## 6. P0/P1 风险与待确认",
        "",
        "- **P0**：若文章涉及支付、提现、监管或安全事件，需回到官方/原始数据核验后再进入产品决策。",
        "- **P1**：留存、付费、LTV、RTP 或玩法概率结论若缺少分母、时间窗和样本量，标记为待核验。",
        f"- 采集缺失日期：{', '.join(missing) if missing else '无'}。",
        "- 当前周报不保存 API Token、Cookie、密码或用户个人明细。",
        "",
        "## 7. 数据与运行记录",
        "",
        f"- 周期：{(batch_window(end_date)[0] if batch else week_dates(end_date)[0]).isoformat()} 至 {(batch_window(end_date)[1] if batch else end_date).isoformat()}（Asia/Hong_Kong）{('；周五批次采集' if batch else '')}。",
        f"- 生成时间：{now_iso()}。",
        "- 原始快照：`data/raw/wechat/YYYY-MM-DD/`。",
        "- 解析结果：`data/processed/wechat/YYYY-MM-DD/articles.json`。",
        "- 授权方式：环境变量注入 API 地址/令牌，或研发提供的授权 HTML/JSON/ZIP 导出。",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--batch", action="store_true", help="Use the single authorized collection batch at --date")
    args = parser.parse_args()
    end_date = dt.date.fromisoformat(args.date)
    root = project_root()
    articles, missing = load_articles(root, [end_date] if args.batch else week_dates(end_date))
    path = render_report(root, end_date, articles, missing, args.batch)
    print(f"wechat weekly report: {len(articles)} articles; output={path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

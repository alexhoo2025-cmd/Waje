#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a source-linked Markdown knowledge note for Play review operations."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    source = ROOT / "data/outputs/play_reviews" / args.date / "analysis.json"
    quality_path = ROOT / "data/outputs/play_reviews" / args.date / "quality.json"
    if not source.exists(): raise SystemExit(f"Missing review analysis: {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    quality = json.loads(quality_path.read_text(encoding="utf-8")) if quality_path.exists() else {}
    items = data.get("items", [])
    has_states = any("record_state" in item for item in items)
    primary_items = [item for item in items if item.get("record_state") == "new"] if has_states else items
    topic_counts = collections.Counter(topic for item in primary_items for topic in item.get("topics", []))
    severity_counts = collections.Counter(item.get("severity") for item in primary_items)
    reply_count = sum(1 for item in primary_items if item.get("has_developer_reply"))
    target_dir = ROOT / "knowledge/01-产品/Google Play用户评价"
    target_dir.mkdir(parents=True, exist_ok=True)
    state_counts = quality.get("source_health", {})
    lines = ["---", "type: google-play-review-analysis", "domain: product", "status: generated", f"updated: {args.date}", "tags: [waje, google-play, user-feedback, operations]", "---", "", f"# Waje Google Play 用户评价分析｜{args.date}", "", "来源：[Waje Casino - Games & Sports](https://play.google.com/store/apps/details?id=com.hfhy.waje.special&hl=en-gb&gl=ng&pli=1)", "", f"本批新增评价：{len(primary_items)} 条；本次观察评价：{len(items)} 条；开发者回复：{reply_count} 条；证据等级：D（公开评论线索）。", "", "[打开 HTML 数据日报](./日报/" + args.date + "-Google%20Play用户评价日报.html)", "", "## 数据质量", "", f"- 采集状态：`{quality.get('status', 'unknown')}`；停止原因：`{quality.get('source_health', {}).get('stop_reason', 'unknown')}`。", f"- 本批新增评价：{state_counts.get('new_count', 0)}；评价更新：{state_counts.get('updated_count', 0)}；已见评价：{state_counts.get('already_seen_count', 0)}；短缺：{state_counts.get('shortfall', 0)}。", f"- 去重后评价：{quality.get('content_health', {}).get('unique_count', len(items))}；版本变化：{quality.get('content_health', {}).get('version_change_count', 0)}。", "", "## 主题分布", ""]
    for topic, count in topic_counts.most_common(): lines.append(f"- {TOPIC_LABELS.get(topic, topic)}：{count}")
    lines += ["", "## 严重度分布", "", *[f"- {severity}：{severity_counts.get(severity, 0)}" for severity in ("P0", "P1", "P2")], "", "## 运营优先事项", ""]
    for item in [item for item in primary_items if item.get("severity") in {"P0", "P1"}][:30]:
        text = (item.get("review_text") or "").replace("\n", " ")[:280]
        lines.append(f"- **{item.get('severity')}｜{item.get('operation_intent')}**：{text}（{item.get('review_date_display') or '日期未知'}）")
    if not any(item.get("severity") in {"P0", "P1"} for item in primary_items): lines.append("- 本批次没有规则命中的 P0/P1，继续监测 P2 反馈并人工复核高互动评价。")
    lines += ["", "## 回复运营观察", "", "- `support_handoff`：将用户导向 Live Chat/Telegram，需结合后续工单数据验证是否解决。", "- `fairness_explanation`：强调 RNG/公平性，不能替代具体资金或结算核查。", "- 单条公开评论不能直接证明真实事故、欺诈或系统故障。", ""]
    target = target_dir / f"{args.date}-Google Play用户评价分析.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    index = target_dir / "README.md"
    if not index.exists():
        index.write_text("---\ntype: moc\nstatus: active\ntags: [google-play, user-feedback]\n---\n\n# Google Play 用户评价知识库\n\n按日记录公开评价、开发者回复、主题分布和运营线索。公开评论属于 D 级证据，不能替代内部订单、客服或资金流水核验。\n", encoding="utf-8")
    print(f"knowledge note={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

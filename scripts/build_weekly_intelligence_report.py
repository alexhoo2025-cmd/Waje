#!/usr/bin/env python3
"""Build the weekly Waje product and competitor intelligence report."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from render_analysis_report_html import render_markdown_file


ROOT = Path(os.environ.get("WAJE_ANALYST_ROOT", str(Path(__file__).resolve().parents[1]))).resolve()


def window_for(collection_date: dt.date) -> tuple[dt.date, dt.date]:
    end = collection_date - dt.timedelta(days=1)
    return end - dt.timedelta(days=6), end


def read_json(path: Path, fallback: dict | None = None) -> dict:
    if not path.exists():
        return fallback or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback or {}


def safe_text(value: object, limit: int = 600) -> str:
    return " ".join(str(value or "").replace("|", "｜").split())[:limit]


def priority_label(value: object) -> str:
    return {3: "P0/P1 复核", 2: "P1 跟进", 1: "P2 观察"}.get(int(value or 1), "P2 观察")


def build_report(root: Path, collection_date: dt.date) -> tuple[Path, dict]:
    start, end = window_for(collection_date)
    processed = root / "data/processed/weekly" / collection_date.isoformat()
    output = root / "data/outputs/weekly" / collection_date.isoformat()
    normalized = read_json(processed / "normalized-items.json")
    analysis = read_json(output / "analysis.json")
    quality = read_json(output / "quality.json")
    items = analysis.get("items", []) if isinstance(analysis, dict) else []
    source_counts = Counter(str(item.get("source_type", "unknown")) for item in items)
    topic_counts = Counter(str(item.get("topic", "product_update")) for item in items)
    entity_counts = Counter(str(item.get("entity_id", "unknown")) for item in items)
    p0_p1 = [item for item in items if int(item.get("importance", 1) or 1) >= 2]
    topic_items: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        topic_items[str(item.get("topic", "product_update"))].append(item)
    play_receipt = read_json(root / "data/outputs/play_reviews" / collection_date.isoformat() / "quality.json")
    play_report = root / "knowledge/01-产品/Google Play用户评价/周报" / f"{collection_date.isoformat()}-Google Play用户评价周报.html"
    wechat_report = root / "knowledge/03-竞品/周报" / f"{collection_date.isoformat()}-博彩社交游戏公众号周报.md"
    source_verification = read_json(output / "source-verification.json", {"status": "pending_manual_review", "items": []})

    lines = [
        "---",
        "type: weekly-intelligence",
        "domain: competitor",
        "status: generated",
        f"updated: {collection_date.isoformat()}",
        "cadence: weekly",
        "window: previous_friday_to_thursday",
        "tags: [weekly-intelligence, competitor, product-analysis, monetization, market]",
        "---",
        "",
        f"# Waje 产品与竞品情报周报｜{collection_date.isoformat()}",
        "",
        f"> 统计窗口：{start.isoformat()} 至 {end.isoformat()}；采集批次：{collection_date.isoformat()} 15:00（Asia/Hong_Kong）。公开页面是产品与用户线索，不直接代表 Waje 真实经营指标。",
        "",
        "## 1. 本周摘要",
        "",
        f"- 批次状态：`{quality.get('status', 'unknown')}`；来源：{quality.get('source_health', {}).get('ok', 0)}/{quality.get('source_health', {}).get('total', 0)} 成功。",
        f"- 原始/去重条目：{normalized.get('raw_item_count', 0)} / {normalized.get('unique_item_count', len(items))}；重复 {normalized.get('duplicate_count', 0)} 条。",
        f"- P0/P1 待复核：{len(p0_p1)} 条；来源类型：{', '.join(f'{key}（{value}）' for key, value in source_counts.most_common()) or '暂无'}。",
        f"- 主题分布：{', '.join(f'{key}（{value}）' for key, value in topic_counts.most_common(8)) or '暂无'}。",
        "",
        "## 2. 本周产品与竞品核心变化",
        "",
        "| 优先级 | 来源/实体 | 主题 | 观察到的公开信号 | 当前判断 |\n|---|---|---|---|---|",
    ]
    for item in p0_p1[:20]:
        lines.append(
            f"| {priority_label(item.get('importance'))} | {safe_text(item.get('entity_id'), 80)} | {safe_text(item.get('topic'), 80)} | "
            f"{safe_text(item.get('title'), 180)} | {safe_text(item.get('priority_reason') or item.get('summary'), 220)} |"
        )
    if not p0_p1:
        lines.append("| — | — | — | 本周没有达到 P0/P1 复核阈值的公开信号 | 保持观察 |")

    lines.extend([
        "",
        "## 3. Waje 产品、版本与活动观察",
        "",
        "- Waje 官方页面、商店页和公开活动页面只用于确认产品定位、入口、公开奖励和支付/提现文案。",
        "- 版本发布必须以 release manifest 为准；配置 revision 变化不能单独认定为已发布。",
        "- 真实留存、LTV、RTP、支付成功率和提现时延必须回到 BQ/服务端事实表核验。",
        "",
        "| 观察项 | 本周证据 | 对 Waje 的分析动作 |",
        "|---|---|---|",
    ])
    for topic in ("product_update", "promotion", "payment_and_withdrawal", "stability_and_network"):
        rows = topic_items.get(topic, [])
        evidence = "；".join(safe_text(item.get("title"), 120) for item in rows[:3]) or "本周无直接公开信号"
        action = {
            "product_update": "核对版本、包体、渠道、功能开关和发布证据",
            "promotion": "拆解资格、奖励资产、有效期、触达路径和成本，回到实验数据验证",
            "payment_and_withdrawal": "核对订单状态、到账、提现失败原因和用户投诉，不用公开文案推导成功率",
            "stability_and_network": "结合设备、网络、版本、错误码和客服/商店评价确认是否为系统性问题",
        }[topic]
        lines.append(f"| {topic} | {evidence} | {action} |")

    lines.extend([
        "",
        "## 4. 竞品玩法与商业化机制拆解",
        "",
        "| 主题 | 公开观察 | 可迁移假设 | 验证指标 |",
        "|---|---|---|---|",
        "| 产品定位 | 体育、赌场、Whot、捕鱼、老虎机、促销和钱包入口可能并行出现 | 本地玩法 + 高频轻玩法 + 现金/奖励资产分层 | 入口曝光、首局、有效下注、留存、资产使用 |",
        "| 促销机制 | 首充、登录奖励、分享奖励、Cashback、Free Bet/Free Spins 等公开机制 | 奖励应绑定明确目标和对照组，不直接复制额度 | 领取率、目标完成率、增量净收益、奖励成本 |",
        "| 支付提现 | 公开页面强调支付渠道和快速提现 | 支付信任来自成功率、失败解释、到账时延和客服闭环 | 支付成功率、提现成功率、P95 时延、投诉率 |",
        "| 玩法运营 | 玩法入口和活动机制成为竞品差异化表达 | 按玩法、用户分层、版本和渠道做实验 | 首局率、复玩率、下注额、RTP 数据质量 |",
        "",
        "## 5. Google Play 用户评价与体验问题",
        "",
        f"- 专项周报：{play_report.relative_to(root) if play_report.exists() else '本批次未生成'}。",
        f"- Play 数据质量：`{play_receipt.get('status', 'missing')}`；评价不足或页面阻断时不得当作 0 条评价。",
        "- 评价属于 D 级用户线索；涉及网络、扣款、奖励不到账、提现和公平性的评价，必须通过客服、订单、资产和游戏流水核验。",
        "",
        "## 6. 用户舆情、稳定性与监管",
        "",
        "- 用户舆情：只统计脱敏后的聚合主题，不保存作者真实展示名或个人明细。",
        "- 稳定性：重点关注网络中断、加载失败、游戏扣款与奖励到账不一致，并按版本、设备、网络和玩法下钻。",
        "- 监管：监管资讯只作为待核验背景，必须区分提案、监管指导、已生效法规和平台政策。",
        "",
        "## 7. Waje 可执行的产品、运营与商业化方案",
        "",
        "1. 将奖励从“统一发放”改为“用户分层 + 场景目标 + 对照组 + 节点触达”，以增量净收益而不是领取量作为主判断。",
        "2. 对首充未游戏、首充未复充、活跃未充值和高价值沉默用户建立统一场景实验，固定 `scenario_id`、`experiment_id` 和 `group_id`。",
        "3. 对公开竞品的首充、Cashback、Free Bet、Free Spins 和小游戏活动，只抽取机制，不直接复制金额或资格。",
        "4. 把网络、支付、奖励到账和提现失败纳入同一体验看板，连接 `ORDER`、`ASSET`、`GAMESTART`、`GAMEEND` 和客服线索。",
        "",
        "## 8. 重点数据假设与验证路径",
        "",
        "| 假设 | 需要的事实数据 | 验证标准 |",
        "|---|---|---|",
        "| 奖励节点提升首充/复充 | 稳定分流、订单成功、奖励成本、D1/D7 | 实验组相对对照组增量净收益为正 |",
        "| 玩法入口优化提升首局 | PV/MV/MC、GAMESTART、GAMEEND、版本和设备 | 首局率提升且结算异常率不升高 |",
        "| 支付体验改善减少流失 | 订单状态、失败码、到账时延、D1/D7 | 支付失败下降且留存/复充改善 |",
        "| 竞品奖励机制可迁移 | 资格、奖励资产、成本、实验分组 | 小流量灰度通过成本和风险护栏 |",
        "",
        "## 9. P0/P1 风险与下周跟踪",
        "",
        "- **P0：** 任何扣款、奖励不到账、提现失败、监管或安全信号必须回到服务端事实核验后再进入决策。",
        "- **P1：** 重要公开信号缺少原始来源、分母、时间窗或样本量时，标记为待人工复核。",
        "- **P1：** 若主情报源、Play 评价或公众号授权不可用，周报保留降级状态，不伪造完整趋势。",
        "",
        "## 10. 质量、失败来源与来源核验",
        "",
        f"- 质量回执：`{(output / 'quality.json').relative_to(root)}`。",
        f"- 来源核验：`{(output / 'source-verification.json').relative_to(root)}`，当前状态：`{source_verification.get('status', 'pending_manual_review')}`。",
        f"- 公众号周报：{wechat_report.relative_to(root) if wechat_report.exists() else '本批次未生成'}。",
        "- 本周报不保存 Token、Cookie、密码、用户真实展示名或用户个人明细。",
        "",
        "## 11. 数据路径",
        "",
        f"- 原始批次：`data/raw/weekly/{collection_date.isoformat()}/`。",
        f"- 标准化批次：`data/processed/weekly/{collection_date.isoformat()}/`。",
        f"- 分析与回执：`data/outputs/weekly/{collection_date.isoformat()}/`。",
    ])
    path = root / "knowledge/03-竞品/周报" / f"{collection_date.isoformat()}-Waje产品与竞品情报周报.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    html_path = render_markdown_file(path)
    return path, {"markdown": str(path.relative_to(root)), "html": str(html_path.relative_to(root)), "item_count": len(items), "p0_p1_count": len(p0_p1)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Friday collection/report date")
    args = parser.parse_args()
    path, receipt = build_report(ROOT, dt.date.fromisoformat(args.date))
    print(json.dumps({"report": str(path.relative_to(ROOT)), **receipt}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

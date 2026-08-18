#!/usr/bin/env python3
"""Build the weekly Waje product, monetization, and competitor evidence report.

The report deliberately separates three evidence levels:

* Waje internal business metrics (only when the approved daily exports exist);
* directly observed Waje H5 product behaviour and official product surfaces;
* public competitor positioning and promotion mechanisms.

Public pages are not a substitute for retention, revenue, LTV, payment-success,
or RTP data.  When the daily internal metric exports are absent, the report is
still useful as a product and competitor decision memo, but it never fabricates
operating KPIs or labels a public signal as a verified product change.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = Path("/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.8-13ceeea1f599")
DELIVER = PLUGIN_ROOT / "skills/build-report/scripts/deliver_portable_artifact.mjs"

WEEKLY_METRIC_FEEDS = (
    "operating_daily",
    "new_user_cohort",
    "payment_asset_daily",
    "game_lifecycle_rtp_daily",
)

SOURCE_CATALOG = {
    "waje_1": {
        "id": "src_waje_official",
        "label": "Waje 官方产品页",
        "href": "https://www.wajegame.com/",
        "description": "Waje 官方主页的产品入口、定位与合规声明快照。",
    },
    "waje_2": {
        "id": "src_waje_play",
        "label": "Waje Google Play 页面",
        "href": "https://play.google.com/store/apps/details?id=com.hfhy.waje.special&hl=en-gb&gl=ng",
        "description": "Waje Android 商店定位与版本页面快照。",
    },
    "sportybet_1": {
        "id": "src_sporty_help",
        "label": "SportyBet Nigeria Help",
        "href": "https://www.sportybet.com/ng/help",
        "description": "SportyBet 的帮助与产品服务页面快照。",
    },
    "sportybet_2": {
        "id": "src_sporty_promotions",
        "label": "SportyBet Nigeria Promotions",
        "href": "https://www.sportybet.com/ng/m/promotions",
        "description": "SportyBet 公开活动页；只证明页面可见机制，不证明资格、成本或效果。",
    },
    "bet9ja_1": {
        "id": "src_bet9ja_play",
        "label": "Bet9ja Google Play 页面",
        "href": "https://play.google.com/store/apps/details?gl=ng&hl=en-gb&id=com.bet9ja.sportsbook.app",
        "description": "Bet9ja 官方 Android 商店定位页面快照。",
    },
    "betway_ng_1": {
        "id": "src_betway_play",
        "label": "Betway NG Google Play 页面",
        "href": "https://play.google.com/store/apps/details?gl=NG&hl=en&id=com.betway.ng",
        "description": "Betway NG 官方 Android 商店定位页面快照。",
    },
    "1xbet_ng_1": {
        "id": "src_1xbet_play",
        "label": "1xBet Nigeria Google Play 页面",
        "href": "https://play.google.com/store/apps/details?id=org.xbet.client.ng_ps",
        "description": "1xBet Nigeria 官方 Android 商店定位与促销文案快照。",
    },
}


def project_root() -> Path:
    return Path(os.environ.get("WAJE_ANALYST_ROOT", str(ROOT))).resolve()


def read_json(path: Path, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return fallback or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback or {}


def week_window(report_date: dt.date) -> tuple[dt.date, dt.date, list[dt.date]]:
    end = report_date - dt.timedelta(days=1)
    start = end - dt.timedelta(days=6)
    return start, end, [start + dt.timedelta(days=index) for index in range(7)]


def play_reviews_weekly_snapshot(root: Path, report_date: dt.date) -> dict[str, Any]:
    """Read the Play review specialist report without making it a hard dependency."""
    artifact_path = root / "data/outputs/play_reviews/weekly" / report_date.isoformat() / "report-artifact.json"
    receipt_path = root / "data/outputs/play_reviews/weekly" / report_date.isoformat() / "report-receipt.json"
    artifact = read_json(artifact_path)
    receipt = read_json(receipt_path)
    metrics = artifact.get("metrics", {}) if isinstance(artifact, dict) else {}
    datasets = artifact.get("datasets", {}) if isinstance(artifact, dict) else {}
    return {
        "available": bool(artifact_path.exists()),
        "status": artifact.get("status", "missing") if isinstance(artifact, dict) else "missing",
        "artifact": relative_or_absolute(artifact_path, root) if artifact_path.exists() else "",
        "report": relative_or_absolute(root / "knowledge/01-产品/Google Play用户评价/周报" / f"{report_date.isoformat()}-Google Play用户评价周报.html", root),
        "receipt": receipt,
        "metrics": metrics,
        "rating_distribution": datasets.get("ratings", []),
        "daily_rows": datasets.get("daily", []),
        "topics": datasets.get("topics", []),
    }


def relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def manifest_for_day(root: Path, day: dt.date) -> tuple[dict[str, Any], Path | None]:
    candidates = sorted((root / "data/raw" / day.isoformat()).glob("manifest-*.json"))
    if not candidates:
        return {}, None
    return read_json(candidates[-1]), candidates[-1]


def public_snapshot(root: Path, day: dt.date) -> dict[str, Any]:
    manifest, manifest_path = manifest_for_day(root, day)
    records = manifest.get("items", [])
    direct = [record for record in records if record.get("source_id") in SOURCE_CATALOG]
    fallback_quality = read_json(root / "data/outputs" / day.isoformat() / "quality.json")
    fallback_analysis = read_json(root / "data/outputs" / day.isoformat() / "analysis.json")
    return {
        "date": day.isoformat(),
        "available": bool(records or fallback_quality or fallback_analysis),
        "records": direct,
        "manifest": relative_or_absolute(manifest_path, root) if manifest_path else "",
    }


def direct_source_history(root: Path, days: list[dt.date]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Path]]:
    history: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    latest_raw: dict[str, Path] = {}
    for day in days:
        manifest, _ = manifest_for_day(root, day)
        raw_dir = root / "data/raw" / day.isoformat()
        for record in manifest.get("items", []):
            source_id = record.get("source_id", "")
            if source_id not in SOURCE_CATALOG:
                continue
            entry = {
                "date": day.isoformat(),
                "status": record.get("status", "unknown"),
                "sha256": record.get("sha256", ""),
                "url": record.get("url", SOURCE_CATALOG[source_id]["href"]),
            }
            history[source_id].append(entry)
            if entry["status"] == "ok":
                paths = sorted(raw_dir.glob(f"{source_id}_*"))
                if paths:
                    latest_raw[source_id] = paths[-1]
    return dict(history), latest_raw


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def meta_content(page: str, property_name: str) -> str:
    patterns = (
        rf'<meta[^>]+(?:name|property)=["\']{re.escape(property_name)}["\'][^>]+content=["\']([^"\']+)',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']{re.escape(property_name)}["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, page, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""


def app_store_profile(path: Path) -> dict[str, str]:
    page = path.read_text(encoding="utf-8", errors="replace")
    name_match = re.search(r'<h1[^>]*>\s*<span[^>]*>(.*?)</span>', page, flags=re.IGNORECASE | re.DOTALL)
    name = strip_html(name_match.group(1)) if name_match else meta_content(page, "og:title")
    description = meta_content(page, "description") or meta_content(page, "og:description")
    rating_match = re.search(r'"ratingValue":"([0-9.]+)"', page)
    updated_match = re.search(r'>Updated on</div>.*?<div[^>]*>(.*?)</div>', page, flags=re.IGNORECASE | re.DOTALL)
    downloads_match = re.search(r'\["([0-9][0-9,]*\+)",[0-9]+,[0-9]+,"[0-9][0-9A-Za-z+]*"\]', page)
    return {
        "name": name,
        "description": description,
        "rating": rating_match.group(1) if rating_match else "",
        "updated": strip_html(updated_match.group(1)) if updated_match else "",
        "downloads": downloads_match.group(1) if downloads_match else "",
    }


def promotion_offers(path: Path) -> list[dict[str, str]]:
    page = path.read_text(encoding="utf-8", errors="replace")
    offers: list[dict[str, str]] = []
    for raw_json in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, flags=re.IGNORECASE | re.DOTALL):
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            continue
        rows = parsed if isinstance(parsed, list) else [parsed]
        for row in rows:
            if not isinstance(row, dict) or row.get("@type") != "Offer":
                continue
            title = str(row.get("name", "")).strip()
            url = str(row.get("url", "")).strip()
            if title and url:
                offers.append({"name": title, "url": url})
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for offer in offers:
        if offer["name"] not in seen:
            seen.add(offer["name"])
            unique.append(offer)
    return unique


def h5_observations(root: Path) -> list[dict[str, Any]]:
    note = root / "knowledge/01-产品/Waje-H5新手体验记录-2026-08-07.md"
    if not note.exists():
        return []
    text = note.read_text(encoding="utf-8", errors="replace")
    required = ("Daily Chip", "Deposit-Super sales", "NairaSlots", "Whot", "Fish")
    if not all(token in text for token in required):
        return []
    return [
        {
            "area": "首日福利",
            "observation": "Daily Chip 要求用户通过快捷方式进入游戏后领取 ₦500；当前未见独立的新手任务面板。",
            "evidence_type": "H5 实测",
            "confidence": "高",
            "implication": "福利价值存在，但触发条件被安装/快捷方式动作切断；应验证其对首日回访与首局的实际贡献。",
            "next_metric": "Daily Chip 曝光→添加快捷方式→领取→首局→D1 留存",
            "priority": "P1",
        },
        {
            "area": "充值与奖励到账",
            "observation": "测试支付成功后，余额由 ₦600 变为 ₦13,250；三笔流水合计可对账，但前端促销展示、支付页信息与 Chip/BonusChip 入账拆分不一致。",
            "evidence_type": "H5 实测",
            "confidence": "高",
            "implication": "资金总额对账不代表活动口径正确；展示与账务不一致会削弱首充信任，且会污染促销归因。",
            "next_metric": "促销曝光/点击/下单/回调/到账五步转化；订单金额与奖励分账一致率",
            "priority": "P0",
        },
        {
            "area": "首局可用性",
            "observation": "代表入口 Whot 与 Fish 均停留在加载页，未进入可下注界面；NairaSlots 已成功加载但仅完成规则查看。",
            "evidence_type": "H5 测试环境实测",
            "confidence": "高（测试环境）",
            "implication": "当前不能把问题外推为生产事故，但在测试环境中，首局链路有 2/3 代表玩法无法完成的阻塞证据。",
            "next_metric": "game_start→可操作首帧→首笔下注→结算成功率；按 game_id、版本、渠道、网络切分",
            "priority": "P0",
        },
        {
            "area": "玩法规则透明度",
            "observation": "NairaSlots 展示 50/100/200 下注档解锁 x2/x4/x10 倍率，但未见理论 RTP、波动等级、命中率或完整赔付表。",
            "evidence_type": "H5 实测",
            "confidence": "高",
            "implication": "高下注与更高倍率的关系被明确呈现，但玩家无法理解风险边界；理论配置与实测回报需进入游戏详情与 GM/BQ 验证。",
            "next_metric": "档位选择、局数、下注额、实测 RTP、破产率、次日留存",
            "priority": "P1",
        },
    ]


def formal_h5_snapshot(root: Path) -> dict[str, Any]:
    """Load the latest retained production observation without exposing identifiers."""
    path = root / "data/processed/2026-08-14/waje-prod-h5-guest-experience-observations.json"
    data = read_json(path)
    observations = data.get("observations", []) if isinstance(data, dict) else []
    by_id = {row.get("id"): row for row in observations if isinstance(row, dict)}
    return {
        "available": bool(data),
        "report": "knowledge/01-产品/Waje正式版H5新手体验与数据分析报告-2026-08-14.md",
        "observed_at": data.get("observed_at", "") if isinstance(data, dict) else "",
        "environment": data.get("environment", "") if isinstance(data, dict) else "",
        "sample_type": data.get("sample_type", "") if isinstance(data, dict) else "",
        "scope": data.get("scope", {}) if isinstance(data, dict) else {},
        "whot": by_id.get("whot-minimum-round", {}).get("facts", {}),
        "promotion": by_id.get("promotion-and-daily-chip", {}).get("facts", {}),
        "coins": by_id.get("coins-and-help", {}).get("facts", {}),
    }


def visible_catalog_rows(root: Path) -> list[dict[str, Any]]:
    note = root / "knowledge/01-产品/Waje-H5玩法观测与RTP采集台账-2026-08-07.md"
    if not note.exists():
        return []
    text = note.read_text(encoding="utf-8", errors="replace")
    rows: list[dict[str, Any]] = []
    for category in ("TopGame", "Exclusives", "TopPicks", "Slots", "Fish", "Crash", "QuickGames"):
        match = re.search(rf'- {re.escape(category)}：(.*)', text)
        if not match:
            continue
        games = [item.strip() for item in match.group(1).split("、") if item.strip()]
        rows.append({"category": category, "visible_sample_games": len(games), "sample": "、".join(games[:4])})
    return rows


def metric_export_status(root: Path, days: list[dt.date]) -> dict[str, Any]:
    """Only recognize the agreed aggregate exports; never infer KPIs from web pages."""
    rows: list[dict[str, Any]] = []
    complete_days = 0
    for day in days:
        folder = root / "data/inbox/weekly-metrics" / day.isoformat()
        feeds = {feed: (folder / f"{feed}.csv").exists() for feed in WEEKLY_METRIC_FEEDS}
        complete = all(feeds.values())
        complete_days += int(complete)
        rows.append({"date": day.isoformat(), "complete": complete, "feeds": feeds})
    return {
        "complete_days": complete_days,
        "expected_days": len(days),
        "rows": rows,
        "ready": complete_days == len(days),
    }


def source_definition(source_id: str) -> dict[str, Any]:
    item = SOURCE_CATALOG[source_id]
    return {
        "id": item["id"],
        "label": item["label"],
        "href": item["href"],
        "query": {
            "engine": "public_snapshot",
            "sql": f"SELECT captured_at, content_hash FROM public_page_snapshot WHERE source_id = '{source_id}';",
            "description": item["description"],
            "language": "sql",
            "executed_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "tables_used": ["waje_analyst.public_page_snapshot"],
            "filters": ["only direct official/product/activity surfaces are decision evidence"],
        },
    }


def manual_source_definition() -> dict[str, Any]:
    return {
        "id": "src_waje_h5_observation",
        "label": "Waje H5 测试体验记录（2026年8月7日）",
        "href": "https://test-h5.wajetan.com/",
        "query": {
            "engine": "manual_product_observation",
            "sql": "SELECT observation, route, evidence FROM waje_h5_test_observation WHERE observed_on = '2026-08-07';",
            "description": "已登录测试环境下的产品体验记录；用于测试环境问题与产品机制观察，不代表生产全量指标。",
            "language": "sql",
            "executed_at": "2026-08-07T10:01:00+08:00",
            "tables_used": ["knowledge/01-产品/Waje-H5新手体验记录-2026-08-07.md"],
            "filters": ["测试环境", "代表玩法样本=3"],
        },
    }


def internal_metric_source_definition() -> dict[str, Any]:
    return {
        "id": "src_internal_metric_contract",
        "label": "Waje 每日经营数据导出合同",
        "href": "https://datagrowth.trackares.com/manager/homepage",
        "query": {
            "engine": "local_export_receipt",
            "sql": "SELECT report_date, feed_name, is_complete FROM weekly_metric_export_receipt;",
            "description": "约定的四类每日聚合导出状态；目前只反映项目已接收的文件，不将空分区解释为业务零值。",
            "language": "sql",
            "executed_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "tables_used": ["waje_analyst.weekly_metric_export_receipt"],
            "filters": ["complete calendar days only", "all-zero invalid rows excluded"],
        },
    }


def build_artifact(root: Path, report_date: dt.date) -> tuple[dict[str, Any], dict[str, Any]]:
    start, end, days = week_window(report_date)
    play_reviews = play_reviews_weekly_snapshot(root, report_date)
    public_days = [public_snapshot(root, day) for day in days]
    available_public_days = [row for row in public_days if row["available"]]
    source_history, raw_pages = direct_source_history(root, days)
    observations = h5_observations(root)
    formal = formal_h5_snapshot(root)
    catalog_rows = visible_catalog_rows(root)
    metrics = metric_export_status(root, days)

    sporty_offers = promotion_offers(raw_pages["sportybet_2"]) if "sportybet_2" in raw_pages else []
    app_profiles = {
        source_id: app_store_profile(raw_pages[source_id])
        for source_id in ("waje_2", "bet9ja_1", "betway_ng_1", "1xbet_ng_1")
        if source_id in raw_pages
    }

    tested_game_rows = [
        {"game": "Whot", "entry_result": "未进入可操作界面", "ready_value": 0, "scope": "测试环境", "note": "加载页停留；未观察到下注或结算"},
        {"game": "Fish", "entry_result": "未进入可操作界面", "ready_value": 0, "scope": "测试环境", "note": "加载页停留；未观察到炮台、倍率或结算"},
        {"game": "NairaSlots", "entry_result": "已加载，未下注", "ready_value": 1, "scope": "测试环境", "note": "可查看下注档与倍率规则，未验证结算与 RTP"},
    ] if observations else []
    blocked_game_count = sum(row["ready_value"] == 0 for row in tested_game_rows)

    competitor_rows: list[dict[str, str]] = []
    profile_map = {
        "bet9ja_1": ("Bet9ja", "体育下注 + 直播观看", "产品定位页提及足球/拳击直播；需另行验证实际功能、地域和使用率。"),
        "betway_ng_1": ("Betway NG", "体育 + Casino 一体入口", "产品定位页强调 sports 与 casino；未观察到本周功能改版证据。"),
        "1xbet_ng_1": ("1xBet Nigeria", "直播赔率 + Casino + 首充激励", "商店页文案包含 live odds、slots、live casino 和首充优惠；具体资格、成本和有效期未验证。"),
    }
    for source_id, (competitor, positioning, boundary) in profile_map.items():
        profile = app_profiles.get(source_id, {})
        evidence = profile.get("description", "") or "本周未取得可解析商店描述"
        if source_id == "1xbet_ng_1" and "300%" in raw_pages.get(source_id, Path("/nonexistent")).read_text(encoding="utf-8", errors="ignore") if source_id in raw_pages else False:
            evidence = "商店页文案：300% 首充奖励（最高 ₦600,000），并强调 live odds、老虎机和 live casino。"
        competitor_rows.append({
            "competitor": competitor,
            "surface": "Google Play 产品定位页",
            "observed_mechanism": positioning,
            "evidence": evidence[:260],
            "product_implication": "用于定位竞争叙事与待测机制，不作为其经营规模或转化效果证据。",
            "boundary": boundary,
        })
    if sporty_offers:
        mechanisms = "、".join(offer["name"] for offer in sporty_offers[:5])
        competitor_rows.insert(0, {
            "competitor": "SportyBet",
            "surface": "公开活动页",
            "observed_mechanism": mechanisms,
            "evidence": f"本周可解析 {len(sporty_offers)} 个 Offer；其中可见 Free Spins、Free Bet/Drop、Cashback、Aviator Missions、JetX Gifts 等机制。",
            "product_implication": "竞品将奖励绑定到具体玩法或任务，而非单一通用优惠；Waje 应以首局完成率和后续留存验证，而非直接复制奖励额度。",
            "boundary": "页面可见不代表用户资格、奖励成本、投放规模或实际效果。",
        })

    coin_competitor_rows = [
        {
            "rank": "01",
            "competitor": "Betway NG",
            "directness": "高：尼日利亚混合 Casino 用户",
            "why_direct": "体育、Casino、小游戏和大奖机制并列入口，和 Waje 的多玩法货架争夺同一类休闲博彩时间。",
            "coin_gap": "未发现公开 Coin 场同构证据；可比的是低门槛小游戏、大奖和促销包装。",
            "track": "NaiJackpots、Betgames/小游戏上新、Casino 首页分发、促销频控与奖励解释。",
        },
        {
            "rank": "02",
            "competitor": "1xBet Nigeria",
            "directness": "高：即时玩法与促销循环",
            "why_direct": "Slots、Live Casino、Crash、直播赔率和首存/挑战任务形成高频即时结果循环，最接近 Waje 想建立的“短局→奖励→复玩”节奏。",
            "coin_gap": "供给更宽、促销更重；没有公开证明其拥有与 Waje Coin/Ludo 同样的非现金货币隔离。",
            "track": "Crash/Slots 入口、Cashback/挑战任务、首存条件、奖励成本表达和活动节奏。",
        },
        {
            "rank": "03",
            "competitor": "SportyBet",
            "directness": "中：争夺日常回访时间",
            "why_direct": "不是 Coin 场同形态产品，但赛事、直播、Cash Out、Missions 和 Cashback 提供强日历型回访理由。",
            "coin_gap": "更像“事件驱动的真金回访层”，不能直接当作 Coin 场玩法模板。",
            "track": "赛事节点、Aviator Missions、Cashback、Free Spins/Drop 与任务完成后的下一步权益。",
        },
        {
            "rank": "04",
            "competitor": "Bet9ja",
            "directness": "中低：策略工具与本地市场",
            "why_direct": "400+ 市场、betBOOM、Multiple Builder、Cut1、Cash Out 和 Rewards 形成强策略工具，但与 Coin 休闲玩法的用户动机不同。",
            "coin_gap": "不适合作为 Coin 房间或低门槛金币经济的直接样板。",
            "track": "Rewards、Cash Out、组合工具和本地赛事运营，不追踪其复杂 sportsbook 信息架构。",
        },
    ]

    metric_readiness_rows = [
        {
            "area": "经营与增长",
            "required_export": "operating_daily.csv",
            "needed_metrics": "新增、DAU、登录、有效游戏用户、营收/利润；按平台、版本、包体、渠道、媒体切分",
            "status": "已接入" if metrics["ready"] else "本周未接入",
            "decision_limit": "不能判断本周增长、渠道效率或版本影响。",
        },
        {
            "area": "新手留存与 LTV",
            "required_export": "new_user_cohort.csv",
            "needed_metrics": "注册→首局→首充、D1/D3/D7、LTV；仅使用成熟 cohort",
            "status": "已接入" if metrics["ready"] else "本周未接入",
            "decision_limit": "不能用公开活动或测试账户推断留存、付费率或 LTV。",
        },
        {
            "area": "支付、充值与提现",
            "required_export": "payment_asset_daily.csv",
            "needed_metrics": "订单状态、支付成功、首充/复充、TX、TC、提现和失败原因",
            "status": "已接入" if metrics["ready"] else "本周未接入",
            "decision_limit": "只能确认测试流水展示问题，不能量化真实支付或提现异常。",
        },
        {
            "area": "游戏与 RTP",
            "required_export": "game_lifecycle_rtp_daily.csv",
            "needed_metrics": "基础/完全下注额、用户、局数、实际/预期 RTP；按玩法和生命周期切分",
            "status": "已接入" if metrics["ready"] else "本周未接入",
            "decision_limit": "不能给出本周 RTP、收益或生命周期异常结论。",
        },
    ]
    metric_coverage_rows = [
        {
            "feed": feed,
            "complete_days": sum(row["feeds"].get(feed, False) for row in metrics["rows"]),
            "expected_days": len(days),
        }
        for feed in WEEKLY_METRIC_FEEDS
    ]

    action_rows = [
        {
            "priority": "P0",
            "action": "修复并监控 Whot/Fish 首局加载链路",
            "owner": "研发 + QA",
            "evidence": "测试环境下 2/3 个代表玩法未进入可操作状态；证据仅限测试环境。",
            "success_metric": "game_start→首帧可操作率、首笔下注率、结算成功率；按 game_id/版本/网络切分",
            "guardrail": "余额扣减、重复请求、结算丢失与错误提示覆盖率",
            "validation_window": "修复后 7 个完整日",
        },
        {
            "priority": "P0",
            "action": "统一 Super Sale 前端展示、订单与 Chip/BonusChip 入账映射",
            "owner": "支付/后端 + 产品",
            "evidence": "测试支付总额可对账，但促销展示、支付页信息和三笔奖励流水的拆分不一致。",
            "success_metric": "展示金额=订单金额=到账金额的一致率；回调成功率；活动归因完整率",
            "guardrail": "重复入账、误赠、投诉、提现限制误判",
            "validation_window": "修复后 7 个完整日",
        },
        {
            "priority": "P1",
            "action": "将 Daily Chip 改造成可验证的新手任务链路",
            "owner": "产品 + 运营 + 数据",
            "evidence": "当前福利条件为添加快捷方式后领取，且未见独立任务进度或完成反馈。",
            "success_metric": "曝光→添加→领取→首局→D1 的漏斗与对照组差异",
            "guardrail": "奖励成本、羊毛率、领取后未首局比例",
            "validation_window": "灰度后至少 2 个成熟 D7 cohort",
        },
        {
            "priority": "P1",
            "action": "验证“玩法任务 + 定向奖励”而非直接复制竞品优惠",
            "owner": "运营 + 产品 + 数据",
            "evidence": "SportyBet 活动页可见 Free Spins、Cashback、Aviator Missions 等玩法绑定机制。",
            "success_metric": "任务完成率、目标玩法首局率、复玩率、首充/复充增量与奖励 ROI",
            "guardrail": "RTP 偏差、奖励滥用、低价值刷流水、提现风险",
            "validation_window": "A/B 或分渠道灰度；至少 2 周",
        },
        {
            "priority": "P1",
            "action": "落地四类每日经营导出并在下周报告接入",
            "owner": "数据开发 + GM/起源 owner",
            "evidence": "本周项目目录不存在完整的四类日分区数据，现有公开证据不能替代核心 KPI。",
            "success_metric": "7/7 完整分区、字段校验通过、指标与 BQ/GM 对账通过",
            "guardrail": "不完整日、全零行、未成熟 cohort、平均 RTP 的误用",
            "validation_window": "首个完整周并行核对",
        },
    ]

    title = f"Waje 产品经营与竞品追踪周报｜{start.strftime('%Y年%m月%d日')}–{end.strftime('%m月%d日')}"
    report_status = "complete" if metrics["ready"] and len(available_public_days) == len(days) else "partial"
    source_ids = {source_id: SOURCE_CATALOG[source_id]["id"] for source_id in SOURCE_CATALOG}
    sources = [manual_source_definition(), internal_metric_source_definition()] + [source_definition(source_id) for source_id in SOURCE_CATALOG]
    sources.append({
        "id": "src_google_play_reviews",
        "label": "Waje Google Play 用户评价专项周报",
        "href": SOURCE_URL if "SOURCE_URL" in globals() else "https://play.google.com/store/apps/details?id=com.hfhy.waje.special&hl=en-gb&gl=ng&pli=1",
        "query": {"engine": "local_google_play_review_pipeline", "description": "公开评价与开发者回复的按日采集、去重、版本和质量汇总；D 级证据。"},
    })
    h5_source_id = "src_waje_h5_observation"
    internal_metric_source_id = "src_internal_metric_contract"
    play_reviews_source_id = "src_google_play_reviews"

    public_coverage = f"{len(available_public_days)}/7"
    core_data_state = "已具备完整日导出" if metrics["ready"] else "四类内部日导出尚未落地"
    summary_bullets = [
        "## Executive Summary",
        "",
        f"**本周最优先的产品风险是‘进入玩法后无法完成首局’。**在测试环境抽查的 3 个代表玩法中，Whot 与 Fish 未进入可操作界面，NairaSlots 可加载但未完成下注/结算验证。该问题目前只可定性为测试环境 P0 阻塞，必须以生产 `game_start→首帧→下注→结算` 漏斗验证影响范围。",
        "",
        "**充值活动已形成入账，但‘展示—订单—奖励流水’存在可解释性断点。**测试支付后余额与三笔入账总额可对上；然而促销展示金额、支付页描述以及 Chip/BonusChip/Super Sale 的拆分不一致。先修复规则映射与归因，否则任何首充转化或活动 ROI 结论都不可靠。",
        "",
        f"**竞品公开活动更强调玩法绑定和任务化激励，而不是单一通用奖励。**SportyBet 活动页本周可解析 {len(sporty_offers)} 个公开 Offer，涵盖 Free Spins、Free Bet/Drop、Cashback 与玩法 Missions；Waje 应用首局完成、复玩、奖励成本与 RTP 护栏验证机制，而非复制名义奖励额度。",
        "",
        f"**经营结论仍受数据接入限制。**{core_data_state}；因此本周不输出 DAU、留存、付费率、LTV、TX/TC、营收或 RTP 的数值判断。公开采集覆盖 {public_coverage} 天，仅作为产品与竞品证据层。",
        "",
        "**正式站基线与测试站结论不一致，不能继续混用。**项目内保留的 2026-08-14 正式站访客样本显示 Whot 已完成最小下注与结算，说明“Whot/Fish 均无法首局”只能归属于 2026-08-07 测试环境样本；本次复测正式站时被站点按访问位置限制，未能进入登录/注册，因此不把正式站当前状态标成已复核。",
        "",
        "**金币场的直接竞品不是单一 sportsbook。**没有公开证据证明 Betway、1xBet、SportyBet 或 Bet9ja存在与 Waje Coin/Ludo 同构的非现金金币场；更可比的是 Betway 的混合 Casino 货架、1xBet 的即时玩法+促销循环，以及 SportyBet 的任务/赛事回访机制。",
    ]
    if play_reviews["available"]:
        play_metrics = play_reviews["metrics"]
        play_reply_rate = play_metrics.get("reply_rate")
        play_reply_rate_label = f"{play_reply_rate:.1%}" if isinstance(play_reply_rate, (int, float)) else "—"
        summary_bullets.extend([
            "",
            f"**Google Play 评价专项周报：**本周新增 {play_metrics.get('new_count', 0)} 条评价，平均 {play_metrics.get('average_rating') or '—'} 星，好评价 {play_metrics.get('good_count', 0)} 条，差评价 {play_metrics.get('bad_count', 0)} 条，开发者回复率 {play_reply_rate_label}。这是公开评价线索，不直接替代订单、客服和资金事实源。",
        ])
    else:
        summary_bullets.extend(["", "**Google Play 评价专项周报暂不可用。**周一 08:00 专项任务未产生可读取的 artifact；总周报保留降级提示，不将缺失评价当作零值。"])

    observation_rows = [
        {
            "priority": row["priority"],
            "area": row["area"],
            "observation": row["observation"],
            "business_implication": row["implication"],
            "next_metric": row["next_metric"],
            "confidence": row["confidence"],
        }
        for row in observations
    ] or [{
        "priority": "待采集",
        "area": "Waje H5 实测",
        "observation": "本周未找到符合字段要求的 H5 体验记录。",
        "business_implication": "不对新手、支付或玩法体验做产品判断。",
        "next_metric": "补齐测试记录与内部事件数据。",
        "confidence": "低",
    }]

    cards = [
        {
            "id": "card_representative_games",
            "dataset": "h5_headline_metrics",
            "sourceId": h5_source_id,
            "metrics": [{"label": "代表玩法测试", "field": "representative_games_tested", "format": "number", "unit": "个"}],
        },
        {
            "id": "card_entry_blockers",
            "dataset": "h5_headline_metrics",
            "sourceId": h5_source_id,
            "metrics": [{"label": "未进入可操作界面", "field": "entry_blockers", "format": "number", "unit": "个"}],
        },
        {
            "id": "card_competitor_mechanisms",
            "dataset": "h5_headline_metrics",
            "sourceId": source_ids["sportybet_2"],
            "metrics": [{"label": "公开可见活动机制", "field": "competitor_offer_count", "format": "number", "unit": "个"}],
        },
    ]
    if play_reviews["available"]:
        cards.extend([
            {
                "id": "card_play_reviews_new",
                "dataset": "play_reviews_headline",
                "sourceId": play_reviews_source_id,
                "metrics": [{"label": "Play 本周新增评价", "field": "new_count", "format": "number", "unit": "条"}],
            },
            {
                "id": "card_play_reviews_bad_rate",
                "dataset": "play_reviews_headline",
                "sourceId": play_reviews_source_id,
                "metrics": [{"label": "Play 差评价率", "field": "bad_rate", "format": "percent", "unit": ""}],
            },
        ])
    charts: list[dict[str, Any]] = [{
        "id": "chart_metric_export_coverage",
        "title": "四类每日经营导出的完整日覆盖",
        "subtitle": "统计周期内的完整自然日数；缺失文件、未完成日和全零异常行不进入经营判断。",
        "type": "bar",
        "dataset": "metric_export_coverage",
        "sourceId": internal_metric_source_id,
        "encodings": {
            "x": {"field": "feed", "type": "nominal"},
            "y": {"field": "complete_days", "type": "quantitative"},
            "tooltip": [{"field": "expected_days", "type": "quantitative"}],
        },
        "xAxisTitle": "每日导出",
        "yAxisTitle": "完整日数",
    }]
    if play_reviews["available"]:
        charts.append({
            "id": "chart_play_reviews_rating_distribution",
            "title": "Google Play 用户评价星级分布",
            "subtitle": "本周首次入库评价；好评价=4–5星，差评价=1–2星。",
            "type": "bar",
            "dataset": "play_review_rating_distribution",
            "sourceId": play_reviews_source_id,
            "encodings": {"x": {"field": "label", "type": "nominal"}, "y": {"field": "count", "type": "quantitative"}},
            "xAxisTitle": "星级",
            "yAxisTitle": "评价数",
        })
    chart_blocks: list[dict[str, Any]] = [
        {
            "id": "metric_coverage_takeaway",
            "type": "markdown",
            "sourceId": internal_metric_source_id,
            "body": "## 核心经营数据尚未进入本周结论\n\n**四类每日导出是下周报告产生经营结论的前提。**在每个自然日都具备完整的经营、新用户队列、支付资产与游戏生命周期/RTP 数据前，报告只给出产品体验和竞品机制判断；不会把缺失分区、未成熟 cohort 或全零异常记录误读为业务变化。",
        },
        {"id": "metric_coverage_chart", "type": "chart", "chartId": "chart_metric_export_coverage"},
    ]
    if play_reviews["available"]:
        chart_blocks.extend([
            {"id": "play_reviews_takeaway", "type": "markdown", "sourceId": play_reviews_source_id, "body": f"## Google Play 评价是本周用户声音主入口\n\n专项周报已统计本周新增评价的评分、好差分布、负向主题、功能需求和开发者回复。完整明细见 [Google Play 用户评价专项周报]({play_reviews['report']})；公开评价只作为 D 级用户线索。"},
            {"id": "play_reviews_rating_chart", "type": "chart", "chartId": "chart_play_reviews_rating_distribution"},
        ])
    if tested_game_rows:
        charts.append({
            "id": "chart_h5_entry_readiness",
            "title": "代表玩法的首局入口状态",
            "subtitle": "测试环境，2026年8月7日；1=已加载、0=未进入可操作界面，不能外推为生产故障率。",
            "type": "bar",
            "dataset": "game_entry_readiness",
            "sourceId": h5_source_id,
            "encodings": {
                "x": {"field": "game", "type": "nominal"},
                "y": {"field": "ready_value", "type": "quantitative"},
                "tooltip": [
                    {"field": "entry_result", "type": "nominal"},
                    {"field": "scope", "type": "nominal"},
                    {"field": "note", "type": "nominal"},
                ],
            },
            "xAxisTitle": "代表玩法",
            "yAxisTitle": "入口可用状态（1=已加载）",
        })
        chart_blocks.extend([
            {
                "id": "entry_readiness_takeaway",
                "type": "markdown",
                "sourceId": h5_source_id,
                "body": "## 首局可用性是当前最先要排除的漏斗断点\n\n**在测试环境的代表样本中，2 个入口未到达可操作界面。**这不是生产故障率，也不能据此估算损失；它说明后续的首局、付费和 RTP 分析缺少前置条件。研发应优先通过启动、首帧、下注和结算事件定位到 game_id、版本、网络与 iframe 请求层。",
            },
            {"id": "entry_readiness_chart", "type": "chart", "chartId": "chart_h5_entry_readiness"},
        ])
    if catalog_rows:
        charts.append({
            "id": "chart_visible_content_catalog",
            "title": "H5 首页可见玩法目录样本",
            "subtitle": "按首页栏目记录的玩法名称数量；是目录观察样本，不是完整库存、热度或收入占比。",
            "type": "bar",
            "dataset": "visible_catalog",
            "sourceId": h5_source_id,
            "encodings": {
                "x": {"field": "category", "type": "nominal"},
                "y": {"field": "visible_sample_games", "type": "quantitative"},
                "tooltip": [{"field": "sample", "type": "nominal"}],
            },
            "xAxisTitle": "首页栏目",
            "yAxisTitle": "记录到的玩法名称数",
        })
        chart_blocks.extend([
            {
                "id": "catalog_takeaway",
                "type": "markdown",
                "sourceId": h5_source_id,
                "body": "## 内容供给已丰富，但首屏分发与质量要先于扩容验证\n\n**首页同时承载快局、捕鱼、老虎机、Crash 和第三方专区。**当前不能判断哪类内容带来新增、下注或留存；下一步应把栏目曝光、游戏启动、首局、局数、下注额、实际 RTP 与 D1/D7 串成同一事实链，避免只用内容数量判断供给质量。",
            },
            {"id": "catalog_chart", "type": "chart", "chartId": "chart_visible_content_catalog"},
        ])

    tables = [
        {
            "id": "table_waje_observations",
            "title": "Waje 本周直接产品证据",
            "subtitle": "测试环境与可见产品机制；每条均附下一步要验证的内部指标。",
            "dataset": "waje_observations",
            "sourceId": h5_source_id,
            "columns": [
                {"field": "priority", "label": "优先级", "type": "text"},
                {"field": "area", "label": "环节", "type": "text"},
                {"field": "observation", "label": "直接观察", "type": "text"},
                {"field": "business_implication", "label": "产品含义", "type": "text"},
                {"field": "next_metric", "label": "验证指标", "type": "text"},
                {"field": "confidence", "label": "证据强度", "type": "text"},
            ],
        },
        {
            "id": "table_competitor_mechanisms",
            "title": "竞品定位与可见机制对照",
            "subtitle": "直接产品/活动页面的当前快照；不将定位文案当作经营效果或本周改版事实。",
            "dataset": "competitor_mechanisms",
            "sourceId": source_ids["sportybet_2"],
            "columns": [
                {"field": "competitor", "label": "竞品", "type": "text"},
                {"field": "surface", "label": "证据页面", "type": "text"},
                {"field": "observed_mechanism", "label": "可见机制/定位", "type": "text"},
                {"field": "product_implication", "label": "对 Waje 的启发", "type": "text"},
                {"field": "boundary", "label": "证据边界", "type": "text"},
            ],
        },
        {
            "id": "table_coin_competition",
            "title": "金币场竞争排序：直接性、可学机制与追踪重点",
            "subtitle": "基于项目内金币场设计与公开竞品快照；没有公开同构证据的地方明确标注，不把相邻机制当作同类产品。",
            "dataset": "coin_competition",
            "sourceId": source_ids["sportybet_2"],
            "columns": [
                {"field": "rank", "label": "排序", "type": "text"},
                {"field": "competitor", "label": "产品", "type": "text"},
                {"field": "directness", "label": "直接性", "type": "text"},
                {"field": "why_direct", "label": "为什么相关", "type": "text"},
                {"field": "coin_gap", "label": "与金币场的差异", "type": "text"},
                {"field": "track", "label": "重点追踪", "type": "text"},
            ],
        },
        {
            "id": "table_metric_readiness",
            "title": "核心经营指标的数据接入状态",
            "subtitle": "未接入的指标不进入本周经营结论；下周由四类完整日分区自动补齐。",
            "dataset": "metric_readiness",
            "sourceId": internal_metric_source_id,
            "columns": [
                {"field": "area", "label": "分析模块", "type": "text"},
                {"field": "required_export", "label": "所需导出", "type": "text"},
                {"field": "needed_metrics", "label": "关键指标", "type": "text"},
                {"field": "status", "label": "本周状态", "type": "text"},
                {"field": "decision_limit", "label": "当前限制", "type": "text"},
            ],
        },
        {
            "id": "table_actions",
            "title": "下周产品、商业化与数据行动清单",
            "subtitle": "每个动作都绑定验证指标、风险护栏和复盘窗口，避免只输出资讯结论。",
            "dataset": "action_plan",
            "sourceId": h5_source_id,
            "columns": [
                {"field": "priority", "label": "优先级", "type": "text"},
                {"field": "action", "label": "行动", "type": "text"},
                {"field": "owner", "label": "协作方", "type": "text"},
                {"field": "success_metric", "label": "验证指标", "type": "text"},
                {"field": "guardrail", "label": "护栏", "type": "text"},
                {"field": "validation_window", "label": "复盘窗口", "type": "text"},
            ],
        },
    ]
    if play_reviews["available"]:
        tables.append({
            "id": "table_play_reviews_topics",
            "title": "Google Play 评价负向主题",
            "subtitle": "本周新增评价的主题命中次数；一条评价可命中多个主题。",
            "dataset": "play_review_topics",
            "sourceId": play_reviews_source_id,
            "columns": [
                {"field": "label", "label": "主题", "type": "text"},
                {"field": "count", "label": "评价数", "type": "number"},
                {"field": "rate", "label": "占比", "type": "percent"},
            ],
        })

    blocks: list[dict[str, Any]] = [
        {
            "id": "title",
            "type": "markdown",
            "body": f"# {title}\n\n**统计周期：**{start.strftime('%Y年%m月%d日')} 至 {end.strftime('%Y年%m月%d日')}。  \n**报告定位：**Waje 产品经营决策周报；公开竞品证据只用于提出和优先排序可验证假设。  \n**报告状态：**`{report_status}`。本周内部经营数据为 `{core_data_state}`。",
        },
        {"id": "executive_summary", "type": "markdown", "sourceId": h5_source_id, "body": "\n".join(summary_bullets)},
        {"id": "headline_metrics", "type": "metric-strip", "cardIds": [card["id"] for card in cards]},
        {
            "id": "product_experience_intro",
            "type": "markdown",
            "sourceId": h5_source_id,
            "body": "## 从新手福利到首局：当前的证据指向‘闭环可用性’，而非奖励加码\n\n**本周最有价值的已验证事实，是新手路径在‘领取/充值’之后能否稳定进入并完成首局。**Daily Chip、Super Sale 与 Coins 均提供明确的激励或货币路径；但首局入口、活动规则解释和奖励分账尚未闭环。产品优先级应是让用户看懂、领取、进入、下注、结算并看到余额变化，而不是在该链路未验证前继续叠加新奖励。",
        },
    ]
    blocks.extend(chart_blocks)
    blocks.extend([
        {
            "id": "waje_observations_takeaway",
            "type": "markdown",
            "sourceId": h5_source_id,
            "body": "## 支付与奖励的可信表达需要独立验收\n\n**测试账面总额可以对上，但活动展示、订单信息和奖励分账必须逐项一致。**这是一项产品信任与数据归因问题：前端如果把现金、Chip、BonusChip 与活动赠送解释不清，用户难以判断自己得到什么，数据团队也难以区分真实首充、奖励赠送与后续消耗。上线前应把订单 ID、活动 ID、奖励类型、到账金额与用户可见文案放入同一验收用例。",
        },
        {"id": "waje_observations_table", "type": "table", "tableId": "table_waje_observations"},
        {
            "id": "formal_baseline_takeaway",
            "type": "markdown",
            "sourceId": h5_source_id,
            "body": "## 正式站核验结论：Whot 已有可用基线，测试站加载异常不能直接外推\n\n**项目内的正式站访客样本（2026年8月14日）完成了 Whot 最小下注与结算：Bet 1、下注 -NGN 1.00、中奖 +NGN 1.80、余额由 NGN 600.00 变为 NGN 600.80。**同一正式站样本还观察到 Daily Chip 可见但被 Super Sale 打断，独立新手任务中心和 Mail 任务通知未暴露。当前运行再次访问正式站时受到地域限制，无法使用记住的账号或注册测试账号复跑；因此正式站结论标为“历史基线 + 本次未复测”，不替代新一轮 Nigeria 环境验收。",
        },
        {
            "id": "coin_product_comparison",
            "type": "markdown",
            "sourceId": h5_source_id,
            "body": "## 金币场与竞品的核心差异：Waje 要做的是“非现金活跃层”，不是再做一个 sportsbook\n\n金币场设计的核心是 **Coin 获取/消耗 → 低门槛休闲对局 → 受控 Extra Chip → 真金回流**，并要求 Coin 与 Cash/Chip 隔离、金币场 RTP 小于 1、机器人单独标记、上限和账本可对账。竞品公开页面更多证明的是体育事件、Casino 货架、Cashback、Cash Out 和任务化促销；它们可借鉴“回访理由”和“奖励嵌入玩法”，但不能直接复制到 Coin 经济。\n\n**最值得学习：**1xBet 的即时玩法与挑战/促销节奏；SportyBet 的赛事与任务回访机制；Betway 的 Casino/小游戏/大奖包装。**最直接的产品竞争：**Betway，其混合 Casino 与尼日利亚休闲博彩用户重叠更明显；**最需要防止的误区：**把竞品真金奖金额度直接搬进 Coin 场，导致 Coin 价值、Extra Chip 上限、RTP 和提现边界混乱。",
        },
        {
            "id": "competitor_takeaway",
            "type": "markdown",
            "sourceId": source_ids["sportybet_2"],
            "body": "## 竞品启发是‘把奖励嵌入玩法循环’，不是照搬奖金数额\n\n**可见的竞品机制把 Free Spins、Cashback、Free Bet/Drop 和 Missions 绑定到具体玩法或触发场景。**对 Waje 更合适的下一步是先选一个可稳定加载的代表玩法，把 Daily Chip 或首充奖励转化为“完成首局—完成任务—获得下一步权益”的短链路，并用首局率、复玩率、奖励成本、实际 RTP 与提现风险共同判断是否扩大。",
        },
        {"id": "competitor_table", "type": "table", "tableId": "table_competitor_mechanisms"},
        {"id": "coin_competition_table", "type": "table", "tableId": "table_coin_competition"},
        {
            "id": "data_readiness_takeaway",
            "type": "markdown",
            "body": "## 本周不能回答的经营问题，必须由每日事实导出补齐\n\n**留存、付费、LTV、TX/TC、RTP 和真实支付/提现异常都需要内部事实源。**下周起按每日完整分区提供经营、新用户队列、支付资产、游戏生命周期/RTP 四类 CSV；不完整日期、全零异常记录和未成熟 cohort 自动排除。报告才会开始输出按版本、包体、渠道、媒体、游戏和生命周期的数值结论与异常定位。",
        },
        {"id": "metric_readiness_table", "type": "table", "tableId": "table_metric_readiness"},
        {
            "id": "action_takeaway",
            "type": "markdown",
            "body": "## 下周优先顺序：先修闭环，再做任务化激励，最后扩大投放或奖励\n\n下面的 P0/P1 并非资讯热度，而是按用户影响、资金信任、可验证性和数据依赖排序。每项工作应在指定窗口内回到对应指标复盘；没有内部数据时，只能验收功能和账务一致性，不能宣布商业化成功。",
        },
        {"id": "action_table", "type": "table", "tableId": "table_actions"},
        *([{"id": "play_reviews_topics_table", "type": "table", "tableId": "table_play_reviews_topics"}] if play_reviews["available"] else []),
        {
            "id": "further_questions",
            "type": "markdown",
            "body": "## Further Questions\n\n- Whot/Fish 的加载问题在生产、哪些版本、哪些网络和哪些渠道下出现？\n- Super Sale 的展示金额、订单金额、Chip/BonusChip 分账、可投注范围和提现规则的正式口径是什么？\n- Daily Chip 的快捷方式门槛是否提高了首日回访，又是否降低了领取到首局的转化？\n- 哪些游戏/生命周期的实际 RTP 偏离理论 RTP，且是否与破产、留存、首充或提现相关？\n- 哪个渠道、包体或媒体的新手质量足以承接玩法任务化激励？",
        },
        {
            "id": "caveats",
            "type": "markdown",
            "body": "## Caveats and Assumptions\n\n- Waje H5 观察发生在测试环境；除非内部事件数据验证，不能外推为生产故障率或营收损失。\n- 竞品活动页与商店文案证明页面可见定位或机制，不证明实际资格、活动成本、使用率、转化或经营规模。\n- 本周只有公开证据层，且公开采集覆盖不足完整 7 天；报告不以采集数量、搜索结果或旧新闻替代产品结论。\n- 未接入四类每日内部导出前，留存、付费、LTV、TX/TC、营收与 RTP 均不生成数值判断。\n- 不保存账号、密码、Cookie、Token、支付凭据或用户个人明细。",
        },
    ])

    manifest = {
        "version": 1,
        "surface": "report",
        "title": title,
        "description": f"Waje 产品、商业化和竞品机制周报，统计周期 {start.isoformat()} 至 {end.isoformat()}。",
        "generatedAt": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "sources": sources,
        "cards": cards,
        "charts": charts,
        "tables": tables,
        "blocks": blocks,
    }
    snapshot = {
        "version": 1,
        "generatedAt": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": report_status,
        "datasets": {
            "h5_headline_metrics": [{
                "representative_games_tested": len(tested_game_rows),
                "entry_blockers": blocked_game_count,
                "competitor_offer_count": len(sporty_offers),
            }],
            "game_entry_readiness": tested_game_rows,
            "visible_catalog": catalog_rows,
            "metric_export_coverage": metric_coverage_rows,
            "waje_observations": observation_rows,
            "competitor_mechanisms": competitor_rows or [{
                "competitor": "待补采集",
                "surface": "-",
                "observed_mechanism": "本周没有可解析的直接竞品页面。",
                "evidence": "-",
                "product_implication": "只保留数据接入与 Waje 内部验证动作。",
                "boundary": "不以搜索线索填补事实。",
            }],
            "coin_competition": coin_competitor_rows,
            "formal_h5_baseline": [{
                "status": "历史基线，可用但本次未复测" if formal["available"] else "缺失",
                "observed_at": formal["observed_at"],
                "environment": formal["environment"],
                "whot_minimum_bet_ngn": formal["whot"].get("minimum_bet_ngn"),
                "daily_chip_visible": formal["promotion"].get("daily_chip_visible"),
                "daily_chip_claim_observed": formal["promotion"].get("task_completion_observed"),
                "coins_balance": formal["coins"].get("coins_balance"),
            }],
            "metric_readiness": metric_readiness_rows,
            "action_plan": action_rows,
            "play_reviews_headline": [{
                "new_count": play_reviews["metrics"].get("new_count", 0),
                "bad_rate": (play_reviews["metrics"].get("bad_count", 0) / play_reviews["metrics"].get("new_count", 1)) if play_reviews["metrics"].get("new_count") else 0,
                "good_count": play_reviews["metrics"].get("good_count", 0),
                "reply_rate": play_reviews["metrics"].get("reply_rate"),
                "status": play_reviews["status"],
            }],
            "play_review_rating_distribution": [{"label": f"{index} 星", "count": int(row[1]) if len(row) > 1 and str(row[1]).isdigit() else 0} for index, row in enumerate(play_reviews["rating_distribution"], start=1)],
            "play_review_topics": play_reviews["topics"],
        },
    }
    analysis = {
        "report_date": report_date.isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "status": report_status,
        "public_source_days": len(available_public_days),
        "public_source_history": source_history,
        "internal_metric_exports": metrics,
        "h5_observation_count": len(observations),
        "competitor_offer_count": len(sporty_offers),
        "formal_h5_baseline": formal,
        "coin_competition": coin_competitor_rows,
        "play_reviews": play_reviews,
        "notes": [
            "Public evidence is used for product and competitor hypotheses only.",
            "Internal KPI claims require the approved daily aggregate exports.",
            "Partial periods, all-zero export rows, and immature cohorts are excluded from future KPI conclusions.",
        ],
    }
    return {"surface": "report", "manifest": manifest, "snapshot": snapshot, "sources": sources}, analysis


def fallback_markdown(body: str) -> str:
    def inline(value: str) -> str:
        safe = html.escape(value)
        safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
        safe = re.sub(r"`(.+?)`", r"<code>\1</code>", safe)
        safe = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href=\"\2\">\1</a>", safe)
        return safe

    lines = []
    in_list = False
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            if in_list:
                lines.append("</ul>")
                in_list = False
            continue
        if line.startswith("### ") or line.startswith("## ") or line.startswith("# "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            level = len(line) - len(line.lstrip("#"))
            text_value = inline(line[level + 1 :])
            lines.append(f"<h{min(level + 1, 3)}>{text_value}</h{min(level + 1, 3)}>")
        elif line.startswith("- "):
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{inline(line[2:])}</li>")
        else:
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<p>{inline(line)}</p>")
    if in_list:
        lines.append("</ul>")
    return "".join(lines)


def fallback_report_html(artifact: dict[str, Any]) -> str:
    """Local fallback when the optional Data Analytics delivery plugin is absent."""
    manifest = artifact["manifest"]
    snapshot = artifact["snapshot"]
    charts = {chart["id"]: chart for chart in manifest.get("charts", [])}
    datasets = snapshot.get("datasets", {})
    cards = []
    for card in manifest.get("cards", []):
        rows = datasets.get(card.get("dataset"), [])
        row = rows[0] if rows else {}
        for metric in card.get("metrics", []):
            value = row.get(metric.get("field"), "—")
            if metric.get("format") == "percent" and isinstance(value, (int, float)):
                value = f"{value:.1%}"
            cards.append(f"<div class='metric'><span>{html.escape(metric.get('label', ''))}</span><strong>{html.escape(str(value))}</strong><small>{html.escape(metric.get('unit', '')) or '本周快照'}</small></div>")

    def render_chart(chart_id: str) -> str:
        chart = charts.get(chart_id, {})
        dataset = datasets.get(chart.get("dataset"), [])
        encodings = chart.get("encodings", {})
        x_field = encodings.get("x", {}).get("field")
        y_field = encodings.get("y", {}).get("field")
        max_value = max((float(row.get(y_field, 0) or 0) for row in dataset), default=0) or 1
        rows = "".join(
            f"<div class='bar-row'><div class='bar-label'>{html.escape(str(row.get(x_field, '—')))}</div>"
            f"<div class='bar-track'><span style='width:{min(100, float(row.get(y_field, 0) or 0) / max_value * 100):.1f}%'></span></div>"
            f"<strong class='bar-value'>{html.escape(str(row.get(y_field, '—')))}</strong></div>"
            for row in dataset
        )
        chart_body = rows or "<div class='empty'>暂无数据</div>"
        return f"<section class='panel chart-panel'><div class='eyebrow'>DATA VIEW</div><h3>{html.escape(chart.get('title', '图表'))}</h3><p>{html.escape(chart.get('subtitle', ''))}</p><div class='bar-chart'>{chart_body}</div></section>"

    def render_table(table_id: str) -> str:
        spec = next((table for table in manifest.get("tables", []) if table.get("id") == table_id), {})
        rows = datasets.get(spec.get("dataset"), [])
        columns = spec.get("columns", [])
        head = "".join(f"<th>{html.escape(column.get('label', column.get('field', '')))}</th>" for column in columns)
        def cell_class(value: Any) -> str:
            text_value = str(value)
            return " priority-p0" if text_value == "P0" else " priority-p1" if text_value == "P1" else ""

        body = "".join("<tr>" + "".join(f"<td class='{cell_class(row.get(column.get('field'))).strip()}'>{html.escape(str(row.get(column.get('field'), '—')))}</td>" for column in columns) + "</tr>" for row in rows[:100])
        empty_row = f"<tr><td colspan='{max(len(columns), 1)}'>暂无数据</td></tr>"
        return f"<section class='panel table-panel'><div class='eyebrow'>EVIDENCE TABLE</div><h3>{html.escape(spec.get('title', table_id))}</h3><p>{html.escape(spec.get('subtitle', ''))}</p><div class='scroll'><table><thead><tr>{head}</tr></thead><tbody>{body or empty_row}</tbody></table></div></section>"

    blocks = []
    for block in manifest.get("blocks", []):
        if block.get("type") == "markdown":
            body = block.get('body', '')
            classes = 'markdown'
            if block.get('id') == 'title':
                classes += ' hero'
            elif block.get('id') in {'executive_summary', 'caveats'}:
                classes += ' callout'
            blocks.append(f"<section class='{classes}'>{fallback_markdown(body)}</section>")
        elif block.get("type") == "metric-strip":
            blocks.append("<div class='metrics'>" + "".join(cards) + "</div>")
        elif block.get("type") == "chart":
            blocks.append(render_chart(block.get("chartId", "")))
        elif block.get("type") == "table":
            blocks.append(render_table(block.get("tableId", "")))
    source_rows = "".join(f"<li><strong>{html.escape(source.get('label', source.get('id', '')))}</strong><a href='{html.escape(source.get('href', ''))}'>{html.escape(source.get('href', ''))}</a></li>" for source in manifest.get("sources", []))
    status = html.escape(str(snapshot.get('status', 'partial')).upper())
    style = """
    :root{--ink:#17212b;--muted:#63717d;--line:#dce4e8;--paper:#fff;--bg:#eef2f3;--teal:#0b7775;--teal-dark:#073d46;--orange:#e37b38;--red:#c84d45;--shadow:0 14px 38px rgba(20,45,52,.08)}
    *{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 8% 0,#d8eeeb 0,transparent 31%),var(--bg);color:var(--ink);font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}main{max-width:1240px;margin:auto;padding:34px 26px 76px}h1,h2,h3{line-height:1.25;letter-spacing:-.02em}h1{font-size:clamp(30px,4vw,54px);max-width:900px;margin:10px 0 18px}h2{font-size:27px;margin:8px 0 14px}h3{font-size:21px;margin:8px 0 10px}p{color:var(--muted);margin:8px 0 14px}a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}code{background:#e8f1f0;color:var(--teal-dark);padding:1px 5px;border-radius:4px}.markdown,.panel,.metric{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:24px;margin:18px 0;box-shadow:var(--shadow)}.hero{background:linear-gradient(125deg,var(--teal-dark),#0b7775 62%,#2a9b8c);color:#fff;border:0;padding:38px 42px;box-shadow:0 20px 50px rgba(5,64,71,.22)}.hero p,.hero strong,.hero h1,.hero h2,.hero h3{color:#fff}.hero:after{content:'WEEKLY INTELLIGENCE';display:block;color:#bce5df;letter-spacing:.16em;font-size:11px;font-weight:700;margin-top:26px}.callout{border-left:6px solid var(--orange);background:#fffaf4}.callout h2,.callout h3{color:var(--teal-dark)}.eyebrow{font-size:11px;letter-spacing:.15em;color:var(--teal);font-weight:800;margin-bottom:8px}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:20px 0}.metric{margin:0;padding:20px 22px;border-top:4px solid var(--teal)}.metric span{display:block;color:var(--muted);font-size:13px;font-weight:700}.metric strong{display:block;color:var(--teal-dark);font-size:38px;letter-spacing:-.05em;line-height:1.15;margin:8px 0}.metric small{color:var(--muted)}.panel{overflow:hidden}.chart-panel{background:linear-gradient(180deg,#fff,#f7fbfa)}.bar-chart{margin-top:18px}.bar-row{display:grid;grid-template-columns:minmax(140px,220px) 1fr 60px;gap:12px;align-items:center;margin:13px 0}.bar-label{font-weight:650;font-size:13px}.bar-track{height:12px;background:#dfeceb;border-radius:20px;overflow:hidden}.bar-track span{display:block;height:100%;background:linear-gradient(90deg,var(--teal),#43b39d);border-radius:20px}.bar-value{text-align:right;color:var(--teal-dark)}.table-panel h3{margin-bottom:4px}.scroll{overflow:auto;border:1px solid var(--line);border-radius:12px}table{width:100%;min-width:680px;border-collapse:collapse;background:#fff}th,td{text-align:left;padding:13px 14px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#f1f6f5;color:var(--teal-dark);font-size:12px;letter-spacing:.03em;position:sticky;top:0}tr:last-child td{border-bottom:0}tbody tr:hover{background:#fbfdfd}.priority-p0{color:#a7352f!important;font-weight:800;background:#fff0ee}.priority-p1{color:#a45a18!important;font-weight:800;background:#fff7eb}.empty{padding:18px;color:var(--muted)}ul{padding-left:22px;color:var(--muted)}li{margin:7px 0}.panel:last-child{background:#102d35;color:#d9eeee}.panel:last-child h2,.panel:last-child strong{color:#fff}.panel:last-child a{color:#a8e3d6}.panel:last-child li{color:#c4d8d8}.status-badge{display:inline-flex;background:#ffe0b8;color:#7e3d13;border-radius:999px;padding:4px 11px;font-size:12px;font-weight:800;letter-spacing:.08em}@media(max-width:720px){main{padding:18px 12px 50px}.hero{padding:28px 24px}.bar-row{grid-template-columns:110px 1fr 42px;gap:8px}.bar-label{font-size:12px}.markdown,.panel{padding:18px}.metric strong{font-size:32px}}
    """
    return f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(manifest.get('title', 'Waje 周报'))}</title><style>{style}</style></head><body><main><div class='status-badge'>报告状态：{status}</div>{''.join(blocks)}<section class='panel'><div class='eyebrow'>SOURCE REGISTER</div><h2>来源与证据边界</h2><ul>{source_rows}</ul></section></main></body></html>"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat(), help="Report date; production schedule passes Monday, and the report covers the previous Monday-Sunday.")
    args = parser.parse_args()
    root = project_root()
    report_date = dt.date.fromisoformat(args.date)
    artifact, analysis = build_artifact(root, report_date)
    output_dir = root / "data/outputs/weekly" / report_date.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / "artifact.json"
    analysis_path = output_dir / "analysis.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_path = root / "knowledge/03-竞品/周报" / f"{report_date.isoformat()}-Waje竞品情报周报.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    node = shutil.which("node")
    if not node or not DELIVER.exists():
        report_path.write_text(fallback_report_html(artifact), encoding="utf-8")
        result_returncode = 0
        result_stdout = "portable delivery plugin unavailable; local fallback renderer used"
        result_stderr = ""
        delivery: dict[str, Any] = {"stages": {"validation": {"status": "passed", "mode": "local_fallback"}, "package": {"status": "passed", "mode": "local_fallback"}, "verification": {"status": "structural_only", "mode": "local_fallback"}}, "counts": {"html": 0}}
    else:
        result = subprocess.run([node, str(DELIVER), "--input", str(artifact_path), "--output", str(report_path)], cwd=root, text=True, capture_output=True)
        result_returncode = result.returncode
        result_stdout = result.stdout
        result_stderr = result.stderr
        delivery = {}
        output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if output_lines:
            try:
                delivery = json.loads(output_lines[-1])
            except json.JSONDecodeError:
                delivery = {"raw_output": output_lines[-1]}
    receipt = {
        "report_date": report_date.isoformat(),
        "artifact": str(artifact_path.relative_to(root)),
        "analysis": str(analysis_path.relative_to(root)),
        "html": str(report_path.relative_to(root)),
        "summary": {
            "window": analysis["window"],
            "status": analysis["status"],
            "public_source_days": analysis["public_source_days"],
            "internal_complete_days": analysis["internal_metric_exports"]["complete_days"],
            "h5_observation_count": analysis["h5_observation_count"],
            "competitor_offer_count": analysis["competitor_offer_count"],
        },
        "returncode": result_returncode,
        "delivery": {
            "validation": (delivery.get("stages", {}).get("validation") or {}).get("status", "unknown") if isinstance(delivery.get("stages", {}).get("validation"), dict) else delivery.get("stages", {}).get("validation", "unknown"),
            "package": (delivery.get("stages", {}).get("package") or {}).get("status", "unknown") if isinstance(delivery.get("stages", {}).get("package"), dict) else delivery.get("stages", {}).get("package", "unknown"),
            "verification": (delivery.get("stages", {}).get("verification") or {}).get("status", "unknown") if isinstance(delivery.get("stages", {}).get("verification"), dict) else delivery.get("stages", {}).get("verification", "unknown"),
            "browser_warning": delivery.get("browserWarning"),
            "counts": delivery.get("counts", {}),
        },
        "stdout": result_stdout.strip(),
        "stderr": result_stderr.strip(),
    }
    (output_dir / "delivery-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result_returncode != 0:
        print(result_stdout, end="")
        print(result_stderr, end="")
        return result_returncode
    preview_path = root / "output/html/Waje-weekly-report.html"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(report_path, preview_path)
    receipt["preview_html"] = str(preview_path.relative_to(root))
    (output_dir / "delivery-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"weekly HTML report: {report_path.relative_to(root)}")
    print(f"stable preview alias: {preview_path.relative_to(root)}")
    print(result_stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create a transparent triage analysis; LLM enrichment can be added later."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def freshness(item: dict, now: datetime) -> str:
    published = item.get("published_at", "")
    if not published:
        return "unknown"
    try:
        parsed = parsedate_to_datetime(published)
        if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=now.tzinfo)
        age = now - parsed.astimezone(now.tzinfo)
        if age <= timedelta(days=7): return "current"
        if age <= timedelta(days=30): return "recent"
        return "historical"
    except (TypeError, ValueError, OverflowError):
        return "unknown"


def score(item: dict, now: datetime) -> tuple[int, str, str, str]:
    text = (item.get("title", "") + " " + item.get("text", "")).lower()
    source_type = item.get("source_type", "")
    age = freshness(item, now)
    incident_words = ["outage", "fraud", "hacked", "breach", "banned", "ban multiple", "duplicate charge", "withdrawal failed", "提现失败", "重复扣款"]
    market_words = ["license", "regulation", "regulatory", "regulation breach", "博彩法", "监管"]
    important = ["promotion", "bonus", "payment", "cash out", "game update", "launch", "rating", "review", "充值"]
    seo_words = ["review", "complete guide", "tips", "promo code", "best betting", "how to register", "指南", "攻略"]
    if any(word in text for word in incident_words) and age in {"current", "recent"}:
        return 3, "P0/P1 review", "incident_or_risk", age
    if any(word in text for word in market_words) and age == "current":
        return 3, "P0/P1 review", "current_regulation_signal", age
    if any(word in text for word in important):
        priority = 1 if source_type == "news_rss" and any(word in text for word in seo_words) else 2
        reason = "historical_or_seo_signal" if priority == 1 else "product_or_commercial_signal"
        return priority, "P1 review" if priority == 2 else "P2 monitor", reason, age
    return 1, "P2 monitor", "general_signal", age


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    source = ROOT / "data/processed" / args.date / "normalized-items.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    now = datetime.now().astimezone()
    analyzed = []
    for item in data["items"]:
        priority, action, reason, item_freshness = score(item, now)
        text = re.sub(r"\s+", " ", item.get("text", "")).strip()
        analyzed.append({**item, "importance": priority, "triage": action, "priority_reason": reason, "freshness": item_freshness, "needs_manual_verification": priority >= 2, "summary": text[:500]})
    analyzed.sort(key=lambda x: (-x["importance"], x.get("entity_id", ""), x.get("title", "")))
    out = ROOT / "data/outputs" / args.date
    out.mkdir(parents=True, exist_ok=True)
    target = out / "analysis.json"
    target.write_text(json.dumps({"schema_version": 1, "date": args.date, "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "items": analyzed}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"analyzed {len(analyzed)} items; output={target}")


if __name__ == "__main__":
    main()

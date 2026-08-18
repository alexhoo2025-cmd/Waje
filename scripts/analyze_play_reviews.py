#!/usr/bin/env python3
"""Add transparent sentiment, topic, severity and operations triage to Play reviews."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TOPICS = {
    "payment_and_withdrawal": ["withdraw", "withdrawal", "deposit", "debited", "balance", "cash out", "money", "充值", "提现"],
    "stability_and_verification": ["network", "loading", "hang", "freeze", "crash", "face verification", "verification", "login", "卡顿", "网络"],
    "fairness_and_game_rules": ["scam", "rigged", "rng", "random", "fair", "win", "lose", "maximum", "match", "card", "spin", "fish", "公平"],
    "customer_support": ["customer service", "support", "telegram", "live chat", "response", "complain", "客服"],
    "promotion_and_referral": ["bonus", "reward", "referral", "invite", "free", "promotion", "welcome"],
    "gameplay_and_feature_request": ["whot", "fish", "slot", "roulette", "baccarat", "game", "feature", "suggest", "matchmaking"],
    "trust_and_responsible_gambling": ["scam", "fraud", "government", "license", "responsible", "addiction", "regulator"],
}

NEGATIVE = ["bad", "worst", "scam", "fraud", "can't", "cannot", "lost", "loss", "failed", "wrong", "never", "hate", "rubbish", "problem", "slow", "blocked"]
POSITIVE = ["good", "great", "excellent", "love", "satisfactory", "success", "successfully", "easy", "fast", "nice", "enjoy"]
P0 = ["money disappeared", "funds gone", "50k", "cannot withdraw", "can't withdraw", "balance vanished", "duplicate debit", "account lost"]
P1 = ["withdraw", "deposit", "debited", "face verification", "network", "loading", "customer service", "blocked"]


def topic_for(text: str) -> list[str]:
    lower = text.lower()
    return [name for name, words in TOPICS.items() if any(word.lower() in lower for word in words)] or ["general_product_feedback"]


def sentiment_for(text: str, rating: int | None) -> str:
    lower = text.lower()
    negative = sum(lower.count(word) for word in NEGATIVE)
    positive = sum(lower.count(word) for word in POSITIVE)
    if rating is not None:
        if rating <= 2: negative += 2
        if rating >= 4: positive += 2
    if negative > positive: return "negative"
    if positive > negative: return "positive"
    return "neutral"


def severity_for(text: str, rating: int | None) -> str:
    lower = text.lower()
    if any(word in lower for word in P0): return "P0"
    if any(word in lower for word in P1) or rating in {1, 2}: return "P1"
    return "P2"


def intent_for(topics: list[str], severity: str, has_reply: bool) -> str:
    if severity == "P0": return "customer_follow_up_and_fund_audit"
    if "payment_and_withdrawal" in topics: return "payment_withdrawal_follow_up"
    if "stability_and_verification" in topics: return "product_reliability_fix"
    if "fairness_and_game_rules" in topics: return "rules_explanation_and_trust_repair"
    if "customer_support" in topics: return "support_process_improvement"
    if "promotion_and_referral" in topics: return "promotion_or_referral_optimization"
    if "gameplay_and_feature_request" in topics: return "gameplay_backlog_review"
    return "monitor_feedback" if not has_reply else "monitor_reply_quality"


def reply_template(record: dict) -> str:
    text = (record.get("developer_reply_text") or "").lower()
    if not text: return "no_reply"
    if "telegram" in text or "live chat" in text: return "support_handoff"
    if "sorry" in text or "apolog" in text: return "apology_and_handoff"
    if "fair" in text or "random" in text or "rng" in text: return "fairness_explanation"
    if "withdraw" in text or "deposit" in text: return "payment_guidance"
    return "general_acknowledgement"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    source = ROOT / "data/processed/play_reviews" / args.date / "reviews.jsonl"
    if not source.exists(): raise SystemExit(f"Missing normalized reviews: {source}")
    output_dir = ROOT / "data/outputs/play_reviews" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)
    analyzed = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        record = json.loads(line)
        review_text = re.sub(r"\s+", " ", record.get("review_text") or "").strip()
        all_text = re.sub(r"\s+", " ", f"{review_text} {record.get('developer_reply_text') or ''}").strip()
        topics = topic_for(review_text)
        sentiment = sentiment_for(review_text, record.get("rating"))
        severity = severity_for(review_text, record.get("rating"))
        analyzed.append({**record, "topics": topics, "sentiment": sentiment, "severity": severity, "operation_intent": intent_for(topics, severity, bool(record.get("has_developer_reply"))), "reply_template": reply_template(record), "is_resolution_signal": bool(re.search(r"resolved|successfully|satisfactory|thank you for updating|got my transfer", all_text, re.I)), "summary": review_text[:500]})
    analyzed.sort(key=lambda item: ({"P0": 0, "P1": 1, "P2": 2}[item["severity"]], item.get("review_date_display") or ""))
    output = output_dir / "analysis.json"
    output.write_text(json.dumps({"schema_version": 1, "date": args.date, "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "items": analyzed}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"analyzed {len(analyzed)} Play reviews; output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

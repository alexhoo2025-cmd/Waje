#!/usr/bin/env python3
"""Create a source- and freshness-aware quality receipt for one daily run."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def latest(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def wechat_health(root: Path, date: str) -> dict:
    manifest_path = latest(root / "data/raw/wechat" / date, "manifest-*.json")
    if not manifest_path:
        return {"status": "missing", "article_count": 0, "errors": [{"reason": "manifest_missing"}]}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    articles = payload.get("articles", [])
    errors = payload.get("errors", [])
    return {
        "status": payload.get("status", "degraded"),
        "article_count": len(articles),
        "errors": errors,
        "source_access_statuses": sorted({str(article.get("source_access_status", "")) for article in articles if article.get("source_access_status")}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    raw_dir = ROOT / "data/raw" / args.date
    output_dir = ROOT / "data/outputs" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = latest(raw_dir, "manifest-*.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path else {"items": []}
    records = manifest.get("items", [])
    ok = [item for item in records if item.get("status") == "ok"]
    failed = [item for item in records if item.get("status") != "ok"]
    normalized_path = ROOT / "data/processed" / args.date / "normalized-items.json"
    analysis_path = output_dir / "analysis.json"
    normalized = json.loads(normalized_path.read_text(encoding="utf-8")) if normalized_path.exists() else {}
    analysis = json.loads(analysis_path.read_text(encoding="utf-8")) if analysis_path.exists() else {}
    wechat = wechat_health(ROOT, args.date)
    priority_counts = collections.Counter(str(item.get("importance")) for item in analysis.get("items", []))
    quality = {
        "schema_version": 1,
        "date": args.date,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "degraded" if failed or wechat["status"] not in {"ok", "not_configured"} else "ready",
        "source_health": {
            "total": len(records),
            "ok": len(ok),
            "failed": len(failed),
            "success_rate": round(len(ok) / len(records), 4) if records else 0,
            "failed_sources": [{"source_id": item.get("source_id"), "url": item.get("url"), "error": item.get("error")} for item in failed],
            "transport_fallbacks": [item.get("source_id") for item in ok if item.get("transport")],
            "by_type": dict(collections.Counter(item.get("source_type", "unknown") for item in records)),
        },
        "content_health": {
            "raw_item_count": normalized.get("raw_item_count", 0),
            "unique_item_count": normalized.get("unique_item_count", 0),
            "duplicate_count": normalized.get("duplicate_count", 0),
            "duplicate_rate": round(normalized.get("duplicate_count", 0) / normalized.get("raw_item_count", 1), 4) if normalized.get("raw_item_count") else 0,
            "stale_item_count": normalized.get("stale_item_count", 0),
            "stale_rate": round(normalized.get("stale_item_count", 0) / (normalized.get("stale_item_count", 0) + normalized.get("raw_item_count", 0)), 4) if normalized.get("stale_item_count", 0) + normalized.get("raw_item_count", 0) else 0,
            "source_type_counts": dict(collections.Counter(item.get("source_type", "unknown") for item in normalized.get("items", []))),
        },
        "analysis_health": {
            "analyzed_count": len(analysis.get("items", [])),
            "priority_counts": dict(priority_counts),
            "manual_review_count": sum(1 for item in analysis.get("items", []) if item.get("needs_manual_verification")),
            "freshness_counts": dict(collections.Counter(item.get("freshness", "unknown") for item in analysis.get("items", []))),
        },
        "wechat_health": wechat,
        "quality_flags": [],
    }
    if failed: quality["quality_flags"].append("source_failure")
    if any(item.get("source_id") == "waje_1" for item in failed): quality["quality_flags"].append("waje_official_source_unavailable")
    if normalized.get("stale_item_count", 0): quality["quality_flags"].append("stale_news_filtered")
    if wechat["status"] not in {"ok", "not_configured"}:
        quality["quality_flags"].append("wechat_collection_degraded")
    if wechat["status"] == "degraded" and not wechat.get("article_count"):
        quality["quality_flags"].append("wechat_no_authorized_articles")
    if not analysis.get("items"): quality["quality_flags"].append("no_analyzed_items")
    target = output_dir / "quality.json"
    target.write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"quality assessed: status={quality['status']}; output={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

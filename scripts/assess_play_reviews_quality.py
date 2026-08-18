#!/usr/bin/env python3
"""Create a quality receipt for a Play review collection run."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def index_health() -> dict:
    path = ROOT / "data/processed/play_reviews/review_index.sqlite3"
    if not path.exists():
        return {"available": False, "review_count": 0, "version_count": 0}
    try:
        db = sqlite3.connect(path)
        result = {
            "available": True,
            "review_count": db.execute("SELECT COUNT(*) FROM reviews_current").fetchone()[0],
            "version_count": db.execute("SELECT COUNT(*) FROM review_versions").fetchone()[0],
            "run_count": db.execute("SELECT COUNT(*) FROM review_runs").fetchone()[0],
        }
        db.close()
        return result
    except sqlite3.Error as exc:
        return {"available": False, "error": str(exc), "review_count": 0, "version_count": 0}


def latest(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    manifest_path = latest(ROOT / "data/raw/play_reviews" / args.date, "manifest-*.json")
    output_dir = ROOT / "data/outputs/play_reviews" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path else {"status": "missing", "errors": ["manifest_missing"]}
    normalized = ROOT / "data/processed/play_reviews" / args.date / "summary.json"
    analysis = ROOT / "data/outputs/play_reviews" / args.date / "analysis.json"
    summary = json.loads(normalized.read_text(encoding="utf-8")) if normalized.exists() else {}
    analyzed = json.loads(analysis.read_text(encoding="utf-8")) if analysis.exists() else {"items": []}
    items = analyzed.get("items", [])
    field_counts = collections.Counter()
    for item in items:
        for field in ("review_text", "rating", "review_date_display"):
            if item.get(field) not in (None, ""): field_counts[field] += 1
    quality = {
        "schema_version": 1,
        "date": args.date,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "ready" if manifest.get("status") == "ok" and items else "degraded",
        "source_health": {"status": manifest.get("status"), "stop_reason": manifest.get("stop_reason"), "errors": manifest.get("errors", []), "source_url": manifest.get("url"), "target_new_count": manifest.get("target_new_count", 0), "new_count": manifest.get("new_count", 0), "updated_count": manifest.get("updated_count", 0), "already_seen_count": manifest.get("already_seen_count", 0), "shortfall": manifest.get("shortfall", 0), "filter": manifest.get("filter", {})},
        "content_health": {"card_count_seen": manifest.get("card_count_seen", 0), "raw_count": summary.get("raw_count", 0), "unique_count": summary.get("unique_count", 0), "duplicate_count": summary.get("duplicate_count", 0), "version_change_count": summary.get("version_change_count", 0)},
        "analysis_health": {"analyzed_count": len(items), "severity_counts": dict(collections.Counter(item.get("severity") for item in items)), "topic_counts": dict(collections.Counter(topic for item in items for topic in item.get("topics", []))), "reply_count": sum(1 for item in items if item.get("has_developer_reply")), "field_non_null_counts": dict(field_counts)},
        "index_health": index_health(),
        "quality_flags": [],
    }
    if manifest.get("status") != "ok": quality["quality_flags"].append("collection_not_ok")
    if manifest.get("status") == "shortfall": quality["quality_flags"].append("new_review_shortfall")
    if not items: quality["quality_flags"].append("no_reviews")
    if manifest.get("stop_reason") == "max_scroll_steps": quality["quality_flags"].append("max_scroll_steps_reached")
    if manifest.get("stop_reason") == "max_reviews": quality["quality_flags"].append("sample_limit_reached")
    target = output_dir / "quality.json"
    target.write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Play review quality: {quality['status']}; output={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

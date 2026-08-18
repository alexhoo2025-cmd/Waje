#!/usr/bin/env python3
"""Normalize public Google Play review snapshots into JSONL and version-safe records."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_display_date(value: str | None) -> str | None:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        return None
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def enrich(record: dict, manifest: dict) -> dict:
    review_date = parse_display_date(record.get("review_date_display"))
    reply_date = parse_display_date(record.get("developer_reply_date_display"))
    reply_lag = None
    if review_date and reply_date:
        reply_lag = (dt.date.fromisoformat(reply_date) - dt.date.fromisoformat(review_date)).days
    rating = record.get("rating")
    rating_bucket = "positive" if rating in {4, 5} else "neutral" if rating == 3 else "negative" if rating in {1, 2} else None
    return {
        **record,
        "schema_version": max(2, int(record.get("schema_version") or 1)),
        "review_type": "user_review",
        "evidence_grade": "D",
        "version_key": record.get("content_hash"),
        "collection_run_id": record.get("collection_run_id") or manifest.get("run_id"),
        "is_backfill": bool(record.get("is_backfill", False)),
        "review_date_parsed": review_date,
        "reply_date_parsed": reply_date,
        "reply_lag_days": reply_lag,
        "rating_bucket": rating_bucket,
    }


def latest_manifest(root: Path, date: str) -> Path | None:
    files = sorted((root / "data/raw/play_reviews" / date).glob("manifest-*.json"))
    return files[-1] if files else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--manifest")
    args = parser.parse_args()
    manifest_path = Path(args.manifest) if args.manifest else latest_manifest(ROOT, args.date)
    if not manifest_path or not manifest_path.exists():
        raise SystemExit(f"No Google Play review manifest found for {args.date}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") not in {"ok", "shortfall"}:
        raise SystemExit(f"Cannot normalize manifest with status={manifest.get('status')}")
    raw_path = ROOT / manifest["raw_file"]
    records = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    unique: dict[str, dict] = {}
    versions: list[dict] = []
    for record in records:
        key = record.get("review_key") or hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        record["review_key"] = key
        record = enrich(record, manifest)
        if key in unique and unique[key].get("content_hash") != record.get("content_hash"):
            versions.append({"review_key": key, "previous_content_hash": unique[key].get("content_hash"), "content_hash": record.get("content_hash"), "captured_at": record.get("captured_at")})
        unique[key] = record
    out_dir = ROOT / "data/processed/play_reviews" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "reviews.jsonl"
    ordered = list(unique.values())
    output_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in ordered) + ("\n" if ordered else ""), encoding="utf-8")
    for state in ("new", "updated", "existing"):
        state_path = out_dir / f"{state}_reviews.jsonl"
        state_rows = [item for item in ordered if item.get("record_state") == state]
        state_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in state_rows) + ("\n" if state_rows else ""), encoding="utf-8")
    (out_dir / "versions.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in versions) + ("\n" if versions else ""), encoding="utf-8")
    summary = {
        "schema_version": 1,
        "date": args.date,
        "manifest": str(manifest_path.relative_to(ROOT)) if manifest_path.is_absolute() else str(manifest_path),
        "raw_count": len(records),
        "unique_count": len(unique),
        "duplicate_count": len(records) - len(unique),
        "version_change_count": len(versions),
        "record_state_counts": {state: sum(1 for item in ordered if item.get("record_state") == state) for state in ("new", "updated", "existing")},
        "backfill_count": sum(1 for item in ordered if item.get("is_backfill")),
        "target_new_count": manifest.get("target_new_count", 0),
        "shortfall": manifest.get("shortfall", 0),
        "output": str(output_path.relative_to(ROOT)),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

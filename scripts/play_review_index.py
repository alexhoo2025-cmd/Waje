#!/usr/bin/env python3
"""Persistent local index for Google Play review identity and versions.

The collector is a Node/Playwright process, while normalization and reporting
are Python processes.  This small SQLite bridge keeps the cross-run identity
state in one place without adding a native Node database dependency.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data/processed/play_reviews/review_index.sqlite3"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS reviews_current (
            review_key TEXT PRIMARY KEY,
            review_id TEXT,
            identity_key TEXT,
            package_name TEXT NOT NULL,
            latest_content_hash TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            latest_json TEXT NOT NULL,
            baseline INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_reviews_current_package ON reviews_current(package_name);
        CREATE TABLE IF NOT EXISTS review_versions (
            review_key TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            record_state TEXT NOT NULL,
            record_json TEXT NOT NULL,
            PRIMARY KEY(review_key, content_hash)
        );
        CREATE TABLE IF NOT EXISTS review_runs (
            run_id TEXT PRIMARY KEY,
            run_date TEXT NOT NULL,
            status TEXT NOT NULL,
            target_new_count INTEGER NOT NULL DEFAULT 0,
            new_count INTEGER NOT NULL DEFAULT 0,
            updated_count INTEGER NOT NULL DEFAULT 0,
            already_seen_count INTEGER NOT NULL DEFAULT 0,
            shortfall INTEGER NOT NULL DEFAULT 0,
            stop_reason TEXT,
            source_url TEXT,
            filter_json TEXT,
            captured_at TEXT,
            finished_at TEXT
        );
        """
    )
    db.commit()
    return db


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def upsert_records(db: sqlite3.Connection, records: list[dict[str, Any]], baseline: bool = False) -> dict[str, int]:
    counts = {"new": 0, "updated": 0, "existing": 0}
    for record in records:
        key = str(record.get("review_key") or "").strip()
        if not key:
            continue
        content_hash = str(record.get("content_hash") or "")
        captured_at = str(record.get("captured_at") or now())
        current = db.execute("SELECT * FROM reviews_current WHERE review_key = ?", (key,)).fetchone()
        if current is None:
            state = "existing" if baseline else "new"
            first_seen = captured_at
            db.execute(
                """INSERT INTO reviews_current
                (review_key, review_id, identity_key, package_name, latest_content_hash,
                 first_seen_at, last_seen_at, latest_json, baseline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (key, record.get("review_id"), record.get("identity_key"), record.get("package_name", ""),
                 content_hash, first_seen, captured_at, json.dumps(record, ensure_ascii=False), int(baseline)),
            )
            db.execute(
                "INSERT OR IGNORE INTO review_versions (review_key, content_hash, captured_at, record_state, record_json) VALUES (?, ?, ?, ?, ?)",
                (key, content_hash, captured_at, state, json.dumps(record, ensure_ascii=False)),
            )
            if not baseline:
                counts[state] += 1
            continue

        state = "existing"
        if content_hash and content_hash != current["latest_content_hash"]:
            state = "updated"
            db.execute(
                "UPDATE reviews_current SET review_id = ?, identity_key = ?, latest_content_hash = ?, last_seen_at = ?, latest_json = ? WHERE review_key = ?",
                (record.get("review_id"), record.get("identity_key"), content_hash, captured_at, json.dumps(record, ensure_ascii=False), key),
            )
            db.execute(
                "INSERT OR IGNORE INTO review_versions (review_key, content_hash, captured_at, record_state, record_json) VALUES (?, ?, ?, ?, ?)",
                (key, content_hash, captured_at, state, json.dumps(record, ensure_ascii=False)),
            )
        else:
            db.execute("UPDATE reviews_current SET last_seen_at = ? WHERE review_key = ?", (captured_at, key))
        counts[state] += 1
    return counts


def seed_existing(db: sqlite3.Connection) -> dict[str, int]:
    existing = db.execute("SELECT COUNT(*) FROM reviews_current").fetchone()[0]
    if existing:
        return {"seeded": 0, "existing": existing}
    records: list[dict[str, Any]] = []
    for path in sorted((ROOT / "data/processed/play_reviews").glob("*/reviews.jsonl")):
        records.extend(load_records(path))
    counts = upsert_records(db, records, baseline=True)
    db.commit()
    return {"seeded": len(records), "indexed_count": db.execute("SELECT COUNT(*) FROM reviews_current").fetchone()[0], **counts}


def export_keys(db: sqlite3.Connection) -> dict[str, str]:
    return {
        row["review_key"]: row["latest_content_hash"] or ""
        for row in db.execute("SELECT review_key, latest_content_hash FROM reviews_current")
    }


def upsert_run(db: sqlite3.Connection, manifest: dict[str, Any]) -> None:
    db.execute(
        """INSERT OR REPLACE INTO review_runs
        (run_id, run_date, status, target_new_count, new_count, updated_count,
         already_seen_count, shortfall, stop_reason, source_url, filter_json,
         captured_at, finished_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (manifest.get("run_id", ""), manifest.get("date", ""), manifest.get("status", "error"),
         int(manifest.get("target_new_count") or 0), int(manifest.get("new_count") or 0),
         int(manifest.get("updated_count") or 0), int(manifest.get("already_seen_count") or 0),
         int(manifest.get("shortfall") or 0), manifest.get("stop_reason"), manifest.get("url"),
         json.dumps(manifest.get("filter") or {}, ensure_ascii=False), manifest.get("fetched_at"), manifest.get("finished_at")),
    )
    db.commit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("init", "export", "seed-existing", "upsert"))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--records")
    parser.add_argument("--manifest")
    args = parser.parse_args()
    db = connect(Path(args.db).resolve())
    try:
        if args.command == "init":
            print(json.dumps({"db": str(Path(args.db).resolve())}, ensure_ascii=False))
        elif args.command == "export":
            print(json.dumps(export_keys(db), ensure_ascii=False, separators=(",", ":")))
        elif args.command == "seed-existing":
            print(json.dumps(seed_existing(db), ensure_ascii=False))
        elif args.command == "upsert":
            if not args.records or not args.manifest:
                raise SystemExit("upsert requires --records and --manifest")
            manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
            counts = upsert_records(db, load_records(Path(args.records)))
            upsert_run(db, {**manifest, **counts})
            print(json.dumps(counts, ensure_ascii=False))
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

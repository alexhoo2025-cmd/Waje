#!/usr/bin/env python3
"""Collect one Friday batch and build the Waje weekly intelligence reports."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import fcntl
import hashlib
import html
import json
import os
import subprocess
import sys
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


CODE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("WAJE_ANALYST_ROOT", str(CODE_ROOT))).resolve()
SCRIPTS = CODE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from analyze_intelligence import freshness, score  # noqa: E402
from collect_intelligence import fetch, safe_name, sha256  # noqa: E402
from normalize_intelligence import TextParser, clean, is_stale, rss_items, topic  # noqa: E402


def read_json(path: Path, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return fallback or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback or {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def week_window(collection_date: dt.date) -> tuple[dt.date, dt.date]:
    end = collection_date - dt.timedelta(days=1)
    return end - dt.timedelta(days=6), end


def batch_id(collection_date: dt.date, start: dt.date, end: dt.date) -> str:
    return f"waje-weekly-{start.isoformat()}-{end.isoformat()}-{collection_date.isoformat()}"


def source_list(config: dict[str, Any]) -> list[dict[str, Any]]:
    collection = config.get("collection", {})
    sources: list[dict[str, Any]] = []
    for entity in config.get("entities", []):
        for index, source in enumerate(entity.get("sources", []), 1):
            sources.append({"id": f"{entity['id']}_{index}", "entity_id": entity["id"], **source})
    recency = int(collection.get("news_query_recency_days", 14))
    for query in config.get("search_queries", []):
        query_text = f"{query['query']} when:{recency}d" if recency > 0 else query["query"]
        params = __import__("urllib.parse", fromlist=["urlencode"]).urlencode({"q": query_text, "hl": "en-NG", "gl": "NG", "ceid": "NG:en"})
        sources.append({"id": query["id"], "entity_id": "market", "type": "news_rss", "url": f"https://news.google.com/rss/search?{params}"})
    return sources


def collect_public_sources(collection_date: dt.date, raw_dir: Path) -> dict[str, Any]:
    config = read_json(ROOT / "config/intel_sources.json")
    collection = config.get("collection", {})
    timeout = int(collection.get("timeout_seconds", 30))
    retries = int(collection.get("retries", 2))
    backoff = int(collection.get("retry_backoff_seconds", 1))
    run_id = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    records: list[dict[str, Any]] = []
    for source in source_list(config):
        record = {
            "source_id": source["id"],
            "entity_id": source["entity_id"],
            "source_type": source["type"],
            "url": source["url"],
            "fetched_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "attempts": 0,
        }
        try:
            body, content_type, attempts, transport = fetch(source["url"], timeout=timeout, retries=retries, backoff_seconds=backoff)
            digest = sha256(body)
            extension = ".xml" if content_type in {"application/rss+xml", "application/xml", "text/xml"} or "news.google.com/rss" in source["url"] else ".html"
            target = raw_dir / f"{safe_name(source['id'])}_{digest[:12]}{extension}"
            if not target.exists():
                target.write_bytes(body)
            record.update({"status": "ok", "content_type": content_type, "sha256": digest, "path": str(target.relative_to(ROOT)), "attempts": attempts})
            if transport:
                record["transport"] = transport
        except Exception as exc:
            record.update({"status": "error", "error": f"{type(exc).__name__}: {exc}", "attempts": retries + 1})
        records.append(record)
    manifest = {"schema_version": 1, "run_id": run_id, "collection_date": collection_date.isoformat(), "items": records}
    manifest_path = raw_dir / "manifest.json"
    write_json(manifest_path, manifest)
    return manifest


def run_command(command: list[str], allowed: set[int] | None = None) -> tuple[int, str, str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_codes = allowed or {0}
    if result.returncode not in allowed_codes:
        return result.returncode, result.stdout[-1000:], result.stderr[-1000:]
    return result.returncode, result.stdout[-1000:], result.stderr[-1000:]


def latest_manifest(directory: Path, pattern: str = "manifest-*.json") -> Path | None:
    paths = sorted(directory.glob(pattern))
    return paths[-1] if paths else None


def collect_play_reviews(collection_date: dt.date) -> dict[str, Any]:
    date = collection_date.isoformat()
    stages: list[dict[str, Any]] = []
    commands = [
        ([sys.executable, str(SCRIPTS / "play_review_index.py"), "seed-existing"], {0}),
        (["node", str(SCRIPTS / "collect_play_reviews.mjs"), "--date", date, "--mode", "incremental", "--min-new-reviews", "200", "--backfill-unseen"], {0, 2}),
    ]
    manifest_path: Path | None = None
    for command, allowed in commands:
        code, stdout, stderr = run_command(command, allowed)
        stages.append({"stage": command[1] if len(command) > 1 else command[0], "returncode": code, "stdout": stdout, "stderr": stderr})
        if command[0] == "node":
            manifest_path = latest_manifest(ROOT / "data/raw/play_reviews" / date)
            if code not in allowed:
                return {"status": "degraded", "stages": stages}
    manifest = read_json(manifest_path) if manifest_path else {}
    if manifest.get("raw_file"):
        normalize = [
            ([sys.executable, str(SCRIPTS / "normalize_play_reviews.py"), "--date", date, "--manifest", str(manifest_path)], {0}),
            ([sys.executable, str(SCRIPTS / "play_review_index.py"), "upsert", "--records", str(ROOT / "data/processed/play_reviews" / date / "reviews.jsonl"), "--manifest", str(manifest_path)], {0}),
            ([sys.executable, str(SCRIPTS / "analyze_play_reviews.py"), "--date", date], {0}),
            ([sys.executable, str(SCRIPTS / "assess_play_reviews_quality.py"), "--date", date], {0}),
        ]
        for command, allowed in normalize:
            code, stdout, stderr = run_command(command, allowed)
            stages.append({"stage": command[1] if len(command) > 1 else command[0], "returncode": code, "stdout": stdout, "stderr": stderr})
            if code not in allowed:
                return {"status": "degraded", "stages": stages, "manifest": str(manifest_path.relative_to(ROOT)) if manifest_path else ""}
    status = manifest.get("status", "degraded") if manifest else "degraded"
    return {"status": status, "stages": stages, "manifest": str(manifest_path.relative_to(ROOT)) if manifest_path else "", "summary": read_json(ROOT / "data/processed/play_reviews" / date / "summary.json")}


def collect_supporting_sources(collection_date: dt.date) -> dict[str, Any]:
    date = collection_date.isoformat()
    result: dict[str, Any] = {"release_watch": {}, "wechat": {}, "play_reviews": {}}
    for key, command in {
        "release_watch": [sys.executable, str(SCRIPTS / "run_release_experience_watch.py"), "--date", date],
        "wechat": [sys.executable, str(SCRIPTS / "collect_wechat_articles.py"), "--date", date],
    }.items():
        code, stdout, stderr = run_command(command, {0})
        result[key] = {"returncode": code, "stdout": stdout, "stderr": stderr}
    result["play_reviews"] = collect_play_reviews(collection_date)
    return result


def normalize_weekly(collection_date: dt.date, raw_dir: Path, processed_dir: Path) -> dict[str, Any]:
    manifest = read_json(raw_dir / "manifest.json", {"items": []})
    config = read_json(ROOT / "config/intel_sources.json")
    max_news_age = int(config.get("collection", {}).get("news_max_age_days", 30))
    now = dt.datetime.now().astimezone()
    items: list[dict[str, Any]] = []
    stale_items: list[dict[str, Any]] = []
    for record in manifest.get("items", []):
        if record.get("status") != "ok":
            continue
        base = {key: record.get(key, "") for key in ("source_id", "entity_id", "source_type", "url", "fetched_at")}
        base["content_hash"] = record.get("sha256", "")
        path = ROOT / record.get("path", "")
        if not path.exists():
            path = raw_dir / Path(record.get("path", "")).name
        if path.suffix == ".xml":
            for item in rss_items(path, base):
                if item.get("source_type") == "news_rss" and is_stale(item.get("published_at", ""), now, max_news_age):
                    stale_items.append({"title": item.get("title", ""), "published_at": item.get("published_at", ""), "url": item.get("url", "")})
                else:
                    items.append(item)
        else:
            parser = TextParser()
            parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
            items.append({**base, "title": clean(parser.title) or record.get("source_id", "source"), "published_at": "", "text": clean(" ".join(parser.parts))[:5000]})
    unique: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for item in items:
        identity = item.get("url") or (item.get("title", "") + item.get("text", "")[:200])
        item["item_id"] = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        item["topic"] = topic(item.get("title", "") + " " + item.get("text", ""))
        if item["item_id"] in unique:
            duplicate_count += 1
        unique[item["item_id"]] = item
    payload = {
        "schema_version": 1,
        "collection_date": collection_date.isoformat(),
        "raw_item_count": len(items),
        "unique_item_count": len(unique),
        "duplicate_count": duplicate_count,
        "stale_item_count": len(stale_items),
        "stale_items": stale_items,
        "items": list(unique.values()),
    }
    write_json(processed_dir / "normalized-items.json", payload)
    return payload


def analyze_weekly(collection_date: dt.date, normalized: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    now = dt.datetime.now().astimezone()
    analyzed: list[dict[str, Any]] = []
    for item in normalized.get("items", []):
        priority, action, reason, item_freshness = score(item, now)
        text = " ".join(str(item.get("text", "")).split())
        analyzed.append({**item, "importance": priority, "triage": action, "priority_reason": reason, "freshness": item_freshness, "needs_manual_verification": priority >= 2, "summary": text[:500]})
    analyzed.sort(key=lambda value: (-value.get("importance", 1), value.get("entity_id", ""), value.get("title", "")))
    payload = {"schema_version": 1, "collection_date": collection_date.isoformat(), "items": analyzed}
    write_json(output_dir / "analysis.json", payload)
    return payload


def assess_quality(collection_date: dt.date, raw_manifest: dict[str, Any], normalized: dict[str, Any], analysis: dict[str, Any], support: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    records = raw_manifest.get("items", [])
    ok = [item for item in records if item.get("status") == "ok"]
    failed = [item for item in records if item.get("status") != "ok"]
    wechat_manifest = latest_manifest(ROOT / "data/raw/wechat" / collection_date.isoformat())
    wechat = read_json(wechat_manifest) if wechat_manifest else {}
    play_quality = read_json(ROOT / "data/outputs/play_reviews" / collection_date.isoformat() / "quality.json")
    quality = {
        "schema_version": 1,
        "collection_date": collection_date.isoformat(),
        "window": {"start": week_window(collection_date)[0].isoformat(), "end": week_window(collection_date)[1].isoformat()},
        "status": "degraded" if failed or wechat.get("status") not in {"ok", "not_configured"} or play_quality.get("status") in {"degraded", "blocked", "shortfall"} else "ready",
        "source_health": {"total": len(records), "ok": len(ok), "failed": len(failed), "success_rate": round(len(ok) / len(records), 4) if records else 0, "failed_sources": failed, "transport_fallbacks": [item.get("source_id") for item in ok if item.get("transport")]},
        "content_health": {key: normalized.get(key, 0) for key in ("raw_item_count", "unique_item_count", "duplicate_count", "stale_item_count")},
        "analysis_health": {"analyzed_count": len(analysis.get("items", [])), "manual_review_count": sum(1 for item in analysis.get("items", []) if item.get("needs_manual_verification"))},
        "wechat_health": {"status": wechat.get("status", "missing"), "article_count": len(wechat.get("articles", [])), "errors": wechat.get("errors", [])},
        "play_reviews_health": {"status": play_quality.get("status", support.get("play_reviews", {}).get("status", "missing")), "summary": read_json(ROOT / "data/processed/play_reviews" / collection_date.isoformat() / "summary.json")},
        "release_watch": read_json(ROOT / "data/outputs/release_experience" / collection_date.isoformat() / "release-watch.json"),
        "quality_flags": [],
    }
    if failed:
        quality["quality_flags"].append("source_failure")
    if wechat.get("status") not in {"ok", "not_configured"}:
        quality["quality_flags"].append("wechat_collection_degraded")
    if play_quality.get("status") in {"degraded", "blocked", "shortfall"}:
        quality["quality_flags"].append("play_reviews_collection_degraded")
    if not analysis.get("items"):
        quality["quality_flags"].append("no_analyzed_items")
    write_json(output_dir / "quality.json", quality)
    review_items = [
        {"title": item.get("title", ""), "topic": item.get("topic", ""), "source_type": item.get("source_type", ""), "url": item.get("url", ""), "status": "pending_manual_review"}
        for item in analysis.get("items", []) if item.get("needs_manual_verification")
    ][:30]
    write_json(output_dir / "source-verification.json", {"schema_version": 1, "collection_date": collection_date.isoformat(), "status": "pending_manual_review" if review_items else "no_items", "items": review_items, "privacy": {"personal_details_stored": False, "credentials_stored": False}})
    return quality


def update_run_log(collection_date: dt.date, stages: list[dict[str, Any]], status: str) -> None:
    output_dir = ROOT / "data/outputs/weekly" / collection_date.isoformat()
    existing = read_json(output_dir / "run-log.json")
    merged = existing.get("stages", []) + stages
    payload = {"schema_version": 1, "job_id": "weekly_waje_intelligence", "collection_date": collection_date.isoformat(), "window": {"start": week_window(collection_date)[0].isoformat(), "end": week_window(collection_date)[1].isoformat()}, "status": status, "stages": merged, "updated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
    write_json(output_dir / "run-log.json", payload)


def collect(collection_date: dt.date, force: bool = False) -> int:
    raw_dir = ROOT / "data/raw/weekly" / collection_date.isoformat()
    output_dir = ROOT / "data/outputs/weekly" / collection_date.isoformat()
    if (raw_dir / "manifest.json").exists() and not force:
        update_run_log(collection_date, [{"stage": "collect", "status": "skipped_existing_batch"}], "skipped_existing")
        print(f"weekly collection skipped: batch={collection_date.isoformat()} already exists")
        return 0
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = collect_public_sources(collection_date, raw_dir)
    support = collect_supporting_sources(collection_date)
    start, end = week_window(collection_date)
    batch = {"schema_version": 1, "batch_id": batch_id(collection_date, start, end), "collection_date": collection_date.isoformat(), "week_start": start.isoformat(), "week_end": end.isoformat(), "source_count": len(manifest.get("items", [])), "success_count": sum(item.get("status") == "ok" for item in manifest.get("items", [])), "failed_sources": [item for item in manifest.get("items", []) if item.get("status") != "ok"], "supporting": support, "status": "degraded" if any(item.get("status") != "ok" for item in manifest.get("items", [])) else "ok"}
    write_json(raw_dir / "batch-manifest.json", batch)
    update_run_log(collection_date, [{"stage": "collect", "status": batch["status"], "source_count": batch["source_count"], "success_count": batch["success_count"]}], batch["status"])
    print(json.dumps(batch, ensure_ascii=False))
    return 0


def report(collection_date: dt.date) -> int:
    raw_dir = ROOT / "data/raw/weekly" / collection_date.isoformat()
    processed_dir = ROOT / "data/processed/weekly" / collection_date.isoformat()
    output_dir = ROOT / "data/outputs/weekly" / collection_date.isoformat()
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_manifest = read_json(raw_dir / "manifest.json", {"items": []})
    normalized = normalize_weekly(collection_date, raw_dir, processed_dir)
    analysis = analyze_weekly(collection_date, normalized, output_dir)
    support = {"play_reviews": {"status": "unknown"}}
    quality = assess_quality(collection_date, raw_manifest, normalized, analysis, support, output_dir)
    stages: list[dict[str, Any]] = [{"stage": "normalize", "status": "ok"}, {"stage": "analyze", "status": "ok"}, {"stage": "quality", "status": quality.get("status", "degraded")}]
    for command in (
        [sys.executable, str(SCRIPTS / "build_weekly_intelligence_report.py"), "--date", collection_date.isoformat()],
        [sys.executable, str(SCRIPTS / "build_play_reviews_report.py"), "--date", collection_date.isoformat(), "--period", "weekly", "--batch"],
        [sys.executable, str(SCRIPTS / "build_wechat_weekly_report.py"), "--date", collection_date.isoformat(), "--batch"],
    ):
        code, stdout, stderr = run_command(command, {0})
        stages.append({"stage": command[1], "status": "ok" if code == 0 else "degraded", "stdout": stdout, "stderr": stderr})
    graph_code, graph_stdout, graph_stderr = run_command([sys.executable, str(CODE_ROOT / "tools/build_graph.py")], {0})
    stages.append({"stage": "graph", "status": "ok" if graph_code == 0 else "degraded", "stdout": graph_stdout, "stderr": graph_stderr})
    final_status = "degraded" if quality.get("status") != "ready" or any(stage.get("status") == "degraded" for stage in stages) else "ok"
    update_run_log(collection_date, stages, final_status)
    print(json.dumps({"status": final_status, "collection_date": collection_date.isoformat(), "normalized_items": normalized.get("unique_item_count", 0), "reports": [stage for stage in stages if stage["stage"].startswith("build_")]}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("collect", "report", "all"), required=True)
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    collection_date = dt.date.fromisoformat(args.date)
    lock_path = ROOT / "data/processed/weekly/.pipeline.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("weekly intelligence pipeline is already running", file=sys.stderr)
            return 3
        if args.mode in {"collect", "all"}:
            collect(collection_date, args.force)
        if args.mode in {"report", "all"}:
            report(collection_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

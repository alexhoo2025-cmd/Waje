#!/usr/bin/env python3
"""Collect public source snapshots and Google News RSS for the daily pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from urllib.error import URLError
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UA = "WajeAnalystIntelligence/1.0 (+local research pipeline)"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")[:80] or "source"


def fetch_once(url: str, timeout: int) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get_content_type()


def fetch_with_curl(url: str, timeout: int) -> tuple[bytes, str]:
    """Fallback for hosts that reject the bundled Python TLS stack."""

    result = subprocess.run(
        ["curl", "-L", "--fail", "--silent", "--show-error", "--compressed", "--max-time", str(timeout), "-A", UA, url],
        check=True,
        capture_output=True,
        timeout=timeout + 5,
    )
    body = result.stdout
    stripped = body.lstrip().lower()
    content_type = "application/xml" if stripped.startswith(b"<?xml") or b"<rss" in stripped[:500] else "text/html"
    return body, content_type


def fetch(url: str, timeout: int = 30, retries: int = 2, backoff_seconds: int = 1) -> tuple[bytes, str, int, str | None]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            body, content_type = fetch_once(url, timeout)
            return body, content_type, attempt + 1, None
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            tls_issue = any(token in message for token in ("tls", "ssl", "protocol version"))
            if tls_issue:
                try:
                    body, content_type = fetch_with_curl(url, timeout)
                    return body, content_type, attempt + 1, "curl_tls_fallback"
                except Exception as curl_exc:
                    last_error = curl_exc
            if attempt < retries:
                time.sleep(backoff_seconds * (2 ** attempt))
    assert last_error is not None
    raise last_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    config = json.loads((ROOT / "config/intel_sources.json").read_text(encoding="utf-8"))
    collection = config.get("collection", {})
    timeout = int(collection.get("timeout_seconds", 30))
    retries = int(collection.get("retries", 2))
    backoff_seconds = int(collection.get("retry_backoff_seconds", 1))
    raw_dir = ROOT / "data/raw" / args.date
    raw_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    manifest = {"schema_version": 1, "run_id": run_id, "date": args.date, "items": []}

    sources = []
    for entity in config["entities"]:
        for index, source in enumerate(entity.get("sources", []), 1):
            sources.append({"id": f"{entity['id']}_{index}", "entity_id": entity["id"], **source})
    for query in config.get("search_queries", []):
        recency = int(collection.get("news_query_recency_days", 14))
        query_text = f"{query['query']} when:{recency}d" if recency > 0 else query["query"]
        params = urllib.parse.urlencode({"q": query_text, "hl": "en-NG", "gl": "NG", "ceid": "NG:en"})
        sources.append({"id": query["id"], "entity_id": "market", "type": "news_rss", "url": f"https://news.google.com/rss/search?{params}"})

    for source in sources:
        record = {"source_id": source["id"], "entity_id": source["entity_id"], "source_type": source["type"], "url": source["url"], "fetched_at": datetime.now().astimezone().isoformat(timespec="seconds"), "attempts": 0}
        try:
            body, content_type, attempts, fetch_mode = fetch(source["url"], timeout=timeout, retries=retries, backoff_seconds=backoff_seconds)
            digest = sha256(body)
            extension = ".xml" if content_type in {"application/rss+xml", "application/xml", "text/xml"} or "news.google.com/rss" in source["url"] else ".html"
            target = raw_dir / f"{safe_name(source['id'])}_{digest[:12]}{extension}"
            if not target.exists():
                target.write_bytes(body)
            record.update({"status": "ok", "content_type": content_type, "sha256": digest, "path": str(target.relative_to(ROOT)), "attempts": attempts})
            if fetch_mode:
                record["transport"] = fetch_mode
        except Exception as exc:
            record.update({"status": "error", "error": f"{type(exc).__name__}: {exc}", "attempts": retries + 1})
        manifest["items"].append(record)

    manifest_path = raw_dir / f"manifest-{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = sum(item["status"] == "ok" for item in manifest["items"])
    print(f"collected {ok}/{len(manifest['items'])} sources; manifest={manifest_path}")


if __name__ == "__main__":
    main()

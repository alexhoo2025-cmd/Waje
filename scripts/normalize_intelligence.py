#!/usr/bin/env python3
"""Normalize HTML/RSS snapshots into deduplicated intelligence items."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import timedelta
from email.utils import parsedate_to_datetime
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self.in_title = False
        self.ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "template"}:
            self.ignored_depth += 1
            return
        if self.ignored_depth: return
        if tag.lower() == "title": self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "template"} and self.ignored_depth:
            self.ignored_depth -= 1
            return
        if self.ignored_depth: return
        if tag.lower() == "title": self.in_title = False

    def handle_data(self, data):
        if self.ignored_depth: return
        text = " ".join(data.split())
        if not text: return
        self.parts.append(text)
        if self.in_title: self.title += text + " "


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def topic(text: str) -> str:
    rules = {
        "payment_and_withdrawal": ["withdraw", "deposit", "payment", "cash out", "充值", "提现"],
        "promotion": ["promotion", "bonus", "cashback", "reward", "free bet", "首存"],
        "stability_and_network": ["crash", "loading", "error", "network", "freeze", "white screen", "闪退"],
        "market_and_regulation": ["regulation", "license", "tax", "nlrc", "market", "博彩", "监管"],
        "gameplay": ["game", "casino", "sports", "whot", "fish", "slot", "crash"],
    }
    lower = text.lower()
    for name, words in rules.items():
        if any(word.lower() in lower for word in words): return name
    return "product_update"


def rss_items(path: Path, base: dict) -> list[dict]:
    root = ElementTree.fromstring(path.read_text(encoding="utf-8", errors="ignore"))
    items = []
    for item in root.findall(".//item"):
        title = clean(item.findtext("title", ""))
        link = clean(item.findtext("link", ""))
        description_html = item.findtext("description", "")
        description = clean(description_html)
        original_url = ""
        original_title = ""
        link_match = re.search(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', description_html, flags=re.I | re.S)
        if link_match:
            original_url = html.unescape(link_match.group(1))
            original_title = clean(re.sub(r"<[^>]+>", " ", link_match.group(2)))
            description = clean(re.sub(r"<[^>]+>", " ", description_html))
        published = clean(item.findtext("pubDate", ""))
        items.append({**base, "title": original_title or title, "url": original_url or link or base["url"], "rss_url": link, "published_at": published, "text": description})
    return items


def is_stale(published_at: str, now: datetime, max_age_days: int) -> bool:
    if not published_at or max_age_days <= 0: return False
    try:
        published = parsedate_to_datetime(published_at)
        if published.tzinfo is None: published = published.replace(tzinfo=now.tzinfo)
        return now - published.astimezone(now.tzinfo) > timedelta(days=max_age_days)
    except (TypeError, ValueError, OverflowError):
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    config_path = ROOT / "config/intel_sources.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    max_news_age = int(config.get("collection", {}).get("news_max_age_days", 30))
    run_now = datetime.now().astimezone()
    raw_dir = ROOT / "data/raw" / args.date
    manifests = sorted(raw_dir.glob("manifest-*.json"))
    if not manifests: raise SystemExit(f"No manifest found in {raw_dir}")
    manifest = json.loads(manifests[-1].read_text(encoding="utf-8"))
    items = []
    stale_items = []
    for record in manifest["items"]:
        if record.get("status") != "ok": continue
        base = {"source_id": record["source_id"], "entity_id": record["entity_id"], "source_type": record["source_type"], "url": record["url"], "fetched_at": record["fetched_at"], "content_hash": record["sha256"]}
        path = ROOT / record["path"]
        if path.suffix == ".xml":
            rss_batch = rss_items(path, base)
            for rss_item in rss_batch:
                if rss_item.get("source_type") == "news_rss" and is_stale(rss_item.get("published_at", ""), run_now, max_news_age):
                    stale_items.append({"title": rss_item.get("title", ""), "published_at": rss_item.get("published_at", ""), "url": rss_item.get("url", ""), "reason": f"older_than_{max_news_age}_days"})
                else:
                    items.append(rss_item)
            continue
        parser_html = TextParser()
        parser_html.feed(path.read_text(encoding="utf-8", errors="ignore"))
        text = clean(" ".join(parser_html.parts))
        items.append({**base, "title": clean(parser_html.title) or record["source_id"], "published_at": "", "text": text[:5000]})

    unique = {}
    duplicate_count = 0
    for item in items:
        identity = item.get("url") or (item["title"] + item["text"][:200])
        item["item_id"] = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        item["topic"] = topic(item["title"] + " " + item["text"])
        if item["item_id"] in unique:
            duplicate_count += 1
        unique[item["item_id"]] = item
    out_dir = ROOT / "data/processed" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "normalized-items.json"
    payload = {
        "schema_version": 1,
        "date": args.date,
        "raw_item_count": len(items),
        "unique_item_count": len(unique),
        "duplicate_count": duplicate_count,
        "stale_item_count": len(stale_items),
        "stale_items": stale_items,
        "items": list(unique.values()),
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"normalized {len(unique)} items; output={output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Shared helpers for the authorized public-account article pipeline."""

from __future__ import annotations

import hashlib
import html as html_lib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]


def project_root() -> Path:
    """Allow isolated tests without changing the production project root."""

    return Path(os.environ.get("WAJE_ANALYST_ROOT", str(ROOT))).resolve()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def safe_name(value: str, fallback: str = "article") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_")
    return cleaned[:100] or fallback


def first_value(mapping: Mapping[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return default


def unwrap_collection(payload: Any) -> list[dict[str, Any]]:
    """Normalize common API/export envelopes to a list of dictionaries."""

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("articles", "items", "results", "records"):
        if isinstance(payload.get(key), list):
            return [item for item in payload[key] if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return unwrap_collection(data)
    return [payload] if any(key in payload for key in ("article_id", "id", "title", "html", "content_html")) else []


def normalize_article(article: Mapping[str, Any], *, source_type: str, account_name: str = "", fetched_at: str | None = None) -> dict[str, Any]:
    """Return the stable article record; only public article fields are retained."""

    html = str(first_value(article, "html", "content_html", "body_html", "content", "body", default="") or "")
    title = str(first_value(article, "title", "name", default="") or "").strip()
    article_id = str(first_value(article, "article_id", "id", "mid", "slug", default="") or "").strip()
    canonical_url = str(first_value(article, "canonical_url", "url", "link", "source_url", default="") or "").strip()
    if not article_id:
        article_id = sha256_text(canonical_url or title or html)[:24]
    if not title and html:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
        title = html_lib.unescape(re.sub(r"\s+", " ", match.group(1)).strip()) if match else article_id
    images = first_value(article, "image_urls", "images", "imageUrls", default=[])
    if isinstance(images, str):
        images = [images]
    if not isinstance(images, list):
        images = []
    images = [str(value) for value in images if value]
    record = {
        "article_id": article_id,
        "account_name": str(first_value(article, "account_name", "account", "公众号", default=account_name) or account_name),
        "title": title,
        "canonical_url": canonical_url,
        "published_at": first_value(article, "published_at", "publish_time", "publishedAt", "date", default=""),
        "fetched_at": fetched_at or now_iso(),
        "html": html,
        "image_urls": images,
        "author": str(first_value(article, "author", "作者", default="") or ""),
        "content_hash": sha256_text(html or canonical_url or title),
        "source_access_status": source_type,
        "source_id": str(first_value(article, "source_id", "source", default="") or ""),
    }
    return record


def dedupe_articles(records: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    unique: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    duplicates: list[dict[str, str]] = []
    for item in records:
        record = dict(item)
        keys = (
            str(record.get("article_id", "")),
            str(record.get("canonical_url", "")),
            str(record.get("content_hash", "")),
        )
        duplicate_of = next((seen[key] for key in keys if key and key in seen), None)
        if duplicate_of:
            duplicates.append({"article_id": str(record.get("article_id", "")), "duplicate_of": duplicate_of, "reason": "id_url_or_content_hash"})
            continue
        identity = str(record.get("article_id", ""))
        for key in keys:
            if key:
                seen[key] = identity
        unique.append(record)
    return unique, duplicates


def redact_error(exc: BaseException) -> str:
    """Return an error suitable for logs; never echo an authorization value."""

    text = f"{type(exc).__name__}: {exc}"
    for env_name in ("WECHAT_ARTICLE_API_TOKEN", "WECHAT_ARTICLE_API_BASE"):
        secret = os.environ.get(env_name)
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text[:500]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

#!/usr/bin/env python3
"""Collect public-account articles through an authorized read-only API or export."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from wechat_common import dedupe_articles, normalize_article, now_iso, project_root, redact_error, safe_name, sha256_text, unwrap_collection, write_json


def load_config(root: Path) -> dict:
    path = root / "config/wechat_sources.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"enabled": False}


def api_get(url: str, token: str, timeout: int) -> object:
    headers = {"User-Agent": "WajeAnalystWechatCollector/1.0", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def join_endpoint(base: str, endpoint: str) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return base.rstrip("/") + "/" + endpoint.lstrip("/")


def collect_api(config: dict, day: str, base: str, token: str) -> tuple[list[dict], list[dict]]:
    api = config.get("api", {})
    timeout = int(api.get("timeout_seconds", 45))
    page_size = int(api.get("page_size", 50))
    start = dt.date.fromisoformat(day)
    params = {
        "published_after": start.isoformat(),
        "published_before": (start + dt.timedelta(days=1)).isoformat(),
        "limit": str(page_size),
    }
    articles: list[dict] = []
    errors: list[dict] = []
    cursor = ""
    for _ in range(100):
        query = dict(params)
        if cursor:
            query["cursor"] = cursor
        list_url = join_endpoint(base, str(api.get("list_path", "/articles")))
        list_url = f"{list_url}?{urllib.parse.urlencode(query)}"
        try:
            payload = api_get(list_url, token, timeout)
        except Exception as exc:
            errors.append({"stage": "list", "status": "error", "error": redact_error(exc)})
            break
        batch = unwrap_collection(payload)
        for summary in batch:
            article_id = str(summary.get("article_id") or summary.get("id") or summary.get("mid") or "")
            if not article_id:
                articles.append(normalize_article(summary, source_type="authorized_api", account_name=config.get("account_name", "")))
                continue
            detail_path = str(api.get("detail_path", "/articles/{article_id}")).replace("{article_id}", urllib.parse.quote(article_id, safe=""))
            try:
                detail = api_get(join_endpoint(base, detail_path), token, timeout)
                detail_items = unwrap_collection(detail)
                article = detail_items[0] if detail_items else (detail if isinstance(detail, dict) else summary)
                articles.append(normalize_article(article, source_type="authorized_api", account_name=config.get("account_name", "")))
            except Exception as exc:
                errors.append({"stage": "detail", "article_id": article_id, "status": "error", "error": redact_error(exc)})
        if not isinstance(payload, dict):
            break
        next_cursor = payload.get("next_cursor") or payload.get("nextCursor") or (payload.get("pagination") or {}).get("next_cursor")
        if not next_cursor or str(next_cursor) == cursor:
            break
        cursor = str(next_cursor)
    return articles, errors


def load_export_file(path: Path, account_name: str) -> list[dict]:
    if path.suffix.lower() == ".zip":
        records: list[dict] = []
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                suffix = Path(name).suffix.lower()
                if suffix not in {".json", ".jsonl", ".html", ".htm"}:
                    continue
                data = archive.read(name)
                records.extend(load_export_bytes(data, suffix, f"{path.name}:{name}", account_name))
        return records
    if path.suffix.lower() == ".pdf":
        return load_pdf(path, account_name)
    return load_export_bytes(path.read_bytes(), path.suffix.lower(), path.name, account_name)


def load_pdf(path: Path, account_name: str) -> list[dict]:
    """Convert an authorized PDF export to text HTML without storing credentials."""

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf_not_installed_for_authorized_pdf_export") from exc
    reader = PdfReader(str(path))
    paragraphs = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text:
            paragraphs.append("<p>" + text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>") + "</p>")
    html = "<article><h1>" + path.stem.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</h1>" + "".join(paragraphs) + "</article>"
    return [normalize_article({"id": path.stem, "title": path.stem, "html": html, "source_id": path.name}, source_type="authorized_export_pdf", account_name=account_name)]


def load_export_bytes(data: bytes, suffix: str, source_name: str, account_name: str) -> list[dict]:
    if suffix in {".html", ".htm"}:
        return [normalize_article({"id": source_name, "html": data.decode("utf-8", errors="replace"), "source_id": source_name}, source_type="authorized_export", account_name=account_name)]
    if suffix == ".jsonl":
        payload: object = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
    else:
        payload = json.loads(data.decode("utf-8"))
    return [normalize_article(item, source_type="authorized_export", account_name=account_name, fetched_at=now_iso()) for item in unwrap_collection(payload)]


def collect_exports(root: Path, config: dict, day: str, source_dir: str | None) -> tuple[list[dict], list[dict], str]:
    directory = Path(source_dir).expanduser() if source_dir else root / str(config.get("fallback", {}).get("incoming_dir", "data/incoming/wechat")) / day
    if not directory.exists():
        return [], [{"stage": "input", "status": "skipped", "error": "no_authorized_export_found"}], "unavailable"
    accepted = set(config.get("fallback", {}).get("accepted_extensions", []))
    records: list[dict] = []
    errors: list[dict] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in accepted:
            continue
        try:
            records.extend(load_export_file(path, str(config.get("account_name", ""))))
        except Exception as exc:
            errors.append({"stage": "input", "source": str(path), "status": "error", "error": redact_error(exc)})
    return records, errors, "authorized_export" if records else "unavailable"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--source-dir", default=None, help="Explicit directory containing an authorized export; useful for backfills/tests.")
    args = parser.parse_args()
    root = project_root()
    config = load_config(root)
    out_dir = root / "data/raw/wechat" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    manifest = {"schema_version": 1, "run_id": run_id, "date": args.date, "source": "wechat_authorized_read_only", "articles": [], "duplicates": [], "errors": [], "status": "skipped"}
    if not config.get("enabled", True):
        manifest["errors"].append({"stage": "config", "status": "skipped", "error": "wechat_source_disabled"})
    else:
        base_env = str(config.get("api", {}).get("base_url_env", "WECHAT_ARTICLE_API_BASE"))
        token_env = str(config.get("api", {}).get("token_env", "WECHAT_ARTICLE_API_TOKEN"))
        base = os.environ.get(base_env, "").strip()
        token = os.environ.get(token_env, "")
        if base:
            records, errors = collect_api(config, args.date, base, token)
            source_status = "authorized_api"
        else:
            records, errors, source_status = collect_exports(root, config, args.date, args.source_dir)
        unique, duplicates = dedupe_articles(records)
        manifest["duplicates"] = duplicates
        manifest["errors"] = errors
        manifest["status"] = "ok" if unique else ("degraded" if errors else "empty")
        for record in unique:
            filename = f"{safe_name(record['article_id'])}-{record['content_hash'][:12]}.json"
            target = out_dir / "articles" / filename
            write_json(target, record)
            manifest["articles"].append({
                "article_id": record["article_id"], "title": record["title"], "canonical_url": record["canonical_url"],
                "content_hash": record["content_hash"], "source_access_status": source_status, "path": str(target.relative_to(root)),
            })
    manifest_path = out_dir / f"manifest-{run_id}.json"
    write_json(manifest_path, manifest)
    print(f"wechat collection: {len(manifest['articles'])} articles; status={manifest['status']}; manifest={manifest_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

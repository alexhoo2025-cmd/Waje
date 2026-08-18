#!/usr/bin/env python3
"""Collect project-scoped Lark messages in read-only silent mode."""

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

from lark_common import dedupe_messages, first_value, normalize_message, now_iso, project_root, redact_error, safe_name, unwrap_messages, write_json


def load_config(root: Path) -> dict:
    path = root / "config/lark_sources.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"enabled": False}


def join_endpoint(base: str, endpoint: str) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return base.rstrip("/") + "/" + endpoint.lstrip("/")


def api_get(url: str, token: str, timeout: int) -> object:
    headers = {"User-Agent": "WajeAnalystLarkCollector/1.0", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def allowed_chat_ids(config: dict) -> list[str]:
    return [str(item.get("chat_id", "")) for item in config.get("allowed_chats", []) if isinstance(item, dict) and item.get("chat_id")]


def collect_api(config: dict, day: str, base: str, token: str) -> tuple[list[dict], list[dict]]:
    api = config.get("api", {})
    timeout = int(api.get("timeout_seconds", 30))
    page_size = int(api.get("page_size", 50))
    start = dt.datetime.combine(dt.date.fromisoformat(day), dt.time.min).astimezone()
    end = start + dt.timedelta(days=1)
    chats = allowed_chat_ids(config)
    if not chats:
        return [], [{"stage": "config", "status": "skipped", "error": "no_allowed_chat_ids"}]
    records: list[dict] = []
    errors: list[dict] = []
    for chat_id in chats:
        page_token = ""
        for _ in range(100):
            params = {
                "container_id_type": "chat",
                "container_id": chat_id,
                "page_size": str(page_size),
                "start_time": str(int(start.timestamp())),
                "end_time": str(int(end.timestamp())),
            }
            if page_token:
                params["page_token"] = page_token
            url = join_endpoint(base, str(api.get("list_path", "/open-apis/im/v1/messages")))
            url = f"{url}?{urllib.parse.urlencode(params)}"
            try:
                payload = api_get(url, token, timeout)
            except Exception as exc:
                errors.append({"stage": "list", "chat_id": chat_id, "status": "error", "error": redact_error(exc)})
                break
            batch = unwrap_messages(payload)
            records.extend(normalize_message(item, source_type="authorized_api", fetched_at=now_iso()) for item in batch)
            data = payload.get("data", {}) if isinstance(payload, dict) else {}
            if not isinstance(data, dict):
                break
            has_more = bool(data.get("has_more") or data.get("hasMore"))
            next_token = str(data.get("page_token") or data.get("pageToken") or "")
            if not has_more or not next_token or next_token == page_token:
                break
            page_token = next_token
    return records, errors


def load_export(path: Path) -> list[dict]:
    if path.suffix.lower() == ".zip":
        records: list[dict] = []
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if Path(name).suffix.lower() not in {".json", ".jsonl"}:
                    continue
                records.extend(load_export_bytes(archive.read(name), Path(name).suffix.lower()))
        return records
    return load_export_bytes(path.read_bytes(), path.suffix.lower())


def load_export_bytes(data: bytes, suffix: str) -> list[dict]:
    if suffix == ".jsonl":
        payload: object = [json.loads(line) for line in data.decode("utf-8", errors="replace").splitlines() if line.strip()]
    else:
        payload = json.loads(data.decode("utf-8", errors="replace"))
    return [normalize_message(item, source_type="authorized_export", fetched_at=now_iso()) for item in unwrap_messages(payload)]


def collect_exports(root: Path, config: dict, day: str, source_dir: str | None) -> tuple[list[dict], list[dict], str]:
    directory = Path(source_dir).expanduser() if source_dir else root / str(config.get("fallback", {}).get("incoming_dir", "data/incoming/lark")) / day
    if not directory.exists():
        return [], [{"stage": "input", "status": "skipped", "error": "no_authorized_export_found"}], "unavailable"
    accepted = set(config.get("fallback", {}).get("accepted_extensions", []))
    records: list[dict] = []
    errors: list[dict] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in accepted:
            continue
        try:
            records.extend(load_export(path))
        except Exception as exc:
            errors.append({"stage": "input", "source": str(path), "status": "error", "error": redact_error(exc)})
    allowed = set(allowed_chat_ids(config))
    if allowed:
        records = [record for record in records if record.get("chat_id") in allowed]
    return records, errors, "authorized_export" if records else "unavailable"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--source-dir", default=None, help="Authorized JSON/JSONL/ZIP export directory; useful for first test.")
    args = parser.parse_args()
    root = project_root()
    config = load_config(root)
    out_dir = root / "data/raw/lark" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    manifest = {"schema_version": 1, "run_id": run_id, "date": args.date, "source": "lark_read_only_silent", "messages": [], "duplicates": [], "errors": [], "status": "skipped", "outbound_actions": 0}
    if not config.get("enabled", True):
        manifest["errors"].append({"stage": "config", "status": "skipped", "error": "lark_source_disabled"})
    elif not config.get("silent_mode", True):
        manifest["errors"].append({"stage": "config", "status": "error", "error": "silent_mode_must_remain_enabled"})
    else:
        base_env = str(config.get("api", {}).get("base_url_env", "LARK_API_BASE"))
        token_env = str(config.get("api", {}).get("token_env", "LARK_API_TOKEN"))
        base = os.environ.get(base_env, "").strip()
        token = os.environ.get(token_env, "")
        if base:
            records, errors = collect_api(config, args.date, base, token)
            source_status = "authorized_api"
        else:
            records, errors, source_status = collect_exports(root, config, args.date, args.source_dir)
        unique, duplicates = dedupe_messages(records)
        manifest["duplicates"] = duplicates
        manifest["errors"] = errors
        manifest["status"] = "ok" if unique else ("degraded" if errors else "empty")
        for record in unique:
            filename = f"{safe_name(record['message_id'])}-{record['content_hash'][:12]}.json"
            target = out_dir / "messages" / filename
            write_json(target, record)
            manifest["messages"].append({"message_id": record["message_id"], "chat_id": record["chat_id"], "created_at": record["created_at"], "path": str(target.relative_to(root)), "source_access_status": source_status})
    manifest_path = out_dir / f"manifest-{run_id}.json"
    write_json(manifest_path, manifest)
    print(f"lark collection: {len(manifest['messages'])} messages; status={manifest['status']}; outbound_actions=0; manifest={manifest_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

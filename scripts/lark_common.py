#!/usr/bin/env python3
"""Shared helpers for the read-only, silent Lark message pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return Path(os.environ.get("WAJE_ANALYST_ROOT", str(ROOT))).resolve()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def safe_name(value: str, fallback: str = "message") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_")
    return cleaned[:100] or fallback


def first_value(mapping: Mapping[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return default


def unwrap_messages(payload: Any) -> list[dict[str, Any]]:
    """Normalize common Lark export/API envelopes to message dictionaries."""

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("messages", "items", "records", "results"):
        if isinstance(payload.get(key), list):
            return [item for item in payload[key] if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return unwrap_messages(data)
    return [payload] if any(key in payload for key in ("message_id", "message_id", "content", "text", "body")) else []


SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(password|passwd|pwd|token|secret|api[_-]?key|cookie|authorization)\s*[:=：]\s*[^\s,;]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)(-----BEGIN [A-Z ]+-----).*?(-----END [A-Z ]+-----)"), r"\1[REDACTED]\2"),
]


def redact_text(value: str) -> str:
    text = str(value or "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()


def redact_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    for env_name in ("LARK_API_TOKEN", "LARK_TENANT_ACCESS_TOKEN", "LARK_APP_SECRET"):
        secret = os.environ.get(env_name)
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return redact_text(text)[:500]


def _sender_hash(message: Mapping[str, Any]) -> str:
    sender = first_value(message, "sender_id", "sender", "sender_id_type", "operator_id", default="")
    if isinstance(sender, dict):
        sender = first_value(sender, "id", "open_id", "user_id", "name", default="")
    return sha256_text(str(sender))[:16] if sender else ""


def normalize_message(message: Mapping[str, Any], *, source_type: str, fetched_at: str | None = None) -> dict[str, Any]:
    """Keep only the project-useful, redacted message fields."""

    text = first_value(message, "text", "content", "body", "message", default="")
    if isinstance(text, dict):
        text = json.dumps(text, ensure_ascii=False)
    text = redact_text(str(text or ""))
    chat_id = first_value(message, "chat_id", "container_id", "conversation_id", default="")
    chat_name = first_value(message, "chat_name", "conversation_name", "chat_title", default="")
    message_id = first_value(message, "message_id", "id", "msg_id", default="")
    created_at = first_value(message, "created_at", "create_time", "timestamp", "time", default="")
    if isinstance(created_at, (int, float)):
        created_at = datetime.fromtimestamp(created_at).astimezone().isoformat(timespec="seconds")
    created_at = str(created_at or "")
    if not message_id:
        message_id = sha256_text(f"{chat_id}|{created_at}|{text}")[:24]
    return {
        "message_id": str(message_id),
        "chat_id": str(chat_id),
        "chat_name": str(chat_name),
        "created_at": created_at,
        "fetched_at": fetched_at or now_iso(),
        "text": text,
        "content_hash": sha256_text(text),
        "sender_hash": _sender_hash(message),
        "reply_to_message_id": str(first_value(message, "reply_to_message_id", "parent_id", default="") or ""),
        "source_access_status": source_type,
    }


def dedupe_messages(records: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    unique: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    duplicates: list[dict[str, str]] = []
    for item in records:
        record = dict(item)
        keys = (str(record.get("message_id", "")), str(record.get("content_hash", "")))
        duplicate_of = next((seen[key] for key in keys if key and key in seen), None)
        if duplicate_of:
            duplicates.append({"message_id": str(record.get("message_id", "")), "duplicate_of": duplicate_of, "reason": "id_or_content_hash"})
            continue
        identity = str(record.get("message_id", ""))
        for key in keys:
            if key:
                seen[key] = identity
        unique.append(record)
    return unique, duplicates


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


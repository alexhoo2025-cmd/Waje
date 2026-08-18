#!/usr/bin/env python3
"""Read, normalize and version Waje's Lark configuration workbook.

The source workbook is always read with the authorized *user* identity.  Full
cell contents are held only in process memory; project outputs contain a
redacted, structured configuration index rather than an original-sheet mirror.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(os.environ.get("WAJE_ANALYST_ROOT", Path(__file__).resolve().parents[1])).resolve()
CONFIG_PATH = ROOT / "config/waje_config_workbook.json"
MAX_DOC_ENTRIES_PER_SHEET = 36

TOPICS = {
    "游戏与场次经济": {
        "filename": "游戏与场次经济.md",
        "purpose": "用于统一游戏、供应商、玩法、场次、下注档位、显隐与推荐逻辑，并与游戏维表、下注和结算事实表核对。",
    },
    "数值与生命周期": {
        "filename": "数值与生命周期.md",
        "purpose": "用于追踪生命周期、PR、预期回报、奖池、盈利控制和熔断配置；实际 RTP 仍以服务端结算事实为准。",
    },
    "任务运营与商业化": {
        "filename": "任务运营与商业化.md",
        "purpose": "用于拆解新手任务、日常任务、弹窗、活动、福利和触达机制，并映射曝光、领取、完成与转化事件。",
    },
    "支付提现与风控": {
        "filename": "支付提现与风控.md",
        "purpose": "用于理解充值、商城、提现、KYC、审核和反作弊配置；支付与资产结论以订单、审核和资产流水事实表为准。",
    },
    "版本分包与平台配置": {
        "filename": "版本分包与平台配置.md",
        "purpose": "用于维护 H5、Android、iOS、分包、货币、客户端能力和历史版本的配置脉络。",
    },
}

URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|cookie|authorization)\b\s*[:=：]\s*([^\s,;]+)"
)
BEARER_RE = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+")
ERROR_VALUE_RE = re.compile(r"^#(?:REF!|NAME\?|VALUE!|N/A|DIV/0!|NUM!|NULL!|SPILL!)$")
NUMERIC_RE = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")
SEMVER_RE = re.compile(r"(?i)(?:h5|app|ios|android)\s*\d+\.\d+(?:\.\d+)?")


class WorkbookReadError(RuntimeError):
    """A source read failed without exposing the source payload in logs."""


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_cli() -> Path:
    explicit = os.environ.get("LARK_CLI_BIN", "").strip()
    if explicit and Path(explicit).is_file():
        return Path(explicit)
    found = shutil.which("lark-cli")
    if found:
        return Path(found)
    candidates = sorted(Path.home().glob(".local/node-*/bin/lark-cli"), reverse=True)
    if candidates:
        return candidates[0]
    raise FileNotFoundError("lark-cli not found; install and bind the Lark CLI first")


def redact_text(value: Any) -> str:
    text = str(value or "")
    text = BEARER_RE.sub(r"\1[REDACTED]", text)
    text = SECRET_RE.sub(lambda match: f"{match.group(1)}=[REDACTED]", text)
    text = EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    text = URL_RE.sub("[URL_REDACTED]", text)
    return text.strip()


def redact_error(value: str) -> str:
    return redact_text(value).replace("\n", " ")[:500]


def run_cli(cli: Path, args: list[str], *, cwd: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    last_error = ""
    for attempt in range(4):
        completed = subprocess.run(
            [str(cli), *args, "--as", "user", "--format", "json"],
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=240,
        )
        output = completed.stdout.strip() or completed.stderr.strip()
        try:
            envelope = json.loads(output) if output else {}
        except json.JSONDecodeError:
            envelope = {}
        message = str(envelope.get("error", {}).get("message", output or "unknown API error"))
        retryable = "rate_limit" in output.lower() or bool(envelope.get("error", {}).get("retryable"))
        if completed.returncode == 0 and envelope.get("ok") is True:
            if envelope.get("identity") != "user":
                raise WorkbookReadError("lark-cli did not use the authorized user identity")
            return envelope
        last_error = redact_error(message)
        if retryable and attempt < 3:
            time.sleep((attempt + 1) * 0.75)
            continue
        break
    raise WorkbookReadError(f"lark-cli failed: {last_error}")


def index_to_column(index: int) -> str:
    result = ""
    value = index + 1
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(65 + remainder) + result
    return result


def safe_key(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", redact_text(value)).strip("_")
    return (cleaned[:100] or fallback)


def scalar_value(value: Any) -> tuple[Any, str]:
    if isinstance(value, bool):
        return value, "boolean"
    if isinstance(value, (int, float)):
        return value, "number"
    text = redact_text(value)
    if text.upper() in {"TRUE", "FALSE"}:
        return text.upper() == "TRUE", "boolean"
    if NUMERIC_RE.fullmatch(text) and not (len(text.lstrip("-")) > 1 and text.lstrip("-").startswith("0")):
        try:
            return (float(text), "number") if "." in text else (int(text), "number")
        except ValueError:
            pass
    return text, "text"


def parse_json_text(value: str) -> Any | None:
    source = value.strip()
    if not source.startswith(("{", "[")):
        return None
    for candidate in (source, source.replace('""', '"')):
        try:
            return json.loads(candidate)
        except (TypeError, ValueError):
            continue
    return None


def flatten_value(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = safe_key(str(key), "key")
            yield from flatten_value(nested, f"{prefix}.{key_text}" if prefix else key_text)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from flatten_value(nested, f"{prefix}[{index}]")
    else:
        yield prefix or "value", value


def parse_annotated_csv(text: str, column_indices: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in csv.reader(io.StringIO(text)):
        if not row:
            continue
        match = re.match(r"^\[row=(\d+)\]\s?(.*)$", row[0])
        if not match:
            continue
        row_number = int(match.group(1))
        row[0] = match.group(2)
        cells = {column_indices[index] if index < len(column_indices) else index_to_column(index): cell for index, cell in enumerate(row)}
        rows.append({"row_number": row_number, "cells": cells})
    return rows


def header_map(rows: list[dict[str, Any]]) -> tuple[int, dict[str, str]]:
    candidates: list[tuple[int, int, dict[str, str]]] = []
    for item in rows[:16]:
        cells = {column: redact_text(value) for column, value in item["cells"].items() if redact_text(value)}
        if len(cells) < 2:
            continue
        hints = sum(1 for value in cells.values() if re.search(r"(?i)(id|name|type|config|字段|配置|说明|场次|游戏|奖励|状态|金额|路径)", value))
        score = len(cells) + hints * 3
        candidates.append((score, item["row_number"], cells))
    if not candidates:
        return 0, {}
    _, row_number, cells = max(candidates, key=lambda item: (item[0], item[1]))
    return row_number, cells


def row_anchor(cells: dict[str, str], headers: dict[str, str], row_number: int) -> str:
    values = [redact_text(value) for value in cells.values() if redact_text(value)]
    if not values:
        return f"row_{row_number}"
    first = safe_key(values[0], f"row_{row_number}")
    if len(values) > 1 and first in {"定义场次", "控制显隐", "推荐场次", "开关"}:
        return f"{first}_{safe_key(values[1], 'value')}"
    return first


def category_for_sheet(sheet_name: str) -> str:
    name = sheet_name.lower()
    if re.search(r"tx|提现|充值|商城|礼包|kyc|risk|审核|反作弊|刷子|人脸|支付", name):
        return "支付提现与风控"
    if re.search(r"生命周期|pr数值|盈利|熔断|破产|发财金", name):
        return "数值与生命周期"
    if re.search(r"任务|弹窗|分享|led", name):
        return "任务运营与商业化"
    if re.search(r"游戏|whot|捕鱼|tada|spribe|omg|pg|拼奈拉|五张牌|21点|体彩|limbo|bet|场次|轻量|外接|顺序|免费玩家|cash上限", name):
        return "游戏与场次经济"
    return "版本分包与平台配置"


def status_for_sheet(sheet_name: str, is_hidden: bool) -> tuple[str, str, str]:
    name = sheet_name.lower()
    if "作废" in name:
        return "obsolete", "archive", "old_historical_reference"
    if is_hidden or "老版" in name or "老表" in name or "老玩家" in name:
        return "historical_reference", "archive", "old_historical_reference" if "老" in name else "new_current_primary"
    if SEMVER_RE.search(sheet_name) or re.search(r"\d{2}年\d+月\d+版", sheet_name) or "圣诞节" in sheet_name or "3.14前" in sheet_name:
        return "historical_reference", "historical_release", "new_current_primary"
    return "current_candidate", "unversioned", "new_current_primary"


def sensitivity_for_topic(topic: str) -> str:
    if topic == "支付提现与风控":
        return "restricted_internal"
    if topic == "数值与生命周期":
        return "restricted_internal"
    return "internal"


def normalize_sheet_entries(sheet: dict[str, Any], csv_payload: dict[str, Any], structure: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if csv_payload.get("has_more"):
        raise WorkbookReadError(f"sheet {sheet['sheet_name']} was truncated and cannot be indexed safely")
    annotated = str(csv_payload.get("annotated_csv", ""))
    column_indices = list(csv_payload.get("col_indices", []))
    if not annotated:
        raise WorkbookReadError(f"sheet {sheet['sheet_name']} did not return readable values")
    rows = parse_annotated_csv(annotated, column_indices)
    header_row, headers = header_map(rows)
    entries: list[dict[str, Any]] = []
    formula_errors = 0
    topic = category_for_sheet(sheet["sheet_name"])
    evidence_state, version_scope, package_scope = status_for_sheet(sheet["sheet_name"], bool(sheet.get("is_hidden")))
    for item in rows:
        number = item["row_number"]
        cells = item["cells"]
        anchor = row_anchor(cells, headers, number)
        for column, raw_value in cells.items():
            raw_text = redact_text(raw_value)
            if not raw_text:
                continue
            header = safe_key(headers.get(column, f"column_{column}"), f"column_{column}")
            base_path = f"{anchor}.{header}"
            parsed = parse_json_text(raw_text)
            leaves = flatten_value(parsed, base_path) if parsed is not None else [(base_path, raw_text)]
            for path, leaf in leaves:
                value, value_type = scalar_value(leaf)
                formula_issue = isinstance(value, str) and bool(ERROR_VALUE_RE.fullmatch(value))
                formula_errors += int(formula_issue)
                record = {
                    "source_revision": sheet["source_revision"],
                    "sheet_id": sheet["sheet_id"],
                    "sheet_name": sheet["sheet_name"],
                    "visibility": "hidden" if sheet.get("is_hidden") else "visible",
                    "source_range": f"{column}{number}",
                    "category": topic,
                    "package_scope": package_scope,
                    "version_scope": version_scope,
                    "evidence_state": evidence_state,
                    "key_path": path,
                    "normalized_value": value,
                    "value_type": value_type,
                    "formula_issue": formula_issue,
                    "sensitivity": sensitivity_for_topic(topic),
                }
                record["content_hash"] = sha256({key: record[key] for key in ("key_path", "normalized_value", "value_type", "formula_issue")})
                entries.append(record)
    metadata = {
        **sheet,
        "category": topic,
        "package_scope": package_scope,
        "version_scope": version_scope,
        "evidence_state": evidence_state,
        "actual_range": csv_payload.get("actual_range", ""),
        "source_read_status": "complete",
        "entry_count": len(entries),
        "formula_issue_count": formula_errors,
        "layout": {
            "merged_cells": structure.get("merged_cells", structure.get("merged_ranges", [])),
            "hidden_rows": structure.get("hidden_rows", []),
            "hidden_columns": structure.get("hidden_cols", structure.get("hidden_columns", [])),
            "frozen": structure.get("frozen", {}),
        },
    }
    metadata["content_hash"] = sha256([{key: entry[key] for key in ("source_range", "key_path", "content_hash")} for entry in entries])
    return entries, metadata


def make_diff(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    old_entries = (previous or {}).get("entries", [])
    new_entries = current.get("entries", [])

    def mapping(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {f"{entry['sheet_id']}|{entry['source_range']}|{entry['key_path']}": entry for entry in entries}

    old_map, new_map = mapping(old_entries), mapping(new_entries)
    added_keys = sorted(new_map.keys() - old_map.keys())
    removed_keys = sorted(old_map.keys() - new_map.keys())
    modified_keys = sorted(key for key in new_map.keys() & old_map.keys() if new_map[key]["content_hash"] != old_map[key]["content_hash"])
    changes = []
    for change_type, keys in (("added", added_keys), ("removed", removed_keys), ("modified", modified_keys)):
        for key in keys:
            after = new_map.get(key)
            before = old_map.get(key)
            changes.append({
                "change_type": change_type,
                "sheet_id": (after or before)["sheet_id"],
                "sheet_name": (after or before)["sheet_name"],
                "source_range": (after or before)["source_range"],
                "key_path": (after or before)["key_path"],
                "before": before.get("normalized_value") if before else None,
                "after": after.get("normalized_value") if after else None,
                "category": (after or before)["category"],
            })
    by_sheet: dict[str, Counter[str]] = defaultdict(Counter)
    for change in changes:
        by_sheet[change["sheet_name"]][change["change_type"]] += 1
    return {
        "previous_revision": (previous or {}).get("revision"),
        "current_revision": current.get("revision"),
        "summary": {"added": len(added_keys), "modified": len(modified_keys), "removed": len(removed_keys)},
        "sheets": [{"sheet_name": name, **dict(counter)} for name, counter in sorted(by_sheet.items())],
        "changes": changes,
    }


def markdown_value(value: Any, limit: int = 160) -> str:
    if isinstance(value, bool):
        text = "true" if value else "false"
    elif value is None:
        text = "—"
    else:
        text = str(value)
    text = text.replace("|", "\\|").replace("\n", " ").strip()
    return text if len(text) <= limit else f"{text[:limit - 1]}…"


def relative_index_link(from_dir: Path, processed_dir: Path) -> str:
    target = processed_dir / "current" / "configuration-index.json"
    return os.path.relpath(target, from_dir).replace(os.sep, "/")


def next_history_path(history_dir: Path, run_date: str, revision: int | str) -> Path:
    """Never overwrite a previous weekly comparison for the same revision."""
    candidate = history_dir / f"{run_date}-revision-{revision}-diff.json"
    if not candidate.exists():
        return candidate
    suffix = 2
    while True:
        candidate = history_dir / f"{run_date}-revision-{revision}-diff-{suffix}.json"
        if not candidate.exists():
            return candidate
        suffix += 1


def write_documents(index: dict[str, Any], diff: dict[str, Any], *, knowledge_dir: Path, topic_dir: Path, processed_dir: Path, source_url: str) -> list[Path]:
    topic_dir.mkdir(parents=True, exist_ok=True)
    docs: list[Path] = []
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    entries_by_sheet: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sheet in index["sheets"]:
        by_topic[sheet["category"]].append(sheet)
    for entry in index["entries"]:
        entries_by_sheet[entry["sheet_id"]].append(entry)

    changed_by_sheet = {row["sheet_name"]: row for row in diff.get("sheets", [])}
    navigation = knowledge_dir / "Waje产品游戏配置资料库.md"
    nav_lines = [
        "---",
        "type: configuration-reference",
        "domain: product-game-and-business-config",
        "product: Waje Special",
        "status: generated",
        f"updated: {index['fetched_at'][:10]}",
        f"source_revision: {index['revision']}",
        "tags: [waje, 新包, 配置, 游戏, 数值, 风控, 生命周期]",
        "---",
        "",
        "# Waje 产品与游戏配置资料库",
        "",
        "> 本资料库由“线上数值新包”工作簿自动拆解。它记录产品设计配置与版本线索，不等同于当前生产事实；RTP、支付、资产、提现和风控结论仍须以服务端配置快照及事实表验证。",
        "",
        "## 1. 同步状态",
        "",
        f"- 来源：[飞书配置工作簿]({source_url})",
        f"- 当前 revision：`{index['revision']}`；读取时间：`{index['fetched_at']}`。",
        f"- 工作表：`{len(index['sheets'])}` 个，其中隐藏 ` {sum(1 for item in index['sheets'] if item.get('is_hidden'))}` 个；结构化配置项：`{len(index['entries'])}` 条。",
        f"- 本次差异：新增 `{diff['summary']['added']}`、修改 `{diff['summary']['modified']}`、删除 `{diff['summary']['removed']}`。",
        "- 更新频率：每周五 15:00（Asia/Hong_Kong）；revision 未变化时不重写资料。",
        "",
        "## 2. 阅读入口",
        "",
    ]
    for topic, spec in TOPICS.items():
        nav_lines.append(f"- [{topic}](./Waje配置资料/{spec['filename']})：{spec['purpose']}")
    nav_lines.extend([
        "",
        "## 3. 本周变更摘要",
        "",
        "| 工作表 | 新增 | 修改 | 删除 |",
        "| --- | ---: | ---: | ---: |",
    ])
    if changed_by_sheet:
        for name, row in sorted(changed_by_sheet.items()):
            nav_lines.append(f"| {name} | {row.get('added', 0)} | {row.get('modified', 0)} | {row.get('removed', 0)} |")
    else:
        nav_lines.append("| 无配置键变化 | 0 | 0 | 0 |")
    nav_lines.extend([
        "",
        "## 4. 全部工作表目录",
        "",
        "| # | 工作表 | 专题 | 可见性 | 证据状态 | 配置项 |",
        "| ---: | --- | --- | --- | --- | ---: |",
    ])
    for sheet in index["sheets"]:
        nav_lines.append(
            f"| {sheet['index'] + 1} | {sheet['sheet_name']} | {sheet['category']} | {'隐藏' if sheet.get('is_hidden') else '可见'} | `{sheet['evidence_state']}` | {sheet['entry_count']} |"
        )
    nav_lines.extend([
        "",
        "## 5. 使用边界",
        "",
        "- `new_current_primary` 是当前新包分析主源；`old_historical_reference`、`historical_release` 与 `obsolete` 仅用于机制和版本演进参考。",
        "- 任何配置数值必须同时核对适用游戏、包、端、版本和生效窗口；工作簿未提供服务端命中证据时，统一标为 `current_candidate`。",
        "- 完整结构化索引（含每项来源单元格、配置键、规范值和哈希）见 [configuration-index.json](" + relative_index_link(knowledge_dir, processed_dir) + ")；项目内不保存整表原始快照。",
        "",
        "## 6. 关联资料",
        "",
        "- [[Waje新老包游戏记录与数值设定资料库-2026-08-13]]",
        "- [[风控数值与机器人机制拆解-2026-08-12]]",
        "- [[Waje全链路数据需求与埋点设计总表-2026-08-11]]",
    ])
    navigation.write_text("\n".join(nav_lines) + "\n", encoding="utf-8")
    docs.append(navigation)

    for topic, spec in TOPICS.items():
        path = topic_dir / spec["filename"]
        lines = [
            "---",
            "type: configuration-reference-topic",
            "product: Waje Special",
            f"topic: {topic}",
            "status: generated",
            f"updated: {index['fetched_at'][:10]}",
            f"source_revision: {index['revision']}",
            "---",
            "",
            f"# Waje 配置资料｜{topic}",
            "",
            f"> {spec['purpose']}",
            "",
            "## 同步与证据口径",
            "",
            f"- 来源 revision：`{index['revision']}`；仅保留结构化、脱敏后的配置键和值。",
            "- `current_candidate` 只代表工作簿中的非历史候选配置；未获得服务端配置快照或规则命中日志前，不得写为现网已生效。",
            f"- 完整数据索引：[configuration-index.json]({relative_index_link(topic_dir, processed_dir)})。",
            "",
            "## 本周变更",
            "",
            "| 类型 | 工作表 | 单元格 | 配置键 | 更新后值 |",
            "| --- | --- | --- | --- | --- |",
        ]
        changed = [item for item in diff.get("changes", []) if item["category"] == topic]
        for item in changed[:80]:
            lines.append(f"| {item['change_type']} | {item['sheet_name']} | {item['source_range']} | `{item['key_path']}` | {markdown_value(item['after'])} |")
        if not changed:
            lines.append("| 无 | — | — | — | — |")
        elif len(changed) > 80:
            lines.append(f"| 其余 {len(changed) - 80} 项 | 见结构化索引 | — | — | — |")

        for sheet in sorted(by_topic.get(topic, []), key=lambda item: item["index"]):
            lines.extend([
                "",
                f"## {sheet['sheet_name']}",
                "",
                f"- 来源：`revision {sheet['source_revision']} / {sheet['sheet_id']} / {sheet['actual_range'] or '已用区域'}`。",
                f"- 状态：`{sheet['evidence_state']}`；包归属：`{sheet['package_scope']}`；版本范围：`{sheet['version_scope']}`；可见性：`{'hidden' if sheet.get('is_hidden') else 'visible'}`。",
                f"- 结构化配置项：`{sheet['entry_count']}`；公式错误显示值：`{sheet['formula_issue_count']}`；合并单元格：`{len(sheet['layout'].get('merged_cells') or [])}`。",
                "",
                "| 单元格 | 配置键 | 值 | 类型 |",
                "| --- | --- | --- | --- |",
            ])
            samples = entries_by_sheet.get(sheet["sheet_id"], [])
            for entry in samples[:MAX_DOC_ENTRIES_PER_SHEET]:
                lines.append(f"| {entry['source_range']} | `{entry['key_path']}` | {markdown_value(entry['normalized_value'])} | {entry['value_type']} |")
            if not samples:
                lines.append("| — | 无可读取配置项 | — | — |")
            elif len(samples) > MAX_DOC_ENTRIES_PER_SHEET:
                lines.append(f"| … | 其余 {len(samples) - MAX_DOC_ENTRIES_PER_SHEET} 项保存在完整结构化索引 | — | — |")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        docs.append(path)
    return docs


def read_sheet(cli: Path, workbook_url: str, sheet: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    structure_envelope: dict[str, Any] = {"data": {}}
    if sheet.get("merged_cells_count") or sheet.get("frozen_rows") or sheet.get("frozen_columns"):
        structure_envelope = run_cli(
            cli,
            ["sheets", "+sheet-info", "--url", workbook_url, "--sheet-id", str(sheet["sheet_id"]), "--include", "merges,hidden_rows,hidden_cols,frozen"],
            cwd=ROOT,
        )
    values_envelope = run_cli(
        cli,
        ["sheets", "+csv-get", "--url", workbook_url, "--sheet-id", str(sheet["sheet_id"]), "--max-chars", "20000000"],
        cwd=ROOT,
    )
    return values_envelope.get("data", {}), structure_envelope.get("data", {})


def collect_index(config: dict[str, Any], *, fetched_at: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    cli = resolve_cli()
    workbook_url = str(config["workbook_url"])
    envelope = run_cli(cli, ["sheets", "+workbook-info", "--url", workbook_url], cwd=ROOT)
    data = envelope.get("data", {})
    revision = data.get("revision")
    if revision is None:
        raise WorkbookReadError("source workbook did not return a revision")
    entries: list[dict[str, Any]] = []
    sheets: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    candidates: list[dict[str, Any]] = []
    for source_sheet in data.get("sheets", []):
        if source_sheet.get("resource_type") != "sheet":
            failures.append({"sheet_id": str(source_sheet.get("sheet_id", "")), "sheet_name": str(source_sheet.get("sheet_name", "")), "error": "unsupported_sheet_resource_type"})
            continue
        sheet = {**source_sheet, "sheet_name": source_sheet.get("sheet_name") or source_sheet.get("title") or "Untitled", "source_revision": revision}
        candidates.append(sheet)

    def fetch_one(sheet: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        csv_payload, structure = read_sheet(cli, workbook_url, sheet)
        return normalize_sheet_entries(sheet, csv_payload, structure)

    workers = max(1, min(int(config.get("read", {}).get("max_parallel_sheets", 4)), 6))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_one, sheet): sheet for sheet in candidates}
        for future in as_completed(futures):
            sheet = futures[future]
            try:
                item_entries, metadata = future.result()
                entries.extend(item_entries)
                sheets.append(metadata)
            except (WorkbookReadError, subprocess.TimeoutExpired) as exc:
                failures.append({"sheet_id": str(sheet["sheet_id"]), "sheet_name": sheet["sheet_name"], "error": redact_error(str(exc))})
            except Exception as exc:
                failures.append({"sheet_id": str(sheet["sheet_id"]), "sheet_name": sheet["sheet_name"], "error": redact_error(str(exc))})
    sheets.sort(key=lambda item: item["index"])
    entries.sort(key=lambda item: (item["sheet_id"], item["source_range"], item["key_path"]))
    index = {
        "schema_version": 1,
        "source_name": config["source_name"],
        "source_url": workbook_url,
        "revision": revision,
        "fetched_at": fetched_at,
        "sheet_count": len(data.get("sheets", [])),
        "hidden_sheet_count": sum(1 for item in data.get("sheets", []) if item.get("is_hidden")),
        "sheets": sheets,
        "entries": entries,
    }
    index["content_hash"] = sha256([{key: entry[key] for key in ("sheet_id", "source_range", "key_path", "content_hash")} for entry in entries])
    return index, failures


def run(config_path: Path, *, run_date: str, force: bool = False, skip_graph: bool = False) -> dict[str, Any]:
    config = load_json(config_path)
    if not config:
        raise FileNotFoundError(f"configuration missing: {config_path}")
    storage = config["storage"]
    processed_dir = ROOT / storage["processed_dir"]
    output_dir = ROOT / storage["output_dir"] / run_date
    knowledge_dir = ROOT / storage["knowledge_dir"]
    topic_dir = ROOT / storage["topic_dir"]
    current_path = processed_dir / "current" / "configuration-index.json"
    started_at = now_iso()
    log: dict[str, Any] = {
        "schema_version": 1,
        "job_id": "waje_config_workbook_weekly",
        "date": run_date,
        "started_at": started_at,
        "status": "error",
        "source": config["source_name"],
        "source_url": config["workbook_url"],
        "schedule": config["schedule"],
        "failures": [],
    }
    try:
        cli = resolve_cli()
        revision = run_cli(cli, ["sheets", "+revision-get", "--url", config["workbook_url"]], cwd=ROOT).get("data", {}).get("revision")
        previous = load_json(current_path)
        log["revision"] = revision
        log["previous_revision"] = (previous or {}).get("revision")
        if previous and previous.get("revision") == revision and not force:
            log.update({"status": "skipped_no_revision", "updated_documents": [], "change_summary": {"added": 0, "modified": 0, "removed": 0}})
            return log
        index, failures = collect_index(config, fetched_at=now_iso())
        log["failures"] = failures
        log["read_sheet_count"] = len(index["sheets"])
        log["expected_sheet_count"] = index["sheet_count"]
        if failures or len(index["sheets"]) != index["sheet_count"]:
            log["status"] = "degraded"
            return log
        diff = make_diff(previous, index)
        history_path = next_history_path(processed_dir / "history", run_date, index["revision"])
        write_json(current_path, index)
        write_json(history_path, diff)
        docs = write_documents(index, diff, knowledge_dir=knowledge_dir, topic_dir=topic_dir, processed_dir=processed_dir, source_url=config["workbook_url"])
        log.update({
            "status": "ok",
            "change_summary": diff["summary"],
            "updated_documents": [str(path.relative_to(ROOT)) for path in docs],
            "index_path": str(current_path.relative_to(ROOT)),
            "diff_path": str(history_path.relative_to(ROOT)),
        })
        if not skip_graph:
            subprocess.run([sys.executable, str(ROOT / "tools/build_graph.py")], cwd=ROOT, check=True)
            log["graph_refreshed"] = True
        return log
    except Exception as exc:  # retain a safe failure receipt for scheduled runs
        log["status"] = "error"
        log["failures"].append({"stage": "run", "error": redact_error(str(exc))})
        return log
    finally:
        log["finished_at"] = now_iso()
        write_json(output_dir / "run-log.json", log)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--force", action="store_true", help="Re-read and rebuild even when the revision is unchanged")
    parser.add_argument("--skip-graph", action="store_true")
    args = parser.parse_args()
    log = run(args.config.resolve(), run_date=args.date, force=args.force, skip_graph=args.skip_graph)
    print(json.dumps({key: log.get(key) for key in ("status", "revision", "previous_revision", "read_sheet_count", "expected_sheet_count", "change_summary", "failures")}, ensure_ascii=False))
    return 0 if log["status"] in {"ok", "skipped_no_revision"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

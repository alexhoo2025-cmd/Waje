#!/usr/bin/env python3
"""Scan the Waje product-department Wiki and refresh local project indexes.

The scanner uses the already-bound Lark CLI user identity. It inventories the
tree on every run, re-reads active non-history Docx nodes because node-list does
not expose a reliable updated_at value, and uses content hashes to identify
new/changed material. It persists metadata/topic summaries rather than full
source documents. It never sends messages or writes to Lark.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CLI_DEFAULT = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
SPACE_ID = "7512752924641001510"
ROOT_NODE_TOKEN = "K7dPwONzTi98z6kc2a9lV9xAgzb"
SOURCE_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/K7dPwONzTi98z6kc2a9lV9xAgzb?fromScene=spaceOverview"
PREVIOUS_CRAWL = ROOT / "data/raw/lark/2026-08-11/product-department-crawl.json"
PREVIOUS_INDEX = ROOT / "data/raw/lark/2026-08-11/product-department-index.json"

HISTORY_TOP_LEVEL = {"HFYL历史文档"}
TOPIC_RULES: dict[str, list[str]] = {
    "需求与版本": ["需求", "版本", "发版", "上线", "热更", "回滚", "排期"],
    "数据与埋点": ["数据", "指标", "报表", "看板", "埋点", "事件", "SQL", "BQ", "Ares", "起源"],
    "支付提现与KYC": ["充值", "提现", "支付", "订单", "KYC", "BVN", "NIN", "审核", "银行卡"],
    "游戏与数值": ["游戏", "玩法", "机器人", "匹配", "奖池", "RTP", "回报比", "投注"],
    "增长与运营": ["新手", "留存", "首充", "礼包", "活动", "Push", "曝光", "推荐", "渠道", "归因"],
    "性能与稳定性": ["性能", "弱网", "设备", "白屏", "崩溃", "ANR", "加载", "WebView", "资源"],
    "项目协同": ["负责人", "排期", "验收", "测试", "联调", "客服", "延期", "阻塞"],
}
STATUS_RULES = [
    "已上线",
    "已发布",
    "已完成",
    "测试中",
    "联调中",
    "进行中",
    "待确认",
    "待开发",
    "待测试",
    "回滚",
    "历史参考",
    "已废弃",
]


class ScanError(RuntimeError):
    pass


def resolve_cli() -> str:
    explicit = os.environ.get("LARK_CLI_BIN", "").strip()
    candidates = [explicit, CLI_DEFAULT]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise ScanError("lark-cli_not_found")


def parse_json_output(raw: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for idx, char in enumerate(raw):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(raw[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ScanError("lark_cli_non_json_output")


def run_cli(cli: str, args: list[str], timeout: int = 90) -> dict[str, Any]:
    env = dict(os.environ)
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    argv = [cli, *args, "--as", "user", "--format", "json"]
    last_error = ""
    for attempt in range(3):
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        raw = (completed.stdout or "") + "\n" + (completed.stderr or "")
        try:
            payload = parse_json_output(raw)
        except ScanError:
            last_error = raw[-1200:].strip()
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise ScanError(last_error or f"lark_cli_exit_{completed.returncode}")
        if payload.get("ok") is True:
            return payload
        error = payload.get("error") or {}
        last_error = str(error.get("message") or error or raw[-1200:]).strip()
        error_type = str(error.get("type") or error.get("subtype") or "").lower()
        if "rate" in error_type or "rate" in last_error.lower() or "frequency limit" in last_error.lower():
            time.sleep(3.0 * (attempt + 1))
            continue
        raise ScanError(last_error or f"lark_cli_exit_{completed.returncode}")
    raise ScanError(last_error or "lark_cli_failed")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def safe_text(value: Any) -> str:
    text = str(value or "")
    return re.sub(r"\s+", " ", text).strip()


def md_cell(value: Any) -> str:
    return safe_text(value).replace("|", "\\|")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def parse_iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def content_string(payload: dict[str, Any]) -> str:
    return str(((payload.get("data") or {}).get("document") or {}).get("content") or "")


def normalize_content(content: str) -> str:
    content = re.sub(r"<[^>]+>", " ", content)
    content = content.replace("\\n", "\n")
    content = re.sub(r"[\u200b-\u200f\ufeff]", "", content)
    return content


def summarize_content(content: str) -> dict[str, Any]:
    normalized = normalize_content(content)
    lower = normalized.lower()
    topic_hits = [topic for topic, words in TOPIC_RULES.items() if any(word.lower() in lower for word in words)]
    status_hits = [word for word in STATUS_RULES if word.lower() in lower]
    headings: list[str] = []
    for line in normalized.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if match:
            heading = safe_text(match.group(1))
            if heading and heading not in headings:
                headings.append(heading)
        if len(headings) >= 12:
            break
    return {
        "content_hash": sha256_text(normalized),
        "content_chars": len(normalized),
        "topic_hits": topic_hits,
        "status_signals": status_hits,
        "headings": headings,
    }


def load_previous() -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, str]]:
    crawl: dict[str, Any] = {}
    index: dict[str, Any] = {}
    if PREVIOUS_CRAWL.exists():
        crawl = json.loads(PREVIOUS_CRAWL.read_text(encoding="utf-8"))
    if PREVIOUS_INDEX.exists():
        index = json.loads(PREVIOUS_INDEX.read_text(encoding="utf-8"))
    previous_docs = index.get("docs") if isinstance(index, dict) else []
    if not isinstance(previous_docs, list):
        previous_docs = []
    previous_by_token = {str(item.get("token")): item for item in previous_docs if isinstance(item, dict) and item.get("token")}
    previous_hashes: dict[str, str] = {}
    for item in crawl.get("docs", []) if isinstance(crawl.get("docs"), list) else []:
        if not isinstance(item, dict) or not item.get("token") or not item.get("content"):
            continue
        previous_hashes[str(item["token"])] = summarize_content(str(item["content"]))["content_hash"]
    return crawl, previous_by_token, previous_hashes


def list_children(cli: str, parent_token: str) -> list[dict[str, Any]]:
    args = [
        "wiki",
        "+node-list",
        "--space-id",
        SPACE_ID,
        "--page-all",
        "--page-limit",
        "0",
        "--page-size",
        "50",
    ]
    if parent_token:
        args.extend(["--parent-node-token", parent_token])
    payload = run_cli(cli, args)
    nodes = ((payload.get("data") or {}).get("nodes") or [])
    return [node for node in nodes if isinstance(node, dict) and node.get("node_token")]


def get_node(cli: str, token: str) -> dict[str, Any]:
    payload = run_cli(cli, ["wiki", "+node-get", "--node-token", token], timeout=60)
    return dict(payload.get("data") or {})


def fetch_doc(cli: str, token: str) -> str:
    url = f"https://ksg964l11fam.sg.larksuite.com/wiki/{token}"
    payload = run_cli(cli, ["docs", "+fetch", "--doc", url, "--doc-format", "markdown", "--detail", "simple"], timeout=120)
    return content_string(payload)


def scan_tree(cli: str, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # The user-facing URL points at the "需求文档" child, but the department
    # project corpus is the whole Wiki space. Start at the numeric space root
    # so owner/topic hubs outside that child are not silently missed.
    found: list[dict[str, Any]] = []
    queue: deque[tuple[str, list[str], int]] = deque()
    seen: set[str] = set()
    try:
        top_level_nodes = list_children(cli, "")
    except Exception as exc:  # noqa: BLE001
        errors.append({"stage": "space_root_list", "space_id": SPACE_ID, "error": safe_text(exc)})
        return found
    for child in top_level_nodes:
        token = str(child.get("node_token"))
        if not token or token in seen:
            continue
        seen.add(token)
        title = safe_text(child.get("title") or child.get("name") or token)
        node = {
            "token": token,
            "title": title,
            "path": [title],
            "level": 1,
            "parent_node_token": "",
            "has_child": bool(child.get("has_child")),
            "obj_type": child.get("obj_type"),
            "node_type": child.get("node_type"),
            "url": f"https://ksg964l11fam.sg.larksuite.com/wiki/{token}",
            "updated_at": None,
        }
        found.append(node)
        if node["has_child"]:
            queue.append((token, [title], 1))
    while queue:
        parent, parent_path, parent_level = queue.popleft()
        try:
            children = list_children(cli, parent)
        except Exception as exc:  # noqa: BLE001
            errors.append({"stage": "node_list", "parent_node_token": parent, "error": safe_text(exc)})
            continue
        for child in children:
            token = str(child.get("node_token"))
            if token in seen:
                continue
            seen.add(token)
            title = safe_text(child.get("title") or child.get("name") or token)
            path = [*parent_path, title]
            node = {
                "token": token,
                "title": title,
                "path": path,
                "level": parent_level + 1,
                "parent_node_token": parent,
                "has_child": bool(child.get("has_child")),
                "obj_type": child.get("obj_type"),
                "node_type": child.get("node_type"),
                "url": f"https://ksg964l11fam.sg.larksuite.com/wiki/{token}",
                "updated_at": None,
            }
            found.append(node)
            if node["has_child"]:
                queue.append((token, path, parent_level + 1))

    # node-list already exposes title, object type and child status. Avoid a
    # node-get call for every leaf: that creates a needless rate-limit storm
    # and is not needed for the content-hash refresh strategy below.
    for node in found:
        node["updated_at"] = None
        node["updated_at_source"] = "not_exposed_by_node_list"
    return found


def enrich_changed_docs(cli: str, nodes: list[dict[str, Any]], previous: dict[str, dict[str, Any]], previous_hashes: dict[str, str], cutoff: dt.datetime | None, errors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    changed: list[dict[str, Any]] = []
    fetch_targets: list[dict[str, Any]] = []
    for node in nodes:
        token = str(node["token"])
        old = previous.get(token, {})
        top_level = str((node.get("path") or [""])[0])
        is_new = token not in previous
        is_changed = False
        node["top_level"] = top_level
        node["is_new"] = is_new
        node["is_changed_since_previous"] = is_changed
        node["evidence_status"] = old.get("evidence_status") or "metadata_observed"
        node["capture_status"] = old.get("captureStatus") or old.get("capture_status") or "metadata_only"
        node["content_chars"] = old.get("contentChars") or old.get("content_chars")
        node["content_hash"] = previous_hashes.get(token) or old.get("content_hash")
        obj_type = str(node.get("obj_type") or "")
        if obj_type == "docx" and top_level not in HISTORY_TOP_LEVEL:
            fetch_targets.append(node)

    def one(node: dict[str, Any]) -> tuple[str, dict[str, Any] | None, str | None]:
        try:
            content = fetch_doc(cli, str(node["token"]))
            return str(node["token"]), summarize_content(content), None
        except Exception as exc:  # noqa: BLE001
            return str(node["token"]), None, safe_text(exc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(one, node) for node in fetch_targets]
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            token, summary, error = future.result()
            if completed == 1 or completed % 25 == 0 or completed == len(futures):
                print(f"lark department content refresh: {completed}/{len(futures)}", flush=True)
            node = next(item for item in fetch_targets if str(item["token"]) == token)
            if error:
                node["capture_status"] = "fetch_failed"
                node["evidence_status"] = "content_fetch_failed"
                errors.append({"stage": "doc_fetch", "token": token, "path": node.get("path"), "error": error})
                continue
            assert summary is not None
            old_hash = previous_hashes.get(token)
            node.update(summary)
            node["capture_status"] = "text"
            node["evidence_status"] = "content_observed_incremental"
            node["content_chars"] = summary["content_chars"]
            node["content_hash"] = summary["content_hash"]
            node["content_changed"] = old_hash != summary["content_hash"]
            node["is_changed_since_previous"] = bool(node.get("is_new") or node["content_changed"])
            if node["is_changed_since_previous"] and node not in changed:
                changed.append(node)
    return changed, fetch_targets


def build_index(nodes: list[dict[str, Any]], crawl_time: str, errors: list[dict[str, Any]], changed: list[dict[str, Any]], fetched: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    for node in nodes:
        counts["nodes"] += 1
        counts[f"level_{node.get('level')}"] += 1
        if node.get("obj_type") == "docx":
            counts["docx"] += 1
        if node.get("capture_status") == "text":
            counts["with_content"] += 1
        else:
            counts["metadata_only"] += 1
        if node.get("top_level") in HISTORY_TOP_LEVEL:
            counts["historical"] += 1
        if node.get("is_new"):
            counts["new"] += 1
        if node.get("is_changed_since_previous"):
            counts["changed"] += 1
    return {
        "schema_version": 2,
        "source_url": SOURCE_URL,
        "space": "产品部门",
        "root_node_token": ROOT_NODE_TOKEN,
        "space_id": SPACE_ID,
        "scanned_at": crawl_time,
        "previous_crawl": "data/raw/lark/2026-08-11/product-department-crawl.json",
        "stats": {**dict(counts), "fetch_targets": len(fetched), "errors": len(errors)},
        "docs": nodes,
        "changed_docs": [str(item["token"]) for item in changed],
        "fetched_docs": [str(item["token"]) for item in fetched],
        "errors": errors,
    }


def change_nodes(index: dict[str, Any], *, include_history: bool = True) -> list[dict[str, Any]]:
    """Return nodes with new/content-changed evidence for human-facing views."""
    nodes = [
        item
        for item in index.get("docs", [])
        if item.get("is_new") or item.get("is_changed_since_previous")
    ]
    if not include_history:
        nodes = [item for item in nodes if item.get("top_level") not in HISTORY_TOP_LEVEL]
    return nodes


def write_index_markdown(index: dict[str, Any], path: Path) -> None:
    stats = index["stats"]
    active_changes = change_nodes(index, include_history=False)
    historical_changes = change_nodes(index, include_history=True)
    historical_changes = [item for item in historical_changes if item.get("top_level") in HISTORY_TOP_LEVEL]
    lines = [
        "# 产品部门项目文档索引（2026-08-31）",
        "",
        f"> 来源：[Lark 产品部门/需求文档]({SOURCE_URL})。本次扫描时间：`{index['scanned_at']}`。目录全量复核，正文只读取新增/变更的非历史 Docx；不向 Lark 发送或修改任何内容。",
        "",
        "## 1. 扫描概览",
        "",
        "| 项目 | 数量/状态 | 说明 |",
        "|---|---:|---|",
        f"| 目录节点总数 | {stats.get('nodes', 0)} | 包含根节点、Docx、Sheet、图片、PDF和动态对象 |",
        f"| Docx 节点 | {stats.get('docx', 0)} | 可继续读取正文的文档节点 |",
        f"| 本次新增节点 | {stats.get('new', 0)} | 相对 2026-08-11 索引 |",
        f"| 本次正文变更候选 | {stats.get('changed', 0)} | 新增节点或正文内容哈希发生变化；完整明细保留在 JSON |",
        f"| 本次读取正文 | {stats.get('fetch_targets', 0)} | 仅限新增/变更且非 HFYL 历史文档 |",
        f"| 正文读取失败 | {sum(1 for e in index.get('errors', []) if e.get('stage') == 'doc_fetch')} | 不以失败或空结果推断内容不存在 |",
        f"| 历史文档节点 | {stats.get('historical', 0)} | 仅作历史参考，不作为当前规则 |",
        f"| 非历史新增/变更明细 | {len(active_changes)} | 进入下方可读清单 |",
        f"| HFYL历史新增/变更 | {len(historical_changes)} | 已进入 JSON 索引；本页不展开，避免历史资料淹没当前项目 |",
        "",
        "## 2. 当前目录分布",
        "",
        "| 顶层目录 | 节点数 | 本次新增/变更 | 正文读取 | 当前用途 |",
        "|---|---:|---:|---:|---|",
    ]
    by_top: dict[str, list[dict[str, Any]]] = {}
    for node in index["docs"]:
        by_top.setdefault(str(node.get("top_level") or "未分类"), []).append(node)
    for top, items in sorted(by_top.items(), key=lambda pair: pair[0]):
        changed = sum(1 for item in items if item.get("is_new") or item.get("is_changed_since_previous"))
        text_count = sum(1 for item in items if item.get("capture_status") == "text")
        if top in HISTORY_TOP_LEVEL:
            purpose = "历史参考/版本演进，禁止直接进入当前结论"
        else:
            purpose = "项目需求、版本、数据、运营或协同资料"
        lines.append(f"| {md_cell(top)} | {len(items)} | {changed} | {text_count} | {purpose} |")
    lines.extend(["", "## 3. 本次新增/变更项目文档（非历史）", "", "| 路径 | 文档 | 状态 | 主题 | 来源 |", "|---|---|---|---|---|"])
    for node in sorted(active_changes, key=lambda item: (str(item.get("top_level")), str(item.get("path")))):
        status = "新增" if node.get("is_new") else "已变更"
        if node.get("capture_status") == "text":
            status += "/正文已读取"
        elif node.get("capture_status") == "fetch_failed":
            status += "/正文读取失败"
        else:
            status += "/仅元数据"
        topics = ", ".join(node.get("topic_hits") or []) or "待分类"
        path_text = " / ".join(str(x) for x in node.get("path") or [])
        lines.append(f"| {md_cell(path_text)} | {md_cell(node.get('title'))} | {status} | {md_cell(topics)} | [打开]({node.get('url')}) |")
    if not active_changes:
        lines.append("| — | 本次未发现新增或变更节点 | — | — | — |")
    lines.extend([
        "",
        f"> HFYL历史文档本次新增/变更 `{len(historical_changes)}` 个，已保留在安全结构化索引中；本页只展示非历史项目，避免把历史参考误读为当前需求或配置。",
    ])
    lines.extend([
        "",
        "## 4. 证据状态说明",
        "",
        "- `metadata_observed`：目录或节点元数据已观察；不代表正文、字段或业务状态已确认。",
        "- `content_observed_incremental`：本次正文已读取并提取主题/状态信号；不把“计划/测试中”写成已上线。",
        "- `metadata_only`：多维表、图片、PDF、动态组件、空页或本次未变更文档，仅保留目录定位。",
        "- `content_fetch_failed`：读取失败，保留失败节点和原因；不解释为空内容。",
        "- `HFYL历史文档`统一作为历史参考，不进入当前新包、RTP、留存、LTV、支付和风控结论。",
        "",
        "## 5. 维护入口",
        "",
        "- 当前扫描回执：`data/outputs/lark/department/2026-08-31/run-log.json`",
        "- 安全结构化索引：`data/processed/lark/department/2026-08-31/department-project-index.json`",
        "- 变更专题摘要：`knowledge/05-运行/2026-08-31-部门项目文档扫描与知识库更新.md`",
        "- 上次基线：`knowledge/01-产品/产品部门文档索引-2026-08-11.md`",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_overview(index: dict[str, Any], path: Path) -> None:
    stats = index["stats"]
    all_changes = change_nodes(index, include_history=True)
    changed = change_nodes(index, include_history=False)
    historical_changes = [item for item in all_changes if item.get("top_level") in HISTORY_TOP_LEVEL]
    topic_counter = Counter(topic for item in changed for topic in item.get("topic_hits") or [])
    lines = [
        "# 产品部门知识库总览（2026-08-31增量复核）",
        "",
        f"> 来源：[Lark 产品部门/需求文档]({SOURCE_URL})。本次不是重写历史资料，而是基于 2026-08-11 基线做目录全量复核和变更正文增量读取。",
        "",
        "## 1. 本次更新结论",
        "",
        f"- 当前目录共 `{stats.get('nodes', 0)}` 个节点，其中 Docx `{stats.get('docx', 0)}` 个；相对上次基线新增 `{stats.get('new', 0)}` 个、正文变更候选 `{stats.get('changed', 0)}` 个。",
        f"- 本次实际读取 `{stats.get('fetch_targets', 0)}` 个新增/变更的非历史正文；正文读取失败 `{sum(1 for e in index.get('errors', []) if e.get('stage') == 'doc_fetch')}` 个，失败节点不作空内容解释。",
        f"- HFYL 历史文档节点 `{stats.get('historical', 0)}` 个，继续保留为版本演进和机制参考，不自动纳入当前业务结论。",
        f"- 人类可读清单展示非历史新增/变更 `{len(changed)}` 个；另有 HFYL 历史新增/变更 `{len(historical_changes)}` 个仅在结构化索引中保留。",
        "- 现行判断仍遵循：最新 PRD/排期/发版与线上配置 > 明确已发布版本报告 > 普通需求文档 > HFYL 历史资料。",
        "",
        "## 2. 变更主题分布",
        "",
        "| 主题 | 变更文档命中数 | 对当前项目的处理 |",
        "|---|---:|---|",
    ]
    for topic, count in topic_counter.most_common():
        action = {
            "需求与版本": "回填版本、配置、生效状态和验收链路；未验收不写成已上线。",
            "数据与埋点": "与 Ares/BQ/Metabase 字段和指标口径对齐，保留待补证。",
            "支付提现与KYC": "以服务端订单/审核/身份事实为准，历史阈值不得直接复用。",
            "游戏与数值": "绑定游戏配置版本、RTP/机器人机制和跑数验收。",
            "增长与运营": "区分活动设计、实际曝光、转化结果和实验状态。",
            "性能与稳定性": "关联版本、设备、网络、加载和错误指标，保留数据质量状态。",
            "项目协同": "提取负责人、排期、验收和阻塞项，计划不等于完成。",
        }.get(topic, "进入对应专题复核。")
        lines.append(f"| {topic} | {count} | {action} |")
    if not topic_counter:
        lines.append("| — | 0 | 本次未识别到新增/变更正文主题。 |")
    lines.extend(["", "## 3. 本次变更文档（非历史）", "", "| 路径 | 文档 | 状态 | 主题/证据 |", "|---|---|---|---|"])
    for node in sorted(changed, key=lambda item: str(item.get("path"))):
        path_text = " / ".join(str(x) for x in node.get("path") or [])
        state = "新增" if node.get("is_new") else "已变更"
        if node.get("capture_status") == "text":
            state += "；正文已读取"
        elif node.get("capture_status") == "fetch_failed":
            state += "；正文读取失败"
        else:
            state += "；仅元数据"
        evidence = ", ".join(node.get("topic_hits") or []) or "未识别主题"
        lines.append(f"| {md_cell(path_text)} | {md_cell(node.get('title'))} | {state} | {md_cell(evidence)} |")
    if not changed:
        lines.append("| — | 本次没有新增/变更文档 | — | — |")
    lines.extend([
        "",
        f"> 历史资料变更不在本节展开：HFYL 历史新增/变更 `{len(historical_changes)}` 个，详见 `data/processed/lark/department/2026-08-31/department-project-index.json`。",
    ])
    lines.extend([
        "",
        "## 4. 当前项目使用规则",
        "",
        "### 需求、版本与配置",
        "",
        "- 需求、排期、发版、配置、验收和回滚必须使用同一项目/版本上下文；单独一份需求文档不能证明功能已上线。",
        "- 数值、概率、奖池、机器人、支付渠道、KYC和提现审核规则必须保留配置版本、生效时间、责任人和回滚证据。",
        "",
        "### 数据与埋点",
        "",
        "- Ares 事件配置、客户端实际调用、起源接收质量和可用于分析四层证据分开记录。",
        "- 页面/模块事件只说明行为；注册、支付、下注、结算、资产、提现和 RTP 结果以服务端事实为准。",
        "- 未授权、权限不足、空结果、未成熟窗口和无样本不能转换为 0 或成功。",
        "",
        "### 历史资料",
        "",
        f"- 当前仍有 `{stats.get('historical', 0)}` 个 HFYL 历史节点；它们用于理解机制演进、提出假设和寻找来源，不进入当前新包 KPI、RTP、留存、LTV、支付或风控的统计分母。",
        "",
        "## 5. 后续维护建议",
        "",
        "1. 优先处理本次变更主题命中“数据与埋点”“支付提现与KYC”“需求与版本”的文档，补齐实际配置和验收证据。",
        "2. 对本次仍为 metadata-only 的动态表格、PDF、图片和空页，登记来源与待补证项，不从标题推断内容。",
        "3. 每周复核节点 `updated_at`，只读取新增/修改正文；保留旧索引，不覆盖历史回执。",
        "",
        "## 6. 关联资产",
        "",
        "- [本次项目文档索引](./产品部门文档索引-2026-08-31.md)",
        "- [本次运行回执](../../data/outputs/lark/department/2026-08-31/run-log.json)",
        "- [上次总览](./产品部门知识库总览-2026-08-11.md)",
        "- [相关文档拆解与知识入库默认工作流](../04-方法/相关文档拆解与知识入库默认工作流.md)",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_change_note(index: dict[str, Any], path: Path) -> None:
    stats = index["stats"]
    changed = change_nodes(index, include_history=False)
    historical_changes = [item for item in change_nodes(index, include_history=True) if item.get("top_level") in HISTORY_TOP_LEVEL]
    lines = [
        "# 部门项目文档扫描与知识库更新（2026-08-31）",
        "",
        f"> 扫描来源：[Lark 产品部门/需求文档]({SOURCE_URL})。本次只读扫描，未发送消息、未修改飞书原文、未保存认证凭据。",
        "",
        "## 1. 运行结果",
        "",
        f"- 状态：`{'partial' if index.get('errors') else 'ok'}`",
        f"- 目录节点：`{stats.get('nodes', 0)}`；Docx：`{stats.get('docx', 0)}`；正文读取：`{stats.get('fetch_targets', 0)}`。",
        f"- 新增：`{stats.get('new', 0)}`；正文变更候选：`{stats.get('changed', 0)}`；历史节点：`{stats.get('historical', 0)}`。",
        f"- 可读项目清单：非历史新增/变更 `{len(changed)}` 个；HFYL历史新增/变更 `{len(historical_changes)}` 个只保留在 JSON，不在本报告展开。",
        f"- 错误/待补证：`{len(index.get('errors', []))}`；未将失败、空结果或未读取页面解释为没有内容。",
        "",
        "## 2. 本次处理逻辑",
        "",
        "```text",
        "产品部门节点树",
        "  → 全量递归列目录和节点元数据",
        "  → 以新增节点与正文内容哈希识别新增/变更候选",
        "  → 只读新增/变更的非 HFYL 历史 Docx 正文",
        "  → 提取主题、状态信号和章节导航，不保存完整正文快照",
        "  → 输出安全索引、变更摘要、知识库总览和运行回执",
        "  → 刷新知识图谱",
        "```",
        "",
        "## 3. 新增/变更清单（非历史）",
        "",
        "| 路径 | 文档 | 状态 | 正文/证据 |",
        "|---|---|---|---|",
    ]
    for node in sorted(changed, key=lambda item: str(item.get("path"))):
        path_text = " / ".join(str(x) for x in node.get("path") or [])
        state = "新增" if node.get("is_new") else "已变更"
        capture = node.get("capture_status") or "metadata_only"
        topics = ", ".join(node.get("topic_hits") or []) or "待分类"
        lines.append(f"| {md_cell(path_text)} | {md_cell(node.get('title'))} | {state} | {capture}; {md_cell(topics)} |")
    if not changed:
        lines.append("| — | 本次没有新增或变更节点 | — | — |")
    lines.extend([
        "",
        f"> HFYL历史文档本次新增/变更 `{len(historical_changes)}` 个，已在安全结构化索引中保留；不进入当前项目清单。",
    ])
    lines.extend([
        "",
        "## 4. 使用边界",
        "",
        "- 目录存在不等于正文可读；正文可读不等于需求已完成；需求完成不等于正式上线。",
        "- HFYL 历史文档仅作历史参考，不能直接作为当前新包 KPI、RTP、留存、LTV、支付或风控结论。",
        "- 个人、账号、联系方式、Token、Cookie、密码和完整原始逐字内容不进入本次正式资料。",
        "",
        "## 5. 产物",
        "",
        "- [部门项目文档索引（2026-08-31）](../01-产品/产品部门文档索引-2026-08-31.md)",
        "- [部门知识库总览（2026-08-31增量复核）](../01-产品/产品部门知识库总览-2026-08-31.md)",
        "- [安全结构化索引](../../data/processed/lark/department/2026-08-31/department-project-index.json)",
        "- [运行回执](../../data/outputs/lark/department/2026-08-31/run-log.json)",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().date().isoformat())
    parser.add_argument("--render-existing", action="store_true", help="仅使用已有结构化索引重新生成可读 Markdown，不访问 Lark")
    args = parser.parse_args()
    if args.render_existing:
        processed_index = ROOT / "data/processed/lark/department" / args.date / "department-project-index.json"
        if not processed_index.exists():
            raise SystemExit(f"processed index not found: {processed_index}")
        index = json.loads(processed_index.read_text(encoding="utf-8"))
        write_index_markdown(index, ROOT / "knowledge/01-产品/产品部门文档索引-2026-08-31.md")
        write_overview(index, ROOT / "knowledge/01-产品/产品部门知识库总览-2026-08-31.md")
        write_change_note(index, ROOT / "knowledge/05-运行/2026-08-31-部门项目文档扫描与知识库更新.md")
        print(json.dumps({"status": "ok", "mode": "render_existing", "processed_index": str(processed_index)}, ensure_ascii=False))
        return 0
    cli = resolve_cli()
    crawl_time = now_iso()
    errors: list[dict[str, Any]] = []
    previous_crawl, previous, previous_hashes = load_previous()
    cutoff = parse_iso(str(previous_crawl.get("crawledAt") or ""))
    nodes = scan_tree(cli, errors)
    changed, fetched = enrich_changed_docs(cli, nodes, previous, previous_hashes, cutoff, errors)
    for node in nodes:
        node.pop("parent_node_token", None) if not node.get("parent_node_token") else None
        node["url"] = node.get("url") or f"https://ksg964l11fam.sg.larksuite.com/wiki/{node['token']}"

    index = build_index(nodes, crawl_time, errors, changed, fetched)
    processed_dir = ROOT / "data/processed/lark/department" / args.date
    output_dir = ROOT / "data/outputs/lark/department" / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / "department-project-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_index_markdown(index, ROOT / "knowledge/01-产品/产品部门文档索引-2026-08-31.md")
    write_overview(index, ROOT / "knowledge/01-产品/产品部门知识库总览-2026-08-31.md")
    write_change_note(index, ROOT / "knowledge/05-运行/2026-08-31-部门项目文档扫描与知识库更新.md")

    run_log = {
        "run_id": f"lark_department_project_docs_{args.date}",
        "started_at": crawl_time,
        "finished_at": now_iso(),
        "status": "partial" if errors else "ok",
        "identity": "user",
        "source_url": SOURCE_URL,
        "space_id": SPACE_ID,
        "root_node_token": ROOT_NODE_TOKEN,
        "previous_crawl_at": previous_crawl.get("crawledAt"),
        "scope_mode": "full_tree_metadata_incremental_non_history_docx_content",
        "counts": index["stats"],
        "errors": errors,
        "outbound_actions": 0,
        "full_source_bodies_persisted": False,
        "credentials_saved": False,
        "outputs": {
            "processed_index": "data/processed/lark/department/2026-08-31/department-project-index.json",
            "markdown_index": "knowledge/01-产品/产品部门文档索引-2026-08-31.md",
            "markdown_overview": "knowledge/01-产品/产品部门知识库总览-2026-08-31.md",
            "change_note": "knowledge/05-运行/2026-08-31-部门项目文档扫描与知识库更新.md",
        },
    }
    (output_dir / "run-log.json").write_text(json.dumps(run_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(run_log, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())

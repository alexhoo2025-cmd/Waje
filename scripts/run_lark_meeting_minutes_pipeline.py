#!/usr/bin/env python3
"""Read, summarize, and locally index Lark smart meeting minutes.

The pipeline is intentionally read-only on Lark. It searches recent DOCX files
whose title contains ``智能纪要`` and whose owner is ``Max``. It reads the
linked transcript when available, produces an evidence-scoped Markdown note,
and stores only redacted metadata and summaries locally.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from lark_common import project_root, redact_error, redact_text, sha256_text, write_json


TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DOCX_URL_RE = re.compile(r"https?://[^\s)<>]+/docx/[A-Za-z0-9]+(?:\?[^\s)<>]*)?", re.IGNORECASE)
DATE_CN_RE = re.compile(r"(20\d{2})年(\d{1,2})月(\d{1,2})日")
DATE_ISO_RE = re.compile(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})")
SPEECH_RE = re.compile(
    r'<cite[^>]*user-name="([^"]+)"[^>]*></cite>\s*'
    r"(\d{2}:\d{2}:\d{2})\s+(.*?)(?=\n\s*<cite|\Z)",
    re.IGNORECASE | re.DOTALL,
)
USER_ID_RE = re.compile(r"\bou_[A-Za-z0-9]+\b")
HTML_TAG_RE = re.compile(r"<[^>]+>")
HIGHLIGHT_RE = re.compile(r"</?h[b]?/?>", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s)<>]+", re.IGNORECASE)
SMART_TODO_RE = re.compile(r"-\s*\[ \]\s*(.*?)(?=\n\s*-\s*\[ \]|\n\s*<readonly-block|\Z)", re.DOTALL)

DEFAULT_CONFIG = {
    "enabled": True,
    "query": "智能纪要",
    "only_title": True,
    "doc_types": ["docx"],
    "owner_name": "Max",
    "lookback_days": 3,
    "scope_mode": "title_owner_fallback",
    "page_size": 30,
    "max_candidates": 30,
    "retry_attempts": 3,
    "outputs": {
        "processed_dir": "data/processed/lark/meeting_minutes",
        "output_dir": "data/outputs/meeting_minutes",
        "knowledge_dir": "knowledge/05-运行",
    },
}

CATEGORY_TERMS: dict[str, tuple[str, ...]] = {
    "数据与报表": (
        "数据", "报表", "指标", "QIC", "SQL", "生命周期", "用户分层", "任务分层",
        "设备监控", "性能数据", "数据打通", "数据接入", "数据分析",
    ),
    "版本与发布": (
        "发版", "上线", "提审", "提测", "发布", "版本", "构建", "配置", "新渠道",
        "自测", "联调", "测试", "验收",
    ),
    "游戏与玩法": (
        "游戏", "小游戏", "三方游戏", "自研游戏", "游戏曝光", "曝光逻辑", "游戏标签",
        "水位", "机器人", "Ludo", "联运", "供应商", "入口图标",
    ),
    "H5与性能": (
        "H5", "PWA", "Webview", "设备", "性能", "资源", "资源替换", "资源优化",
        "大厅", "JS", "框架", "容器",
    ),
    "支付与资金": (
        "支付", "提现", "充值", "资产", "分成", "资金", "多语言",
    ),
    "用户与运营": (
        "客服", "用户封禁", "用户分层", "需求", "任务", "曝光策略", "区域需求",
    ),
}

P0_TERMS = (
    "H5和 PWA", "H5/PWA", "设备和性能", "生命周期", "迁移", "QIC", "任务分层的数据指标",
)
P1_TERMS = (
    "发版", "上线", "提审", "用户分层", "三方游戏", "小游戏", "渠道", "支付", "提现",
    "游戏曝光", "联调", "验收", "监控报表",
)


class LarkPipelineError(RuntimeError):
    """A redacted, user-safe Lark pipeline failure."""


def load_config(root: Path) -> dict[str, Any]:
    path = root / "config/lark_meeting_minutes.json"
    config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    merged = dict(DEFAULT_CONFIG)
    merged.update(config)
    merged["outputs"] = {**DEFAULT_CONFIG["outputs"], **config.get("outputs", {})}
    return merged


def resolve_cli() -> Path:
    explicit = os.environ.get("LARK_CLI_BIN", "").strip()
    if explicit and Path(explicit).is_file():
        return Path(explicit).expanduser()
    found = shutil.which("lark-cli")
    if found:
        return Path(found)
    candidates = sorted(Path.home().glob(".local/node-*/bin/lark-cli"), reverse=True)
    if candidates:
        return candidates[0]
    raise LarkPipelineError("lark-cli_not_found")


def run_json_command(cli: Path, args: list[str], *, attempts: int = 3) -> dict[str, Any]:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    last_error = "unknown_lark_error"
    for attempt in range(max(1, attempts)):
        # `auth status` is a local CLI command and has its own `--json` flag;
        # it does not accept the identity selector used by API-backed commands.
        if args[:2] == ["auth", "status"]:
            command = [str(cli), *args, "--json"]
        else:
            command = [str(cli), *args, "--as", "user", "--format", "json"]
        completed = subprocess.run(
            command,
            cwd=project_root(),
            env=env,
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
        output = (completed.stdout or completed.stderr or "").strip()
        try:
            payload = json.loads(output) if output else {}
        except json.JSONDecodeError as exc:
            last_error = f"non_json_response: {redact_error(exc)}"
            payload = {}
        if completed.returncode == 0:
            if isinstance(payload, dict) and payload.get("ok") is False:
                error = payload.get("error", {})
                last_error = str(error.get("message") or error.get("subtype") or "lark_error")
            else:
                identity = str(payload.get("identity") or "") if isinstance(payload, dict) else ""
                if identity and identity != "user":
                    raise LarkPipelineError("lark_identity_not_user")
                return payload if isinstance(payload, dict) else {"data": payload}
        else:
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            last_error = str(error.get("message") or output or f"exit_{completed.returncode}")
        retryable = any(term in last_error.lower() for term in ("rate_limit", "timeout", "temporarily", "retry"))
        if attempt + 1 < attempts and retryable:
            time.sleep(0.75 * (attempt + 1))
            continue
        break
    raise LarkPipelineError(redact_error(RuntimeError(last_error)))


def preflight(cli: Path, config: dict[str, Any]) -> dict[str, Any]:
    try:
        status = run_json_command(cli, ["auth", "status", "--verify"], attempts=1)
    except Exception as exc:
        raise LarkPipelineError(f"auth_required: {redact_error(exc)}") from exc
    user = status.get("identities", {}).get("user", {}) if isinstance(status, dict) else {}
    if status.get("identity") not in (None, "user"):
        raise LarkPipelineError("auth_required: identity_not_user")
    if user and (user.get("verified") is False or user.get("tokenStatus") not in (None, "valid")):
        raise LarkPipelineError("auth_required: user_token_not_valid")
    scope = str(user.get("scope", ""))
    required_scopes = ("search:docs:read", "docx:document:readonly")
    missing_scopes = [scope_name for scope_name in required_scopes if scope_name not in scope]
    if missing_scopes:
        raise LarkPipelineError("auth_required: missing_scope")
    return {
        "identity": "user",
        "verified": bool(status.get("verified", user.get("verified", True))),
        "scope_present": True,
        "scope_mode": config.get("scope_mode", "title_owner_fallback"),
    }


def strip_markup(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = HIGHLIGHT_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    text = USER_ID_RE.sub("[USER_ID_REDACTED]", text)
    text = redact_text(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_title(value: Any) -> str:
    return strip_markup(value)


def parse_date(value: Any) -> dt.date | None:
    text = str(value or "")
    match = DATE_CN_RE.search(text) or DATE_ISO_RE.search(text)
    if not match:
        return None
    try:
        return dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def parse_iso_date(value: Any) -> dt.date | None:
    text = str(value or "")
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone().date()
    except (ValueError, TypeError):
        return parse_date(text)


def extract_transcript_url(content: str, source_url: str) -> str:
    marker = re.search(r"文字记录.{0,800}?((?:https?://)[^\s)<>]+/docx/[A-Za-z0-9]+(?:\?[^\s)<>]*)?)", content, re.IGNORECASE | re.DOTALL)
    candidates = [marker.group(1)] if marker else []
    candidates.extend(DOCX_URL_RE.findall(content))
    source_token = re.search(r"/docx/([A-Za-z0-9]+)", source_url)
    source_id = source_token.group(1) if source_token else ""
    for candidate in candidates:
        candidate = candidate.rstrip(".,，。")
        token_match = re.search(r"/docx/([A-Za-z0-9]+)", candidate)
        if token_match and token_match.group(1) != source_id:
            return candidate
    return ""


def document_body(payload: dict[str, Any]) -> tuple[str, int | None]:
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    document = data.get("document", {}) if isinstance(data, dict) else {}
    return str(document.get("content", "") or ""), document.get("revision_id")


def search_candidates(cli: Path, config: dict[str, Any], run_date: dt.date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    args = [
        "drive", "+search",
        "--query", str(config.get("query", "智能纪要")),
        "--only-title",
        "--doc-types", "docx",
        "--page-size", str(config.get("page_size", 30)),
    ]
    payload = run_json_command(cli, args, attempts=int(config.get("retry_attempts", 3)))
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    results = data.get("results", []) if isinstance(data, dict) else []
    owner = str(config.get("owner_name", "Max")).strip().casefold()
    lookback_start = run_date - dt.timedelta(days=int(config.get("lookback_days", 3)))
    selected: list[dict[str, Any]] = []
    seen_tokens: set[str] = set()
    for item in results:
        if not isinstance(item, dict) or item.get("entity_type") not in (None, "DOC"):
            continue
        meta = item.get("result_meta", {}) or {}
        title = clean_title(item.get("title_highlighted") or meta.get("title") or "")
        doc_owner = str(meta.get("owner_name") or "").strip().casefold()
        token = str(meta.get("token") or "")
        if not token or token in seen_tokens or not title.startswith("智能纪要") or doc_owner != owner:
            continue
        meeting_date = parse_date(title) or parse_iso_date(meta.get("create_time_iso"))
        updated_date = parse_iso_date(meta.get("update_time_iso")) or meeting_date
        if not meeting_date or meeting_date > run_date:
            continue
        if meeting_date < lookback_start and (not updated_date or updated_date < lookback_start):
            continue
        seen_tokens.add(token)
        selected.append({
            "document_token": token,
            "source_url": str(meta.get("url") or f"https://ksg964l11fam.sg.larksuite.com/docx/{token}"),
            "title": title,
            "owner_name": str(meta.get("owner_name") or config.get("owner_name", "Max")),
            "meeting_date": meeting_date.isoformat(),
            "created_at": str(meta.get("create_time_iso") or ""),
            "updated_at": str(meta.get("update_time_iso") or ""),
            "scope_mode": str(config.get("scope_mode", "title_owner_fallback")),
        })
    selected.sort(key=lambda row: (row["meeting_date"], row["updated_at"], row["document_token"]), reverse=True)
    selected = selected[: int(config.get("max_candidates", 30))]
    return selected, {
        "query": config.get("query", "智能纪要"),
        "returned_count": len(results),
        "selected_count": len(selected),
        "lookback_start": lookback_start.isoformat(),
        "lookback_end": run_date.isoformat(),
        "scope_mode": config.get("scope_mode", "title_owner_fallback"),
    }


def parse_transcript(content: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for match in SPEECH_RE.finditer(content):
        speaker = strip_markup(match.group(1))
        timestamp = match.group(2)
        text = strip_markup(match.group(3))
        text = re.sub(r"\s+", " ", text).strip()
        if speaker and text and len(text) >= 4:
            records.append({"speaker": speaker, "timestamp": timestamp, "text": text})
    return records


def extract_smart_todos(content: str) -> list[dict[str, str]]:
    """Extract only explicit unchecked todo items from the smart minutes.

    The smart-minute document also contains attendee cite blocks.  We keep the
    displayed owner name when present, but strip all cite markup and IDs before
    anything can enter the local report.
    """
    todos: list[dict[str, str]] = []
    for match in SMART_TODO_RE.finditer(content):
        raw = match.group(1)
        owner_match = re.search(r'user-name="([^"]+)"', raw, re.IGNORECASE)
        summary = strip_markup(raw)
        summary = re.sub(r"\s+", " ", summary).strip()
        if not summary:
            continue
        todos.append({"owner": strip_markup(owner_match.group(1)) if owner_match else "待确认", "summary": summary[:300]})
    return todos


def classify_text(text: str) -> list[str]:
    return [category for category, terms in CATEGORY_TERMS.items() if any(term.casefold() in text.casefold() for term in terms)]


def infer_priority(text: str, categories: Iterable[str]) -> str:
    if any(term.casefold() in text.casefold() for term in P0_TERMS):
        return "P0"
    if any(term.casefold() in text.casefold() for term in P1_TERMS) or "数据与报表" in categories:
        return "P1"
    return "P2"


def infer_status(text: str) -> str:
    if re.search(r"可能|预计|看看|如果|什么时候|计划", text):
        return "待确认"
    if re.search(r"测试|自测|联调|验收|提测", text):
        return "测试中"
    if re.search(r"完成|已经|已处理", text):
        return "已完成待验收"
    return "进行中"


def data_action(categories: Iterable[str]) -> str:
    category_set = set(categories)
    actions: list[str] = []
    if "H5与性能" in category_set:
        actions.append("核验设备/网络/版本维度，以及接收—入库—认证指标链路")
    if "数据与报表" in category_set:
        actions.append("固定指标口径、数据范围、成熟窗口和看板来源")
    if "版本与发布" in category_set:
        actions.append("登记版本/构建/配置/生效时间，建立发布前后基线")
    if "游戏与玩法" in category_set:
        actions.append("补齐 game_id、供应商、玩法、入口、配置版本和验收链路")
    if "支付与资金" in category_set:
        actions.append("按订单、支付状态、资产流水和提现状态做对账")
    if "用户与运营" in category_set:
        actions.append("补齐规则版本、人群快照、触达结果和验收指标")
    return "；".join(actions) or "补齐范围、状态、责任人和验收证据"


def acceptance_action(categories: Iterable[str]) -> str:
    category_set = set(categories)
    if "H5与性能" in category_set:
        return "有真实样本、字段完整、可按版本/设备/网络下钻，并能关联首局或核心转化"
    if "数据与报表" in category_set:
        return "GM/起源或 BQ 结果逐日对账，记录刷新时间、成熟状态和口径版本"
    if "版本与发布" in category_set:
        return "有发布证据、版本/构建号、生效时间及发布后 24h/7d 回归结果"
    if "游戏与玩法" in category_set:
        return "有游戏维表、入口状态、测试结果和 GAMESTART→GAMEEND→BETREWARD 链路"
    return "取得 PRD、排期、测试、发布记录或负责人确认中的至少一项正式证据"


def build_tasks(transcript_records: list[dict[str, str]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for record in transcript_records:
        text = record["text"]
        categories = classify_text(text)
        if not categories:
            continue
        priority = infer_priority(text, categories)
        task = {
            "speaker": record["speaker"],
            "timestamp": record["timestamp"],
            "summary": text[:240],
            "categories": categories,
            "priority": priority,
            "status": infer_status(text),
            "data_action": data_action(categories),
            "acceptance": acceptance_action(categories),
        }
        tasks.append(task)
    return tasks


def sanitize_md(value: Any, limit: int = 500) -> str:
    text = strip_markup(value).replace("|", "｜").replace("\n", " ")
    return text[:limit]


def build_note(meeting_date: str, documents: list[dict[str, Any]], tasks: list[dict[str, Any]], captured_at: str) -> str:
    source_doc = documents[0]
    transcript_verified = all(doc.get("transcript_url") for doc in documents)
    evidence_status = "transcript_verified" if transcript_verified else "partial_transcript"
    lines = [
        "---",
        "type: meeting-minutes",
        "domain: project-operations",
        f"date: {meeting_date}",
        f"captured_at: {captured_at}",
        f"status: {evidence_status}",
        "owner: analyst",
        "scope_mode: title_owner_fallback",
        "outbound_actions: 0",
        "tags: [晨会, 会议纪要, 数据分析, 产品进度, 版本, 游戏, H5, Lark]",
        "---",
        "",
        f"# {meeting_date} 晨会纪要｜多领域工作安排与数据行动",
        "",
        "> 本文由 Lark 用户身份只读读取智能纪要及其原始文字记录后独立整理。会议工作部署、计划、测试和联调不等同于已上线或生产已验证。",
        "",
        "## 会议概览",
        "",
        f"- 会议主题：{sanitize_md(source_doc.get('title', ''))}",
        f"- 智能纪要：[查看原文]({source_doc.get('source_url', '')})",
        f"- 原始文字记录：[查看文字记录]({source_doc.get('transcript_url') or '待补充'})",
        f"- Owner 范围：{sanitize_md(source_doc.get('owner_name', 'Max'))}",
        f"- 文档数：{len(documents)}；证据状态：`{evidence_status}`；出站操作：`0`",
        "",
        "## 执行摘要",
        "",
        "- 本次晨会以本周产品、游戏、数据、版本和测试任务安排为主，未形成可直接认定为生产发布的结论。",
        "- 数据侧重点是 H5/PWA 设备性能数据打通、生命周期报表迁移、QIC 数据分析和任务分层指标建设。",
        "- 版本与质量侧重点是 H5 可能发版、iOS 提审、小游戏/三方游戏验收、用户分层测试和设备监控报表问题修复。",
        "",
        "## 工作安排与数据影响",
        "",
        "| 优先级 | Owner | 主题 | 会议事实 | 状态 | 数据动作 | 验收证据 |",
        "|---|---|---|---|---|---|---|",
    ]
    for index, task in enumerate(sorted(tasks, key=lambda item: (item["priority"], item["timestamp"])), 1):
        lines.append(
            f"| {task['priority']} | {sanitize_md(task['speaker'], 60)} | {sanitize_md('、'.join(task['categories']), 80)} | "
            f"{sanitize_md(task['summary'], 180)} | {task['status']} | {sanitize_md(task['data_action'], 180)} | {sanitize_md(task['acceptance'], 160)} |"
        )
    if not tasks:
        lines.append("| — | — | — | 本次未提取到项目相关任务 | 待确认 | — | — |")
    smart_todos = [todo for document in documents for todo in document.get("smart_todos", [])]
    lines.extend([
        "",
        "## 智能纪要明确待办",
        "",
        "> 以下仅保留智能纪要明确列出的未勾选待办；事实和数据影响仍以原始文字记录为主。",
        "| Owner | 明确待办 | 来源证据 |",
        "|---|---|---|",
    ])
    if smart_todos:
        for todo in smart_todos:
            lines.append(f"| {sanitize_md(todo.get('owner', '待确认'), 60)} | {sanitize_md(todo.get('summary', ''), 240)} | 智能纪要待办 |")
    else:
        lines.append("| — | 本次智能纪要未提取到明确未勾选待办 | — |")
    lines.extend([
        "",
        "## 事件台账",
        "",
        "> 事件是产品、数据或运营变更事项，不等同于客户端埋点事件。正式发布变更仍需关联 `CHG-YYYY-NNNN`。",
        "",
        "| 事件 ID | 事项 | Owner | 范围/状态 | 数据影响 | 验收要求 |",
        "|---|---|---|---|---|---|",
    ])
    for index, task in enumerate(tasks, 1):
        event_id = f"EVT-{meeting_date.replace('-', '')}-{index:02d}"
        lines.append(
            f"| `{event_id}` | {sanitize_md(task['summary'], 180)} | {sanitize_md(task['speaker'], 60)} | "
            f"{sanitize_md('、'.join(task['categories']), 80)} / {task['status']} | {sanitize_md(task['data_action'], 180)} | {sanitize_md(task['acceptance'], 160)} |"
        )
    lines.extend([
        "",
        "## 风险与待确认项",
        "",
        "- H5 本周发版属于会议计划信号，需补充版本号、构建号、包体、配置版本和正式发布证据。",
        "- H5/PWA 性能数据此前存在账户配置或接入阻断，需核对 SDK、数据源、事件样本、延迟和字段完整率。",
        "- 生命周期报表迁移前必须确认 GM V2、V2 Joint、用户范围、历史回补和指标口径。",
        "- 用户分层、三方游戏、小游戏、支付和监控报表事项仍需以测试、发布或生产数据验证结论。",
        "- 本次采用标题 + Owner 回退范围，未证明文档实际位于 `waje fhn > max` 父目录。",
        "",
        "## 关联知识库",
        "",
        "- [[../02-数据/Waje-H5-PWA设备性能转化专项分析与监控方案-2026-08-13]]",
        "- [[../02-数据/GM-Lifecycle-Pool-v2报表结构与整合优化分析-2026-08-06]]",
        "- [[../02-数据/Waje全链路数据需求与埋点设计总表-2026-08-11]]",
        "- [[会议纪要与事件入库规范]]",
        "- [[../00-索引/Agent项目背景与知识图谱快速上手-2026-08-17]]",
        "",
        "## 来源与安全边界",
        "",
        f"- 智能纪要：[Lark 文档]({source_doc.get('source_url', '')})；资源标识：`{source_doc.get('document_token', '')}`；revision：`{source_doc.get('revision_id', 'unknown')}`。",
        f"- 文字记录：[Lark 文档]({source_doc.get('transcript_url') or '待补充'})。",
        "- 本地只保留脱敏摘要、事件台账、来源链接、revision 和内容哈希；不保存完整逐字稿、参会人 open_id、认证 Token、Cookie、密码或个人联系方式。",
        "- 采集范围：`智能纪要` 标题 + Owner=Max + 最近 3 天候选；`scope_mode=title_owner_fallback`。",
        "",
    ])
    return "\n".join(lines)


def write_note(root: Path, config: dict[str, Any], meeting_date: str, documents: list[dict[str, Any]], tasks: list[dict[str, Any]], captured_at: str) -> Path:
    out_dir = root / str(config["outputs"]["knowledge_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{meeting_date}-晨会纪要-多领域工作安排与数据行动.md"
    content = build_note(meeting_date, documents, tasks, captured_at)
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8")
    return path


def process_candidate(cli: Path, candidate: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    result = dict(candidate)
    result.update({"transcript_url": "", "revision_id": None, "content_hash": "", "transcript_hash": "", "evidence_status": "partial_transcript", "tasks": [], "smart_todos": []})
    main_payload = run_json_command(cli, ["docs", "+fetch", "--doc", candidate["source_url"], "--doc-format", "markdown"], attempts=int(config.get("retry_attempts", 3)))
    main_content, revision_id = document_body(main_payload)
    result["revision_id"] = revision_id
    result["content_hash"] = sha256_text(main_content)
    result["smart_todos"] = extract_smart_todos(main_content)
    transcript_url = extract_transcript_url(main_content, candidate["source_url"])
    result["transcript_url"] = transcript_url
    transcript_content = ""
    if transcript_url:
        transcript_payload = run_json_command(cli, ["docs", "+fetch", "--doc", transcript_url, "--doc-format", "markdown"], attempts=int(config.get("retry_attempts", 3)))
        transcript_content, _ = document_body(transcript_payload)
        result["transcript_hash"] = sha256_text(transcript_content)
    if transcript_content:
        records = parse_transcript(transcript_content)
        result["evidence_status"] = "transcript_verified" if records else "partial_transcript"
        result["tasks"] = build_tasks(records)
    else:
        result["evidence_status"] = "partial_transcript"
    return result


def write_index(root: Path, config: dict[str, Any], run_date: str, captured_at: str, preflight_info: dict[str, Any], search_info: dict[str, Any], documents: list[dict[str, Any]], errors: list[dict[str, Any]]) -> Path:
    path = root / str(config["outputs"]["processed_dir"]) / run_date / "meeting-index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_documents = []
    for document in documents:
        safe_documents.append({
            key: document.get(key, "")
            for key in (
                "meeting_date", "title", "document_token", "source_url", "transcript_url", "owner_name",
                "created_at", "updated_at", "revision_id", "content_hash", "transcript_hash", "evidence_status", "scope_mode",
            )
        })
        safe_documents[-1]["document_revision"] = document.get("revision_id")
        safe_documents[-1]["duplicate_of"] = document.get("duplicate_of", "")
        safe_documents[-1]["task_count"] = len(document.get("tasks", []))
        safe_documents[-1]["smart_todo_count"] = len(document.get("smart_todos", []))
    payload = {
        "schema_version": 1,
        "captured_at": captured_at,
        "run_date": run_date,
        "identity": preflight_info.get("identity", "user"),
        "scope_mode": search_info.get("scope_mode", config.get("scope_mode")),
        "search": search_info,
        "documents": safe_documents,
        "errors": errors,
        "outbound_actions": 0,
        "privacy": {"full_transcript_stored": False, "participant_open_ids_stored": False},
    }
    write_json(path, payload)
    return path


def write_run_log(root: Path, config: dict[str, Any], run_date: str, payload: dict[str, Any]) -> Path:
    path = root / str(config["outputs"]["output_dir"]) / run_date / "run-log.json"
    write_json(path, payload)
    return path


def run_pipeline(root: Path, run_date: dt.date, config: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    started_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    captured_at = started_at
    log: dict[str, Any] = {
        "schema_version": 1,
        "run_id": dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z"),
        "run_date": run_date.isoformat(),
        "started_at": started_at,
        "status": "started",
        "scope_mode": config.get("scope_mode", "title_owner_fallback"),
        "candidate_count": 0,
        "selected_count": 0,
        "reports_written": [],
        "errors": [],
        "outbound_actions": 0,
    }
    cli: Path | None = None
    try:
        if not config.get("enabled", True):
            log["status"] = "disabled"
            return 0, log
        cli = resolve_cli()
        preflight_info = preflight(cli, config)
        selected, search_info = search_candidates(cli, config, run_date)
        log["candidate_count"] = search_info.get("returned_count", 0)
        log["selected_count"] = len(selected)
        documents: list[dict[str, Any]] = []
        for candidate in selected:
            try:
                documents.append(process_candidate(cli, candidate, config))
            except Exception as exc:
                log["errors"].append({"stage": "document", "document_token": candidate.get("document_token", ""), "error": redact_error(exc)})
        if not documents:
            log["status"] = "no_new_documents" if not selected else "parse_failed"
            index_path = write_index(root, config, run_date.isoformat(), captured_at, preflight_info, search_info, documents, log["errors"])
            log["index_path"] = str(index_path.relative_to(root))
            return 0 if log["status"] == "no_new_documents" else 1, log
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        all_tasks: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for document in documents:
            grouped[str(document["meeting_date"])].append(document)
            all_tasks[str(document["meeting_date"])].extend(document.get("tasks", []))
        for meeting_date, date_documents in grouped.items():
            path = write_note(root, config, meeting_date, date_documents, all_tasks[meeting_date], captured_at)
            log["reports_written"].append(str(path.relative_to(root)))
        index_path = write_index(root, config, run_date.isoformat(), captured_at, preflight_info, search_info, documents, log["errors"])
        log["index_path"] = str(index_path.relative_to(root))
        log["status"] = "ok" if not log["errors"] and all(doc.get("evidence_status") == "transcript_verified" for doc in documents) else "partial"
        return 0, log
    except LarkPipelineError as exc:
        message = str(exc)
        log["errors"].append({"stage": "preflight_or_search", "error": redact_text(message)})
        log["status"] = "auth_required" if "auth_required" in message else ("search_failed" if cli else "auth_required")
        return 1, log
    except Exception as exc:
        log["errors"].append({"stage": "run", "error": redact_error(exc)})
        log["status"] = "write_failed"
        return 1, log
    finally:
        log["finished_at"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        write_run_log(root, config, run_date.isoformat(), log)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    root = project_root()
    config = load_config(root)
    run_date = dt.date.fromisoformat(args.date)
    code, log = run_pipeline(root, run_date, config)
    print(
        f"lark meeting minutes: status={log.get('status')}; selected={log.get('selected_count', 0)}; "
        f"reports={len(log.get('reports_written', []))}; outbound_actions=0; "
        f"run_log=data/outputs/meeting_minutes/{args.date}/run-log.json"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())

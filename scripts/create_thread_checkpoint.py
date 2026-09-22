#!/usr/bin/env python3
"""Create a compact, recoverable checkpoint for a long-running Codex task.

The script scans only explicitly supplied project-relative scopes. It records a
bounded Git summary, recent receipts, recent artifacts, decisions, blockers,
and next steps. Existing CURRENT.md files are archived before atomic updates.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Iterable
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Hong_Kong")
RECEIPT_NAMES = {
    "receipt.json",
    "run-receipt.json",
    "run_receipt.json",
    "final-run-receipt.json",
    "delivery-receipt.json",
    "production-receipt.json",
    "validation-report.json",
    "quality.json",
    "run-log.json",
}
ARTIFACT_NAMES = {
    "artifact.json",
    "analysis.json",
    "source-data.json",
    "report.md",
    "report.html",
}
ARTIFACT_SUFFIXES = {".md", ".html", ".pdf", ".xlsx", ".xls", ".csv", ".png"}
SKIP_PARTS = {
    ".git",
    ".venv",
    ".venv-wechat",
    "node_modules",
    "__pycache__",
    "history",
}
SENSITIVE = re.compile(
    r"\bsk-[A-Za-z0-9_-]{12,}|Bearer\s+\S{12,}|-----BEGIN .*PRIVATE KEY-----",
    re.IGNORECASE,
)
PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def clean_text(value: str) -> str:
    text = " ".join(str(value).strip().split())
    if SENSITIVE.search(text):
        raise ValueError("checkpoint text appears to contain a credential")
    return text


def run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def safe_path(root: Path, value: str | Path, *, must_exist: bool = False) -> Path:
    path = Path(value)
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"path is outside project root: {value}")
    if must_exist and not resolved.exists():
        raise FileNotFoundError(value)
    return resolved


def relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-.")
    if not slug:
        raise ValueError("slug must contain ASCII letters, digits, dot, dash, or underscore")
    return slug


def iter_files(scopes: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for scope in scopes:
        candidates = [scope] if scope.is_file() else scope.rglob("*")
        for path in candidates:
            if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield resolved


def safe_json(path: Path) -> dict[str, Any] | None:
    if path.stat().st_size > 2_000_000:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def extract_status(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("status"),
        (payload.get("quality") or {}).get("status") if isinstance(payload.get("quality"), dict) else None,
        (payload.get("validation") or {}).get("status") if isinstance(payload.get("validation"), dict) else None,
    ]
    return next((str(item) for item in candidates if item not in (None, "")), "unknown")


def extract_run_at(payload: dict[str, Any]) -> str:
    for key in ("run_at", "completed_at", "finished_at", "generated_at", "started_at", "date"):
        if payload.get(key) not in (None, ""):
            return clean_text(str(payload[key]))
    return "unknown"


def extract_window(payload: dict[str, Any]) -> str:
    value = payload.get("window")
    if isinstance(value, dict):
        start = value.get("start") or value.get("from") or value.get("window_start")
        end = value.get("end") or value.get("to") or value.get("window_end")
        timezone = value.get("timezone")
        parts = [str(item) for item in (start, end, timezone) if item not in (None, "")]
        return " / ".join(parts) if parts else "unknown"
    if value not in (None, ""):
        return clean_text(str(value))
    start = payload.get("window_start")
    end = payload.get("window_end")
    return " / ".join(str(item) for item in (start, end) if item not in (None, "")) or "unknown"


def discover_receipts(
    root: Path,
    scopes: list[Path],
    explicit: list[Path],
    limit: int,
) -> list[dict[str, str]]:
    candidates = set(explicit)
    candidates.update(path for path in iter_files(scopes) if path.name in RECEIPT_NAMES)
    ordered = sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)
    records: list[dict[str, str]] = []
    for path in ordered[:limit]:
        payload = safe_json(path)
        records.append(
            {
                "path": relative(root, path),
                "status": extract_status(payload) if payload else "unreadable_or_non_json",
                "run_at": extract_run_at(payload) if payload else "unknown",
                "window": extract_window(payload) if payload else "unknown",
            }
        )
    return records


def discover_artifacts(
    root: Path,
    scopes: list[Path],
    explicit: list[Path],
    limit: int,
) -> list[dict[str, str | int]]:
    candidates = set(explicit)
    candidates.update(scope for scope in scopes if scope.is_file())
    for path in iter_files(scopes):
        if path.name in RECEIPT_NAMES:
            continue
        if path.name in ARTIFACT_NAMES or path.suffix.lower() in ARTIFACT_SUFFIXES:
            candidates.add(path)
    ordered = sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)
    return [
        {
            "path": relative(root, path),
            "bytes": path.stat().st_size,
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime, TIMEZONE).isoformat(timespec="seconds"),
        }
        for path in ordered[:limit]
    ]


def git_snapshot(root: Path, scopes: list[Path], max_paths: int) -> dict[str, Any]:
    branch = run(["git", "branch", "--show-current"], root) or "unknown"
    lines = [line for line in run(["git", "status", "--short", "--untracked-files=all"], root).splitlines() if line]
    counts = Counter((line[:2].strip() or "unknown") for line in lines)
    scope_names = [relative(root, scope) for scope in scopes]

    def is_relevant(line: str) -> bool:
        path_text = line[3:].split(" -> ")[-1]
        return any(path_text == scope or path_text.startswith(scope.rstrip("/") + "/") for scope in scope_names)

    relevant = [line for line in lines if is_relevant(line)]
    display = relevant if relevant else lines
    return {
        "branch": branch,
        "total_changes": len(lines),
        "counts": dict(sorted(counts.items())),
        "relevant_changes": relevant[:max_paths],
        "display_changes": display[:max_paths],
        "omitted": max(0, len(display) - max_paths),
    }


def bullets(values: Iterable[str], empty: str = "- （未提供）") -> str:
    cleaned = [clean_text(value) for value in values if str(value).strip()]
    return "\n".join(f"- {value}" for value in cleaned) if cleaned else empty


def receipt_markdown(records: list[dict[str, str]]) -> str:
    if not records:
        return "- （扫描范围内未发现回执）"
    return "\n".join(
        f"- `{item['path']}`｜状态 `{item['status']}`｜时间 `{item['run_at']}`｜窗口 `{item['window']}`"
        for item in records
    )


def artifact_markdown(records: list[dict[str, str | int]]) -> str:
    if not records:
        return "- （扫描范围内未发现产物）"
    return "\n".join(
        f"- `{item['path']}`｜{item['bytes']} bytes｜{item['modified_at']}"
        for item in records
    )


def git_markdown(snapshot: dict[str, Any]) -> str:
    count_text = ", ".join(f"{key}={value}" for key, value in snapshot["counts"].items()) or "clean"
    lines = [
        f"- 分支：`{snapshot['branch']}`",
        f"- 全工作区变更：{snapshot['total_changes']}（{count_text}）",
    ]
    if snapshot["relevant_changes"]:
        lines.append("- 与本任务扫描范围相关：")
    elif snapshot["display_changes"]:
        lines.append("- 扫描范围未命中变更；以下为工作区变更样本：")
    else:
        lines.append("- 工作区无变更。")
    lines.extend(f"  - `{line}`" for line in snapshot["display_changes"])
    if snapshot["omitted"]:
        lines.append(f"  - 另有 {snapshot['omitted']} 项未展开。")
    return "\n".join(lines)


def render(template: str, values: dict[str, str]) -> str:
    output = template
    for key, value in values.items():
        output = output.replace("{{" + key + "}}", value)
    remaining = sorted(set(PLACEHOLDER.findall(output)))
    if remaining:
        raise ValueError(f"unresolved template placeholders: {remaining}")
    return output.rstrip() + "\n"


def atomic_write(path: Path, content: str) -> tuple[str, str | None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return "unchanged", None
    history_path: Path | None = None
    if path.exists():
        history_dir = path.parent / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(TIMEZONE).strftime("%Y%m%dT%H%M%S%z")
        history_path = history_dir / f"CURRENT-{stamp}.md"
        history_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)
    return "updated" if history_path else "created", str(history_path) if history_path else None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="Human-readable task name")
    parser.add_argument("--slug", required=True, help="ASCII checkpoint directory name")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--status", default="in_progress")
    parser.add_argument("--window", default="未指定")
    parser.add_argument("--scope", action="append", required=True, help="Project-relative file or directory; repeatable")
    parser.add_argument("--receipt", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--decision", action="append", default=[])
    parser.add_argument("--blocker", action="append", default=[])
    parser.add_argument("--next", dest="next_steps", action="append", default=[])
    parser.add_argument("--do-not-repeat", action="append", default=[])
    parser.add_argument("--output", help="Default: analysis/thread_handoffs/<slug>/CURRENT.md")
    parser.add_argument("--template", default="analysis/thread_handoffs/TEMPLATE.md")
    parser.add_argument("--max-receipts", type=int, default=6)
    parser.add_argument("--max-artifacts", type=int, default=12)
    parser.add_argument("--max-git-paths", type=int, default=20)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    slug = slugify(args.slug)
    task = clean_text(args.task)
    objective = clean_text(args.objective)
    status = clean_text(args.status)
    window = clean_text(args.window)
    scopes = [safe_path(root, item, must_exist=True) for item in args.scope]
    explicit_receipts = [safe_path(root, item, must_exist=True) for item in args.receipt]
    explicit_artifacts = [safe_path(root, item, must_exist=True) for item in args.artifact]
    template_path = safe_path(root, args.template, must_exist=True)
    output = safe_path(root, args.output or f"analysis/thread_handoffs/{slug}/CURRENT.md")

    receipts = discover_receipts(root, scopes, explicit_receipts, max(1, args.max_receipts))
    output_relative = relative(root, output)
    artifacts = [
        item
        for item in discover_artifacts(root, scopes, explicit_artifacts, max(1, args.max_artifacts) + 1)
        if item["path"] != output_relative
    ][: max(1, args.max_artifacts)]
    git = git_snapshot(root, scopes, max(1, args.max_git_paths))
    generated_at = datetime.now(TIMEZONE).isoformat(timespec="seconds")
    resume_prompt = (
        f"继续“{task}”。先读取 AGENTS.md、{output_relative}，以及检查点列出的最新回执。"
        "以当前文件、在线状态和用户最新指令为准；不要导入旧聊天全文，不重复已完成步骤。"
    )
    values = {
        "TASK_NAME": task,
        "STATUS": status,
        "GENERATED_AT": generated_at,
        "OBJECTIVE": objective,
        "WINDOW": window,
        "SCOPES": bullets(relative(root, scope) for scope in scopes),
        "DECISIONS": bullets(args.decision),
        "RECEIPTS": receipt_markdown(receipts),
        "ARTIFACTS": artifact_markdown(artifacts),
        "GIT_STATUS": git_markdown(git),
        "BLOCKERS": bullets(args.blocker, "- 无已知阻断。"),
        "NEXT_STEPS": bullets(args.next_steps),
        "DO_NOT_REPEAT": bullets(args.do_not_repeat),
        "RESUME_PROMPT": resume_prompt,
    }
    content = render(template_path.read_text(encoding="utf-8"), values)
    if args.dry_run:
        print(content, end="")
        return 0
    result, history = atomic_write(output, content)
    print(
        json.dumps(
            {
                "status": result,
                "output": relative(root, output),
                "history": relative(root, Path(history)) if history else None,
                "receipts": len(receipts),
                "artifacts": len(artifacts),
                "git_changes": git["total_changes"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Optional Claude interpretation stage with deterministic extract-only publication.

The coordinator must separately review generated interpretations. Exact extracts
can enter the report immediately; their source scope is printed alongside them.
"""
import html
import json
import os
from pathlib import Path
import time

try:
    from .claude_bridge import Bridge, ROOT, READY, assert_safe, read, write
except ImportError:
    from claude_bridge import Bridge, ROOT, READY, assert_safe, read, write


def enrich(stage, sources, window, quality, root=ROOT):
    """Retired daily-task hook: never dispatch, even when called by old clients."""
    return {"status": "not_run", "reason": "routine_workflow_excluded", "markdown": "", "html": ""}


def publish_accepted(bridge, tid, output, original=None):
    """Publish reviewed interpretation to a NEW local Markdown deliverable."""
    delivered = bridge.collect(tid)
    if delivered["status"] != "accepted":
        raise ValueError("coordinator acceptance required before publication")
    out = Path(output).resolve()
    if not out.is_relative_to(ROOT) or out.is_relative_to(ROOT / ".git") or out.suffix != ".md":
        raise ValueError("output must be a project Markdown path")
    result = delivered["result"]
    text = ""
    if original:
        source = Path(original).resolve()
        if not source.is_relative_to(ROOT) or source.suffix != ".md":
            raise ValueError("original must be project Markdown")
        text = source.read_text() + "\n"
    text += "## Claude 协作分析（主 Agent 已验收）\n\n" + result["summary"] + "\n\n"
    for f in result["findings"]:
        text += f"- [{f['kind']}] {f['text']}（证据：{', '.join(f['evidence_ids'])}）\n"
    if result["open_questions"]:
        text += "\n待确认：" + "；".join(result["open_questions"]) + "\n"
    text += f"\n任务回执：{tid}\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as f:
        f.write(text)
    write(bridge.root / tid / "publication.json", {"status": "published_local", "path": str(out.relative_to(ROOT))})
    return {"status": "published_local", "path": str(out)}

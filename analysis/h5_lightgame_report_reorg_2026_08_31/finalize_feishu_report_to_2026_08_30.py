#!/usr/bin/env python3
"""Finish two stale source notes left after the revision-754 refresh."""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC = "https://ksg964l11fam.sg.larksuite.com/wiki/QYbiws4OEit03Uke92rlfzmcgWb"
RECEIPT = ROOT / "feishu_refresh_revision754_receipt_2026_09_01.json"
ENV = os.environ.copy()
ENV["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
ENV["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"


def call(args: list[str]) -> dict:
    result = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=ENV, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    value = json.loads(result.stdout)
    if value.get("ok") is not True:
        raise RuntimeError(json.dumps(value, ensure_ascii=False))
    return value


def fetch() -> dict:
    return call(["docs", "+fetch", "--doc", DOC, "--detail", "full", "--format", "json"])["data"]["document"]


def find(content: str, tag: str, needle: str) -> str:
    for match in re.finditer(rf"<{tag}\b[^>]*\bid=\"([^\"]+)\"[^>]*>.*?</{tag}>", content, re.S):
        if needle in html.unescape(match.group(0)):
            return match.group(1)
    raise KeyError(f"Cannot locate {tag}: {needle}")


def update(tag: str, needle: str, xml: str) -> int:
    doc = fetch()
    out = call(["docs", "+update", "--doc", doc["document_id"], "--command", "block_replace", "--block-id", find(doc["content"], tag, needle), "--content", xml])
    return out["data"]["document"]["revision_id"]


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f'<th background-color="light-gray" vertical-align="top"><p>{item}</p></th>' for item in headers)
    body = "".join("<tr>" + "".join(f'<td vertical-align="top"><p>{item}</p></td>' for item in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def main() -> None:
    revision1 = update(
        "p",
        "起源新增留存完整至8月29日",
        "<p><b>来源与状态：</b>飞书《新包新增用户分析》修订754的注册与首充留存完整至8月30日；GA4页面行为仍完整至8月27日；服务端游戏事件按各报表完整日提供。H5加载与可玩事件缺失；下注、结算服务端事实存在，但入口、游戏和局次关联未通过。缺失环节不计为用户流失。</p>",
    )
    appendix = table(
        ["数据项", "状态", "说明"],
        [
            ["飞书《新包新增用户分析》修订754", "certified", "完整至8月30日；新增与新增首充留存均按字段最大有效批次统计"],
            ["GA4日表（外部平台）", "provisional", "8月21—27连续7日；全部WEB；标准D3 Day待重算"],
            ["GA4用户级关联", "blocked", "user_id事件覆盖不足，不能和起源留存做用户级归因"],
            ["GA4性能与游戏过程", "blocked", "无GAME_LOAD/READY、Web Vitals和错误事件"],
            ["Origin GAMESTART / GAMEEND", "blocked", "GAMESTART覆盖不完整；GAMEEND异常约6.13%"],
            ["Metabase游戏深度", "provisional", "首充用户累计快照，不是首次开局时序"],
        ],
    )
    revision2 = update("table", "起源 BQ-新增付费用户分析", appendix)
    receipt = {"status": "ok", "source_revision": 754, "source_as_of": "2026-08-30", "report_revision": revision2, "updated": ["funnel_source", "appendix_source"], "previous_revision": revision1}
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()

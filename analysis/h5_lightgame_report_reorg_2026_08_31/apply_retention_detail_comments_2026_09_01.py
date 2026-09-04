#!/usr/bin/env python3
"""Apply stakeholder edits: detailed retention comparisons and clear date scope."""
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
SUMMARY = json.loads((ROOT / "origin_retention_refresh_2026_08_30.json").read_text(encoding="utf-8"))
RECEIPT = ROOT / "retention_detail_comment_receipt_2026_09_01.json"
GROUPS = ["H5自然", "H5 Facebook", "H5 Google", "PWA自然"]
METRICS = ["D2 Day", "D3 Day", "D7 Day", "D15 Day"]
ENV = os.environ.copy()
ENV["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
ENV["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"


def call(args: list[str]) -> dict:
    done = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=ENV, text=True, capture_output=True)
    if done.returncode:
        raise RuntimeError(done.stderr.strip() or done.stdout.strip())
    result = json.loads(done.stdout)
    if result.get("ok") is not True:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return result


def fetch() -> dict:
    return call(["docs", "+fetch", "--doc", DOC, "--detail", "full", "--format", "json"])["data"]["document"]


def find(content: str, tag: str, needle: str) -> str:
    pattern = re.compile(rf"<{tag}\b[^>]*\bid=\"([^\"]+)\"[^>]*>.*?</{tag}>", re.S)
    for match in pattern.finditer(content):
        if needle in html.unescape(match.group(0)):
            return match.group(1)
    raise KeyError(f"{tag}: {needle}")


def replace(tag: str, needle: str, xml: str) -> int:
    doc = fetch()
    response = call(["docs", "+update", "--doc", doc["document_id"], "--command", "block_replace", "--block-id", find(doc["content"], tag, needle), "--content", xml])
    return response["data"]["document"]["revision_id"]


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def pp(value: float | None) -> str:
    return "N/A" if value is None else f"{value:+.1%}"


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f'<th background-color="light-gray" vertical-align="top"><p>{value}</p></th>' for value in headers)
    body = "".join("<tr>" + "".join(f'<td vertical-align="top"><p>{value}</p></td>' for value in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def main() -> None:
    changes = []
    comparison = {row["group"]: row for row in SUMMARY["pre_post"]}
    prepost_rows = []
    for group in GROUPS:
        row = comparison[group]
        values = []
        for metric in METRICS:
            before, after, delta = row[metric]["pre"]["rate"], row[metric]["post"]["rate"], row[metric]["delta"]
            values.append(f"{pct(before)} → {pct(after)}（{pp(delta)}）")
        prepost_rows.append([group, *values])
    changes.append(("prepost_intro", replace("p", "比较口径：", "<p><b>比较口径：</b>上线前为2026年6月16日—7月13日；上线后为2026年7月14日—8月30日。每项均使用已达到对应Dn Day、且源表有值的最大有效批次。表内依次展示“上线前留存 → 上线后留存（变化）”。</p>")))
    changes.append(("prepost_table", replace("table", "日均新增变化", table(["渠道/运行形态", "D2 Day", "D3 Day", "D7 Day", "D15 Day"], prepost_rows))))

    post = SUMMARY["post_register"]
    changes.append(("post_intro", replace("p", "上线后从7月14日开始累计至8月30日", "<p><b>来源：飞书《新包新增用户分析》修订754。</b>上线后从7月14日累计至8月30日；D2 / D3 / D7 / D15分别使用源表中截至8月29日、8月27日、8月23日、8月15日的最大有效批次。</p>")))
    post_rows = [[group, *(pct(post[group][metric]["rate"]) for metric in METRICS)] for group in GROUPS]
    changes.append(("post_table", replace("table", "149,876", table(["渠道/运行形态", *METRICS], post_rows))))

    phases = SUMMARY["phase_summary"]
    baseline = phases[0]["metrics"]
    phase_rows = []
    for phase in phases:
        rates = " / ".join(pct(phase["metrics"][metric]["rate"]) for metric in METRICS)
        if phase["phase"] == "上线前基线":
            deltas = "—"
        else:
            deltas = " / ".join(pp(phase["metrics"][metric]["rate"] - baseline[metric]["rate"]) for metric in METRICS)
        phase_rows.append([phase["phase"], phase["window"], f"{phase['new_users']:,}", rates, deltas])
    changes.append(("phase_table", replace("table", "后续追踪", table(["阶段", "日期窗口", "新增用户", "D2 / D3 / D7 / D15 Day", "相对上线前基线"], phase_rows))))
    changes.append(("phase_conclusion", replace("p", "结论：8/11至今", "<p><b>阶段结论：</b>后续追踪期（8月11日—30日）相对上线前基线，D2 / D3 / D7 / D15 Day为<b>+5.0pp / +3.7pp / +2.1pp / +1.6pp</b>。Color Dice与Opera阶段也高于基线；但每个阶段均叠加版本、KYC、投放和埋点变化，只能说明阶段走势改善，不能归因于单款游戏。</p>")))

    snapshot = {
        "H5自然": ("46.3%", "31.6%", "+15.8pp", "+13.6pp"),
        "H5 Facebook": ("32.4%", "20.6%", "+3.6pp", "+5.4pp"),
        "H5 Google": ("44.2%", "23.4%", "+6.4pp", "+0.7pp"),
        "PWA自然": ("48.9%", "29.6%", "+1.3pp", "+0.7pp"),
    }
    rows = [[group, *values] for group, values in snapshot.items()]
    changes.append(("latest_heading", replace("h1", "近期新增留存", "<h1>最新新增批次：D2/D3与上线前基线对比</h1>")))
    changes.append(("latest_table", replace("table", "8月27日注册批次", table(["8月27日注册批次", "D2 Day", "D3 Day", "D2相对基线", "D3相对基线"], rows))))
    changes.append(("latest_note", replace("p", "该快照只展示截至8月30日", "<p><b>解读：</b>8月27日注册批次在四个渠道的D2/D3均高于上线前基线；其中H5自然提升<b>+15.8pp / +13.6pp</b>。该快照仅展示截至8月30日已达到统计口径的D2/D3，D7及更长期尚未达到观察日，不在本表展示。</p>")))

    changes.append(("metabase_heading", replace("h1", "游戏深度：近期首充用户累计快照", "<h1>游戏深度：截至2026年8月28日的首充用户累计快照（外部生产Metabase）</h1>")))
    changes.append(("metabase_scope", replace("p", "外部生产Metabase的用户×游戏聚合快照", "<p><b>统计时间：</b>2026年8月28日查询快照。外部生产Metabase的 <code>stat_game_bet_gain</code> 为用户×游戏累计快照，当前无法从表中还原固定起止日期；展示的是截至查询时的近期首充用户累计局数与下注。<code>update_at</code>不是首次开局时间，因此该表不代表全体新增用户首日漏斗，也不能判断付费前后顺序。</p>")))

    final = fetch()
    payload = {"status": "ok", "report_revision": final["revision_id"], "updated": [name for name, _ in changes]}
    RECEIPT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()

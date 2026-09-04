#!/usr/bin/env python3
"""Repair a partial Feishu refresh and finish the requested data updates."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC_ID = "GyZddVm2powgFBxLwH0l18Qzguf"
RECEIPT = ROOT / "refresh_2026_08_29_receipt.json"


def call(args: list[str]) -> dict:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    result = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    response = json.loads(result.stdout)
    if response.get("ok") is not True:
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    return response


def fetch() -> tuple[str, int]:
    response = call(["docs", "+fetch", "--doc", DOC_ID, "--detail", "with-ids", "--format", "json"])
    doc = response["data"]["document"]
    return doc["content"], doc["revision_id"]


def direct_id(xml: str, tag: str, literal: str) -> str:
    """Find the target tag itself, without allowing an earlier tag to span the document."""
    closing = f"</{tag}>"
    start = 0
    marker = f"<{tag}"
    while True:
        left = xml.find(marker, start)
        if left < 0:
            break
        open_end = xml.find(">", left)
        right = xml.find(closing, open_end)
        if open_end < 0 or right < 0:
            break
        block = xml[left:right + len(closing)]
        if literal in block:
            match = re.search(r'\bid="([^"]+)"', block[:open_end-left])
            if not match:
                raise KeyError(f"No id on {tag} that contains {literal}")
            return match.group(1)
        start = right + len(closing)
    raise KeyError(f"No {tag} contains {literal}")


def first_table_after(xml: str, heading: str) -> str:
    pos = xml.find(heading)
    if pos < 0:
        raise KeyError(heading)
    match = re.search(r'<table\b[^>]*\bid="([^"]+)"', xml[pos:])
    if not match:
        raise KeyError(f"No table after {heading}")
    return match.group(1)


def replace(block_id: str, content: str) -> None:
    call(["docs", "+update", "--doc", DOC_ID, "--command", "block_replace", "--block-id", block_id, "--content", content])


def insert_after(block_id: str, content: str) -> None:
    call(["docs", "+update", "--doc", DOC_ID, "--command", "block_insert_after", "--block-id", block_id, "--content", content])


def delete(block_id: str) -> None:
    call(["docs", "+update", "--doc", DOC_ID, "--command", "block_delete", "--block-id", block_id])


# Repair the two misplaced blocks created in an interrupted prior pass.
xml, _ = fetch()
if xml.find("新增首充与新增未付费：与上线前对比") < xml.find("数据范围："):
    heading_id = direct_id(xml, "h2", "新增首充与新增未付费：与上线前对比")
    table_id = first_table_after(xml, "新增首充与新增未付费：与上线前对比")
    summary_id = direct_id(xml, "p", "分群对比：")
    anchor_id = direct_id(xml, "p", "分群观察：")
    call([
        "docs", "+update", "--doc", DOC_ID, "--command", "block_move_after",
        "--block-id", anchor_id, "--src-block-ids", f"{heading_id},{table_id},{summary_id}",
    ])
    xml, _ = fetch()
    old_summary_id = direct_id(xml, "p", "分群观察：")
    delete(old_summary_id)

# Restore the historical-retention heading that was changed by the interrupted pass.
xml, _ = fetch()
bad_historical_id = direct_id(xml, "h1", "近期五款游戏：页面触达与短期回访")
if xml.find("历史留存结构：四渠道差异") < 0:
    replace(bad_historical_id, '<h1 seq="auto">历史留存结构：四渠道差异</h1>')

# The actual current-five-game section stays separate from Top Games nine.
xml, _ = fetch()
if "当前五款游戏：页面触达与短期回访" in xml:
    current_heading_id = direct_id(xml, "h1", "当前五款游戏：页面触达与短期回访")
    replace(current_heading_id, "<h1>近期五款游戏：页面触达与短期回访</h1>")
xml, _ = fetch()
if "核心发现：8月21—27日Keno触达规模最大" in xml:
    current_callout_id = direct_id(xml, "callout", "核心发现：8月21—27日Keno触达规模最大")
    replace(
        current_callout_id,
        """
<callout emoji="💡" background-color="light-blue" border-color="blue">
  <p><b>短期观察：</b>8月21—27日，Keno在近期五款追踪游戏中页面触达最大，Plinko人均页面浏览最高；Limbo的D1应用回访较高，Plinko的D3相对更稳。</p>
  <p><b>判断边界：</b>页面进入与应用回访只能说明相关性，不能据此认定单款游戏提升了留存。</p>
</callout>
""",
    )

# Expand the existing product Top Games section rather than replacing the five-game tracker.
xml, _ = fetch()
if "产品定义的Top Games九款对照" in xml:
    h2_id = direct_id(xml, "h2", "产品定义的Top Games九款对照")
    replace(h2_id, "<h2>产品Top Games九款：轻量化4款与非轻量化5款对照</h2>")
xml, _ = fetch()
if "Top Games固定为Whot、Limbo、CoinFlip、Keno、ColorDice、Hilo、Plinko、Tower和Bottle spin" in xml:
    description_id = direct_id(xml, "p", "Top Games固定为Whot、Limbo、CoinFlip、Keno、ColorDice、Hilo、Plinko、Tower和Bottle spin")
    replace(
        description_id,
        "<p><b>分组：</b>轻量化4款为CoinFlip、Limbo、Keno、ColorDice；非轻量化5款为Whot、Hilo、Plinko、Tower、Bottle spin。页面触达统计至8月27日；D1、D3分别只纳入已达到对应观察天数的新访客。</p>",
    )

xml, _ = fetch()
top_heading = "产品Top Games九款：轻量化4款与非轻量化5款对照"
top_table_id = first_table_after(xml, top_heading)
if "07_产品TopGames九款_D1D3回访.png" not in xml:
    insert_after(
        top_table_id,
        '<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/07_产品TopGames九款_D1D3回访.png" width="880" caption="产品Top Games九款D1/D3应用回访；紫色标签代表轻量化4款"/>',
    )

xml, _ = fetch()
top_table_id = first_table_after(xml, top_heading)
if "Tower / 9013" not in xml:
    replace(
        top_table_id,
        """
<table>
  <thead><tr><th><p>分组</p></th><th><p>游戏 / ID</p></th><th><p>新访客</p></th><th><p>D1应用回访</p></th><th><p>D3应用回访</p></th><th><p>观察状态</p></th></tr></thead>
  <tbody>
    <tr><td><p>非轻量化</p></td><td><p>Whot / 6001</p></td><td><p>1,109</p></td><td><p>30.6%（n=935）</p></td><td><p>14.0%（n=529）</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>Limbo / 9008</p></td><td><p>647</p></td><td><p>29.0%（n=544）</p></td><td><p>13.9%（n=316）</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>CoinFlip / 9001</p></td><td><p>425</p></td><td><p>31.6%（n=351）</p></td><td><p>17.6%（n=204）</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>Keno / 9010</p></td><td><p>270</p></td><td><p>36.4%（n=231）</p></td><td><p>13.6%（n=140）</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>ColorDice / 9003</p></td><td><p>413</p></td><td><p>25.2%（n=325）</p></td><td><p>15.7%（n=102）</p></td><td><p>可观察</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Hilo / 9011</p></td><td><p>184</p></td><td><p>34.4%（n=151）</p></td><td><p>16.7%（n=78）</p></td><td><p>小样本</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Plinko / 9016</p></td><td><p>365</p></td><td><p>31.3%（n=310）</p></td><td><p>17.3%（n=196）</p></td><td><p>可观察</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Tower / 9013</p></td><td><p>122</p></td><td><p>38.1%（n=84）</p></td><td><p>N/A</p></td><td><p>8/25上线，D3未成熟</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Bottle spin / 2003</p></td><td><p>709</p></td><td><p>31.4%（n=601）</p></td><td><p>11.0%（n=353）</p></td><td><p>可观察</p></td></tr>
  </tbody>
</table>
""",
    )

xml, _ = fetch()
if "解读：Top Games是产品固定分组" in xml:
    judgement_id = direct_id(xml, "p", "解读：Top Games是产品固定分组")
    replace(
        judgement_id,
        "<p><b>解读：</b>轻量化4款的D1范围为25.2%—36.4%，D3范围为13.6%—17.6%；非轻量化5款中Tower仅有D1样本，Hilo的D3分母为78人。当前只能做同窗口对照，不能据此判断轻量化整体优于或弱于非轻量化游戏。</p>",
    )

xml, revision = fetch()
required = [
    "历史留存结构：四渠道差异",
    "新增留存最新完整日为8月29日",
    "统计期间关键更新与干扰项",
    "新增首充与新增未付费：与上线前对比",
    "产品Top Games九款：轻量化4款与非轻量化5款对照",
    "轻量化4款为CoinFlip、Limbo、Keno、ColorDice",
    "Tower / 9013",
]
missing = [item for item in required if item not in xml]
if missing:
    raise RuntimeError(f"Readback missing: {missing}")
RECEIPT.write_text(json.dumps({
    "status": "ok",
    "revision_id": revision,
    "retention_cutoff": "2026-08-29",
    "ga4_cutoff": "2026-08-27",
    "source_revisions": {"new_user_sheet": 732, "update_records": 1830, "game_code_technical_doc": 790},
    "validated_strings": required,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "ok", "revision_id": revision}, ensure_ascii=False))

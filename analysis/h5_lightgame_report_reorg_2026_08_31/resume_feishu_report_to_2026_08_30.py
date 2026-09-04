#!/usr/bin/env python3
"""Finish the revision-754 refresh after the first guarded update batch."""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC = "https://ksg964l11fam.sg.larksuite.com/wiki/QYbiws4OEit03Uke92rlfzmcgWb"
SUMMARY = json.loads((ROOT / "origin_retention_refresh_2026_08_30.json").read_text(encoding="utf-8"))
RECEIPT = ROOT / "feishu_refresh_revision754_receipt_2026_09_01.json"
GROUPS = ["H5自然", "H5 Facebook", "H5 Google", "PWA自然"]
METRICS = ["D2 Day", "D3 Day", "D7 Day", "D15 Day", "D30 Day"]
ENV = os.environ.copy()
ENV["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
ENV["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"


def call(args: list[str]) -> dict:
    completed = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=ENV, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    output = json.loads(completed.stdout)
    if output.get("ok") is not True:
        raise RuntimeError(json.dumps(output, ensure_ascii=False))
    return output


def fetch() -> dict:
    return call(["docs", "+fetch", "--doc", DOC, "--detail", "full", "--format", "json"])["data"]["document"]


def block_id(content: str, tag: str, needle: str) -> str:
    for match in re.finditer(rf"<{tag}\b[^>]*\bid=\"([^\"]+)\"[^>]*>.*?</{tag}>", content, re.S):
        if needle in html.unescape(match.group(0)):
            return match.group(1)
    raise KeyError(f"{tag}: {needle}")


def replace(tag: str, needle: str, xml: str) -> int:
    doc = fetch()
    result = call(["docs", "+update", "--doc", doc["document_id"], "--command", "block_replace", "--block-id", block_id(doc["content"], tag, needle), "--content", xml])
    return result["data"]["document"]["revision_id"]


def replace_img(name: str, path: str, caption: str) -> int:
    doc = fetch()
    for match in re.finditer(r"<img\b[^>]*/>", doc["content"]):
        if f'name="{name}"' in match.group(0):
            image_id = re.search(r'id="([^"]+)"', match.group(0)).group(1)
            xml = f'<img path="@./{path}" name="{name}" width="1600" height="900" caption="{caption}"/>'
            result = call(["docs", "+update", "--doc", doc["document_id"], "--command", "block_replace", "--block-id", image_id, "--content", xml])
            return result["data"]["document"]["revision_id"]
    raise KeyError(name)


def insert_after(tag: str, needle: str, xml: str) -> int:
    doc = fetch()
    if "新增首充用户留存（截至8月30日）" in html.unescape(doc["content"]):
        return doc["revision_id"]
    result = call(["docs", "+update", "--doc", doc["document_id"], "--command", "block_insert_after", "--block-id", block_id(doc["content"], tag, needle), "--content", xml])
    return result["data"]["document"]["revision_id"]


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def pp(value: float | None) -> str:
    return "N/A" if value is None else f"{value:+.1%}"


def table(headers: list[str], rows: list[list[str]]) -> str:
    thead = "".join(f'<th background-color="light-gray" vertical-align="top"><p>{header}</p></th>' for header in headers)
    tbody = "".join("<tr>" + "".join(f'<td vertical-align="top"><p>{cell}</p></td>' for cell in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</table>"


def main() -> None:
    post = SUMMARY["post_register"]
    changes = []
    rows = []
    for group in GROUPS:
        p = post[group]
        rows.append([group, *(f"{pct(p[metric]['rate'])}（n={p[metric]['population']:,}）" for metric in ["D2 Day", "D3 Day", "D7 Day", "D15 Day"])])
    changes.append(("post_table", replace("table", "41.1%", table(["渠道/运行形态", "D2 Day", "D3 Day", "D7 Day", "D15 Day"], rows))))
    changes.append(("post_note", replace("p", "正向信号集中在H5自然和Google；Facebook没有改善", "<p><b>解读：</b>上线后累计的正向信号仍集中在H5自然和Google：H5自然D7 Day为<b>14.2%</b>，Google为<b>14.1%</b>。Facebook D7 Day仅<b>6.7%</b>；PWA自然D7 Day为<b>12.1%</b>，低于上线前基线。D15 Day延续同一方向：H5自然<b>7.0%</b>，Google<b>8.0%</b>，Facebook<b>3.5%</b>，PWA自然<b>6.6%</b>。</p>")))
    changes.append(("d15_boundary", replace("callout", "D15 Day观察边界：", "<callout emoji=\"📌\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>最大有效样本：</b>D2 Day、D3 Day、D7 Day、D15 Day的上线后样本分别覆盖47、45、41、31—33个有效注册批次；D30 Day只有4—6个上线后批次，故仅在历史长周期表中方向性展示。</p></callout>")))

    changes.append(("curve", replace_img("03_起源同批注册DnDay留存曲线.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/03_起源同批注册DnDay留存曲线.png", "来源：飞书《新包新增用户分析》修订754；同一批注册用户Dn Day留存曲线")))
    changes.append(("decay", replace_img("04_起源DnDay留存衰减.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/04_起源DnDay留存衰减.png", "来源：飞书《新包新增用户分析》修订754；四渠道Dn Day分阶段留存衰减")))

    phases = SUMMARY["phase_summary"]
    phase_rows = []
    for phase in phases:
        m = phase["metrics"]
        phase_rows.append([phase["phase"], phase["window"], f"{phase['new_users']:,}", " / ".join(pct(m[item]["rate"]) for item in ["D2 Day", "D3 Day", "D7 Day", "D15 Day"])])
    changes.append(("phase_table", replace("table", "当前期", table(["阶段", "日期窗口", "新增用户", "D2 Day / D3 Day / D7 Day / D15 Day"], phase_rows))))
    changes.append(("phase_chart", replace_img("05_起源轻量化节点D3Day留存.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/05_起源轻量化节点D3Day留存.png", "来源：飞书《新包新增用户分析》修订754 + 更新记录；四渠道D3 Day留存变化")))

    latest_d3 = {
        "H5自然": (3149, "46.3%", "31.6%"),
        "H5 Facebook": (5451, "32.4%", "20.6%"),
        "H5 Google": (851, "44.2%", "23.4%"),
        "PWA自然": (550, "48.9%", "29.6%"),
    }
    snapshot_rows = [[group, f"{new_users:,}", d2, d3, "N/A", "N/A"] for group, (new_users, d2, d3) in latest_d3.items()]
    changes.append(("latest_snapshot", replace("table", "8月26日注册批次", table(["8月27日注册批次", "新增", "D2 Day", "D3 Day", "D7 Day", "D15 Day"], snapshot_rows))))

    first_pay = SUMMARY["post_first_pay"]
    changes.append(("firstpay_source", replace("p", "T0为首次成功现金充值日", "<p><b>来源与口径：</b>飞书《新包新增用户分析》修订754中的新增首充用户留存字段。首充用户以对应注册批次的首充人数作为分母，D2/D3/D7/D15/D30均只使用源表有值且达到观察天数的最大有效批次；这与“注册批次留存”分母不同，单独展示。</p>")))
    firstpay_rows = []
    for group in GROUPS:
        p = first_pay[group]
        firstpay_rows.append([group, *(pct(p[metric]["rate"]) for metric in METRICS)])
    firstpay_xml = "<h2>新增首充用户留存（截至8月30日）</h2><p><b>样本范围：</b>上线后7月14日—8月30日；D2/D3/D7/D15分别覆盖47/45/41/33个有效首充批次（PWA D15为31个）。D30仅4—6个批次，作方向参考。</p>" + table(["渠道/运行形态", *METRICS], firstpay_rows) + '<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/06_新增首充用户DnDay留存_截止8月30日.png" name="06_新增首充用户DnDay留存_截止8月30日.png" width="1600" height="900" caption="来源：飞书《新包新增用户分析》修订754；新增首充用户Dn Day留存（截至8月30日）"/><p><b>解读：</b>新增首充用户中，H5 Google D7 Day为<b>16.0%</b>、H5自然为<b>15.7%</b>，均显著高于H5 Facebook的<b>7.7%</b>；PWA自然为<b>12.6%</b>。首充用户留存与整体注册留存方向一致：Facebook承接质量偏弱，H5自然与Google更稳。</p>'
    changes.append(("firstpay_insert", insert_after("p", "飞书《新包新增用户分析》修订754中的新增首充用户留存字段", firstpay_xml)))

    changes.append(("funnel_source", replace("p", "跨来源共同完整日截至", "<p><b>来源与状态：</b>飞书《新包新增用户分析》修订754的注册与首充留存完整至8月30日；GA4页面行为仍完整至8月27日；服务端游戏事件按各报表完整日提供。H5加载与可玩事件缺失；下注、结算服务端事实存在，但入口、游戏和局次关联未通过。缺失环节不计为用户流失。</p>")))
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
    changes.append(("appendix", replace("table", "GA4日表", appendix)))

    doc = fetch()
    RECEIPT.write_text(json.dumps({"status": "ok", "source_revision": 754, "source_as_of": "2026-08-30", "report_revision": doc["revision_id"], "updated": [name for name, _ in changes]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RECEIPT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()

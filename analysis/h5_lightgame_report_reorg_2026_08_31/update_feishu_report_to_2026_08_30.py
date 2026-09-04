#!/usr/bin/env python3
"""Apply the revision-754 retention refresh to the existing Feishu report.

The script only replaces data blocks and source notes that are derived from the
new-user workbook. Existing user-made layout, comments, and non-retention
sections are preserved.
"""
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
CHARTS = ROOT / "charts"
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
    payload = json.loads(completed.stdout)
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def fetch() -> dict:
    return call(["docs", "+fetch", "--doc", DOC, "--detail", "full", "--format", "json"])["data"]["document"]


def find_block_id(content: str, tag: str, needle: str) -> str:
    pattern = re.compile(rf"<{tag}\b[^>]*\bid=\"([^\"]+)\"[^>]*>.*?</{tag}>", re.S)
    for match in pattern.finditer(content):
        if needle in html.unescape(match.group(0)):
            return match.group(1)
    raise KeyError(f"{tag} block not found for: {needle}")


def replace_block(tag: str, needle: str, content: str) -> int:
    document = fetch()
    block_id = find_block_id(document["content"], tag, needle)
    result = call(["docs", "+update", "--doc", document["document_id"], "--command", "block_replace", "--block-id", block_id, "--content", content])
    return result["data"]["document"]["revision_id"]


def insert_after(tag: str, needle: str, content: str) -> int:
    document = fetch()
    if "新增首充用户留存（截至8月30日）" in html.unescape(document["content"]):
        return document["revision_id"]
    block_id = find_block_id(document["content"], tag, needle)
    result = call(["docs", "+update", "--doc", document["document_id"], "--command", "block_insert_after", "--block-id", block_id, "--content", content])
    return result["data"]["document"]["revision_id"]


def replace_image(name: str, rel_path: str, caption: str) -> int:
    document = fetch()
    for match in re.finditer(r"<img\b[^>]*/>", document["content"]):
        raw = match.group(0)
        if f'name="{name}"' not in raw:
            continue
        block_id = re.search(r'id="([^"]+)"', raw).group(1)
        replacement = f'<img path="@./{rel_path}" name="{name}" width="1600" height="900" caption="{caption}"/>'
        result = call(["docs", "+update", "--doc", document["document_id"], "--command", "block_replace", "--block-id", block_id, "--content", replacement])
        return result["data"]["document"]["revision_id"]
    raise KeyError(f"Image not found: {name}")


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def pp(value: float | None) -> str:
    return "N/A" if value is None else f"{value:+.1%}"


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th background-color=\"light-gray\" vertical-align=\"top\"><p>{item}</p></th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td vertical-align=\"top\"><p>{item}</p></td>" for item in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def retention_rows(matrix: dict, include_population: bool = False) -> list[list[str]]:
    rows = []
    for group in GROUPS:
        values = []
        for metric in METRICS:
            point = matrix[group][metric]
            value = pct(point["rate"])
            values.append(f"{value}（n={point['population']:,}）" if include_population else value)
        rows.append([group, *values])
    return rows


def main() -> None:
    if SUMMARY["quality"]["status"] != "passed":
        raise RuntimeError("Source quality gate did not pass")
    changes = []

    changes.append(("scope", replace_block("p", "数据范围与来源：", "<p><b>数据范围与来源：</b>飞书《新包新增用户分析》修订754的新增用户与新增首充用户留存完整至2026年8月30日。历史累计使用2026年6月16日—8月30日；上线前基线为6月16日—7月13日，上线后累计为7月14日—8月30日。GA4游戏页面行为仍覆盖2026年8月21日—27日；外部生产Metabase仅提供近期首充用户的累计游戏快照。所有结果均为脱敏聚合数据。</p>")))
    changes.append(("cutoff", replace_block("callout", "来源截止日不同：", "<callout emoji=\"💡\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>留存数据已更新：</b>起源《新包新增用户分析》完整至8月30日，并对每个留存指标使用源表中已达到统计口径的最大有效批次。GA4页面行为仍只完整至8月27日；外部生产Metabase仅作首充分群参考。</p></callout>")))
    changes.append(("summary", replace_block("callout", "起源注册留存：", "<callout emoji=\"💡\" background-color=\"light-blue\" border-color=\"blue\"><p><b>起源注册留存：</b><span background-color=\"light-yellow\">正向信号集中在H5自然和Google</span>。上线后累计至8月30日，H5自然D7 Day为<b>14.2%</b>，较基线提升<b>+4.3pp</b>；H5 Google为<b>14.1%</b>，提升<b>+1.6pp</b>。Facebook日均新增增加<b>7.0%</b>，D7 Day反而下降<b>0.2pp</b>；PWA日均新增扩大<b>152.9%</b>，D7 Day下降<b>1.9pp</b>。</p><p><b>新增首充用户留存：</b>H5 Google的D7 Day为<b>16.0%</b>，H5自然为<b>15.7%</b>；H5 Facebook仅<b>7.7%</b>，仍是首充用户后续留存的主要短板。</p><p><b>GA4游戏页观察：</b>Limbo页面触达最大；Keno的D2 Day应用回访最高；Plinko的人均页面浏览较高。旧GA4的“D3”实际是D4 Day，不能当作Waje D3 Day理解。</p><p><b>数据边界：</b>H5加载、可玩、可下注事件未采集。下注和结算服务端事实存在，但尚未与入口、游戏和局次进行关联。</p></callout>")))

    source_table = table(
        ["来源", "用于什么", "时间范围", "业务显示与状态"],
        [
            ["飞书《新包新增用户分析》修订754", "新增用户及新增首充用户注册批次留存、渠道与阶段对照", "6/16—8/30", "D2/D3/D7/D15/D30均取源表最大有效批次；主数据源"],
            ["GA4 BigQuery（外部平台）", "首次访问、游戏页触达、应用回访、设备结构", "8/21—8/27", "D2 Day可用；旧D0+3结果标为D4 Day；标准D3 Day待重算"],
            ["外部生产Metabase平台", "近期首充用户×游戏累计局数与下注快照", "累计快照", "仅作首充分群观察，不代表首日漏斗"],
            ["Firebase Web配置（外部平台）", "核验Web App、Analytics和Performance接入", "配置快照", "Web App已注册；未关联Analytics流；无Performance Web指标"],
            ["起源服务端事件", "GAMESTART、下注、结算与资产事实", "按报表完整日", "入口—游戏—局次关联未通过，完整漏斗blocked"],
        ],
    )
    changes.append(("source_table", replace_block("table", "GA4 BigQuery（外部平台）", source_table)))
    changes.append(("dn_rule", replace_block("callout", "统一留存日：", "<callout emoji=\"📌\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>统一留存日：</b>D1 Day为注册/首次访问当天；D2 Day为次日；D3 Day为第3个自然日。<code>Dn Day = cohort_date + (n - 1) 天</code>。本报告起源留存字段已映射为Dn Day；GA4旧字段只作已标注的过渡参考，不用于横向比较。</p></callout>")))

    all_register = SUMMARY["all_register"]
    changes.append(("history_heading", replace_block("h1", "历史注册留存：", "<h1>注册批次留存：四渠道最大有效样本（截至8月30日）</h1>")))
    history_table = table(["渠道/运行形态", *METRICS], retention_rows(all_register))
    changes.append(("history_table", replace_block("table", "D2 Day / D3 Day / D7 Day / D15 Day / D30 Day", history_table)))
    changes.append(("history_note", replace_block("p", "H5 Google在各留存节点", "<p><b>样本范围：</b>D2 Day、D3 Day、D7 Day、D15 Day分别使用各渠道源表中截至8月29日、8月27日、8月23日、8月15日的最大有效注册批次；D30 Day仅有23—33个批次，作为长周期方向观察，不参与短期结论。</p><p><b>解读：</b>H5 Google在各留存节点仍领先标准H5 Facebook；PWA自然在D2 Day、D3 Day保持较高，但到D7 Day与H5自然接近。PWA与标准H5的入口、运行形态和流量结构不同，不能直接下产品定论。</p>")))
    changes.append(("history_chart", replace_image("01_起源四渠道DnDay留存对比.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/01_起源四渠道DnDay留存对比.png", "来源：飞书《新包新增用户分析》修订754；四渠道注册批次Dn Day留存（截至8月30日）")))

    comparison = {row["group"]: row for row in SUMMARY["pre_post"]}
    changes.append(("prepost_heading", replace_block("h1", "上线前后效果：", "<h1>轻量化上线后累计有效留存：H5自然与Google提升，Facebook与PWA未同步</h1>")))
    changes.append(("prepost_window", replace_block("p", "比较窗口：", "<p><b>比较口径：</b>上线前基线为2026年6月16日—7月13日；上线后累计为2026年7月14日—8月30日。每项留存只使用已达到对应Dn Day且源表有值的最大有效批次；新增使用日均规模比较，避免窗口长度不同造成误读。</p>")))
    prepost_table_rows = []
    for group in GROUPS:
        row = comparison[group]
        metrics = " / ".join(pp(row[metric]["delta"]) for metric in ["D2 Day", "D3 Day", "D7 Day", "D15 Day"])
        judgement = {
            "H5自然": "留存全面改善",
            "H5 Facebook": "扩量未改善",
            "H5 Google": "质量升、规模降",
            "PWA自然": "扩量伴随留存下降",
        }[group]
        prepost_table_rows.append([group, pp(row["daily_new_change"]), metrics, judgement])
    prepost_table = table(["渠道/运行形态", "日均新增变化", "D2 / D3 / D7 / D15 Day变化", "综合判断"], prepost_table_rows)
    changes.append(("prepost_table", replace_block("table", "新增变化", prepost_table)))
    changes.append(("prepost_chart", replace_image("02_起源上线前后DnDay留存变化.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/02_起源上线前后DnDay留存变化.png", "来源：飞书《新包新增用户分析》修订754；上线前基线与7月14日后最大有效样本留存变化")))

    post = SUMMARY["post_register"]
    changes.append(("post_heading", replace_block("h2", "上线后累计追踪：", "<h2>上线后累计追踪：2026年7月14日至8月30日</h2>")))
    changes.append(("post_scope", replace_block("p", "上线后累计从7月14日开始", "<p><b>来源：飞书《新包新增用户分析》修订754。</b>上线后从7月14日开始累计至8月30日。D2 Day、D3 Day、D7 Day、D15 Day分别使用截至8月29日、8月27日、8月23日、8月15日的最大有效注册批次；各渠道样本数直接见下表。</p>")))
    post_rows = []
    for group in GROUPS:
        points = post[group]
        post_rows.append([
            group,
            f"{pct(points['D2 Day']['rate'])}（n={points['D2 Day']['population']:,}）",
            f"{pct(points['D3 Day']['rate'])}（n={points['D3 Day']['population']:,}）",
            f"{pct(points['D7 Day']['rate'])}（n={points['D7 Day']['population']:,}）",
            f"{pct(points['D15 Day']['rate'])}（n={points['D15 Day']['population']:,}）",
        ])
    changes.append(("post_table", replace_block("table", "D2 Day D3 Day D7 Day D15 Day", table(["渠道/运行形态", "D2 Day", "D3 Day", "D7 Day", "D15 Day"], post_rows))))
    changes.append(("post_note", replace_block("p", "正向信号集中在H5自然和Google；Facebook没有改善", "<p><b>解读：</b>上线后累计的正向信号仍集中在H5自然和Google：H5自然D7 Day为<b>14.2%</b>，Google为<b>14.1%</b>。Facebook D7 Day仅<b>6.7%</b>；PWA自然D7 Day为<b>12.1%</b>，低于上线前基线。D15 Day延续同一方向：H5自然<b>7.0%</b>，Google<b>8.0%</b>，Facebook<b>3.5%</b>，PWA自然<b>6.6%</b>。</p>")))
    changes.append(("d15_note", replace_block("callout", "D15 Day观察边界：", "<callout emoji=\"📌\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>最大有效样本：</b>本节不补零。D2 Day、D3 Day、D7 Day、D15 Day的上线后样本分别覆盖47、45、41、31—33个有效注册批次；D30 Day只有4—6个上线后批次，故仅在历史长周期表中方向性展示。</p></callout>")))

    changes.append(("curve_chart", replace_image("03_起源同批注册DnDay留存曲线.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/03_起源同批注册DnDay留存曲线.png", "来源：飞书《新包新增用户分析》修订754；同一批注册用户Dn Day留存曲线")))
    changes.append(("decay_chart", replace_image("04_起源DnDay留存衰减.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/04_起源DnDay留存衰减.png", "来源：飞书《新包新增用户分析》修订754；四渠道Dn Day分阶段留存衰减")))

    phases = SUMMARY["phase_summary"]
    phase_rows = []
    for phase in phases:
        m = phase["metrics"]
        phase_rows.append([phase["phase"], phase["window"], f"{phase['new_users']:,}", " / ".join(pct(m[item]["rate"]) for item in ["D2 Day", "D3 Day", "D7 Day", "D15 Day"])])
    changes.append(("phase_table", replace_block("table", "上线前基线", table(["阶段", "日期窗口", "新增用户", "D2 Day / D3 Day / D7 Day / D15 Day"], phase_rows))))
    changes.append(("phase_chart", replace_image("05_起源轻量化节点D3Day留存.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/05_起源轻量化节点D3Day留存.png", "来源：飞书《新包新增用户分析》修订754 + 更新记录；四渠道D3 Day留存变化")))

    first_pay = SUMMARY["post_first_pay"]
    changes.append(("firstpay_source", replace_block("p", "T0为首次成功现金充值日", "<p><b>来源与口径：</b>飞书《新包新增用户分析》修订754中的新增首充用户留存字段。首充用户以对应注册批次的首充人数作为分母，D2/D3/D7/D15/D30均只使用源表有值且达到观察天数的最大有效批次；这与“注册批次留存”分母不同，单独展示。</p>")))
    firstpay_block = "<h2>新增首充用户留存（截至8月30日）</h2><p><b>样本范围：</b>上线后7月14日—8月30日；D2/D3/D7/D15分别覆盖47/45/41/33个有效首充批次（PWA D15为31个）。D30仅4—6个批次，作方向参考。</p>" + table(["渠道/运行形态", *METRICS], retention_rows(first_pay)) + '<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/06_新增首充用户DnDay留存_截止8月30日.png" name="06_新增首充用户DnDay留存_截止8月30日.png" width="1600" height="900" caption="来源：飞书《新包新增用户分析》修订754；新增首充用户Dn Day留存（截至8月30日）"/><p><b>解读：</b>新增首充用户中，H5 Google D7 Day为<b>16.0%</b>、H5自然为<b>15.7%</b>，均显著高于H5 Facebook的<b>7.7%</b>；PWA自然为<b>12.6%</b>。首充用户留存与整体注册留存方向一致：Facebook承接质量偏弱，H5自然与Google更稳。</p>'
    changes.append(("firstpay_insert", insert_after("p", "飞书《新包新增用户分析》修订754中的新增首充用户留存字段", firstpay_block)))

    changes.append(("funnel_source", replace_block("p", "跨来源共同完整日截至", "<p><b>来源与状态：</b>飞书《新包新增用户分析》修订754的注册与首充留存完整至8月30日；GA4页面行为仍完整至8月27日；服务端游戏事件按各报表完整日提供。H5加载与可玩事件缺失；下注、结算服务端事实存在，但入口、游戏和局次关联未通过。缺失环节不计为用户流失。</p>")))

    changes.append(("appendix_source", replace_block("table", "GA4日表", table(
        ["数据项", "状态", "说明"],
        [
            ["飞书《新包新增用户分析》修订754", "certified", "完整至8月30日；新增与新增首充留存均按字段最大有效批次统计"],
            ["GA4日表（外部平台）", "provisional", "8月21—27连续7日；全部WEB；标准D3 Day待重算"],
            ["GA4用户级关联", "blocked", "user_id事件覆盖不足，不能和起源留存做用户级归因"],
            ["GA4性能与游戏过程", "blocked", "无GAME_LOAD/READY、Web Vitals和错误事件"],
            ["Origin GAMESTART / GAMEEND", "blocked", "GAMESTART覆盖不完整；GAMEEND异常约6.13%"],
            ["Metabase游戏深度", "provisional", "首充用户累计快照，不是首次开局时序"],
        ],
    ))))

    final_doc = fetch()
    RECEIPT.write_text(json.dumps({
        "status": "ok",
        "source_revision": SOURCE_REVISION,
        "report_revision": final_doc["revision_id"],
        "updated": [name for name, _ in changes],
        "source_as_of": "2026-08-30",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(json.loads(RECEIPT.read_text(encoding="utf-8")), ensure_ascii=False))


if __name__ == "__main__":
    main()

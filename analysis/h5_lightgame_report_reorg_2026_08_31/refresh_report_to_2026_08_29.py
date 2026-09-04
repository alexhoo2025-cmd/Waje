#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC_ID = "GyZddVm2powgFBxLwH0l18Qzguf"
RECEIPT = ROOT / "refresh_2026_08_29_receipt.json"

if RECEIPT.exists():
    raise SystemExit("receipt exists; refusing duplicate report refresh")


def call(args: list[str]) -> dict:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    result = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:])
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def replace(block_id: str, content: str) -> None:
    call(["docs", "+update", "--doc", DOC_ID, "--command", "block_replace", "--block-id", block_id, "--content", content])


def insert_after(block_id: str, content: str) -> dict:
    return call(["docs", "+update", "--doc", DOC_ID, "--command", "block_insert_after", "--block-id", block_id, "--content", content])


# Latest source status: retention through 8/29, GA4 behavior through 8/27.
replace(
    "doxlg7eXZeJ4M7pnF4OS0Y1odBd",
    "<p><b>数据范围：</b>历史留存为2026年6月16日—8月16日；GA4行为最新完整日为8月27日；新增留存最新完整日为8月29日。</p>",
)
replace(
    "doxlgbvBpMaOQDJ1nVZEyNh3zte",
    """
<callout emoji="⚠️" background-color="light-yellow" border-color="yellow">
  <p><b>数据截止差异：</b>新增留存已更新至8月29日；GA4游戏页面行为仍只到8月27日。8月30日尚未形成完整日数据，不补零、不以部分日代替完整日。</p>
</callout>
""",
)

replace(
    "doxlg3rlf7z6GbXTGeHsNFK1jnh",
    "<p>上线后累计从7月14日开始；以8月29日为观察日。D1截至8月28日、D3截至8月26日、D7截至8月22日、D15截至8月14日。</p>",
)
latest_table = """
<table>
  <thead><tr><th><p>渠道/运行形态</p></th><th><p>D1</p></th><th><p>D3</p></th><th><p>D7</p></th><th><p>D15</p></th></tr></thead>
  <tbody>
    <tr><td><p>H5自然</p></td><td><p>41.1%</p></td><td><p>24.3%</p></td><td><p>14.1%</p></td><td><p>6.8%</p></td></tr>
    <tr><td><p>H5 Facebook</p></td><td><p>26.9%</p></td><td><p>14.8%</p></td><td><p>6.5%</p></td><td><p>3.3%</p></td></tr>
    <tr><td><p>H5 Google</p></td><td><p>43.4%</p></td><td><p>26.8%</p></td><td><p>14.0%</p></td><td><p>7.6%</p></td></tr>
    <tr><td><p>PWA自然</p></td><td><p>43.2%</p></td><td><p>26.3%</p></td><td><p>11.4%</p></td><td><p>5.9%</p></td></tr>
  </tbody>
</table>
"""
replace("doxlg1gcGlaU5XcEQghZ6ejvoAd", latest_table)

# Latest daily cohort with D1/D3 fully observed at the new cutoff.
recent_table = """
<table>
  <thead><tr><th><p>8月26日注册批次</p></th><th><p>新增</p></th><th><p>D1</p></th><th><p>D3</p></th><th><p>D7</p></th><th><p>D15</p></th></tr></thead>
  <tbody>
    <tr><td><p>H5自然</p></td><td><p>3,284</p></td><td><p>48.7%</p></td><td><p>27.6%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
    <tr><td><p>H5 Facebook</p></td><td><p>4,818</p></td><td><p>27.0%</p></td><td><p>18.9%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
    <tr><td><p>H5 Google</p></td><td><p>1,111</p></td><td><p>42.7%</p></td><td><p>21.4%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
    <tr><td><p>PWA/PWW</p></td><td><p>595</p></td><td><p>45.2%</p></td><td><p>26.9%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
  </tbody>
</table>
"""
replace("doxlgvJwf96ialWx2DRhSYr1S4g", recent_table)

# Product/department update nodes, based on 新包 revision 1830.
events_xml = """
<h2>统计期间关键更新与干扰项</h2>
<table>
  <thead><tr><th><p>日期</p></th><th><p>节点</p></th><th><p>报告处理</p></th></tr></thead>
  <tbody>
    <tr><td><p>7/14</p></td><td><p>Limbo 9008上线</p></td><td><p>发布节点</p></td></tr>
    <tr><td><p>7/15—7/16</p></td><td><p>Limbo下线后于7/16 17:20恢复</p></td><td><p>单独标注，不与稳定期混算</p></td></tr>
    <tr><td><p>7/23</p></td><td><p>H5 2.1.14、Keno 9010、KYC功能同日上线</p></td><td><p>多项变更重叠，只做阶段观察</p></td></tr>
    <tr><td><p>7/29</p></td><td><p>ColorDice 9003上线</p></td><td><p>发布节点</p></td></tr>
    <tr><td><p>8/06</p></td><td><p>Opera渠道包自动归因上报</p></td><td><p>归因口径变更，不作产品效果</p></td></tr>
    <tr><td><p>8/21</p></td><td><p>Hilo 9011、Plinko 9016上线</p></td><td><p>当前仅观察短期页面与回访</p></td></tr>
    <tr><td><p>8/25</p></td><td><p>Tower 9013上线；Plinko最大扶持金额按整单计算</p></td><td><p>Tower D3未成熟；Plinko需排除规则变更的直接归因</p></td></tr>
    <tr><td><p>8/15—8/16</p></td><td><p>Facebook投放账户封禁</p></td><td><p>流量结构干扰，不作体验判断</p></td></tr>
  </tbody>
</table>
"""
insert_after("doxlgp7tu84wMxrt5JCn3G4ARvf", events_xml)

# Paid-vs-unpaid historical comparison, preserving the original current values.
paid_compare_xml = """
<h2>新增首充与新增未付费：与上线前对比</h2>
<table>
  <thead><tr><th><p>用户组</p></th><th><p>上线前注册当日有游戏</p></th><th><p>上线后注册当日有游戏</p></th><th><p>上线前7天有游戏</p></th><th><p>上线后7天有游戏</p></th></tr></thead>
  <tbody>
    <tr><td><p>当日新增首充</p></td><td><p>95.9%</p></td><td><p>94.5%</p></td><td><p>96.5%</p></td><td><p>95.4%</p></td></tr>
    <tr><td><p>当日新增未付费</p></td><td><p>40.7%</p></td><td><p>40.4%</p></td><td><p>42.3%</p></td><td><p>42.1%</p></td></tr>
  </tbody>
</table>
<p><b>解读：</b>上线后两组7天游戏参与均仅小幅下降：新增首充下降1.1个百分点，新增未付费下降0.2个百分点。首充与未付费之间约53个百分点的参与差距保持稳定，不能解释为轻量化上线导致首充用户普遍不玩游戏。</p>
"""
insert_after("doxlgvJwf96ialWx2DRhSYr1S4g", paid_compare_xml)
replace(
    "doxlgcaL3wj6EsHmX5Js9d4itIc",
    "<p><b>分群观察：</b>上线后当日新增首充用户7天内有任意游戏记录为95.4%，较上线前96.5%下降1.1个百分点；当日新增未付费为42.1%，较上线前42.3%下降0.2个百分点。该指标用于用户结构对照，不等同轻量化游戏参与率。</p>",
)

# Expand current game section to the product-defined Top Games nine and split the groups.
replace("doxlgIRH18Hpio4HpF2RfFlHSUb", "<h1>产品Top Games九款：页面触达与短期回访</h1>")
replace(
    "doxlgSi0nveQZIBmRILPxiqLr6c",
    """
<callout emoji="💡" background-color="light-blue" border-color="blue">
  <p><b>分组：</b>轻量化4款为CoinFlip、Limbo、Keno、ColorDice；非轻量化5款为Whot、Hilo、Plinko、Tower、Bottle spin。</p>
  <p><b>当前观察：</b>Top Games中Whot触达最大；轻量化4款里Keno触达最大、Limbo D1回访最高；非轻量化5款中Plinko D3回访较高。页面进入和应用回访只支持关联观察。</p>
</callout>
""",
)

top_games_table = """
<table>
  <thead><tr><th><p>分组</p></th><th><p>游戏/ID</p></th><th><p>新访客</p></th><th><p>D1回访</p></th><th><p>D3回访</p></th><th><p>观察状态</p></th></tr></thead>
  <tbody>
    <tr><td><p>非轻量化</p></td><td><p>Whot / 6001</p></td><td><p>1,109</p></td><td><p>30.7% (n=935)</p></td><td><p>14.0% (n=529)</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>Limbo / 9008</p></td><td><p>647</p></td><td><p>29.0% (n=544)</p></td><td><p>13.9% (n=316)</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>CoinFlip / 9001</p></td><td><p>425</p></td><td><p>31.6% (n=351)</p></td><td><p>17.6% (n=204)</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>Keno / 9010</p></td><td><p>270</p></td><td><p>36.4% (n=231)</p></td><td><p>13.6% (n=140)</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>ColorDice / 9003</p></td><td><p>413</p></td><td><p>25.2% (n=325)</p></td><td><p>15.7% (n=102)</p></td><td><p>可观察</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Hilo / 9011</p></td><td><p>184</p></td><td><p>34.4% (n=151)</p></td><td><p>16.7% (n=78)</p></td><td><p>小样本</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Plinko / 9016</p></td><td><p>365</p></td><td><p>31.3% (n=310)</p></td><td><p>17.3% (n=196)</p></td><td><p>可观察</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Tower / 9013</p></td><td><p>122</p></td><td><p>38.1% (n=84)</p></td><td><p>N/A</p></td><td><p>8/25上线，D3未成熟</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Bottle spin / 2003</p></td><td><p>709</p></td><td><p>31.4% (n=601)</p></td><td><p>11.0% (n=353)</p></td><td><p>可观察</p></td></tr>
  </tbody>
</table>
"""
replace("doxlgjSyPDBabZDdgXjcuCad1kf", top_games_table)
insert_after(
    "doxlg9TiGMeU8GoD4q4GTqTcmkb",
    '<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/07_产品TopGames九款_D1D3回访.png" width="880" caption="产品Top Games九款D1/D3应用回访；紫色标签为轻量化4款"/>',
)
replace(
    "doxlgex2XaqkiPjTFp6BaPNytsg",
    "<p><b>解读：</b>Top Games是产品固定分组，不等于流量排名。轻量化4款的D1范围为25.2%—36.4%，D3范围为13.6%—17.6%；非轻量化5款中Tower仅有D1样本、Hilo属于小样本。当前不能据此判断轻量化整体优于或弱于非轻量化游戏。</p>",
)

readback = call(["docs", "+fetch", "--doc", DOC_ID, "--scope", "keyword", "--keyword", "新增留存最新完整日为8月29日|统计期间关键更新与干扰项|新增首充与新增未付费：与上线前对比|产品Top Games九款：页面触达与短期回访|轻量化4款", "--detail", "with-ids", "--format", "json"])
receipt = {
    "status": "ok",
    "revision_id": readback["data"]["document"]["revision_id"],
    "retention_cutoff": "2026-08-29",
    "ga4_cutoff": "2026-08-27",
    "source_revisions": {"new_user_sheet": 732, "update_records": 1830},
    "readback": readback["data"]["document"]["content"],
}
RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "ok", "revision_id": receipt["revision_id"]}, ensure_ascii=False))

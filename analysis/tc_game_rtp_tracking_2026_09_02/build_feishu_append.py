#!/usr/bin/env python3
"""Build the precise append-only Feishu XML for the V2 RTP tracking section."""
from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "report_data.json").read_text(encoding="utf-8"))
OUT = ROOT / "feishu_append.xml"


def pct(value, digits=2):
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def pp(value, digits=2):
    return "N/A" if value is None else f"{value:+.{digits}f}pp"


def amount(value):
    if value is None:
        return "N/A"
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:.2f}亿"
    if abs(value) >= 10_000:
        return f"{value / 10_000:.2f}万"
    return f"{value:,.0f}"


def table(headers, rows):
    heads = "".join(f'<th background-color="light-gray"><p>{html.escape(h)}</p></th>' for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td><p>{html.escape(str(cell))}</p></td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table>"


overall = DATA["overall_7d"]
new_games = DATA["new_games"]
all_games = DATA["all_games_7d"]

status_map = {
    "Hilo": "持续观察：实际低于预期2.00pp",
    "Plinko": "持续观察：实际高于预期0.95pp",
    "Tower": "数据不足：仅6个完整自然日",
}

new_rows = []
for name in ("Hilo", "Plinko", "Tower"):
    g = new_games[name]
    new_rows.append([
        name,
        g["game_id"],
        f'{g["launch"][5:]}—08/30',
        f'{g["days"]}天',
        amount(g["complete_bet"]),
        pct(g["actual_rtp"]),
        pct(g["expected_rtp"]),
        pp(g["rtp_gap_pp"]),
        amount(g["profit_vs_expected"]),
        pp(g["adjustment_pp"]),
        status_map[name],
    ])

all_rows = []
for g in all_games:
    available = "可比" if g["rtp_gap_pp"] is not None else "N/A·预期缺失"
    all_rows.append([
        g["game"], amount(g["complete_bet"]), pct(g["actual_rtp"]),
        pct(g["expected_rtp"]), pp(g["rtp_gap_pp"]), pct(g["expected_coverage"]),
        pp(g["adjustment_pp"]), available,
    ])

xml = f'''<h1>持续追踪：全游戏与新上线游戏RTP（截至2026年8月30日）</h1>
<callout emoji="📌" background-color="light-blue" border-color="blue"><p><b>与8月28日TC审计的关系：</b>前文为历史TC快照；本节新增生命周期池V2（Joint）修订1583的全游戏回报与下注追踪。两类数据用于交叉排查，不反向改写历史TC判断。</p><p><b>统一命名：</b>以下“RTP”均指<b>生命周期池完全实际回报比（RTP观察值）</b>，并非已经完成最终结算、退款、免费注和配置版本核验的正式RTP审计。</p></callout>
<h2>近7日全游戏：下注规模与回报偏离</h2>
<p><b>全盘观察：</b>2026年8月24—30日完全下注额为<b>{amount(overall["complete_bet"])}</b>，完全实际回报比为<b>{pct(overall["actual_rtp"])}</b>。预期回报字段仅覆盖<b>{pct(overall["expected_coverage"])}</b>的下注额；在可比范围内，完全实际回报比为{pct(overall["actual_rtp_expected_subset"])}，较完全预期回报比{pct(overall["expected_rtp"])}低{abs(overall["rtp_gap_pp"]):.2f}个百分点。</p>
<img path="@./analysis/tc_game_rtp_tracking_2026_09_02/assets/02_近7日全游戏回报偏离与下注规模.png" caption="近7日全游戏：RTP偏离与完全下注规模"/>
{table(["游戏", "完全下注额", "完全实际回报比", "完全预期回报比", "RTP差异", "预期覆盖", "调整影响", "可比状态"], all_rows)}
<h2>Hilo、Plinko、Tower：上线后专项</h2>
<callout emoji="🔎" background-color="light-yellow" border-color="yellow"><p><b>优先结论：</b>Hilo上线后10日完全实际回报比低于预期<b>2.00个百分点</b>；Plinko高于预期<b>0.95个百分点</b>；Tower高于预期<b>1.58个百分点</b>，但仅6日样本。三者均未达到“高RTP、高调整影响、高下注额”同时出现的优先TC解释门槛，当前只列为持续观察或数据不足。</p></callout>
{table(["游戏", "Game ID", "统计期间", "完整日", "完全下注额", "完全实际回报比", "完全预期回报比", "RTP差异", "实际减预期盈利", "调整影响", "状态"], new_rows)}
<img path="@./analysis/tc_game_rtp_tracking_2026_09_02/assets/01_新游戏逐日实际与预期回报比.png" caption="新上线游戏逐日完全实际/预期回报比"/>
<img path="@./analysis/tc_game_rtp_tracking_2026_09_02/assets/03_新游戏生命周期回报偏离.png" caption="新上线游戏生命周期1—4的RTP偏离"/>
<h2>与TC的关系与下一步核查</h2>
<p>RTP与TC存在关联，但不是线性关系：玩家的历史余额、大奖分布、提现节奏、Bonus、资产转换、退款和跨日结算都会改变TC。因此，单款游戏的短期回报偏离不能直接解释全站TC。只有<b>高回报、调整影响明显、下注规模足够大</b>三项同时出现时，才升级为优先核查对象。</p>
<ol><li><b>P0：</b>补齐游戏×配置版本×有效局数×最终派奖×取消/退款×免费注/Bonus聚合事实，验证生命周期池观察值与最终结算一致。</li><li><b>P0：</b>为Hilo补充猜测、Skip、Cash Out、赔率分布；为Plinko补充难度、ROW、球数、倍率分布；为Tower补充层数、提现/失败、倍率与封顶触发。</li><li><b>P1：</b>Tower累计满7个完整自然日后，与Hilo、Plinko按相同上线年龄复测；同时按生命周期和配置版本定位偏离。</li></ol>
<h2>口径与数据边界</h2>
<p><b>来源：</b>GM Lifecycle Pool V2（Joint）飞书工作簿修订1583；生命周期奖池分游戏汇总与生命周期明细。全游戏窗口为8月24—30日；Hilo/Plinko为8月21—30日；Tower为8月25—30日。</p><p>预期回报比为0、Infinity、缺失或无有效下注的记录，保留在下注规模中，但不进入实际与预期RTP偏离比较，统一标记“<b>N/A·预期缺失</b>”。当前缺少有效局数、最终结算、取消/退款、免费注/Bonus、配置版本和用户级大奖分布，因此本节不输出故障结论或用户明细。</p>'''

OUT.write_text(xml, encoding="utf-8")
print(OUT)

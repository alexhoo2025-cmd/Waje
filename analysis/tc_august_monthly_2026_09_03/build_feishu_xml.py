#!/usr/bin/env python3
"""Create native Feishu XML for the already-created independent monthly report."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def esc(value) -> str:
    return html.escape("N/A" if value is None else str(value), quote=False)


def money(value):
    if value is None:
        return "N/A"
    sign = "-" if value < 0 else ""
    v = abs(value)
    if v >= 100_000_000:
        return f"{sign}{v / 100_000_000:.2f}亿"
    if v >= 10_000:
        return f"{sign}{v / 10_000:.2f}万"
    return f"{value:,.0f}"


def pct(value):
    return "N/A" if value is None else f"{value * 100:.2f}%"


def pp(value):
    return "N/A" if value is None else f"{value * 100:+.2f}个百分点"


def p(value) -> str:
    return f"<p>{esc(value)}</p>"


def table(headers, rows, widths=None, cell_backgrounds=None) -> str:
    colgroup = ""
    if widths:
        colgroup = "<colgroup>" + "".join(f'<col width="{w}"/>' for w in widths) + "</colgroup>"
    head = "<thead><tr>" + "".join(f"<th><p>{esc(h)}</p></th>" for h in headers) + "</tr></thead>"
    body_rows = []
    for row_index, row in enumerate(rows):
        backgrounds = cell_backgrounds[row_index] if cell_backgrounds and row_index < len(cell_backgrounds) else []
        cells = []
        for col_index, value in enumerate(row):
            background = backgrounds[col_index] if col_index < len(backgrounds) else None
            attr = f' background-color="{background}"' if background else ""
            cells.append(f"<td{attr}><p>{esc(value)}</p></td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    body = "<tbody>" + "".join(body_rows) + "</tbody>"
    return f"<table>{colgroup}{head}{body}</table>"


def deviation_background(value) -> str | None:
    if value is None or abs(value) < 0.0005:
        return None
    magnitude = abs(value)
    if value > 0:
        return "light-green"
    return "light-red"


def row_deviation_background(value) -> str | None:
    if value is None or abs(value) < 0.01:
        return None
    return "light-green" if value > 0 else "light-red"


def tc_background(value) -> str | None:
    if value is None or abs(value) < 0.0005:
        return None
    return "light-green" if value > 0 else "light-red"


def detail_row_background(row) -> list[str | None]:
    row_background = row_deviation_background(row.get("average_gap"))
    styles = [row_background] * 9
    config_background = deviation_background(row.get("rtp_gap"))
    if config_background:
        styles[8] = config_background
    return styles


def main() -> None:
    weekly = json.loads((OUT / "weekly_overview.json").read_text(encoding="utf-8"))
    monthly = json.loads((OUT / "monthly_overview.json").read_text(encoding="utf-8"))
    life = json.loads((OUT / "lifecycle_summary.json").read_text(encoding="utf-8"))
    games = json.loads((OUT / "game_summary.json").read_text(encoding="utf-8"))
    distribution = json.loads((OUT / "distribution_analysis.json").read_text(encoding="utf-8"))
    detail = json.loads((OUT / "display_detail_lifecycle_3_4_50.json").read_text(encoding="utf-8"))
    full_detail = json.loads((OUT / "monthly_detail_124.json").read_text(encoding="utf-8"))
    hidden_detail_count = len([row for row in full_detail if row["lifecycle"] in (3, 4)]) - len(detail)
    tc = json.loads((OUT / "tc_daily.json").read_text(encoding="utf-8"))["rows"]
    new_user = json.loads((OUT / "new_user_context.json").read_text(encoding="utf-8"))
    quality = json.loads((OUT / "quality_checks.json").read_text(encoding="utf-8"))

    weekly_rows = [[
        row["label"],
        f"{row['observed_days']}/{row['expected_days']}",
        str(row["observed_game_count"]),
        money(row["full_bet"]),
        money(row["daily_average_bet"]),
        pct(row["actual_rtp"]),
        pct(row["tc"]),
        pct(row["config_coverage"]),
        "实际聚合｜已核对" if row["tc_data_state"] == "actual_aggregate_verified_overlap" else row["tc_data_state"],
    ] for row in weekly]
    life_rows = [[
        f"生命周期{row['lifecycle']}", money(row["full_bet"]), money(row["actual_profit"]),
        pct(row["actual_rtp"]), pct(row["expected_rtp"]), pct(row["config_coverage"]), pp(row["rtp_gap"]),
    ] for row in life]
    game_rows = [[
        row["game"], money(row["full_bet"]), pct(row["bet_share"]), money(row["actual_profit"]), pct(row["profit_share"]), pp(row["profit_bet_share_gap"]), pct(row["actual_rtp"]), pct(row["expected_rtp"]),
        pct(row["config_coverage"]), pp(row["rtp_gap"]), str(row["active_days"]),
    ] for row in games[:15]]
    game_backgrounds = [[deviation_background(row["rtp_gap"]), None, None, None, None, deviation_background(row["profit_bet_share_gap"]), None, None, None, deviation_background(row["rtp_gap"]), None] for row in games[:15]]
    sorted_detail = sorted(detail, key=lambda x: (x["game"].lower(), x["lifecycle"]))
    detail_rows = [[
        row["game"], f"生命周期{row['lifecycle']}", money(row["full_bet"]), pct(row["actual_rtp"]),
        pct(row["lifecycle_average_rtp"]), pp(row["average_gap"]), row["average_status"],
        pct(row["expected_rtp"]), pp(row["rtp_gap"]),
    ] for row in sorted_detail]
    detail_backgrounds = [detail_row_background(row) for row in sorted_detail]
    tc_rows = [[r["business_date"], money(r["success_recharge_amount"]), money(r["success_withdraw_amount"]), pct(r["tc_rate"]), pp(r.get("baseline_delta")), r.get("baseline_status")] for r in tc]
    tc_backgrounds = [[tc_background(r.get("baseline_delta"))] * 6 for r in tc]
    new_rows = [[
        r["segment"], str(r["accepted_days"]), f"{r['new_users']:,.0f}", f"{r['new_payers']:,.0f}",
        pct(r["new_pay_rate"]), pct(r["d1_retention"]), pct(r["d3_retention"]), pct(r["d7_retention"]),
    ] for r in new_user.get("rows", [])]
    context_average = new_user.get("weighted_average", {})
    new_backgrounds = []
    for row in new_user.get("rows", []):
        deltas = []
        for key in ("new_pay_rate", "d1_retention", "d3_retention", "d7_retention"):
            value = row.get(key)
            average = context_average.get(key)
            if value is not None and average is not None:
                deltas.append(value - average)
        row_background = "light-red" if any(delta <= -0.05 for delta in deltas) else ("light-blue" if any(delta >= 0.05 for delta in deltas) else None)
        styles = [row_background] * 8
        for key in ("new_pay_rate", "d1_retention", "d3_retention", "d7_retention"):
            value = row.get(key)
            average = context_average.get(key)
            if value is not None and average is not None and value - average >= 0.05:
                styles[4 + ("new_pay_rate", "d1_retention", "d3_retention", "d7_retention").index(key)] = "light-blue"
            elif value is not None and average is not None and value - average <= -0.05:
                styles[4 + ("new_pay_rate", "d1_retention", "d3_retention", "d7_retention").index(key)] = "light-red"
        new_backgrounds.append(styles)
    new_user_table_xml = table(["包体/渠道", "成熟日期数", "新增人数", "新增付费人数", "新增付费率", "次日留存", "3日留存", "7日留存"], new_rows, [210, 100, 120, 140, 110, 100, 100, 100], new_backgrounds)
    if new_user.get("rows"):
        highest_context = max(new_user["rows"], key=lambda r: r.get("new_pay_rate") or -1)
        lowest_context = min(new_user["rows"], key=lambda r: r.get("new_pay_rate") if r.get("new_pay_rate") is not None else 999)
        context_analysis_xml = (
            f"<callout emoji=\"📌\" background-color=\"light-blue\" border-color=\"blue\"><p><b>总体加权平均：</b>新增付费率 {esc(pct(context_average.get('new_pay_rate')))}；"
            f"次日留存 {esc(pct(context_average.get('d1_retention')))}；3日留存 {esc(pct(context_average.get('d3_retention')))}；7日留存 {esc(pct(context_average.get('d7_retention')))}。"
            "高亮规则：相对对应加权平均值偏离至少5个百分点的包体/渠道整行突出显示；蓝色为高于平均，红色为低于平均，单项指标保留更强颜色。</p></callout>"
            f"<p><b>简要分析：</b>{esc(highest_context['segment'])}在新增付费率和留存指标上整体高于平均，{esc(lowest_context['segment'])}整体低于平均。"
            "这说明包体/渠道对应的用户结构或投放质量存在差异，仍需结合归因链路、样本成熟度和上报完整性核查，不能仅凭本表判定因果。</p>"
        )
    else:
        context_analysis_xml = "<p>当前没有可用于比较的成熟包体/渠道数据。</p>"
    game_table_xml = table(["游戏", "完全下注额", "下注额占比", "实际盈利", "盈利占比", "盈利占比−下注额占比", "实际RTP", "配置预期RTP", "配置覆盖率", "实际-预期", "有效日期"], game_rows, [150, 135, 105, 135, 105, 145, 100, 120, 120, 100, 80], game_backgrounds)
    game_by_name = {row["game"]: row for row in games}
    easywin = game_by_name.get("EasyWin")
    distribution_note_xml = (
        f"<callout emoji=\"📈\" background-color=\"light-green\" border-color=\"green\"><p><b>分布汇总与推荐策略：</b>下注额前5款合计占 {esc(pct(distribution['top5_bet_share']))}，前8款合计占 {esc(pct(distribution['top8_bet_share']))}；盈利贡献前5款合计占 {esc(pct(distribution['top5_profit_share']))}，月度结果集中在少数游戏。"
        f"Whot下注额占比 {esc(pct(game_by_name['Whot']['bet_share']))}、盈利占比 {esc(pct(game_by_name['Whot']['profit_share']))}、实际RTP {esc(pct(game_by_name['Whot']['actual_rtp']))}；OMG下注额占比 {esc(pct(game_by_name['OMG']['bet_share']))}、盈利占比 {esc(pct(game_by_name['OMG']['profit_share']))}、实际RTP {esc(pct(game_by_name['OMG']['actual_rtp']))}。"
        f"建议：高规模游戏作为主推荐池但不只按盈利排序；Whot、OMG进入风险观察池，先核查留存、体验、退出/放弃和业务成功率；EasyWin实际RTP {esc(pct(easywin['actual_rtp']))}但下注额占比仅 {esc(pct(easywin['bet_share']))}，只做小流量测试；第三方游戏不用配置偏离直接决定推荐。</p></callout>"
    )
    package_split_note_xml = (
        "<callout emoji=\"🧩\" background-color=\"light-blue\" border-color=\"blue\"><p><b>后续包体拆分：</b>本期为全产品汇总，生命周期源快照没有平台/包体字段，不能反推 Android 或 H5。后续需按 platform × package_name × version × game × lifecycle 分层，并增加平台、包体、版本、下注额/盈利及包体内与全产品占比栏位；包体分层合计必须与全产品对账，缺少字段时显示待补字段。</p></callout>"
    )
    tc_table_xml = table(["业务日", "成功充值金额", "成功提现金额", "TC比", "偏离月度基线", "偏离状态"], tc_rows, [160, 180, 180, 100, 120, 100], tc_backgrounds)
    detail_table_xml = table(["游戏", "生命周期", "下注额", "实际RTP", "该生命周期平均RTP", "偏离平均", "偏离状态", "配置预期RTP", "实际-预期"], detail_rows, [150, 100, 120, 120, 140, 120, 100, 120, 120], detail_backgrounds)
    valid_detail = [row for row in detail if row.get("average_gap") is not None]
    largest_detail_outlier = max(valid_detail, key=lambda row: abs(row["average_gap"])) if valid_detail else None
    negative_detail_impact = sorted([row for row in valid_detail if row["average_gap"] < 0], key=lambda row: row["full_bet"] * abs(row["average_gap"]), reverse=True)
    if valid_detail:
        life3 = next((row["lifecycle_average_rtp"] for row in valid_detail if row["lifecycle"] == 3), None)
        life4 = next((row["lifecycle_average_rtp"] for row in valid_detail if row["lifecycle"] == 4), None)
        impact_refs = "、".join(f"{row['game']}-生命周期{row['lifecycle']}（{pp(row['average_gap'])}，下注{money(row['full_bet'])}）" for row in negative_detail_impact[:2])
        detail_analysis_xml = (
            f"<callout emoji=\"📊\" background-color=\"light-blue\" border-color=\"blue\"><p><b>明细简析：</b>生命周期3加权平均RTP为 {esc(pct(life3))}，生命周期4为 {esc(pct(life4))}。"
            f"绝对偏离最大的项目是 {esc(largest_detail_outlier['game'])}-生命周期{largest_detail_outlier['lifecycle']}（{esc(pp(largest_detail_outlier['average_gap']))}），需结合下注规模判断。"
            f"按偏离幅度与下注规模共同看，优先关注 {esc(impact_refs)}；高亮仅表示相对同生命周期平均值偏离，不代表因果或系统故障。</p></callout>"
        )
    else:
        detail_analysis_xml = "<p>当前没有可用于计算生命周期平均的有效RTP行。</p>"
    scope_table_xml = table(["项目", "口径"], [
        ["生命周期数据", "GM Lifecycle Pool V2（Joint）日级导出；核心统计使用生命周期1—4"],
        ["RTP", "1 − SUM(完全实际盈利) ÷ SUM(完全下注额)；按累计金额加权"],
        ["下注额占比", "单款游戏生命周期1—4完全下注额 ÷ 月度生命周期1—4完全下注总额；仅表示下注规模"],
        ["实际盈利", "完全实际盈利字段按游戏汇总；月度合计为生命周期1—4完全实际盈利求和"],
        ["盈利占比", "单款游戏完全实际盈利 ÷ 月度完全实际盈利总额"],
        ["分布差异", "盈利占比 − 下注额占比；用于识别规模与盈利贡献不一致的游戏"],
        ["配置预期RTP", "自研或有有效配置的游戏采用有效来源预期回报比；Tada、OMG、PP等第三方游戏不适用该口径，显示N/A不代表数据缺失"],
        ["配置覆盖率", "有有效预期RTP配置的下注额 ÷ 生命周期1—4完全下注总额；第三方游戏不纳入分子，不作为缺失判断"],
        ["TC比", "成功提现金额 ÷ 成功充值金额；充值 type=1,status=3；提现 type=2,status=103"],
        ["展示清理", "只删除整列全部为0或空白的字段；保留N/A、待补数据和局部0"],
    ], [180, 640])

    image_path = lambda name: f"<img path=\"@./analysis/tc_august_monthly_2026_09_03/assets/{name}\"/>"
    xml = f"""<h1 seq="auto">月度结论</h1>
<p>统计周期：2026-08-01—2026-08-31；业务时区：Asia/Hong_Kong；数据状态：实际聚合。</p>
<callout emoji="✅" background-color="light-green" border-color="green"><p><b>结论先行：</b>生命周期1—4累计完全下注额为 {esc(money(monthly['full_bet']))}，实际RTP为 {esc(pct(monthly['actual_rtp']))}；TC查询返回 {len(tc)}/31 个业务日，并通过 8/19—8/31 与本地快照的金额重叠核对。TaDa（源数据名 Tada）与PP合计下注额为 {esc(money(monthly['third_party_tada_pp']['combined_bet']))}，占月度总下注额 {esc(pct(monthly['third_party_tada_pp']['combined_share']))}。月度游戏×生命周期明细共124行，最后详细区展示有有效下注的生命周期3/4共{len(detail)}行；无有效数据的{hidden_detail_count}行隐藏。</p></callout>

<h1 seq="auto">统计范围与口径</h1>
{scope_table_xml}

<h1 seq="auto">四周整体对比</h1>
<p>四个周期按 7/7/7/10 天划分。第4周期为月末10天，横向比较时同时查看日均下注额。</p>
{table(["周期", "有效日期", "游戏数", "下注额", "日均下注额", "实际RTP", "TC比", "配置覆盖率", "状态"], weekly_rows, [210, 90, 80, 120, 120, 100, 90, 110, 160])}
<callout emoji="ℹ️" background-color="light-blue" border-color="blue"><p><b>配置覆盖率说明：</b>有效预期RTP配置对应的完全下注额 ÷ 生命周期1—4的完全下注总额。它只表示有多少下注额可以进行实际RTP与配置预期RTP对比，不代表游戏数覆盖率或实际RTP表现。第三方游戏不提供可比的预期RTP，该情况属于口径不适用，不是数据缺失；真正的配置异常另行核验。</p></callout>
{image_path('01_四周TC与生命周期RTP.png')}

<h1 seq="auto">生命周期1—4回报结构</h1>
{table(["生命周期", "完全下注额", "实际盈利", "实际RTP", "配置预期RTP", "配置覆盖率", "实际-预期"], life_rows, [120, 140, 140, 100, 120, 120, 130])}
<p>Tada、OMG、PP等第三方游戏没有可比的预期RTP，表中显示N/A表示口径不适用，不是数据缺失。</p>
<p>图表采用组合展示：柱状图表示完全下注额，折线表示实际RTP；配置预期RTP以虚线作为对照。左右坐标轴分别表示金额和百分比。</p>
{image_path('02_生命周期RTP与下注额.png')}

<h1 seq="auto">分游戏回报与生命周期深钻</h1>
<p>以下先按生命周期1—4完全下注额列出主要游戏。下注额占比 = 单款游戏生命周期1—4完全下注额 ÷ 月度生命周期1—4完全下注总额。游戏组合图采用柱状图表示各游戏完全下注额、折线表示实际RTP；柱顶标注下注额和月度下注额占比，折线点标注实际RTP。TaDa（源数据名 Tada）下注额为 {esc(money(monthly['third_party_tada_pp']['tada_bet']))}，占 {esc(pct(monthly['third_party_tada_pp']['tada_share']))}；PP下注额为 {esc(money(monthly['third_party_tada_pp']['pp_bet']))}，占 {esc(pct(monthly['third_party_tada_pp']['pp_share']))}；两者合计占 {esc(pct(monthly['third_party_tada_pp']['combined_share']))}。配置预期RTP和偏离程度在表格中查看。偏离值按正负使用不同色调：绿色系表示正偏离，红色系表示负偏离；非零偏离从浅色开始，绝对偏离达到约0.5、1、2、5个百分点时颜色逐级加深。热力图中的游戏名称和对应格子也按同生命周期平均RTP的偏离程度同步高亮。只有配置有效的项目参与实际-预期判断。小额游戏的极端比例不直接判定为经营问题。</p>
{game_table_xml}
{distribution_note_xml}
{package_split_note_xml}
{image_path('03_主要游戏下注规模.png')}
{image_path('04_生命周期3与4RTP热力图.png')}
{image_path('06_主要游戏盈利贡献.png')}

<h1 seq="auto">TC日级核验</h1>
<p>Metabase查询返回31个日期。报告中的TC以金额重新计算，不直接使用页面显示的两位小数。</p>
<p>日级基线为8月加权TC比；偏离值按正负使用不同色调，绿色表示高于基线，红色表示低于基线，绝对偏离越大颜色越深，仅表示优先核查，不代表归因结论。</p>
{tc_table_xml}
{image_path('05_每日TC趋势.png')}

<h1 seq="auto">新增用户付费背景</h1>
<p>成熟背景数据覆盖 2026-08-06—2026-08-30；8/1—8/5及8/31不纳入成熟留存结论。该来源没有游戏维度，只作为包体/渠道背景。</p>
{new_user_table_xml}
{context_analysis_xml}

<h1 seq="auto">数据限制与行动建议</h1>
<callout emoji="⚠️" background-color="light-yellow" border-color="orange"><p><b>需要注意：</b>第三方游戏没有可比的预期RTP，显示N/A属于口径不适用，不是数据缺失；实际-预期对比只适用于有有效配置的项目。</p></callout>
<ol><li>TC后续如出现重叠日期差异，先核对时间范围、金额单位和状态映射。</li></ol>

<h1 seq="auto">全部游戏 × 生命周期1—4明细</h1>
<p>正文展示有有效下注的生命周期3/4，共{len(detail)}行；无有效数据的{hidden_detail_count}行隐藏；完整124行保存在本地分析快照。</p>
{detail_analysis_xml}
{detail_table_xml}

<h1 seq="auto">来源与回执</h1>
<p>生命周期：本地 GM Lifecycle Pool V2（Joint）8月1—31日原始快照；TC：Metabase 只读聚合查询；新增用户背景：Origin BQ新增付费用户分析成熟日期快照。</p>
<p>本地审计目录：analysis/tc_august_monthly_2026_09_03/。所有输出为聚合数据，不含用户、订单明细、支付账户、设备唯一标识或凭据。</p>"""
    (OUT / "feishu_append.xml").write_text(xml, encoding="utf-8")
    (OUT / "feishu_game_table.xml").write_text(game_table_xml, encoding="utf-8")
    (OUT / "feishu_tc_table.xml").write_text(tc_table_xml, encoding="utf-8")
    (OUT / "feishu_detail_table.xml").write_text(detail_table_xml, encoding="utf-8")
    (OUT / "feishu_new_user_table.xml").write_text(new_user_table_xml, encoding="utf-8")
    (OUT / "feishu_scope_table.xml").write_text(scope_table_xml, encoding="utf-8")
    print(OUT / "feishu_append.xml")


if __name__ == "__main__":
    main()

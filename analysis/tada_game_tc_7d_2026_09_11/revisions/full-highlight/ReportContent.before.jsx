import React from "react";
import {
  DataComponent, DataTable, EvidenceChart, MetricCard, ReportSection, RichNarrative, useDataApp,
} from "../../data-app-public.jsx";

const nf = new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 0 });
const pct = (v, d = 2) => v == null ? "N/A" : `${(v * 100).toFixed(d)}%`;
const pp = (v, d = 2) => v == null ? "N/A" : `${v >= 0 ? "+" : ""}${v.toFixed(d)}个百分点`;
const change = (v, d = 2) => v == null ? "N/A" : `${v >= 0 ? "+" : ""}${(v * 100).toFixed(d)}%`;
const amount = (v) => {
  if (v == null) return "N/A";
  const sign = v < 0 ? "-" : "", x = Math.abs(v);
  if (x >= 1e8) return `${sign}${(x / 1e8).toFixed(2)}亿`;
  if (x >= 1e4) return `${sign}${(x / 1e4).toFixed(2)}万`;
  return `${sign}${x.toLocaleString("zh-CN", { maximumFractionDigits: 2 })}`;
};
const tone = (v) => !Number.isFinite(v) || v === 0 ? "neutral" : v > 0 ? "negative" : "positive";

function EvidenceTable({ id, title, queryId, rows, displayRows, columns, caption, searchable = false }) {
  return <DataComponent id={id} title={title} queryId={queryId} kind="table"
    displayRows={displayRows} sourceRows={rows} description={caption}>
    <DataTable rows={displayRows} columns={columns} caption={caption} searchable={searchable} />
  </DataComponent>;
}

export function ReportContent() {
  const { snapshot, reviewedRows, appTitle, canEdit, mode, setAppTitle } = useDataApp();
  const daily = reviewedRows("daily_overview", ["date"]);
  const games = reviewedRows("game_summary");
  const drivers = reviewedRows("rtp_drivers");
  const heatmap = reviewedRows("heatmap", ["date"]);
  const reconciliation = reviewedRows("reconciliation", ["date"]);
  const A = snapshot.analysis ?? {}, overall = A.overall ?? {}, corr = A.correlation ?? {};
  const move = A.sep10_change_vs_prior5 ?? {}, decomp = A.rtp_decomposition ?? {};
  const complete = daily.filter((r) => r.period_status === "完整日"), sep10 = complete.at(-1), prior = complete.slice(0, -1);
  const avg = (field) => prior.reduce((sum, row) => sum + row[field], 0) / prior.length;
  const priorTc = prior.reduce((sum, row) => sum + row.withdraw, 0) / prior.reduce((sum, row) => sum + row.recharge, 0);
  const topDriver = drivers[0], x7 = drivers.find((row) => row.game === "680_X7 HOT");
  const driverRows = [...drivers.slice(0, 8), ...[...drivers].sort((a, b) => a.excess_payout - b.excess_payout).slice(0, 5)]
    .filter((row, index, rows) => rows.findIndex((item) => item.game === row.game) === index)
    .sort((a, b) => b.excess_payout - a.excess_payout)
    .map((row) => ({
      game: row.game,
      "相对基线多／少派奖（万）": row.excess_payout / 1e4,
      impactType: row.excess_payout > 0 ? "多派奖（需复核）" : "少派奖（抵消）",
    }));
  const moneyRows = [
    { period: "9月5—9日日均", "成功充值（亿）": avg("recharge") / 1e8, "成功提现（亿）": avg("withdraw") / 1e8 },
    { period: "9月10日", "成功充值（亿）": sep10?.recharge / 1e8, "成功提现（亿）": sep10?.withdraw / 1e8 },
  ];
  const rateRows = daily.map((row) => ({
    date: row.date, "游戏加权RTP（%）": row.rtp * 100, "Tada参与用户TC（%）": row.tc_rate * 100,
    partial_note: row.partial_note,
  }));
  const heatRows = heatmap.map((row) => ({
    date: row.date, game: row.game, "RTP（%）": row.rtp * 100, bet: row.bet,
    netWin: row.net_win, status: row.partial_day ? "部分日" : "完整日",
  }));
  const driverTable = drivers.slice(0, 12).map((row, index) => ({
    排名: index + 1, 游戏: row.game, "9月10日RTP": row.sep10_rtp, "前5日RTP": row.baseline_rtp,
    RTP变化: row.rtp_change_pp, 相对基线多派奖: amount(row.excess_payout),
    当日下注: amount(row.sep10_bet), 当日平台净盈利: amount(row.sep10_net_win),
  }));
  const moneyTable = [
    { 对比: "9月5—9日日均", 成功充值: amount(avg("recharge")), 成功提现: amount(avg("withdraw")), TC: priorTc },
    { 对比: "9月10日", 成功充值: amount(sep10?.recharge), 成功提现: amount(sep10?.withdraw), TC: sep10?.tc_rate },
    { 对比: "变化", 成功充值: change(move.recharge_change), 成功提现: change(move.withdraw_change), TC变化: move.tc_change_pp },
  ];
  const reconTable = reconciliation.map((row) => ({
    日期: row.date, Currency下注: amount(row.vendor_bet), Lifecycle下注: amount(row.lifecycle_bet),
    下注差异: row.bet_difference_pct, Currency盈利: amount(row.vendor_profit),
    Lifecycle盈利: amount(row.lifecycle_profit), 盈利差异: row.profit_difference_pct,
  }));
  const gameTable = [...games].sort((a, b) => b.bet - a.bet).map((row) => ({
    排名: row.bet_rank, 游戏: row.game, 类型: row.game_type, 下注额: amount(row.bet),
    下注份额: row.bet_share, 派奖额: amount(row.win), 平台净盈利: amount(row.net_win),
    玩家净赢: amount(row.player_net_gain), 加权RTP: row.rtp, 局数: row.total_count,
  }));

  return <article className="report-content" aria-label="Tada TC异常与游戏RTP拆解">
    <header className="report-hero">
      <h1 data-data-app-title contentEditable={canEdit && mode === "edit"} suppressContentEditableWarning
        onBlur={canEdit && mode === "edit" ? (event) => setAppTitle(event.currentTarget.textContent.trim() || appTitle) : undefined}>{appTitle}</h1>
      <RichNarrative id="report:description" className="report-deck" label="编辑报告说明"
        value="核心观察日：2026年9月10日｜对比：9月5—9日｜9月11日仅作部分日观察" />
    </header>

    <ReportSection id="summary" title="执行摘要" queryId="tc_daily"
      queryIds={["tc_daily", "rtp_drivers"]} sourceRowsByQuery={{ tc_daily: daily, rtp_drivers: drivers }}
      showHeading={false} className="report-summary">
      <RichNarrative id="summary:body" className="report-summary-lead" label="编辑执行摘要" value={`## 执行摘要

- **TC异常的直接原因是提现增长快于充值。** 9月10日Tada参与用户提现较前5日日均增加 **${pct(move.withdraw_change)}**，充值增加 **${pct(move.recharge_change)}**，TC升至 **${pct(sep10?.tc_rate)}**，提高 **${Math.abs(move.tc_change_pp).toFixed(2)}个百分点**。
- **游戏侧RTP异常集中于3 Lucky Chong Tian Pao。** Tada加权RTP提高 **${Math.abs(decomp.total_change_pp).toFixed(2)}个百分点**；其中 **${pct(decomp.within_game_effect_share, 1)}** 来自同款游戏RTP变化。3 Lucky Chong Tian Pao相对自身基线多派奖 **${amount(topDriver?.excess_payout)}**，是最大贡献项。
- **该游戏是首要排查对象，但不能认定为TC异常的唯一原因。** 游戏侧净多派奖 **${amount(decomp.net_excess_payout)}**，仅相当于提现增量的 **${pct(decomp.net_excess_vs_withdraw_increase, 1)}**；资金记录也未绑定具体子游戏。`} />
    </ReportSection>

    <div className="report-facts" aria-label="核心数据">
      <MetricCard id="metric-tc" title="9月10日TC" queryId="tc_daily" sourceRows={daily}
        value={pct(sep10?.tc_rate)} comparison={pp(move.tc_change_pp)} deltaTone="negative" description="较9月5—9日加权水平" />
      <MetricCard id="metric-withdraw" title="提现变化" queryId="tc_daily" sourceRows={daily}
        value={change(move.withdraw_change)} comparison={`增加${amount(move.withdraw_increase)}`} deltaTone="negative" description="9月10日较前5日日均" />
      <MetricCard id="metric-recharge" title="充值变化" queryId="tc_daily" sourceRows={daily}
        value={change(move.recharge_change)} comparison={`增加${amount(move.recharge_increase)}`} deltaTone="positive" description="9月10日较前5日日均" />
      <MetricCard id="metric-excess" title="游戏侧净多派奖" queryId="rtp_drivers" sourceRows={drivers}
        value={amount(decomp.net_excess_payout)} comparison={`${pct(decomp.net_excess_vs_withdraw_increase, 1)}的提现增量`} deltaTone="negative" description="相对各游戏前5日RTP基线" />
    </div>

    <section className="report-section">
      <ReportSection id="tc-overview" title="TC异常" queryId="tc_daily" showHeading={false} sourceRows={daily}>
        <RichNarrative id="tc-overview:body" className="report-analysis" label="编辑TC异常分析" value={`## 01｜先看整体：提现增长是TC升高的直接原因

9月10日成功提现由前5日日均${amount(avg("withdraw"))}增至${amount(sep10?.withdraw)}，增长${change(move.withdraw_change)}；成功充值由${amount(avg("recharge"))}增至${amount(sep10?.recharge)}，增长${change(move.recharge_change)}。提现多增${amount(move.withdraw_increase - move.recharge_increase)}，TC因此由${pct(priorTc)}升至${pct(sep10?.tc_rate)}。`} />
      </ReportSection>
      <div className="chart-pair">
        <EvidenceChart id="money-change" queryId="tc_daily" title="9月10日充值与提现对比" rows={moneyRows} sourceRows={daily}
          height={300} spec={{ type: "bar", x: "period", y: "成功充值（亿）", fields: ["成功充值（亿）", "成功提现（亿）"],
            valueDecimals: 2, colors: { "成功充值（亿）": "var(--chart-1)", "成功提现（亿）": "var(--chart-3)" } }} />
        <EvidenceChart id="tc-rtp-link" queryId="tc_daily" title="每日Tada参与用户TC与游戏RTP" rows={rateRows} sourceRows={daily}
          height={300} spec={{ type: "line", x: "date", y: "游戏加权RTP（%）", fields: ["游戏加权RTP（%）", "Tada参与用户TC（%）"],
            valueDecimals: 2, colors: { "游戏加权RTP（%）": "var(--chart-1)", "Tada参与用户TC（%）": "var(--chart-3)" }, annotations: [
              { id: "sep10", kind: "point", at: "2026-09-10", field: "Tada参与用户TC（%）", label: "TC 87.40%" },
              { id: "partial", kind: "event", at: "2026-09-11", field: "partial_note", label: "部分日" },
            ] }} />
      </div>
      <EvidenceTable id="money-table" title="TC核心数据" queryId="tc_daily" rows={daily} displayRows={moneyTable}
        caption="TC按充值与提现金额加权；9月11日部分日不参与对比。" columns={[
          { field: "对比", label: "对比" }, { field: "成功充值", label: "成功充值" },
          { field: "成功提现", label: "成功提现" },
          { field: "TC", label: "TC", renderCell: pct },
          { field: "TC变化", label: "TC变化", renderCell: pp, deltaTone: tone },
        ]} />
    </section>

    <section className="report-section">
      <ReportSection id="rtp-driver-story" title="RTP贡献拆解" queryId="rtp_drivers" showHeading={false} sourceRows={drivers}>
        <RichNarrative id="rtp-driver-story:body" className="report-analysis" label="编辑RTP贡献分析" value={`## 02｜再看游戏：RTP抬升主要来自同款游戏回报变化

9月10日Tada加权RTP较前5日上升${pp(decomp.total_change_pp)}。其中游戏结构变化贡献${pp(decomp.mix_effect_pp)}，同款游戏RTP变化贡献${pp(decomp.within_game_effect_pp)}，占总抬升的${pct(decomp.within_game_effect_share, 1)}。

各游戏正向多派奖合计${amount(decomp.positive_excess_payout)}，被其他游戏少派奖${amount(Math.abs(decomp.negative_excess_payout))}抵消后，净多派奖${amount(decomp.net_excess_payout)}。`} />
      </ReportSection>
      <EvidenceChart id="rtp-driver" queryId="rtp_drivers" title="9月10日各游戏相对自身RTP基线的派奖偏差" rows={driverRows} sourceRows={drivers}
        height={520} spec={{ type: "horizontalBar", x: "game", y: "相对基线多／少派奖（万）", valueDecimals: 1,
          startAtZero: true, series: "impactType", colorBySign: false,
          colors: { "多派奖（需复核）": "#d85b52", "少派奖（抵消）": "#2f9b73" } }} />
      <EvidenceTable id="driver-table" title="RTP抬升贡献最大的游戏" queryId="rtp_drivers" rows={drivers} displayRows={driverTable}
        caption="基线为同款游戏9月5—9日加权RTP；正值表示9月10日相对基线多派奖。" columns={[
          { field: "排名", label: "排名" }, { field: "游戏", label: "游戏" },
          { field: "9月10日RTP", label: "9月10日RTP", renderCell: pct },
          { field: "前5日RTP", label: "前5日RTP", renderCell: pct },
          { field: "RTP变化", label: "RTP变化", renderCell: pp, deltaTone: tone },
          { field: "相对基线多派奖", label: "相对基线多派奖" },
          { field: "当日下注", label: "当日下注" }, { field: "当日平台净盈利", label: "当日平台净盈利" },
        ]} />
    </section>

    <section className="report-section">
      <ReportSection id="focus-game" title="异常游戏" queryId="rtp_drivers" showHeading={false} sourceRows={drivers}>
        <RichNarrative id="focus-game:body" className="report-analysis focus-callout" label="编辑异常游戏分析" value={`## 03｜具体游戏：3 Lucky Chong Tian Pao是首要复核对象

**9月10日该游戏下注${amount(topDriver?.sep10_bet)}，RTP由前5日${pct(topDriver?.baseline_rtp)}升至${pct(topDriver?.sep10_rtp)}。** 相对自身基线多派奖${amount(topDriver?.excess_payout)}，当日玩家净赢${amount(Math.max(-(topDriver?.sep10_net_win ?? 0), 0))}，对游戏侧RTP抬升的正向贡献最大。

第二至第四位为${drivers[1]?.game}、${drivers[2]?.game}和${drivers[3]?.game}。作为反例，下注规模最大的X7 HOT当日相对自身基线少派奖${amount(Math.abs(x7?.excess_payout))}，不是本次RTP升高来源。`} />
      </ReportSection>
      <EvidenceChart id="rtp-heatmap" queryId="heatmap" title="重点游戏逐日RTP" rows={heatRows} sourceRows={heatmap}
        height={560} spec={{ type: "heatmap", x: "date", y: "RTP（%）", series: "game", showValues: true,
          reverseRows: true, valueDecimals: 1, missingValues: "gap", colorDomain: [90, 110], seriesOrder: A.focus_games,
          tooltipFields: [{ field: "bet", label: "下注额" }, { field: "netWin", label: "平台净盈利" }, { field: "status", label: "日期状态" }] }} />
    </section>

    <ReportSection id="conclusion" title="结论与行动" queryId="tc_daily"
      queryIds={["tc_daily", "rtp_drivers", "reconciliation"]}
      sourceRowsByQuery={{ tc_daily: daily, rtp_drivers: drivers, reconciliation }} showHeading={false}>
      <RichNarrative id="conclusion:body" className="report-caveat" label="编辑结论与行动" value={`## 04｜结论：游戏异常是关联线索，不是完整原因

完整日RTP与TC的Pearson相关为${corr.pearson_rtp_tc?.toFixed(2)}、Spearman为${corr.spearman_rtp_tc?.toFixed(2)}，但只有6天且共同受9月10日高点影响。游戏侧净多派奖仅相当于提现增量的${pct(decomp.net_excess_vs_withdraw_increase, 1)}，不能提现直接归因给3 Lucky Chong Tian Pao。

1. **先复核3 Lucky Chong Tian Pao。** 检查最终派奖、取消退款、Bonus、版本和高倍结果。
2. **再追踪完整日TC。** 若后续仍高于9月5—9日水平，再拆解提现人数、金额分布和资金节奏。
3. **统一两套Tada金额口径。** Currency Summary与GM Lifecycle的每日下注差异为1.78%—5.41%，未确认时区、结算状态和Bonus范围前不合并。`} />
    </ReportSection>

    <section className="report-section appendix-section">
      <RichNarrative id="appendix:intro" className="report-analysis" label="编辑附表说明"
        value={`## 附表｜数据范围与完整游戏明细

9月11日仅统计至12:39（拉各斯），约为前6个完整日日均下注的${pct(overall.partial_day_bet_share_vs_prior6_average, 1)}。Currency Summary未提供币种和日期时区，金额统一写作“源报表单位”。`} />
      <EvidenceTable id="reconciliation-table" title="Currency Summary与GM Lifecycle逐日对账" queryId="reconciliation"
        rows={reconciliation} displayRows={reconTable} caption="两套来源只对账、不合并。" columns={[
          { field: "日期", label: "日期" }, { field: "Currency下注", label: "Currency下注" },
          { field: "Lifecycle下注", label: "Lifecycle下注" },
          { field: "下注差异", label: "下注差异", renderCell: change, deltaTone: tone },
          { field: "Currency盈利", label: "Currency盈利" }, { field: "Lifecycle盈利", label: "Lifecycle盈利" },
          { field: "盈利差异", label: "盈利差异", renderCell: change, deltaTone: tone },
        ]} />
      <EvidenceTable id="game-table" title="161款游戏完整汇总" queryId="game_summary" rows={games}
        displayRows={gameTable} caption="按累计下注额排序；9月11日为部分日。" searchable columns={[
          { field: "排名", label: "排名" }, { field: "游戏", label: "游戏" }, { field: "类型", label: "类型" },
          { field: "下注额", label: "下注额" }, { field: "下注份额", label: "下注份额", renderCell: pct },
          { field: "派奖额", label: "派奖额" }, { field: "平台净盈利", label: "平台净盈利" },
          { field: "玩家净赢", label: "玩家净赢" },
          { field: "加权RTP", label: "加权RTP", renderCell: pct, deltaTone: (v) => v > 1 ? "negative" : "neutral" },
          { field: "局数", label: "局数", renderCell: (v) => nf.format(v) },
        ]} />
    </section>
  </article>;
}

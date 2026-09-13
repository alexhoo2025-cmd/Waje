import React from "react";
import { DataComponent, DataTable, EvidenceChart, MetricCard, ReportSection, RichNarrative, useDataApp } from "../../data-app-public.jsx";

const pct=(v,d=2)=>v==null?"N/A":new Intl.NumberFormat("zh-CN",{style:"percent",minimumFractionDigits:d,maximumFractionDigits:d}).format(v);
const pp=(v,d=2)=>v==null?"N/A":`${v>=0?"+":""}${v.toFixed(d)}个百分点`;
const change=(v,d=2)=>v==null?"N/A":`${v>=0?"+":""}${(v*100).toFixed(d)}%`;
const amount=(v)=>v==null?"N/A":Math.abs(v)>=1e8?`${(v/1e8).toFixed(2)}亿`:Math.abs(v)>=1e4?`${(v/1e4).toFixed(2)}万`:new Intl.NumberFormat("zh-CN").format(v);

function EvidenceTable({id,title,queryId,rows,displayRows,caption}){
  const columns=Object.keys(displayRows[0]??{}).map(field=>({field,label:field}));
  return <DataComponent id={id} title={title} queryId={queryId} kind="table" displayRows={displayRows} sourceRows={rows} description={caption}>
    <DataTable rows={displayRows} columns={columns} caption={caption} searchable={displayRows.length>8} pageSize={8} compactNumbers={false}/>
  </DataComponent>;
}

export function ReportContent(){
  const {reviewedRows,appTitle,canEdit,mode,setAppTitle}=useDataApp();
  const tcWeek=reviewedRows("tc_week"),tcDaily=reviewedRows("tc_daily",["date"]),games=reviewedRows("game_compare");
  const newGames=reviewedRows("new_games"),newDaily=reviewedRows("new_game_daily",["date"]),lifecycle=reviewedRows("lifecycle"),anomalies=reviewedRows("anomalies");
  const [base,current]=tcWeek,tcChange=(current?.tc??0)-(base?.tc??0);
  const totalBetBase=games.reduce((s,r)=>s+(r.bet_prev||0),0),totalBetCurrent=games.reduce((s,r)=>s+(r.bet_curr||0),0);
  const totalProfitBase=games.reduce((s,r)=>s+(r.bet_prev||0)*(1-(r.rtp_prev||0)),0),totalProfitCurrent=games.reduce((s,r)=>s+(r.bet_curr||0)*(1-(r.rtp_curr||0)),0);
  const overallRtpBase=1-totalProfitBase/totalBetBase,overallRtpCurrent=1-totalProfitCurrent/totalBetCurrent,betChange=totalBetCurrent/totalBetBase-1,rtpChange=(overallRtpCurrent-overallRtpBase)*100;
  const tcChart=tcDaily.map(r=>({date:r.date,tcRate:r.tc_rate,period:r.period}));
  const drivers=[...games].sort((a,b)=>Math.abs(b.bet_delta)-Math.abs(a.bet_delta)).slice(0,12).map(r=>({game:r.game,"下注增减（亿）":r.bet_delta/1e8}));
  const comparable=games.filter(r=>r.rtp_gap_curr_pp!=null).sort((a,b)=>Math.abs(b.rtp_gap_curr_pp)-Math.abs(a.rtp_gap_curr_pp)).slice(0,15).map(r=>({game:r.game,"实际－预期（百分点）":r.rtp_gap_curr_pp,"本周下注（亿）":r.bet_curr/1e8}));
  const newDailyChart=newDaily.map(r=>({date:r.date,game:r.game,actualRtp:r.actual_rtp})),lifeChart=lifecycle.map(r=>({game:r.game,lifecycle:`周期${r.lifecycle}`,gapPp:r.rtp_gap_pp}));
  const topGames=[...games].sort((a,b)=>b.bet_curr-a.bet_curr).slice(0,15).map(r=>({游戏:r.game,上期下注:amount(r.bet_prev),本期下注:amount(r.bet_curr),下注变化:change(r.bet_change_pct),上期RTP:pct(r.rtp_prev),本期RTP:pct(r.rtp_curr),RTP变化:pp(r.rtp_change_pp),本期实际减预期:pp(r.rtp_gap_curr_pp),排名:`${r.rank_prev} → ${r.rank_curr}`}));
  const newTable=newGames.map(r=>({游戏:r.game,上线日:r.launch,上期下注:amount(r.bet_prev),本期下注:amount(r.bet_curr),下注变化:change(r.bet_change_pct),上期RTP:pct(r.rtp_prev),本期RTP:pct(r.rtp_curr),RTP变化:pp(r.rtp_change_pp),本期实际减预期:pp(r.rtp_gap_curr_pp)}));
  const anomalyTable=anomalies.map(r=>({游戏:r.game,本期下注:amount(r.bet),实际RTP:pct(r.actual_rtp),预期RTP:pct(r.expected_rtp),差异:pp(r.gap_pp),相对预期盈利差:amount(r.profit_vs_expected)}));
  const periodRows=tcWeek.map(r=>({窗口:r.period,成功充值:amount(r.recharge),成功提现:amount(r.withdraw),TC:pct(r.tc),充值订单:new Intl.NumberFormat("zh-CN").format(r.recharge_orders),提现订单:new Intl.NumberFormat("zh-CN").format(r.withdraw_orders)}));
  const maxPositive=[...games].sort((a,b)=>b.bet_delta-a.bet_delta).slice(0,2),maxNegative=[...games].sort((a,b)=>a.bet_delta-b.bet_delta).slice(0,2);
  const expectedCoverage=games.reduce((s,r)=>s+(r.expected_coverage_curr||0)*r.bet_curr,0)/totalBetCurrent;
  const easy=anomalies.find(r=>r.game==="EasyWin"),tower=anomalies.find(r=>r.game==="Tower"),hilo=anomalies.find(r=>r.game==="Hilo"),blackjack=anomalies.find(r=>r.game==="Blackjack");

  return <article className="report-content" aria-label="Waje TC与RTP周度分析">
    <header className="report-hero"><h1 data-data-app-title contentEditable={canEdit&&mode==="edit"} suppressContentEditableWarning onBlur={canEdit&&mode==="edit"?e=>setAppTitle(e.currentTarget.textContent.trim()||appTitle):undefined}>{appTitle}</h1><RichNarrative id="report:description" className="report-deck" label="编辑报告说明" value="9月4—10日对比8月28日—9月3日｜两个连续7天窗口｜Asia/Hong_Kong"/></header>

    <ReportSection id="summary" title="执行摘要" queryId="tc_week" queryIds={["tc_week","game_compare","anomalies"]} sourceRowsByQuery={{tc_week:tcWeek,game_compare:games,anomalies}} showHeading={false} className="report-summary">
      <RichNarrative id="summary:body" className="report-summary-lead" label="编辑执行摘要" value={`## 执行摘要

- **TC升至${pct(current?.tc)}，资金流出增长快于流入。** 成功充值${change(current?.recharge/base?.recharge-1)}，成功提现${change(current?.withdraw/base?.withdraw-1)}，TC较基线上升${pp(tcChange*100)}。重点看9月10日单日TC ${pct(tcDaily.at(-1)?.tc_rate)} 是否延续。
- **下注增长${change(betChange)}，实际RTP升至${pct(overallRtpCurrent)}。** 本期完全下注${amount(totalBetCurrent)}；实际RTP较基线上升${pp(rtpChange)}。在有预期值的${pct(expectedCoverage,1)}下注范围内，实际与预期基本贴近。
- **下注增量主要来自${maxPositive[0].game}和${maxPositive[1].game}。** 两者分别增加${amount(maxPositive[0].bet_delta)}和${amount(maxPositive[1].bet_delta)}；${maxNegative[0].game}和${maxNegative[1].game}分别减少${amount(Math.abs(maxNegative[0].bet_delta))}和${amount(Math.abs(maxNegative[1].bet_delta))}，抵消部分增长。
- **EasyWin、Tower与Hilo继续优先复核。** EasyWin实际RTP ${pct(easy?.actual_rtp)}，但下注仅${amount(easy?.bet)}；Tower高于预期${pp(tower?.gap_pp)}，Hilo低于预期${pp(hilo?.gap_pp)}。偏离是复核信号，不是故障结论。`}/>
    </ReportSection>

    <div className="report-facts" aria-label="核心指标"><MetricCard id="metric-tc" title="本期TC" queryId="tc_week" sourceRows={tcWeek} value={pct(current?.tc)} comparison={`较基线 ${pp(tcChange*100)}`} negative={tcChange>0} description="成功提现÷成功现金充值"/><MetricCard id="metric-recharge" title="成功充值" queryId="tc_week" sourceRows={tcWeek} value={amount(current?.recharge)} comparison={`较基线 ${change(current?.recharge/base?.recharge-1)}`} description="9月4—10日"/><MetricCard id="metric-bet" title="完全下注额" queryId="game_compare" sourceRows={games} value={amount(totalBetCurrent)} comparison={`较基线 ${change(betChange)}`} description="25款有下注游戏"/><MetricCard id="metric-rtp" title="实际RTP" queryId="game_compare" sourceRows={games} value={pct(overallRtpCurrent)} comparison={`较基线 ${pp(rtpChange)}`} description="按完全下注额加权"/></div>

    <section className="report-section"><ReportSection id="tc-overview" title="资金侧：TC升高来自提现增长更快" queryId="tc_week" showHeading={false} sourceRows={tcWeek}><RichNarrative id="tc-overview:body" className="report-analysis" label="编辑资金分析" value={`## 资金侧：TC升高来自提现增长更快

本期成功充值由${amount(base?.recharge)}增至${amount(current?.recharge)}，增长${change(current?.recharge/base?.recharge-1)}；成功提现由${amount(base?.withdraw)}增至${amount(current?.withdraw)}，增长${change(current?.withdraw/base?.withdraw-1)}。提现增速高于充值，TC因此由${pct(base?.tc)}升至${pct(current?.tc)}。

日度TC在${pct(Math.min(...tcDaily.map(r=>r.tc_rate)))}—${pct(Math.max(...tcDaily.map(r=>r.tc_rate)))}之间波动，9月10日达到${pct(tcDaily.at(-1)?.tc_rate)}。一个高点不足以判断趋势，应继续观察后续完整日。`}/></ReportSection>
      <EvidenceChart id="tc-daily" queryId="tc_daily" title="过去14个完整日TC" rows={tcChart} sourceRows={tcDaily} height={320} spec={{type:"line",x:"date",y:"tcRate",series:"period",valueDecimals:2,colors:{"基线：8月28日—9月3日":"var(--chart-2)","本期：9月4—10日":"var(--chart-1)"}}}/>
      <EvidenceTable id="tc-table" title="两个7天窗口资金汇总" queryId="tc_week" rows={tcWeek} displayRows={periodRows} caption="TC按窗口充值与提现金额加权，不是单日TC的简单平均。"/>
      <RichNarrative id="channel-gap" className="report-disclosure report-warning" label="编辑渠道数据状态" value="**渠道TC本期不展示。** BigQuery同日画像无法覆盖绝大多数历史注册用户，不能据此形成完整注册渠道归属；参考报告的渠道维度需等待同口径渠道表更新。"/></section>

    <section className="report-section"><ReportSection id="game-overview" title="游戏侧：下注增长集中，整体RTP保持在预期附近" queryId="game_compare" showHeading={false} sourceRows={games}><RichNarrative id="game-overview:body" className="report-analysis" label="编辑游戏总览" value={`## 游戏侧：下注增长集中，整体RTP保持在预期附近

完全下注额增加${amount(totalBetCurrent-totalBetBase)}，其中${maxPositive[0].game}贡献${pct(maxPositive[0].bet_delta/(totalBetCurrent-totalBetBase),1)}、${maxPositive[1].game}贡献${pct(maxPositive[1].bet_delta/(totalBetCurrent-totalBetBase),1)}。两者合计超过总增量，说明其他游戏的下降抵消了部分增长。

整体实际RTP由${pct(overallRtpBase,3)}升至${pct(overallRtpCurrent,3)}。有预期值的范围仅覆盖约${pct(expectedCoverage,1)}的下注；在该可比范围内，实际RTP高于预期约0.05个百分点，暂未显示全局性偏离。`}/></ReportSection>
      <EvidenceChart id="bet-drivers" queryId="game_compare" title="下注变化影响最大的12款游戏" rows={drivers} sourceRows={games} height={420} spec={{type:"horizontalBar",x:"game",y:"下注增减（亿）",valueDecimals:2,startAtZero:true}}/>
      <EvidenceChart id="rtp-gap" queryId="game_compare" title="可比游戏实际RTP与预期RTP差异" rows={comparable} sourceRows={games} height={470} spec={{type:"horizontalBar",x:"game",y:"实际－预期（百分点）",valueDecimals:2,startAtZero:true}}/>
      <EvidenceTable id="game-table" title="头部游戏周度比较" queryId="game_compare" rows={games} displayRows={topGames} caption="按本期完全下注额排序；N/A表示该游戏缺少有效预期RTP。"/></section>

    <section className="report-section"><ReportSection id="new-games" title="新游戏：Plinko增长，Tower与Hilo回报方向相反" queryId="new_games" showHeading={false} sourceRows={newGames}><RichNarrative id="new-games:body" className="report-analysis" label="编辑新游戏分析" value={`## 新游戏：Plinko增长，Tower与Hilo回报方向相反

Plinko下注增长${change(newGames.find(r=>r.game==="Plinko")?.bet_change_pct)}，实际RTP降至${pct(newGames.find(r=>r.game==="Plinko")?.rtp_curr)}；Tower下注变化${change(newGames.find(r=>r.game==="Tower")?.bet_change_pct)}，实际RTP升至${pct(newGames.find(r=>r.game==="Tower")?.rtp_curr)}；Hilo下注小幅增长${change(newGames.find(r=>r.game==="Hilo")?.bet_change_pct)}，但实际RTP降至${pct(newGames.find(r=>r.game==="Hilo")?.rtp_curr)}。

三款游戏的下注规模都远低于头部游戏，不能仅凭RTP偏离判定全盘风险；需要结合最终派奖、有效局数、取消退款、Bonus及版本配置复核。`}/></ReportSection>
      <EvidenceChart id="new-game-daily" queryId="new_game_daily" title="新游戏本期逐日实际RTP" rows={newDailyChart} sourceRows={newDaily} height={360} spec={{type:"line",x:"date",y:"actualRtp",series:"game",valueDecimals:2,colors:{Hilo:"var(--chart-2)",Plinko:"var(--chart-3)",Tower:"var(--chart-1)"}}}/>
      <EvidenceTable id="new-game-table" title="新游戏周度比较" queryId="new_games" rows={newGames} displayRows={newTable} caption="本期为9月4—10日；偏离按有预期值的下注范围计算。"/>
      <EvidenceChart id="lifecycle" queryId="lifecycle" title="新游戏各生命周期RTP偏离" rows={lifeChart} sourceRows={lifecycle} height={300} spec={{type:"heatmap",x:"lifecycle",y:"gapPp",series:"game",showValues:true,valueDecimals:1,missingValues:"gap",categoryOrder:["周期1","周期2","周期3","周期4"],seriesOrder:["Hilo","Plinko","Tower"],colorDomain:[-10,10]}}/></section>

    <section className="report-section"><ReportSection id="anomalies" title="重点偏离：先按规模复核EasyWin、Tower与Hilo" queryId="anomalies" showHeading={false} sourceRows={anomalies}><RichNarrative id="anomalies:body" className="report-analysis" label="编辑偏离分析" value={`## 重点偏离：先按规模复核EasyWin、Tower与Hilo

EasyWin实际RTP达到${pct(easy?.actual_rtp)}，较预期高${pp(easy?.gap_pp)}，且两周下注接近翻倍；虽然规模只有${amount(easy?.bet)}，偏离持续扩大，仍应优先核对大额派奖和最终结算。

Tower本期实际RTP超过100%，Hilo低于预期7.77个百分点；Blackjack也低于预期4.53个百分点，但下注仅${amount(blackjack?.bet)}。复核优先级应同时看偏离幅度与下注规模。`}/></ReportSection>
      <EvidenceTable id="anomaly-table" title="本期RTP偏离超过3个百分点的游戏" queryId="anomalies" rows={anomalies} displayRows={anomalyTable} caption="正值表示实际RTP高于预期，负值表示低于预期；均为观察信号。"/></section>

    <ReportSection id="actions" title="建议与数据边界" queryId="game_compare" queryIds={["game_compare","anomalies","tc_week"]} sourceRowsByQuery={{game_compare:games,anomalies,tc_week:tcWeek}} showHeading={false}><RichNarrative id="actions:body" className="report-caveat" label="编辑建议" value={`## 建议与数据边界

1. **P0｜先核对EasyWin、Tower和Hilo。** 检查最终派奖、有效局数、取消退款、免费注／Bonus及配置版本；EasyWin同时检查是否由少数大额派奖主导。
2. **P1｜拆解Tada与Fish的下注增长。** 判断增长来自参与人数、局数、人均下注还是入口份额变化，不把同期资金增长直接归因于游戏。
3. **P1｜继续观察9月10日TC高点。** 若后续完整日仍处高位，再拆分提现人数、金额分布和支付节奏。

**口径：** TC＝成功提现÷成功现金充值；实际RTP＝1－完全实际盈利÷完全下注额。预期差异仅在预期值有效的下注范围内计算。两个窗口均为7个完整自然日，时区Asia/Hong_Kong。

**限制：** 当前缺少有效局数、最终结算状态、取消退款、Bonus、配置版本和用户级大奖分布；渠道TC因注册渠道归属不完整而未展示。TC与RTP同步变化不代表因果关系。`}/></ReportSection>
  </article>;
}

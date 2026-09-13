#!/usr/bin/env python3
import html,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;D=json.loads((ROOT/'analysis-results.json').read_text())
OUT=Path(sys.argv[1]);WORK=OUT.parent;ASSETS=WORK/'assets';ASSETS.mkdir(exist_ok=True)
for name in ['tc-daily','bet-drivers','rtp-gap','new-game-daily','lifecycle']:shutil.copy2(ROOT/'lark-assets'/f'{name}.png',ASSETS/f'{name}.png')
e=lambda v:html.escape(str(v),quote=True)
pct=lambda v,d=2:'N/A'if v is None else f'{v*100:.{d}f}%'
pp=lambda v,d=2:'N/A'if v is None else f'{v:+.{d}f}pp'
chg=lambda v,d=2:'N/A'if v is None else f'{v:+.{d}%}'
def amount(v):
    if v is None:return'N/A'
    if abs(v)>=1e8:return f'{v/1e8:.2f}亿'
    if abs(v)>=1e4:return f'{v/1e4:.2f}万'
    return f'{v:,.0f}'
def cell(v,bg=None,bold=False):return f'<td{f" background-color=\"{bg}\""if bg else""} vertical-align="middle"><p>{"<b>"if bold else""}{e(v)}{"</b>"if bold else""}</p></td>'
def table(headers,rows,widths=None):
    cols=''if not widths else'<colgroup>'+''.join(f'<col width="{w}"/>'for w in widths)+'</colgroup>'
    head='<thead><tr>'+''.join(f'<th background-color="medium-gray"><p><b>{e(h)}</b></p></th>'for h in headers)+'</tr></thead>'
    return'<table>'+cols+head+'<tbody>'+''.join('<tr>'+''.join(x if isinstance(x,str)and x.startswith('<td')else cell(x)for x in row)+'</tr>'for row in rows)+'</tbody></table>'
def move(v,display,strong=0.1):
    bg='light-green'if v>=strong else'light-blue'if v>=0 else'light-red'if v<=-strong else'light-orange';return cell(display,bg,True)
def img(name,caption):return f'<img path="@./{e(WORK.as_posix())}/assets/{name}.png" name="{e(caption)}.png" caption="{e(caption)}"/>'
tc=D['tc'];base,current=tc['previous'],tc['current'];games=D['game_comparison'];gp=D['game_overall'];easy=next(r for r in D['anomalies']if r['game']=='EasyWin');tower=next(r for r in D['anomalies']if r['game']=='Tower');hilo=next(r for r in D['anomalies']if r['game']=='Hilo')
pos=D['bet_drivers']['positive'];neg=D['bet_drivers']['negative'];expected_coverage=gp['current']['expected_coverage']
tc_rows=[[r['biz_date'],amount(r['recharge']),amount(r['withdraw']),pct(r['tc_rate'])]for r in tc['daily']]
game_rows=[]
for r in games[:15]:
    gap='N/A'if r['rtp_gap_curr_pp']is None else pp(r['rtp_gap_curr_pp']);gap_cell=cell(gap)if r['rtp_gap_curr_pp']is None else move(r['rtp_gap_curr_pp'],gap,3)
    game_rows.append([r['game'],amount(r['complete_bet_prev']),amount(r['complete_bet_curr']),move(r['bet_change_pct'],chg(r['bet_change_pct']),.1),pct(r['actual_rtp_prev']),pct(r['actual_rtp_curr']),move(r['rtp_change_pp'],pp(r['rtp_change_pp']),1),gap_cell,f"{r['rank_prev']} → {r['rank_curr']}"])
new_rows=[]
for g in D['new_games']:
    p,c=g['previous'],g['current'];new_rows.append([g['game'],g['launch'],amount(p['complete_bet']),amount(c['complete_bet']),move(g['bet_change_pct'],chg(g['bet_change_pct']),.2),pct(p['actual_rtp']),pct(c['actual_rtp']),move(g['rtp_change_pp'],pp(g['rtp_change_pp']),3),move(c['rtp_gap_pp'],pp(c['rtp_gap_pp']),3)])
life_rows=[]
for g in D['new_games']:
    for r in g['lifecycle']:
        gap=r['rtp_gap_pp'];life_rows.append([g['game'],r['lifecycle'],amount(r['complete_bet']),pct(r['actual_rtp']),pct(r['expected_rtp']),move(gap,pp(gap),3)])
anomaly_rows=[]
for r in D['anomalies']:
    action={'EasyWin':'核对大额派奖、最终结算和有效局数；偏离持续扩大但规模较小。','Tower':'核对层数、Cash Out、封顶触发及倍率分布。','Hilo':'核对猜测、Skip、Cash Out及赔率分布。','Blackjack':'保持小样本观察并核对最终结算。'}[r['game']]
    anomaly_rows.append([r['game'],amount(r['complete_bet']),pct(r['actual_rtp']),pct(r['expected_rtp']),move(r['rtp_gap_pp'],pp(r['rtp_gap_pp']),3),action])
xml=f'''<title>Waje TC回升，但EasyWin、Tower与Hilo仍需复核｜截至2026年9月10日</title>
<h1 seq="auto">执行摘要</h1>
<callout emoji="💡" background-color="light-blue" border-color="blue"><ol>
<li><b>TC升至{pct(current['tc'])}，资金流出增长快于流入。</b>成功充值{chg(tc['recharge_change_pct'])}，成功提现{chg(tc['withdraw_change_pct'])}，TC较基线上升{pp(tc['change_pp'])}。</li>
<li><b>下注增长{chg(gp['bet_change_pct'])}，实际RTP升至{pct(gp['current']['actual_rtp'])}。</b>本期完全下注{amount(gp['current']['complete_bet'])}；在有预期值的{pct(expected_coverage,1)}下注范围内，实际与预期基本贴近。</li>
<li><b>下注增量主要来自{e(pos[0]['game'])}和{e(pos[1]['game'])}。</b>分别增加{amount(pos[0]['bet_delta'])}和{amount(pos[1]['bet_delta'])}；{e(neg[0]['game'])}和{e(neg[1]['game'])}抵消部分增长。</li>
<li><b>EasyWin、Tower与Hilo继续优先复核。</b>EasyWin实际RTP {pct(easy['actual_rtp'])}，Tower高于预期{pp(tower['rtp_gap_pp'])}，Hilo低于预期{pp(hilo['rtp_gap_pp'])}。偏离是复核信号，不是故障结论。</li>
</ol></callout>
<grid><column width-ratio="0.25"><p><b>本期TC</b></p><p><b><span text-color="blue">{pct(current['tc'])}</span></b></p><p>较基线{pp(tc['change_pp'])}</p></column><column width-ratio="0.25"><p><b>成功充值</b></p><p><b>{amount(current['recharge'])}</b></p><p>{chg(tc['recharge_change_pct'])}</p></column><column width-ratio="0.25"><p><b>完全下注额</b></p><p><b>{amount(gp['current']['complete_bet'])}</b></p><p>{chg(gp['bet_change_pct'])}</p></column><column width-ratio="0.25"><p><b>实际RTP</b></p><p><b>{pct(gp['current']['actual_rtp'])}</b></p><p>{pp(gp['actual_rtp_change_pp'])}</p></column></grid>
<h1 seq="auto">资金侧：TC升高来自提现增长更快</h1>
<p>成功充值由<b>{amount(base['recharge'])}</b>增至<b>{amount(current['recharge'])}</b>，增长{chg(tc['recharge_change_pct'])}；成功提现由<b>{amount(base['withdraw'])}</b>增至<b>{amount(current['withdraw'])}</b>，增长{chg(tc['withdraw_change_pct'])}。提现增速高于充值，TC因此由{pct(base['tc'])}升至{pct(current['tc'])}。</p>
{table(['窗口','成功充值','成功提现','TC','充值订单','提现订单'],[['8月28日—9月3日',amount(base['recharge']),amount(base['withdraw']),pct(base['tc']),f"{base['recharge_orders']:,}",f"{base['withdraw_orders']:,}"],['9月4—10日',amount(current['recharge']),amount(current['withdraw']),move(tc['change_pp'],pct(current['tc']),1),f"{current['recharge_orders']:,}",f"{current['withdraw_orders']:,}"]],[150,130,130,90,110,110])}
<p><b>日度TC波动仍明显。</b>9月10日达到{pct(tc['daily'][-1]['tc_rate'])}，一个高点不足以判断趋势，应继续观察后续完整日。</p>{img('tc-daily','过去14个完整日TC')}
{table(['业务日','成功充值','成功提现','TC'],tc_rows,[140,150,150,100])}
<callout emoji="⚠️" background-color="light-yellow" border-color="yellow"><p><b>渠道TC本期不展示。</b>BigQuery同日画像无法覆盖绝大多数历史注册用户，不能据此形成完整注册渠道归属；等待同口径渠道表更新后再补充。</p></callout>
<h1 seq="auto">游戏侧：下注增长集中，整体RTP保持在预期附近</h1>
<p>完全下注额增加<b>{amount(gp['current']['complete_bet']-gp['previous']['complete_bet'])}</b>，其中{e(pos[0]['game'])}贡献{pct(pos[0]['bet_delta']/D['bet_drivers']['total_delta'],1)}、{e(pos[1]['game'])}贡献{pct(pos[1]['bet_delta']/D['bet_drivers']['total_delta'],1)}。两者合计超过总增量，说明其他游戏下降抵消了部分增长。</p>{img('bet-drivers','下注变化影响最大的12款游戏')}
<p>整体实际RTP由{pct(gp['previous']['actual_rtp'],3)}升至{pct(gp['current']['actual_rtp'],3)}。有预期值的范围覆盖{pct(expected_coverage,1)}下注；在可比范围内，实际RTP高于预期{pp(gp['current']['rtp_gap_pp'])}，暂未显示全局性偏离。</p>{img('rtp-gap','可比游戏实际RTP与预期RTP差异')}
{table(['游戏','上期下注','本期下注','下注变化','上期RTP','本期RTP','RTP变化','实际-预期','排名'],game_rows,[115,105,105,95,90,90,95,100,75])}
<h1 seq="auto">新游戏：Plinko增长，Tower与Hilo回报方向相反</h1>
<p>Plinko下注增长{chg(next(g for g in D['new_games']if g['game']=='Plinko')['bet_change_pct'])}；Tower下注下降但实际RTP升至{pct(next(g for g in D['new_games']if g['game']=='Tower')['current']['actual_rtp'])}；Hilo下注小幅增长，但实际RTP降至{pct(next(g for g in D['new_games']if g['game']=='Hilo')['current']['actual_rtp'])}。三款下注规模均远低于头部游戏，不能仅凭RTP偏离判定全盘风险。</p>
{table(['游戏','上线日','上期下注','本期下注','下注变化','上期RTP','本期RTP','RTP变化','实际-预期'],new_rows,[90,105,100,100,90,85,85,90,95])}{img('new-game-daily','新游戏本期逐日实际RTP')}
<p><b>生命周期偏离方向分化。</b>以下仅展示本期生命周期1—4；颜色表示偏离方向与幅度。</p>{img('lifecycle','新游戏各生命周期RTP偏离')}{table(['游戏','生命周期','完全下注额','实际RTP','预期RTP','差异'],life_rows,[90,90,120,100,100,100])}
<h1 seq="auto">重点偏离：先按规模复核EasyWin、Tower与Hilo</h1>
<p>EasyWin实际RTP达到<b>{pct(easy['actual_rtp'])}</b>，较预期高{pp(easy['rtp_gap_pp'])}，且两周下注接近翻倍；虽然本期下注仅{amount(easy['complete_bet'])}，偏离持续扩大，仍应优先核对大额派奖和最终结算。Tower实际RTP超过100%；Hilo低于预期7.77个百分点。复核优先级应同时看偏离幅度与下注规模。</p>
{table(['游戏','本期下注','实际RTP','预期RTP','差异','处理建议'],anomaly_rows,[90,105,90,90,90,280])}
<h1 seq="auto">建议与数据边界</h1><ol><li><b>P0｜先核对EasyWin、Tower和Hilo。</b>检查最终派奖、有效局数、取消退款、免费注/Bonus及配置版本；EasyWin同时检查是否由少数大额派奖主导。</li><li><b>P1｜拆解Tada与Fish的下注增长。</b>判断增长来自参与人数、局数、人均下注还是入口份额变化，不把同期资金增长直接归因于游戏。</li><li><b>P1｜继续观察9月10日TC高点。</b>若后续完整日仍处高位，再拆分提现人数、金额分布和支付节奏。</li></ol>
<h1 seq="auto">口径与来源</h1><callout emoji="💡" background-color="light-gray" border-color="gray"><p><b>比较窗口：</b>本期为9月4—10日，基线为8月28日—9月3日，均为7个完整自然日，时区Asia/Hong_Kong。</p><p><b>指标口径：</b>TC=成功提现÷成功现金充值；实际RTP=1−完全实际盈利÷完全下注额。预期差异仅在预期值有效的下注范围内计算。</p><p><b>来源：</b>资金来自企业BigQuery服务端成功事件；RTP来自GM Lifecycle Pool v2 (Joint)，9月10日四表结构、去重和勾稽已通过。</p><p><b>限制：</b>缺少有效局数、最终结算状态、取消退款、Bonus、配置版本和用户级大奖分布；渠道TC因注册渠道归属不完整未展示。TC与RTP同步变化不代表因果关系。</p></callout>
<p><a type="url-preview" href="https://ksg964l11fam.sg.larksuite.com/wiki/O4wuw0DsxiACgxkf5XAl6RTHgYO">参考报告：截至9月7日的TC与RTP周度分析</a></p>'''
OUT.write_text(xml);(ROOT/'report.xml').write_text(xml)
(ROOT/'report.md').write_text(f'''# Waje TC回升，但EasyWin、Tower与Hilo仍需复核｜截至2026年9月10日

## 执行摘要

- 本期TC为{pct(current['tc'])}，较基线上升{pp(tc['change_pp'])}；成功充值{chg(tc['recharge_change_pct'])}，成功提现{chg(tc['withdraw_change_pct'])}。
- 完全下注额为{amount(gp['current']['complete_bet'])}，增长{chg(gp['bet_change_pct'])}；实际RTP为{pct(gp['current']['actual_rtp'])}，上升{pp(gp['actual_rtp_change_pp'])}。
- Tada和Fish是主要下注增量来源；EasyWin、Tower、Hilo优先复核。
- 渠道TC因本期注册渠道归属不完整未展示，不以未知渠道数据替代。

完整表格、图表、建议和来源边界见HTML与飞书报告。''')
print(json.dumps({'draft':str(OUT),'chars':len(xml),'tables':xml.count('<table>'),'images':xml.count('<img ')},ensure_ascii=False))

import importlib.util,json,subprocess,csv,html
from pathlib import Path
from datetime import date
R=Path(__file__).resolve().parent
P=R.parents[1]
s=importlib.util.spec_from_file_location('w',P/'analysis/tc_game_rtp_weekly_2026_09_08/build_weekly_analysis.py'); w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
raw=w.old.annotated_rows(R/'sources/game-live.json')
live=[w.old.game_row(r) for r in raw]
merged={(r['date'],r['game']):r for r in live}
supp=w.read_game_rows()
for r in supp:
    if str(r['date']) in ['2026-09-03','2026-09-07']: merged[(r['date'],r['game'])]=r
rows=sorted([r for r in merged.values() if r['game']=='Tower' and '2026-08-11'<=str(r['date'])<='2026-09-07'],key=lambda r:r['date'])
def agg(rs):
    a=w.old.aggregate(rs); B=sum(r['base_bet'] for r in rs); F=sum(r['complete_bet'] for r in rs); Q=sum(r['base_actual_profit'] for r in rs); C=sum(r['bankruptcy'] for r in rs); U=sum(r['personal_control'] for r in rs)
    a.update(base_bet=B,base_profit=Q,full_bet=F,compensation_pp=-C/F*100,control_pp=-U/F*100,denominator_pp=Q*(1/B-1/F)*100)
    assert abs(a['adjustment_pp']-sum(a[k] for k in ['compensation_pp','control_pp','denominator_pp']))<1e-8
    return a
windows={k:agg([r for r in rows if lo<=str(r['date'])<=hi]) for k,lo,hi in [('first','2026-08-25','2026-08-31'),('second','2026-09-01','2026-09-07'),('post','2026-08-25','2026-09-07')]}
daily=[dict(date=str(r['date']),**agg([r])) for r in rows]
assert all(abs(r['complete_actual_profit']-r['base_actual_profit']-r['bankruptcy']-r['personal_control'])<.01 for r in rows)
detail=w.old.annotated_rows(R/'sources/detail-live.json');dd=[w.detail_row(r) for r in detail if r['游戏']=='Tower'];dd=[r for r in dd if r]
dm={(r['date'],r['lifecycle']):r for r in dd}
for r in w.read_detail_rows():
    if r['game']=='Tower' and str(r['date']) in ['2026-09-03','2026-09-07']:dm[(r['date'],r['lifecycle'])]=r
life=[]
for lifeid in range(1,5):
    a=agg([r for r in dm.values() if r['lifecycle']==lifeid and '2026-08-25'<=str(r['date'])<='2026-09-07']);life.append(dict(lifecycle=lifeid,**a))
assert abs(sum(r['complete_bet'] for r in life)-windows['post']['complete_bet'])<.01
delta={k:windows['second'][k]-windows['first'][k] for k in ['actual_rtp','base_rtp','adjustment_pp']}
data=dict(windows=windows,daily=daily,lifecycle=life,change=delta,pre_window='2026-08-11/2026-08-24',pre_observed_dates=[str(r['date']) for r in rows if str(r['date'])<'2026-08-25'],status='partial_causal_identification',supplement_dates=['2026-09-03','2026-09-07'])
(R/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str))
def p(v):return f'{v*100:.3f}%'
def n(v):return f'{v:,.2f}'
def pp(v):return f'{v:+.3f}个百分点'
def table(head,rs):
    return '<table><thead><tr>'+''.join('<th background-color="light-gray"><p><b>'+html.escape(h)+'</b></p></th>' for h in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td><p>'+html.escape(str(c))+'</p></td>' for c in row)+'</tr>' for row in rs)+'</tbody></table>'
intro='现有数据不支持直接贴水是近期RTP提升的主要来源；8月25日调整是否通过改变基础开奖概率产生间接影响，目前不能排除。'
doc=['<title>Tower回报补偿调整与RTP提升诊断｜8月11日—9月7日</title>', '<h1 seq="auto">汇总结论（Executive Summary）</h1>', '<callout background-color="light-blue" border-color="blue"><p><b>'+intro+'</b></p><p>调整后第一周完全RTP为99.031%，第二周为100.611%，上升1.580个百分点。其中基础RTP上升2.124个百分点，补偿及控制的净口径影响减少0.545个百分点。</p><p>调整后14天，完全RTP99.662%，基础RTP99.527%，两者仅差0.135个百分点；完全RTP高于同期预期2.808个百分点。基础回报本身偏高是需要优先解释的现象。</p></callout>',
'<h1 seq="auto">追溯结果：调整前没有完整两周可比样本</h1><p>已全量读取飞书“新用户生命周期数据V2-含联运”分游戏及详细奖池子表，当前修订1600。8月11日—23日没有Tower记录；8月24日仅基础/完全下注3,600.55、实际利润-21,542.47，复算RTP698.311%。基础与完全口径一致，没有直接补偿差额。该记录可能与早期测试、结算或样本口径有关，不能视作成熟前期基线，也不能擅自删为错误。</p><p>项目历史记录将8月24日列为计划上线、8月25日列为上线节点。因此上线和用户说明的补偿调整可能同时发生，缺少可比对照。事件日期采用用户提供的8月25日；尚未取得当日配置差异、灰度范围及生效时间。</p><p>在线表缺少9月3日和9月7日。本次仅用本项目此前已完成独立补采与校验的两日快照补足后期；其他日期以本轮飞书读取为准。</p>',
'<h1 seq="auto">按金额复算：基础回报提高，净补偿影响下降</h1>',table(['窗口','完全下注额','基础RTP','完全RTP','预期RTP','完全减基础'],[[label,n(a['complete_bet']),p(a['base_rtp']),p(a['actual_rtp']),p(a['expected_rtp']),pp(a['adjustment_pp'])] for key,label in [('first','8/25—8/31'),('second','9/1—9/7'),('post','8/25—9/7')] for a in [windows[key]]]),
'<p>所有RTP使用各自累计下注与累计利润重算。基础RTP分母是基础下注，完全RTP分母是完全下注；不使用完全下注加权每日基础RTP。上表两周都处于调整之后，因此它能解释近期提升的账面组成，不能替代调整前后因果估计。</p>',
'<h1 seq="auto">补偿、个人控制与分母效应分别贡献多少</h1><p>14天逐日均满足：完全实际利润＝基础实际利润＋总破产保护金额＋总个人盈利控制金额。破产保护在源表为负数，个人盈利控制通常为正数。完整拆解为：完全RTP−基础RTP＝−破产保护/完全下注−个人控制/完全下注＋基础利润×(1/基础下注−1/完全下注)。</p>',
table(['窗口','破产保护金额（原符号）','个人控制金额','保护贡献','控制贡献','分母效应','净影响'],[[label,n(a['bankruptcy']),n(a['personal_control']),pp(a['compensation_pp']),pp(a['control_pp']),pp(a['denominator_pp']),pp(a['adjustment_pp'])] for key,label in [('first','第一周'),('second','第二周'),('post','后14天')] for a in [windows[key]]]),
'<p>第二周破产保护减少、个人盈利控制增加，合计作用转为压低完全RTP；完全RTP仍上升，是基础RTP上升抵消并超过这一影响。因此“直接补偿发得更多导致第二周RTP升高”与账面证据不符。净影响只衡量报表中的直接会计调整；若补偿规则改变了基础开奖、投注选择或玩家结构，其影响可能已进入基础RTP。</p>',
'<h1 seq="auto">生命周期与日级证据</h1>',table(['生命周期','后14天下注','基础RTP','完全RTP','预期RTP','净调整'],[[r['lifecycle'],n(r['complete_bet']),p(r['base_rtp']),p(r['actual_rtp']),p(r['expected_rtp']),pp(r['adjustment_pp'])] for r in life]),
'<p>生命周期4下注规模最大；其基础RTP已超过100%，净调整略为负向。优先排查该阶段的开奖概率、倍率、Cash Out层级及派奖结构。生命周期是用户阶段分类，不能解释为Tower的爬塔层数。</p>',
table(['日期','完全下注','基础RTP','完全RTP','净调整'],[[r['date'],n(r['complete_bet']),p(r['base_rtp']),p(r['actual_rtp']),pp(r['adjustment_pp'])] for r in daily]),
'<h1 seq="auto">产品机制意味着哪些原因仍需验证</h1><p>Tower_backend_draw_logic当前文档要求：目标RTP在Bet成功时固化为当局快照；第一层成功概率＝目标RTP/第一层倍率，后续层成功概率＝上一层倍率/当前层倍率；Cash Out派彩受最大赢金封顶限制。若8月25日修改的是目标RTP或其注入方式，可能直接改变基础回报；若只修改额外补偿发放，优先表现为完全与基础口径之差。封顶减少可能提高实际回报，但必须核对历史配置与实际触发分布。</p><p>当前配置资料同时列出生命周期预期回报、pr扶持、个人盈利控制和tower开奖配置路径，说明需要分清变更所属模块。当前产品文档是机制说明，不是8月25日生产部署证据。</p>',
'<h1 seq="auto">诊断结论与下一步验证</h1><ol><li><b>直接账面补偿：不支持作为近期提升主因。</b>第二周净影响为负，基础RTP已超过100%。</li><li><b>8月25日规则调整的总因果效应：尚不能识别。</b>调整前仅1个低金额日，上线同期发生，缺少生产配置前后差异与有效局数，无法给出可信提升百分比或显著性。</li><li><b>优先取得变更证据：</b>8月25日变更单、参数旧值/新值、生效时间、包体/人群及当局RTP快照分布，以确认改的是额外补偿还是基础开奖目标。</li><li><b>优先验证生命周期4：</b>按配置版本、难度、终止层级、下注档位汇总基础下注、实际派奖、补偿、控制及封顶触发。比较同配置同人群，检验高RTP是否仍存在。</li><li><b>补齐局级聚合：</b>有效局数、赔付二阶矩与大额派奖集中度，才能计算不确定区间。条件允许时使用随机保留旧补偿规则的对照组；观察比较只能给关联。</li></ol>',
'<h1 seq="auto">来源与口径</h1><p>金额沿用生命周期报表单位；RTP差额单位为百分点。负利润代表本统计口径下玩家净赢，并非财务净利润。缺失日期不补零。</p><ul><li><a href="https://ksg964l11fam.sg.larksuite.com/wiki/ZBD4wPBsricBWMktFqilAGxlgte">生命周期价值报表：本轮读取修订1600</a></li><li><a href="https://ksg964l11fam.sg.larksuite.com/wiki/Of2Dwtb4jiXz5Qkv4Nule94KgSg">Tower后台开奖逻辑：当前修订1</a></li><li><a href="https://ksg964l11fam.sg.larksuite.com/wiki/QEMPwuzd4ijebRk7vwGlCHS0gAf">Tower产品需求：当前修订50</a></li></ul>']
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1500,850),'white');dr=ImageDraw.Draw(im)
ft=lambda z:ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',z)
dr.text((50,25),'Tower 基础与完全RTP：调整后两周对比',font=ft(32),fill='#17324D')
dr.text((50,80),'8/25—9/7；两段都在调整后，不能替代调整前后因果比较。',font=ft(20),fill='#60748A')
for j,(key,label) in enumerate([('first','8/25—8/31'),('second','9/1—9/7')]):
 a=windows[key];x=300+j*650
 for idx,(metric,color,title) in enumerate([('base_rtp','#2F6FBE','基础RTP'),('actual_rtp','#25846E','完全RTP')]):
  xx=x+idx*175;val=a[metric]*100; yy=630-(val-96)*95
  dr.rectangle((xx,yy,xx+100,630),fill=color);dr.text((xx-12,yy-40),f'{val:.3f}%',font=ft(23),fill=color);dr.text((xx-5,648),title,font=ft(21),fill='#17324D')
 dr.text((x,705),label,font=ft(24),fill='#17324D');dr.text((x,750),'净影响 '+pp(a['adjustment_pp']),font=ft(22),fill='#17324D')
for val in [96,97,98,99,100,101]:
 y=630-(val-96)*95;dr.text((50,y-12),str(val)+'%',font=ft(20),fill='#60748A')
dr.text((50,815),'纵轴聚焦96%—101%，比较细微RTP差额；蓝=基础，绿=完全。',font=ft(18),fill='#60748A')
im.save(R/'rtp-comparison.png')
doc.insert(7,'<img path="@./analysis/tower_compensation_diagnostic_2026_09_08/rtp-comparison.png" caption="Tower基础与完全RTP对照"/>')
content='\n'.join(doc)
if (R/'preperiod-correction.xml').exists():
 start=content.index('<p>已全量读取');end=content.index('</p>',start)+4
 content=content[:start]+(R/'preperiod-correction.xml').read_text()+content[end:]
 start=content.index('<callout');end=content.index('</callout>',start)+len('</callout>')
 content=content[:start]+'<callout background-color="light-blue" border-color="blue"><p><b>8月25日调整是否使Tower的RTP提升，目前缺少可比的调整前数据，尚不能判定。</b>前14天仅有8月24日一条小额异常记录；V1/V2同日数据存在重大差异。后期两周的RTP上升分解不可作为调整前后因果结论。</p><p>后期第二周完全RTP上升1.580个百分点，基础RTP上升2.124个百分点，而净补偿及控制影响减少0.545个百分点。</p></callout>'+content[end:]
(R/'report.xml').write_text(content)
import sys
if len(sys.argv)>1:(P/sys.argv[1]).write_text(content)
(R/'report.md').write_text('# Tower回报补偿调整与RTP提升诊断\n\n'+intro+'\n\n'+json.dumps(windows,ensure_ascii=False,indent=2))
print(json.dumps(dict(windows=windows,pre_dates=data['pre_observed_dates'],life=life),ensure_ascii=False))

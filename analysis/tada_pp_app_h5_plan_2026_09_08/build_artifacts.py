from pathlib import Path
import json,hashlib,html,re,subprocess,datetime
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def save(n,o):(P/n).write_text(json.dumps(o,ensure_ascii=False,indent=2))
sources=[
 ('games','knowledge/02-数据/Waje-游戏代码与名称统一映射表-2026-08-31.md','身份字典与版本；不把目录游戏数当实际上线数'),
 ('for_you','knowledge/02-数据/For You推荐模块APP-H5埋点开发需求-2026-08-31.md','MV/MC模块与链路设计；绑定与实际接收待核'),
 ('h5_audit','knowledge/02-数据/Waje-H5起源埋点上报全量盘点-2026-08-28.md','历史事件覆盖与异常，只作本轮核验入口'),
 ('tc_rtp','knowledge/02-数据/Waje-TC异常、RTP与资产流水诊断框架-2026-08-28.md','TC、RTP、GGR、资金与结算边界'),
 ('tada_mechanics','knowledge/02-数据/TaDa-Games投注机制属性总表拆解-2026-08-06.md','多目标、多段与多人共局；数量与日期不作为现期业务值'),
 ('x7_history','analysis/x7_hot_tada_currency_summary_2026_09_04/report.md','头部和品类分析线索；第三方快照窗口/币种未明确，不拼入本期'),
 ('platform','knowledge/02-数据/数据平台与报表.md','起源BQ、GM Joint与Metabase职责及迁移边界')]
save('sources.json',[{'id':i,'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),'use':u,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'current_production_certified':False} for i,p,u in sources])
text=(P/'方案.md').read_text();paras=text.split('\n\n');tables=[]
for para in paras:
 if para.startswith('|'):
  rr=[[x.strip() for x in line.strip('|').split('|')] for line in para.splitlines()]
  tables.append({'headers':rr[0],'rows':rr[2:]})
metric=tables[1]
lookup={'投注':['bets','daily_or_window','currency_amount_or_share'],'渗透':['activity+bets','window','fraction'],'活跃':['activity+opens+bets','daily_and_window','users_or_days'],'深度':['bets+round_mapping','daily_and_window','count_or_amount'],'回报':['bets+settlements','settled_bet_cohort','fraction_or_amount'],'回访':['bets+complete_calendar','cohort_date_x_observation_day','fraction'],'资金':['wallet+account_cohort','window','amount_or_fraction'],'加载':['open_attempts+linked_bets','attempt_cohort','fraction_or_ms']}
metrics=[]
for i,row in enumerate(metric['rows'],1):
 topic,name,formula,purpose=row;source,grain,unit=lookup[topic]
 metrics.append({'id':f'M{i:02d}','topic':topic,'name':name,'definition_and_algorithm':formula,'purpose':purpose,'source_contract':source,'grain':grain,'unit':unit,'dimensions':['actual_platform','cohort','provider','game_or_category','currency','asset_scope'],'denominator_rule':formula if '÷' in formula or '分母' in formula else '见算法；计数先按对应唯一键去重','data_state':'design_only_not_measured'})
save('metric-dictionary.json',metrics);save('table-model.json',tables)
out=[]
def inline(s):
 s=html.escape(s,quote=True);s=re.sub(r'`([^`]+)`',r'<span>\1</span>',s)
 return re.sub(r'\*\*(.+?)\*\*',r'<b><span background-color="light-blue">\1</span></b>',s)
for para in paras:
 if not para.strip():continue
 if para.startswith('# '):out.append('<title>'+inline(para[2:])+'</title>')
 elif para.startswith('## '):out.append('<h1>'+inline(para[3:])+'</h1>')
 elif para.startswith('### '):out.append('<h2>'+inline(para[4:])+'</h2>')
 elif para.startswith('!['):out.append('<img path="@./analysis/tada_pp_app_h5_plan_2026_09_08/analysis-flow.png" caption="分析链路示意；无业务测量数据"/>')
 elif para.startswith('|'):
  rr=[[c.strip() for c in line.strip('|').split('|')] for line in para.splitlines()];cols=rr[0]
  out.append('<table><colgroup>'+''.join(f'<col width="{1020//len(cols)}"/>' for _ in cols)+'</colgroup><thead><tr>'+''.join('<th background-color="light-gray"><p>'+inline(c)+'</p></th>' for c in cols)+'</tr></thead><tbody>')
  for row in rr[2:]:out.append('<tr>'+''.join('<td vertical-align="top"><p>'+inline(c)+'</p></td>' for c in row)+'</tr>')
  out.append('</tbody></table>')
 elif para.startswith('- '):out.append('<ul>'+''.join('<li>'+inline(l[2:])+'</li>' for l in para.splitlines())+'</ul>')
 elif re.match(r'\d+\. ',para):out.append('<ol>'+''.join('<li>'+inline(re.sub(r'^\d+\. ','',l))+'</li>' for l in para.splitlines())+'</ol>')
 else:out.append('<p>'+inline(para)+'</p>')
xml='\n'.join(out);(ROOT/'draft_b3c51a76_folder/draft.xml').write_text(xml);(P/'release.xml').write_text(xml)
# Schematic only: no quantitative chart or invented business data.
def txt(x,y,lines):return ''.join(f'<text x="{x}" y="{y+i*30}" text-anchor="middle" font-family="PingFang SC" font-size="21" fill="#234358">{html.escape(s)}</text>' for i,s in enumerate(lines))
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560"><rect width="1200" height="560" fill="#f6f9fc" rx="20"/>'+txt(600,43,['先比较表现，再验证原因'])
for i,(a,b) in enumerate([('游戏与资源','身份／品类／可玩范围'),('曝光与入口','人数／位置／分配'),('打开与加载','成功／耗时／缓存')]):
 x=45+i*395;svg+=f'<rect x="{x}" y="83" width="330" height="96" rx="14" fill="#e3eef6" stroke="#91acbe"/>'+txt(x+165,119,[a,b])
 if i<2:svg+=f'<path d="M{x+337},131 H{x+380}" stroke="#7697ab" stroke-width="3"/><polygon points="{x+372},124 {x+383},131 {x+372},138" fill="#7697ab"/>'
svg+='<path d="M1000,179 V218 H210 V258" fill="none" stroke="#7697ab" stroke-width="3"/><polygon points="203,252 217,252 210,262" fill="#7697ab"/>'
for i,(a,b) in enumerate([('有效投注','份额／人数／笔数与局数'),('对应结算','RTP／毛收入／覆盖'),('持续参与','同端回访／跨端迁移')]):
 x=45+i*395;svg+=f'<rect x="{x}" y="265" width="330" height="96" rx="14" fill="#e8f3ed" stroke="#96b2a1"/>'+txt(x+165,300,[a,b])
svg+='<path d="M375,313 H430 M210,361 V380 H1000 V368" fill="none" stroke="#7697ab" stroke-width="3"/><polygon points="423,306 435,313 423,320" fill="#7697ab"/><polygon points="993,372 1007,372 1000,362" fill="#7697ab"/>'
svg+='<rect x="150" y="401" width="900" height="94" rx="14" fill="#fff2d9" stroke="#b8a27b"/>'+txt(600,438,['TC另看共享钱包：成功提现 ÷ 成功现金充值','按互斥参与人群比较，不把钱包资金直接归因厂商'])+txt(600,540,['所有指标统一窗口、人群、实际端、币种及资产；图示为分析设计'])+'</svg>'
(P/'analysis-flow.svg').write_text(svg)
save('build-receipt.json',{'status':'design_generated','tables':len(tables),'metric_entries':len(metrics),'text_chars':len(text),'production_rows':0})
print(json.dumps({'tables':len(tables),'metrics':len(metrics),'chars':len(text)},ensure_ascii=False))

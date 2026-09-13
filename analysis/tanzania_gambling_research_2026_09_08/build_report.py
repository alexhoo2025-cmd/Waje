"""One canonical content model for HTML, Markdown and Lark."""
from pathlib import Path
import json,re,statistics,sqlite3
from datetime import datetime,timezone
from analyze import load,save,brand,grid,yn,numeric
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
TITLE='坦桑尼亚博彩行业与产品调研｜竞争差异与Waje启示'
N=load('normalized.json');BS=N['brands'];PAY=N['payment'];EXT=load('external-evidence.json')
NOW=datetime.now(timezone.utc).isoformat()
A={'surface':'report','manifest':{'version':1,'surface':'report','title':TITLE,'generatedAt':NOW,'sources':[], 'cards':[],'charts':[],'tables':[],'blocks':[]},'snapshot':{'version':1,'generatedAt':NOW,'status':'ready','datasets':{}}}
M=A['manifest'];D=A['snapshot']['datasets'];MAP=[]
M['sources']=[{'id':'raw','label':'Research TZ _ Bet.xlsx｜原始调研记录','description':'12张工作表，含3张隐藏表；原采集日期、抽样方法与测试样本量未提供。金额TZS。具体单元格保留在图表数据与本地底稿。'},{'id':'derived','label':'坦桑行业调研数据.xlsx｜同源加工版','description':'13张表，265个公式全部复算缓存一致；业务语义及跨版本变化单独审查，不作为第二独立证据。'},{'id':'review','label':'原始Excel与逐项官方核验','description':'本地external-evidence.json记录官方链接、核验日期与状态；核验值不覆盖原始Excel。'},{'id':'waje','label':'Waje产品总览及产品部门知识库｜本地资料','description':'2026-08-03产品总览与2026-08-31产品部门资料。用于玩法/资金/多端背景，非坦桑上线或性能证据。'}]+[{'id':e['id'],'label':e['label'],'href':e['href'],'description':e['period']+'；'+e['status']+'。'+e['facts']} for e in EXT]
def md(id,body,source=None):
    b={'id':id,'type':'markdown','body':body}
    if source:b['sourceId']=source
    M['blocks'].append(b)
def table(id,title,rows,cols,source='raw'):
    rows=[{k:('未记录' if v is None else v) for k,v in r.items()} for r in rows]
    D[id]=rows
    M['tables'].append({'id':id,'title':title,'dataset':id,'sourceId':source,'layout':'full','density':'spacious','defaultSort':{'field':cols[0][0],'direction':'asc'},'columns':[{'field':k,'label':l,'type':'number' if rows and all(isinstance(r.get(k),(int,float)) for r in rows) else 'text'} for k,l in cols]})
    M['blocks'].append({'id':id+'_block','type':'table','tableId':id})
def chart(id,title,rows,x,y,xlabel,ylabel,source='raw',type='bar',series=None,subtitle='',fmt=None):
    D[id]=rows
    enc={'x':{'field':x,'type':'quantitative' if type=='line' else 'ordinal','label':xlabel},'y':{'field':y,'type':'quantitative','label':ylabel}}
    if fmt:enc['y']['format']=fmt
    if id=='bonus_curve':enc['x']['type']='ordinal'
    if series:enc['color']={'field':series,'type':'nominal','label':'分组'}
    c={'id':id,'title':title,'subtitle':subtitle,'type':type,'dataset':id,'sourceId':source,'layout':'full','encodings':enc,'palette':{'kind':'categorical' if series else 'sequential','name':'blue-gold'},'labels':{'values':'endpoints' if type=='line' else 'all'}}
    if series:c['legend']={'position':'bottom'}
    if fmt:c['valueFormat']=fmt
    if type=='line':c['settings']={'showPoints':'always'}
    M['charts'].append(c);M['blocks'].append({'id':id+'_block','type':'chart','chartId':id})
    MAP.append({'chart':id,'question':title,'family':type,'rows':len(rows),'fields':[x,y,series],'palette':'blue/gold + categorical roots as needed','source':source,'qa':'canonical shared reader; static light PNG for Lark','note':'年度仅5点采用柱形；串关按有序场次数值绘线，不是时间趋势。' if id in ['mobile_pay','bonus_curve'] else '比较图；来源和分母随数据保留'})
def link(id):
    e=next(x for x in EXT if x['id']==id);return f"[{e['label']}]({e['href']})"
def money(v):
    n=numeric(v)
    return f'{n:,.0f}' if n is not None else str(v or '未记录').replace('∞','原表称无上限').replace('pending','待确认')
def percent(v):return f'{v*100:g}%' if isinstance(v,(int,float)) else str(v or '未记录')

md('title','# '+TITLE)
md('summary',f'''## 执行摘要

**坦桑的产品竞争建立在手机钱包和多玩法之上，Waje应优先做好支付与轻量体验。** 17个支付样本全部记录手机钱包推送支付；19个主表样本中17个明确记录Casino，15个记录体育提前结算。央行数据也显示，2025年移动支付交易量同比增长24.1%。

**低门槛充值很常见，提现门槛才是容易被忽略的差异。** 支付样本的最低存款中位数为**100 TZS**、最低提现中位数为**1,000 TZS**；12/17家提现门槛更高。应同时看能否充值、能否顺利取回余额和费用是否清楚。

**奖励不能只比最高倍率，内容不能只比游戏名字。** SportPesa串关奖励在材料中出现800%、1,000%、350%三种口径；Crash表同时出现SPRIBE、Aviator LLC及替代游戏。更有价值的比较是参与条件、兑现方式和真实产品组合。

**这两份表适合做竞品能力地图，不足以证明市场份额或投资回报。** 它们是同源材料；本报告覆盖全部25张表，并补充官方核验。优先借鉴本地支付、清晰余额和活动说明；测试轻量内容与多端衔接；暂缓照搬超高倍率促销。

来源：两份Excel及{link('bot-2025')}。官网核验截至2026年9月8日；原调研采集日期未标注。''')

md('industry','## 一、行业背景｜数字支付在增长，博彩收入规模仍有缺口\n\n**当地具备数字娱乐所需的支付与网络基础，但网络能力并不均匀。** 下面把人口、支付、通信和博彩税收分开看，避免把订阅数当人数、把税收当市场收入。')
table('industry_facts','行业关键数据及范围',[
 {'metric':'博彩税收','value':'约2,600亿 TZS','period':'2025年（原文年度）','scope':'GBT监管口径，以坦桑大陆为主','meaning':'2026年4月23日官方说明；非GGR或投注额'},
 {'metric':'线上体育经营名录','value':'33条','period':'2026年9月8日读取','scope':'坦桑大陆','meaning':'当前网页名单条目；不是独立品牌市场份额'},
 {'metric':'线下体育经营名录','value':'8条','period':'2026年9月8日读取','scope':'坦桑大陆','meaning':'与线上有重叠，合计不可当独立公司数'},
 {'metric':'移动支付交易量','value':'79.594亿笔；同比+24.1%','period':'2025年','scope':'全国支付系统','meaning':'全行业交易，并非博彩支付'},
 {'metric':'活跃手机钱包','value':'7,577.6万订阅','period':'2025年末前90天','scope':'全国','meaning':'活跃SIM账户；一人可有多个'},
 {'metric':'互联网订阅','value':'6,279.4万；较3月+6.48%','period':'2026年6月末','scope':'全国','meaning':'订阅数，不是去重网民'},
 {'metric':'人口普查','value':'全国6,174.1万；大陆5,985.1万','period':'2022年','scope':'全国含桑给巴尔188.98万','meaning':'历史人口且含未成年人，不能作为博彩客群'},
 {'metric':'博彩总收入／品牌市场份额','value':'未获得可比现行数据','period':'当前','scope':'待补','meaning':'不据税收、功能数或促销规模反推'}
],[('metric','指标'),('value','数据'),('period','统计期'),('meaning','如何理解')],'review')
md('payment_macro',f'''**支付普及在持续扩大，优先适配手机钱包有明确外部依据。** 2025年交易量79.594亿笔，较2024年增加15.455亿笔；交易金额约255.13万亿TZS，同比增加28.3%。下面是同一央行口径的年度交易量，反映支付基础设施使用强度，不代表博彩需求增速。

来源：{link('bot-2025')}。''','bot-2025')
chart('mobile_pay','移动支付年度交易量',[{'year':str(y),'billion_tx':v/1000,'million_tx':v,'period':'自然年','source':'BoT附表H1（2024精确值取正文）'} for y,v in zip(range(2021,2026),[3158.48,3595.04,5061.20,6413.94,7959.40])],'year','billion_tx','年份','十亿笔','bot-2025',subtitle='2021—2025年；全行业移动支付，不是博彩支付')
md('network_macro',f'''**轻量体验仍有价值：约39.2%的互联网订阅属于2G。** 2026年6月，移动宽带订阅约3,757.6万，2G约2,462.8万，固定网络约59万。网络覆盖扩大不等于每台设备都能顺畅加载重资源游戏；Waje应按网络和设备分档验证加载及恢复体验。

来源：{link('tcra-2026')}，第35页。分项与总计相差1条，按原表保留。''','tcra-2026')
chart('network_mix','互联网订阅的接入方式',[{'type':t,'million':v/1e6,'subscriptions':v,'share':v/62793986,'period':'2026年6月','denominator':62793986} for t,v in [('移动宽带（3G/4G/5G）',37575797),('2G',24628003),('固定网络',590185)]],'type','million','接入方式','百万订阅','tcra-2026',subtitle='2026年6月末；订阅不是独立人数')
md('tax_history',f'''**体育在历史税收结构中占主导，但不能据此推断今天的收入结构。** GBT 2020/21财年体育税收868亿TZS，占当年博彩税收的65.8%；该年总税收比2019/20增长48.1%。它只能作为历史背景。2025年约2,600亿的新闻数据与旧财年不拼接计算增长率。

来源：{link('gbt-history')}；当前说明见{link('gbt-2025tax')}。''')
table('tax_types','博彩税收业态结构（历史，不是当前市场份额）',[{'type':t,'old':v0,'new':v1,'share':f'{v1/132*100:.1f}%'} for t,v0,v1 in [('体育博彩',52.10,86.80),('线下Casino',11.56,14.06),('互联网Casino',1.99,3.25),('老虎机门店与酒吧',18.04,21.76),('40机经营点',1.06,1.43),('短信彩票',4.35,4.70)]],[('type','业态'),('old','2019/20（十亿TZS）'),('new','2020/21（十亿TZS）'),('share','2020/21占比')],'gbt-history')

md('competition','## 二、竞争格局｜多玩法是常见配置，差异在组合与承接\n\n**样本已经超出纯体育产品：Casino和提前结算是常见能力。** 主表19家中，Casino明确“有”17家、“无”1家，另1家仅记门店；明确记录样本中的覆盖率为17/18=94.4%，若以全部19家计，下限为89.5%。提前结算为15/19=78.9%。这说明应把内容及资金体验一起比较，而不是只数体育赛事。','raw')
features=[]
for f,label in [('casino','Casino'),('cashout','体育提前结算'),('horse','赛马'),('dog','赛狗'),('virtual_football','虚拟足球'),('spin','转盘'),('keno','Keno')]:
    counts=load('initial_stats.json')[f];features.append({'feature':label,'coverage':counts['yes']/counts['denominator'],'yes':counts['yes'],'explicit':counts['denominator'],'unknown':counts['unknown_or_named'],'all_brands':19,'source':'ONLINE '+f,'scope':'仅原表明确YES/NO；命名产品待核'})
features.sort(key=lambda x:x['coverage'],reverse=True)
chart('feature_coverage','样本功能覆盖率',features,'feature','coverage','功能','有明确记录样本中的比例',fmt='percent',subtitle='分子为YES；分母为YES+NO，其他描述保留未核实')
table('feature_denominators','功能覆盖分母',features,[('feature','功能'),('yes','有'),('explicit','明确记录'),('unknown','其他／待核')])
md('license_note',f'''**多数样本能在监管名单定位，但“在名录”不等于所有玩法、渠道均完成合规验证。** 19家中16家完成商号规范匹配，Parimatch与名单“Parimacth”近似，需再核对主体；Mbet与WinPrincess未获明确匹配。完整对照见附表。名单还包含样本外品牌，因此本报告不把样本覆盖率当作全市场普及率。

来源：{link('gbt-operators')}。''','gbt-operators')

md('thresholds','## 三、支付与门槛｜充值容易，取回余额的条件更分化\n\n**最低体育下注的样本中位数是100 TZS，14/19家不高于100 TZS。** 原表范围为1—500 TZS，说明低门槛较普遍，但不意味着越低越好。官方SportPesa条款现为100 TZS，与原表10不同；betPawa官网仍说明可低至1 TSh。报告保留原值，并将现行核验单列。\n\n**支付样本更值得关注的是存提门槛差。** 17家中12家最低提现高于最低存款，5家相同；中位数分别为100和1,000 TZS。这是两组中位数的10倍关系，不是“典型用户需充值10倍”或统一提现规则。','raw')
paired=[]
for p in sorted(PAY,key=lambda x:(-x['min_withdraw'],x['brand'])):
    for measure,field in [('最低存款','min_deposit'),('最低提现','min_withdraw')]:paired.append({'brand':p['brand'],'metric':measure,'amount':p[field],'ratio':p['ratio'],'currency':'TZS','source':p['source'],'status':'原调研记录'})
chart('deposit_withdraw','代表品牌最低存款与提现门槛',[r for r in paired if r['brand'] in ['Premier Bet','Parimatch','GSB','Meridian Bet','Betika','SportyBet','betPawa']],'brand','amount','品牌','TZS',series='metric',subtitle='7家展示高、中、低及存提相等情形；完整17家见下表，均为原材料')
table('payment_limits','存款、提现门槛与限额（TZS）',[{'brand':p['brand'],'dep':money(p['min_deposit']),'wd':money(p['min_withdraw']),'maxwd':money(p['max_withdraw']),'gap':f"{p['ratio']:g}倍",'source':p['source']} for p in PAY],[('brand','品牌'),('dep','最低存款'),('wd','最低提现'),('maxwd','最高提现原值'),('gap','门槛比'),('source','来源单元格')])
md('payment_checks',f'''**跨表冲突已经影响实际判断，支付金额应以具体渠道为单位。** GSB、SportPesa、Betika三家的最低存款记录不一致。本次已找到支持GSB和Betika最低100 TZS的官网正文；SportPesa最低存款仍保留10/100冲突，不擅自选值。另一个重要变化是Betika官网写有门店存款，原支付表却记“无”。

来源：{link('gsb-deposit')}、{link('betika-terms')}、{link('sportpesa-terms')}。''')
checked=[
 {'brand':'GSB','item':'最低存款','raw':'主表500；两支付表100','current':'100 TZS；帮助页所列渠道','result':'当前官方支持100；原值保留'},
 {'brand':'GSB','item':'最高存款','raw':'5,000,000','current':'帮助页所列方式1,000,000','result':'渠道／时间范围不同，单列'},
 {'brand':'Betika','item':'最低存款','raw':'主表/支付表100；另一表500','current':'手机钱包100 TZS','result':'当前官方支持100'},
 {'brand':'Betika','item':'最低提现／门店存款','raw':'最低500；门店存款NO','current':'最低500；官网有门店存款流程','result':'最低值支持；门店能力冲突'},
 {'brand':'SportPesa','item':'最低存款','raw':'主表10；两支付表100','current':'本次未确认现行最低存款','result':'留冲突，不混入当前排名'},
 {'brand':'SportPesa','item':'最低下注／最高奖金','raw':'最低10；最高33,000,000','current':'最低100；单注5,000,000／串关25,000,000／每日30,000,000','result':'先区分单注、串关与日限额'},
 {'brand':'betPawa','item':'Mixx by Yas存款','raw':'最低100；最高5,000,000','current':'100—5,000,000 TZS','result':'此渠道范围获支持'},
 {'brand':'Premier Bet','item':'150%首存／最低提现4,000','raw':'原材料记录','current':'官网访问被拦截','result':'仅材料支持，非现行承诺'},
 {'brand':'SportyBet','item':'串关奖励与入金说明','raw':'多表条件冲突','current':'实际页面451访问限制','result':'保留冲突；不采用搜索摘要更新'},
 {'brand':'Betway','item':'BetSaver返还条件','raw':'免费注、动态计算','current':'原页空白／跳转后被拦截','result':'仅材料支持，需当地验证'},
 {'brand':'Meridian Bet','item':'返还活动','raw':'最高100倍、Freebet','current':'100倍阶梯已读；资金兑现属性未明确','result':'倍率条件支持；兑现方式待核'}]
table('verified_terms','重点品牌：原记录与官网核验',checked,[('brand','品牌'),('item','核验项'),('raw','原调研记录'),('current','当前读取'),('result','结论')],'review')
md('payment_methods','### 手机钱包是基础设施，“USSD支付”与“USSD投注”分别统计\n\n**17/17家记录推送支付与电话钱包支付；银行卡仅2/17，银行转账0/17。** 这只是样本记录，不能推出当地银行渠道完全不存在。钱包付款码有16/17条明确记录；它用于转账，与不打开网页即可投注的短码不是同一种能力。Premier短码被标为未启用，加工版仍判“有”，本报告不沿用该判断。','raw')
methods=[]
for f,l in [('push','手机钱包推送'),('phone','电话钱包支付'),('shop','门店／代金券'),('card','银行卡'),('bank','银行转账'),('prepaid','预付卡')]:
    y=sum(yn(p[f])=='有' for p in PAY);ex=sum(yn(p[f])!='未核实' for p in PAY);methods.append({'method':l,'yes':y,'explicit':ex,'unknown':17-ex,'rate':y/ex if ex else None})
chart('payment_methods_chart','支付方式的样本记录',methods,'method','yes','方式','品牌数',subtitle='17家支付样本；类别可重叠，不能相加')
md('payment_time','### 到账速度只作线索，先保障状态透明\n\n**材料中的秒级时长不足以给品牌排性能名次。** 存款、提现各有15家记录具体秒数，另各2家称“即时”；具体记录中位数分别30秒、45秒。没有测试日期、次数、金额与失败样本，这些不是本次实测，也不能当服务承诺。\n\n**对Waje更可执行的启示是显示完整资金状态。** 将“已发起—待手机确认—处理中—已到账／失败”分开，明确费用与可提现余额；同时统计成功、失败、处理中占比及成功样本P50/P95。原表提现费用大多写NO，却缺少电信方费用范围，不能据此宣传免费提现。','raw')

md('bonus','## 四、奖励机制｜真正的差异在条件，不在最高数字\n\n**先比较常用场次，再看极端上限。** 原串关阶梯覆盖9个品牌；第10场奖励从10%到40%，第30场从50%到330%，但各品牌最低赔率、奖金计算基础和适用赛事不同，不能直接当收益率。下面保留全部9家在指定场次的原记录；缺值、移除和跨表冲突显式标注。','raw')
ladderrows=[]
for name in sorted(set(x['brand'] for x in N['ladder'])):
    selected={x['legs']:x for x in N['ladder'] if x['brand']==name}
    row={'brand':name,'odds':selected[3]['odds'],'status':'跨表冲突' if name in ['SportyBet','SportPesa'] else '历史材料；当前另核'}
    for day in [3,5,10,20,30,50]:row['n'+str(day)]=percent(selected[day]['raw']) if selected[day]['bonus'] is not None else '已移除' if str(selected[day]['raw']).strip()=='removed' else '未记录'
    ladderrows.append(row)
table('bonus_steps','指定场次的串关奖励原记录',ladderrows,[('brand','品牌'),('odds','最低单场赔率'),('n3','3场'),('n5','5场'),('n10','10场'),('n20','20场'),('n30','30场'),('n50','50场'),('status','质量状态')])
md('bonus_curve_note','**奖励梯度分化主要出现在高场次，且不同梯度不能横向等价。** 下图只展示原阶梯中4个代表品牌的1—30场完整记录，避免把冲突最突出的SportyBet和SportPesa画成确定曲线。曲线表达“同一材料内奖励如何随场次变化”，不代表当前规则、获胜概率或投入回报。','raw')
chart('bonus_curve','代表品牌的串关奖励阶梯',[x for x in N['ladder'] if x['brand'] in ['Throne Bet','Meridian Bet','betPawa','PM Bet'] and x['legs']<=30 and x['bonus'] is not None],'legs','bonus','串关场次','奖励比例',type='line',series='brand',fmt='percent',subtitle='原材料1—30场；非时间趋势、非预期收益率')
md('bonus_current',f'''**现行活动已与材料存在差异，旧阶梯不能用于上线配置。** betPawa官网现在显示3场及以上、每场赔率至少1.20，60场最高1,250%，并说明不设固定阶梯表；材料为60场1,000%。SportPesa材料的800%／1,000%／350%尚不能归并，SportyBet的3场9%与5场5%也应留疑。

来源：{link('pawa-bonus')}；其他冲突见原始《Online Multibet》和《Combined Multibet Deep Analysis》。''')
md('refund_intro','### 返还并非保本：现金、免费注与限制条件要同屏\n\n**7项返还机制中混有6项线上及1项Throne线下记录，不能排统一“价值榜”。** 本金倍数、奖金增幅与免费注是三种不同口径；例如Gwala的1,000%为本金10倍，而WiBet材料写1,000倍，两者相差100倍。先明确触发条件、资金属性、上限及有效期，才能评价吸引力和资金成本。','raw')
refund=[
 {'brand':'GSB','condition':'至少2场，仅错1场；获胜部分赔率≥25','award':'1—50倍本金；最高100万TZS','asset':'返到账户','status':'官方条件已支持；提现属性按账户条款'},
 {'brand':'Meridian Bet','condition':'至少2场且有赛前项，仅错1场，真实资金','award':'1—100倍本金；最高倍率档赔率≥950','asset':'材料称免费注，官网未明确','status':'阶梯和主要条件支持；资金属性待核'},
 {'brand':'Betway','condition':'材料：至少6场、每场赔率1.5+，动态计算','award':'材料上限750万；另例图出现1,500万','asset':'免费注','status':'上限冲突；官网访问受限'},
 {'brand':'Throne（线下）','condition':'材料：2场起，仅错1场，赔率25起','award':'材料最高100倍本金','asset':'钱包','status':'门店访查记录；未外部核实'},
 {'brand':'WiBet','condition':'材料：8—20场、单场1.3起','award':'材料宣传1,000倍；另有100万上限','asset':'钱包','status':'原页无正文；倍率解释未核实'},
 {'brand':'SportyBet','condition':'材料：启用One Cut并调整滑杆','award':'随方案计算','asset':'钱包','status':'动态规则；原页不可访问'},
 {'brand':'Gwala Bet','condition':'材料：7—40场、单场1.5起','award':'100%—1,000%本金，即1—10倍','asset':'免费注','status':'原页未读到条款'}]
table('refund_conditions','返还活动条件对照',refund,[('brand','品牌／渠道'),('condition','参与条件'),('award','奖励与上限'),('asset','兑现方式'),('status','核验状态')],'review')
md('refund_example',f'''**GSB的50倍要跨过较高条件，不是普通输单获得50倍。** 官网按剔除输场后的获胜赔率分档，750以上才进入50倍档，返还最高100万TZS；Meridian的100倍档对应950以上。两者都不能只用总赔率或最高倍数计算一个“平均返还率”。

来源：{link('gsb-refund')}、{link('meridian-refund')}、{link('meridian-rules')}。''')
welcome=[{'brand':b['brand'],'offer':b['welcome'],'limit':'原材料未完整记录参与金额、流水要求、期限及可提现属性'} for b in BS if str(b['welcome']).strip().upper()!='NO']
md('welcome_note','### 首存活动｜先补完整成本条件，再讨论活动力度\n\n**原主表10家记录首存类或新客活动，但其中WiBet是注册奖励，Throne仅写“有”。** 金额、流水要求、期限及现金属性普遍不全，因此下表保留宣传记录、不计算统一获客成本。Waje应把奖励用途、领取条件、失效时间和可提现规则写在同一处，并同步观察投诉及误解率。','raw')
table('welcome_offers','原材料记录的新客活动',welcome,[('brand','品牌'),('offer','原活动记录'),('limit','对比边界')])

md('content','## 五、内容与分发｜Crash要认产品，APP要认渠道\n\n**Crash内容并非一个“Aviator”字段就能代表。** 供应商表17家中13家标SPRIBE、1家标Aviator LLC、3家两者均无；至少Sokabet记录Zeppelin替代品。主表却把Sokabet记为Aviator有，Parimatch和WiBet的跨表记录也不一致。应按“品牌—产品—供应商—渠道”建立对照，暂不计算统一Aviator市占率。','raw')
table('crash_suppliers','Crash产品与供应商原记录',N['supplier'],[('brand','品牌'),('spribe','SPRIBE'),('llc','Aviator LLC'),('related','相关产品原记录')])
crash=[]
for r,v in grid('AVIATOR').items():
    if r<3 or 'B' not in v:continue
    crash.append({'brand':brand(v['B']),'game':v['C'],'min':money(v.get('D')),'max':money(v.get('E')),'promo':'有记录' if str(v.get('F')).strip().upper() not in ['NO','NONE'] else '无','source':f'AVIATOR!B{r}:G{r}'})
md('crash_prices','**同属Crash，游戏的门槛也不同。** 隐藏表15条产品记录的最低下注中位数为200 TZS，范围1—2,000：最低值来自Sokabet的Zeppelin，最高值来自Premier的Navigator。不能把两端差距解释为同一款SPRIBE Aviator的价格差。','raw')
table('crash_stakes','隐藏表：具体Crash产品门槛（TZS）',crash,[('brand','品牌'),('game','产品原名'),('min','最低下注'),('max','最高下注'),('promo','活动记录')])
md('apps_intro','### Android覆盖更广，但有APP不等于可从商店安装\n\n**16个应用样本中13家记录Android体育应用、8家记录iOS体育应用；商店分发分别只有4家Google Play、6家App Store。** 这反映原材料的分发差异，不是当前上架核验，也不是下载量。桌面安装、官网下载安装包与商店上架应独立观察。','raw')
chart('app_channels','应用与商店分发的样本覆盖',[{'capability':n,'brands':v,'denominator':16,'share':v/16,'unknown_outside_sheet':3,'scope':'体育APP／对应商店原记录'} for n,v in [('Android应用',13),('iOS应用',8),('Google Play',4),('App Store',6)]],'capability','brands','分发能力','品牌数',subtitle='16家应用样本；应用存在与商店分发分别统计')
table('app_matrix','应用分发对照（原材料）',N['apps'],[('brand','品牌'),('android','Android体育'),('ios','iOS体育'),('playstore','Google Play'),('appstore','App Store')])
md('ux_intro','### 隐藏表补充了有用的界面线索\n\n**输入区提示不是处处可见，Web与手机也并非完全一致。** 16家ALERTS样本中，存款金额条／提示在Web记“有”7家、手机6家；下注范围提示Web为4/15明确记录、手机5/16。Mbet存款提示Web有而手机无。该表只表明原作者记录的提示状态，不证明可用性或转化影响；适合转成下一轮界面测试清单。','raw')
table('input_help','Web与手机端输入提示',N['alerts'],[('brand','品牌'),('stake_web','下注提示Web'),('stake_mobile','下注提示手机'),('deposit_web','存款提示Web'),('deposit_mobile','存款提示手机')])

md('retail','## 六、线上与线下｜相同品牌也有不同门槛\n\n**5个配对品牌的线下最低体育下注均为500 TZS，比线上高2.5—5倍。** GSB与PM Bet线上100、线下500；Premier、Throne、Meridian线上200、线下500。原样本体现了渠道门槛差，而不是证明线下用户更高价值。','raw')
chart('retail_pair','同品牌线上与线下最低体育下注',[{'brand':r['brand'],'channel':c,'amount':r[f],'delta':r['delta'],'source':r['source'],'currency':'TZS'} for r in N['retail'] for c,f in [('线上','online'),('线下','retail')]],'brand','amount','品牌','TZS',series='channel',subtitle='5家配对样本；原调研记录')
table('retail_table','配对门槛差异',N['retail'],[('brand','品牌'),('online','线上TZS'),('retail','线下TZS'),('delta','绝对差TZS'),('ratio','线下／线上倍数')])
rg=grid('RETAIL MULTIBET');rt=[]
for c,v in rg[2].items():
    if c=='A':continue
    row={'brand':brand(v)}
    for n in [3,5,10,20,30,50]:
        row['n'+str(n)]=percent(rg.get(n+3,{}).get(c))
    rt.append(row)
md('retail_bonus','**线下奖励同样需要独立版本。** RETAIL主表5家有4家记录串关奖励，另一张线下阶梯表覆盖4家；不能将线上优惠直接用于门店。下表保留线下指定场次记录，缺值标注未记录；Throne线下100倍返还也独立于其线上能力。','raw')
table('retail_bonus_steps','线下串关阶梯原记录',rt,[('brand','品牌'),('n3','3场'),('n5','5场'),('n10','10场'),('n20','20场'),('n30','30场'),('n50','50场')])

md('waje','## 七、Waje启示｜先提升可用性与透明度，再验证内容扩展\n\n**Waje已有多玩法、资金账户与APP/H5产品背景，适合借鉴的是服务与组织方式，而不是宣传倍率。** 本地资料记录Whot、Fish、Slots、Crash等入口；这些只作为产品背景，不代表已具备坦桑运营资质、当地支付或现行客户端性能。\n\n以下为产品建议，尚非效果结论。按“先能用、再易懂、最后验证新增价值”排序；成年识别、费用与损失提示、限额、自我排除及安全退出路径作为共同约束。','waje')
actions=[
 {'priority':'优先借鉴','item':'本地手机钱包与资金状态','evidence':'17/17支付样本记录钱包推送；12/17提现门槛更高','action':'按当地钱包展示费用、限额、处理中与失败原因；提供清楚提现入口','metric':'支付成功率、到账P95、重复申请率、提现投诉率','condition':'支付供应商和当地合规验证后实施'},
 {'priority':'优先借鉴','item':'奖励与余额说明','evidence':'7项返还混合现金、钱包和免费注；上限多处冲突','action':'同屏显示可用/可提现余额、领取与失效条件、流水进度','metric':'规则理解率、异常咨询量、奖励到账准确率','condition':'展示事实，不以高倍率诱导加大投注'},
 {'priority':'优先借鉴','item':'轻量首屏与弱网恢复','evidence':'2G约占39.2%互联网订阅；APP商店覆盖低于应用存在','action':'按设备/网络测资源体积、可玩时间、断线恢复；保留网页入口','metric':'可玩成功率、首屏/可玩P75与P95、恢复成功率','condition':'在真实当地设备与网络验证'},
 {'priority':'值得验证','item':'Crash与短局内容组织','evidence':'17家供应商表中13家标SPRIBE，并有多种替代产品','action':'先明确供应商及规则，以少量合规内容验证入口理解与稳定性','metric':'入口识别率、加载成功率、正常结束率、用户投诉与风险指标','condition':'不以数量替代需求，不预设博彩收益'},
 {'priority':'值得验证','item':'APP与网页协同','evidence':'应用存在和上架比例不同；Web/手机提示有差异','action':'统一登录后余额、支付状态和安全跳转，分别观察同端/跨端回访','metric':'跳转成功率、状态一致率、跨端返回完成率','condition':'用户选择优先，避免强制下载'},
 {'priority':'暂缓采用','item':'直接复制体育串关／极高返还','evidence':'奖励基数、赔率及上限不一；Waje各玩法结构不同','action':'先审适配性、资金成本和用户保护，不据最高倍数决定上线','metric':'条款理解、奖金成本、投诉/纠纷、风险事件','condition':'缺少可比收入、获客成本及合规依据'}]
table('actions','建议优先级与验证指标',actions,[('priority','优先级'),('item','方向'),('action','建议动作'),('metric','验收指标'),('condition','条件')],'review')
md('followup','### 下一步只补会改变决策的证据\n\n1. **业务与合规：** 确认经营范围、服务商资格、成年用户与资金保护要求；补齐现行博彩收入和目标客群资料后再讨论进入规模。\n2. **产品与支付：** 针对已验证的低存款门槛，设计当地手机钱包、余额及提现状态的只读走查；后续支付实测另行安排授权与测试样本。\n3. **研究：** 补Premier、SportyBet、Betway当地可访问条款，以及Mbet、WinPrincess主体；补齐剩余品牌的渠道级限额和活动生效期。\n4. **数据：** 持续按同一字段记录“产品/渠道/金额/日期/来源/状态”，用更新记录替代覆盖历史数值。')

md('appendix','## 附表｜品牌、来源与核验边界\n\n**数据可用于探索性竞品比较，不能当全市场抽样调查。** 两份Excel合计25张表全部读取；两版ONLINE共同18家、378个可比字段归一化后一致。加工版ONLINE缺WinPrincess，另在Profile中补列；它并未构成一份独立调查。加工版265个公式与缓存均复算一致，但公式计算正确不代表业务分类正确。原作者的价值评分缺少评分依据，保留于本地原文，不作为本报告排名。\n\n下表以原始ONLINE的19品牌为固定范围；“未核实”表示证据不足，不表示无牌照、无功能或不在经营。','review')
entities={'GSB':'Fido Technologies Ltd','Premier Bet':'Entertainment Africa Limited','Throne Bet':'Throne Bet Ltd','Meridian Bet':'Bit Tech Limited','PM Bet':'Playmaster Gaming Corporation Limited','betPawa':'Choplife Gaming Limited','SportyBet':'Marawin Limited','SportPesa':'Nexis Global Limited','Betway':'Media Bay Limited','Betika':'Paladin & Associates Company Ltd','Sokabet':'Digital Gaming Solutions Limited','WasafiBet':'Wasafi Bet Company Limited','Gwala Bet':'Whiteball Company Limited','888Bet':'Port Achia Tanzania Limited','Parimatch':'Ultimate Gaming System Limited（近似商号Parimacth）','LeonBet':'Sandstorm Company Limited','WiBet':'Cleopatra Gaming (T) Ltd'}
lic=[{'brand':b['brand'],'entity':entities.get(b['brand'],'未核实'),'status':'商号规范匹配' if b['brand'] in entities and b['brand']!='Parimatch' else '近似商号，待复核' if b['brand']=='Parimatch' else '未找到明确对应','scope':'线上体育名单'} for b in BS]
table('license_matrix','19个品牌与官方经营主体对照',lic,[('brand','样本品牌'),('entity','监管名单经营主体'),('status','匹配状态')],'gbt-operators')
def capability(v):
    if v is None:return '未记录'
    return '有' if str(v).strip().upper()=='YES' else '无' if str(v).strip().upper()=='NO' else str(v).strip()
table('brand_matrix','完整主表能力对照（原记录）',[{'brand':b['brand'],'stake':money(b['min_stake']),'casino':capability(b['casino']),'aviator':capability(b['aviator']),'cashout':capability(b['cashout']),'ussd':('未启用' if 'NOT ACTIVE' in str(b['ussd']).upper() else '短码记录' if str(b['ussd']).startswith('*') else capability(b['ussd'])),'maxwin':money(b['max_win'])} for b in BS],[('brand','品牌'),('stake','最低体育下注TZS'),('casino','Casino'),('aviator','Aviator栏'),('cashout','提前结算'),('ussd','USSD投注'),('maxwin','最高奖金原值TZS')])
issues=[
 {'issue':'同源加工与品牌版本','impact':'两份不是独立调查；原始19品牌，加工版部分字段不同','handling':'固定原始19品牌；所有公式保存依赖与复算结果'},
 {'issue':'最低存款三家冲突','impact':'GSB 500/100；SportPesa 10/100；Betika 100/500','handling':'GSB与Betika获官方支持；SportPesa存款留冲突'},
 {'issue':'USSD误判','impact':'Premier Not Active被公式判YES；钱包付款码混入投注判断','handling':'将未启用、钱包支付、短码投注分开'},
 {'issue':'奖励比例与资金属性','impact':'SportPesa800/1000/350；Sporty9%/5%；倍数与百分比混用','handling':'逐场次原值保留；不制作收益率排名'},
 {'issue':'Crash识别','impact':'Sokabet、Throne、Parimatch、WiBet等多表不一致','handling':'供应商、产品与渠道分别展示；不算统一市占率'},
 {'issue':'Summary图范围','impact':'图表类别混入Methodology文字；图XML存在不支持的分组值','handling':'共享阅读器从底层数值重画，不复用原汇总图'},
 {'issue':'到账速度／费用／税率','impact':'无测试样本；NO费用未说明承担方；原税率10%—17%范围混杂','handling':'材料时长不作承诺；现行税率与端到端费用暂不据表定案'},
 {'issue':'主观评分','impact':'Best Value Score无评分方法','handling':'仅保存作者意见；不转成竞争力客观排名'},
 {'issue':'现行行业收入','impact':'官方公开年报目录仅可取旧期，新闻税收不能替代GGR','handling':'不输出当前GGR、品牌份额或进入市场回报估计'}]
table('issues','影响判断的数据问题',issues,[('issue','问题'),('impact','影响'),('handling','本报告处理')],'review')
table('source_status','外部核验记录',[{'source':e['label'],'period':e['period'],'status':e['status'],'url':e['href']} for e in EXT],[('source','来源'),('period','统计期／读取日'),('status','状态'),('url','原始链接')],'review')
md('closing','**使用建议：** 将本报告作为产品验证清单和竞品底稿。已读官方页面支持相关金额或规则的存在，不等于完成全部渠道实测；未核实项只限制对应结论。HTML和飞书由同一份报告数据生成，后续更新可定位到具体品牌和单元格。')

def markdown_all():
    parts=[]
    for b in M['blocks']:
        if b['type']=='markdown':parts.append(b['body'])
        elif b['type']=='table':
            t=next(t for t in M['tables'] if t['id']==b['tableId']);cols=t['columns'];rows=D[t['dataset']]
            parts.extend(['### '+t['title'],'| '+' | '.join(c['label'] for c in cols)+' |','|'+'|'.join('---' for c in cols)+'|'])
            parts.extend('| '+' | '.join(str(r[c['field']]).replace('|','／').replace('\n',' ') for c in cols)+' |' for r in rows)
        else:
            c=next(c for c in M['charts'] if c['id']==b['chartId']);parts.append(f"![{c['title']}](lark_assets/{c['id']}.png)\n\n{c['subtitle']}")
    return '\n\n'.join(parts)+'\n'
# Keep original workbook/Python provenance alongside the actually executed local
# SQL read. This database is a reviewed report snapshot, not a production source.
db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row;queries=[]
for item in M['charts']+M['tables']:
    rows=D[item['dataset']];fields=list(dict.fromkeys(k for row in rows for k in row))
    ident=item['dataset'];db.execute('CREATE TABLE "'+ident+'" ('+', '.join('"'+k+'"' for k in fields)+')')
    db.executemany('INSERT INTO "'+ident+'" VALUES ('+','.join('?' for k in fields)+')',[[r.get(k) for k in fields] for r in rows])
    sql='SELECT '+', '.join('"'+k+'"' for k in fields)+' FROM "'+ident+'" ORDER BY rowid;'
    reread=[dict(r) for r in db.execute(sql)];assert reread==rows,(ident,'SQL readback mismatch')
    controlling=next(s for s in M['sources'] if s['id']==item['sourceId'])
    sid='query_'+ident
    M['sources'].append({'id':sid,'label':controlling['label'],'href':controlling.get('href',''),'path':'analysis/tanzania_gambling_research_2026_09_08/build_report.py','description':controlling['description']+'；原始计算见extract.py/analyze.py，SQLite仅为可复算报告快照读取。','query':{'engine':'sqlite','sql':sql,'tables_used':[ident],'description':'从本地已复算快照读取；非线上数据库查询。来源单元格和原值保留在cells.json及normalized.json。','executed_at':NOW}})
    item['sourceId']=sid;queries.append({'id':ident,'sql':sql,'rows':len(rows),'original_source':controlling['id']})
db.commit()
with sqlite3.connect(P/'report-snapshot.sqlite3') as target:db.backup(target)
save('query-verification.json',queries)
save('artifact.json',A);save('chart-map.json',MAP)
(P/'report.md').write_text(markdown_all())
save('report-design.json',{'audience':'product stakeholders','spine':'行业基础→样本配置→支付差异→活动条件→内容分发→渠道差异→Waje验证优先级','source_boundary':'原材料静态探索；现行条款独立列；不计算市场份额','required_roles':{'title':'title','summary':'summary','findings':'industry through retail','recommendations':'waje/actions','further_questions':'followup','caveats':'就近说明+附表'},'language_override':'按用户要求全中文标题与正文，保留必要品牌与缩写','checks':['8个模块','19品牌','25工作表','265公式复算','同源不当独立','无未知填零','官方/材料/冲突/访问受限分开']})
print(json.dumps({'charts':len(M['charts']),'tables':len(M['tables']),'blocks':len(M['blocks']),'characters':len(markdown_all()),'title':TITLE},ensure_ascii=False))

import csv,io,json,re,subprocess,html
from pathlib import Path
from datetime import date,timedelta,datetime
R=Path(__file__).resolve().parent;P=R.parents[1]
def read(name):
 d=json.loads((R/'sources'/name).read_text());rr=list(csv.reader(io.StringIO(d['annotated_csv'])));h=[re.sub(r'\s|\\n','',re.sub(r'^\[row=\d+\]\s*','',v)) for v in rr[0]];out=[]
 for row in rr[1:]:
  if not row:continue
  row[0]=re.sub(r'^\[row=\d+\]\s*','',row[0]);r=dict(zip(h,row));name=r.get('游戏',r.get('游戏类型',''))
  if re.sub(r'[\s_-]','',name).lower() not in ['tower','9013','爬塔']:continue
  for fmt in ['%Y/%m/%d','%Y-%m-%d','%m/%d/%y']:
   try:r['day']=datetime.strptime(row[0],fmt).date().isoformat();out.append(r);break
   except ValueError:pass
 return out
allsets={n:read(n) for n in ['v1-games.json','v1-detail.json','game-live.json','detail-live.json']}
def table(headers,rows):return '<table><thead><tr>'+''.join('<th background-color="light-gray"><p><b>'+html.escape(h)+'</b></p></th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td><p>'+html.escape(str(v))+'</p></td>' for v in r)+'</tr>' for r in rows)+'</tbody></table>'
days=[]
for i in range(14):
 day=(date(2026,8,11)+timedelta(days=i)).isoformat();hit=[r for r in allsets['game-live.json'] if r['day']==day]
 days.append([day,'无Tower记录' if not hit else hit[0]['基础下注额'],'N/A' if not hit else hit[0]['完全下注额'],'N/A' if not hit else hit[0]['完全实际盈利'],'N/A' if not hit else '698.311%','缺失，不计零' if not hit else '仅1日小额异常样本'])
section='<p><b>调整前14天与调整后14天必须分开展示。</b>前版仅比较调整后的两周，未在主表展现调整前数据，无法直接回答8月25日调整效果。本次补查V1历史报表（修订9）的分游戏与详细奖池，并与V2（修订1600）交叉核对。</p>'
section+=table(['窗口','计划天数 / 有记录天数','完全下注额','基础RTP','完全RTP','前后变化是否可判定'],[
['调整前 8/11—8/24','14 / 1','3,600.55（仅8/24）','698.311%（仅8/24）','698.311%（仅8/24）','否：13日无记录，唯一日异常'],
['调整日 8/25','1 / 1','1,294,167.16','100.154%','100.464%','日内生效时间未确认'],
['调整后 8/25—9/7','14 / 14','23,919,751.63','99.527%','99.662%','相对调整前：N/A，不计算因果增幅'],
['后期第一周 8/25—8/31','7 / 7','14,367,805.10','98.679%','99.031%','只作调整后走势参照'],
['后期第二周 9/1—9/7','7 / 7','9,551,946.53','100.804%','100.611%','较后期第一周+1.580个百分点']])
section+='<p><b>调整前逐日覆盖：</b>以下N/A表示报表没有Tower记录，不代表实际下注为零；8月24日为观察到的单日值，不扩展为两周总量。</p>'+table(['日期','基础下注','完全下注','实际利润','实际RTP','状态'],days)
section+='<p><b>V1与V2同日口径不一致，不能拼接或互相替代。</b>V1的8月24日下注为0、利润−22,000，表内RTP虽显示0%，按金额公式应为N/A；V2同日下注3,600.55、利润−21,542.47。8月25日V1下注7,407，V2下注1,294,167.16，表明两者覆盖范围或数据处理存在重大差异，尚未确定原因。</p>'+table(['日期','来源','完全下注','完全实际利润','金额复算RTP'],[['8/24','V1','0.00','-22,000.00','N/A（分母为0）'],['8/24','V2','3,600.55','-21,542.47','698.311%'],['8/25','V1','7,407.00','4,280.32','42.212%'],['8/25','V2','1,294,167.16','-6,000.64','100.464%']])
section+='<p>目前在这两份历史报表中仍未检出8月11日—23日Tower/9013记录。若存在另一份覆盖老版Tower、其他游戏ID或其他包体的历史报表，应先核实映射和范围后纳入。现有证据只能分析后期RTP组成，不能断言8月25日调整前后RTP升高。</p><p><a href="https://ksg964l11fam.sg.larksuite.com/wiki/YdCPw8309izVigkMq8HlFohNgdh">本次补查：Lifecycle Pool 2026.7.1-8.25（V1）</a></p>'
(R/'preperiod-correction.xml').write_text(section)
(R/'preperiod-audit.json').write_text(json.dumps({k:{'tower_rows':len(v),'dates':sorted(set(r['day'] for r in v))} for k,v in allsets.items()},ensure_ascii=False,indent=2))
cli='/Users/robin/.local/node/bin/lark-cli';doc='ArbPdvZluov5h3xp920l7bWugTg'
res=subprocess.run([cli,'docs','+update','--doc',doc,'--command','block_replace','--block-id','doxlg8WfGDqeMqkNteQqp3IZlxg','--content',section,'--as','user','--format','json'],capture_output=True,text=True);print(res.stdout);res.check_returncode()
summary='<callout background-color="light-blue" border-color="blue"><p><b>8月25日调整是否使Tower的RTP提升，目前缺少可比的调整前数据，尚不能判定。</b>前14天只有8月24日一条小额异常记录；V1/V2同日数据差异明显。下文已补列调整前逐日覆盖和前后窗口对照。</p><p><b>已能确认的是调整后的账面结构：</b>第二周完全RTP较第一周上升1.580个百分点，而净补偿及控制影响减少0.545个百分点，基础RTP上升2.124个百分点。此结果不支持直接额外补偿增加为后期上涨主因；仍不能排除规则通过基础开奖或人群结构发挥作用。</p></callout>'
res=subprocess.run([cli,'docs','+update','--doc',doc,'--command','block_replace','--block-id','doxlg1PyQyBSzG0sduj1qDEwUve','--content',summary,'--as','user','--format','json'],capture_output=True,text=True);print(res.stdout);res.check_returncode()
# Keep the correction reproducible without overwriting unrelated cloud changes.
old=(R/'report.xml').read_text();start=old.index('<callout');end=old.index('</callout>',start)+len('</callout>');old=old[:start]+summary+old[end:]
start=old.index('<p>已全量读取');end=old.index('</p>',start)+4;old=old[:start]+section+old[end:];(R/'report.xml').write_text(old)

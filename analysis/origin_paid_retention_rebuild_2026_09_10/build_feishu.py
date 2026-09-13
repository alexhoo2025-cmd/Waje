import json,re,html,xml.etree.ElementTree as E
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];OUT=P/'feishu-2026-09-11'
a=json.loads((OUT/'source-artifact.json').read_text());data=json.loads((P/'analysis.json').read_text());channels=json.loads((P/'channels.json').read_text());images={r['id']:r for r in json.loads((OUT/'chart-captures.json').read_text())}
def inline(s):
 return ''.join('<b>'+html.escape(t[2:-2])+'</b>' if t.startswith('**')and t.endswith('**')else html.escape(t)for t in re.split(r'(\*\*[^*]+\*\*)',str(s)))
def md(body):
 out=[];lines=body.splitlines();i=0
 while i<len(lines):
  s=lines[i].strip()
  if not s:i+=1;continue
  if s.startswith('#'):
   text=re.sub(r'^\d+[｜|.、]\s*','',s.lstrip('#').strip());out.append('<h1 seq="auto">'+inline(text)+'</h1>')
  elif s.startswith('- ')or re.match(r'^\d+\. ',s):
   ordered=not s.startswith('- ');tag='ol'if ordered else'ul';items=[]
   while i<len(lines)and(re.match(r'^\d+\. ',lines[i])if ordered else lines[i].startswith('- ')):
    items.append('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',lines[i]))+'</li>');i+=1
   out.append('<'+tag+'>'+''.join(items)+'</'+tag+'>');continue
  else:out.append('<p>'+inline(s)+'</p>')
  i+=1
 return '\n'.join(out)
def val(v):return f'{v:,}'if isinstance(v,int)else f'{v:,.2f}'if isinstance(v,float)else str(v)
style_records=[]
def table(spec):
 rows=a['snapshot']['datasets'][spec['dataset']];cols=spec['columns'];tid=spec['id'];ratecols={c['field']for c in cols if re.fullmatch(r'第(?:2|7|15|30)日',c['field'])}
 extrema={}
 if tid=='new-paid':
  for field in ratecols:
   day=int(re.search(r'\d+',field)[0]);raw=[next(r['rate_pct']for r in data['retention']if r['unit']==channels[i]['sheet']and r['population']=='新增付费'and r['sample_mode']=='各日达标范围'and r['day']==day)for i in range(len(rows))]
   extrema[field]=(raw,max(raw),min(raw))
 peaks={c['field']:max(float(r[c['field']].strip('%'))for r in rows)for c in cols[1:]}if tid=='decay-detail'else{}
 widths=[180]+[100]*(len(cols)-1)
 out=['<p><b>'+html.escape(spec['title'])+'</b></p>']
 if tid=='new-paid':out.append('<p>同列比较：蓝色为最高留存率，橙色为最低留存率；显示值相同时按原始精度判定。</p>')
 if tid=='decay-detail':out.append('<p>衰减越大，暖色色阶越深；标注各列峰值。蓝色负值表示回访率回升。</p>')
 out.append('<table><colgroup>'+''.join(f'<col width="{w}"/>'for w in widths)+'</colgroup><thead><tr>'+''.join('<th background-color="light-gray"><p><b>'+html.escape(c['label'])+'</b></p></th>'for c in cols)+'</tr></thead><tbody>')
 for i,row in enumerate(rows):
  cells=[]
  for j,col in enumerate(cols):
   field=col['field'];v=val(row[field]);bg='light-gray'if i%2 else None;marker=None;strong=False
   if field in extrema:
    values,mx,mn=extrema[field]
    if values[i]==mx:bg='light-blue';marker='最高';strong=True
    elif values[i]==mn:bg='light-orange';marker='最低';strong=True
   if tid=='decay-detail'and j>0:
    n=float(v.strip('%'));bg='light-blue'if n<0 else'light-orange'if n>=15 else'light-yellow'if n>=8 else'light-gray';strong=True
    if n==peaks[field]:marker='峰值'
   text=('<b>'+inline(v)+'</b>')if strong else inline(v)
   if marker:text+='<br/>'+marker
   cells.append('<td vertical-align="middle"'+(f' background-color="{bg}"'if bg else'')+'><p>'+text+'</p></td>')
   if marker or(tid=='decay-detail'and j>0):style_records.append({'table':tid,'row':i,'column':j,'value':v,'background':bg,'marker':marker})
  out.append('<tr>'+''.join(cells)+'</tr>')
 out.append('</tbody></table>');return '\n'.join(out)
out=['<title>'+html.escape(a['manifest']['title'])+'</title>']
for block in a['manifest']['blocks']:
 if block['id']=='title':continue
 if block['type']=='markdown':
  text=md(block['body'])
  if block['id']=='summary':
   heading,rest=text.split('</h1>',1);text=heading+'</h1>\n<callout background-color="light-blue" border-color="blue">'+rest+'</callout>'
  out.append(text)
 elif block['type']=='table':out.append(table(next(t for t in a['manifest']['tables']if t['id']==block['tableId'])))
 elif block['type']=='chart':
  im=images[block['chartId']];relative=Path(im['path']).relative_to(ROOT);out.append(f'<img path="@./{relative}" width="820" name="'+html.escape(im['title'],quote=True)+'"/>')
xml='\n'.join(out);E.fromstring('<doc>'+xml+'</doc>');assert xml.count('<table>')==6 and xml.count('<img ')==5
(ROOT/'draft_6db4a0f1_folder/draft.xml').write_text(xml)
(OUT/'release.xml').write_text(xml)
(OUT/'table-styles.json').write_text(json.dumps(style_records,ensure_ascii=False,indent=2))
print(json.dumps({'tables':6,'images':5,'headings':xml.count('<h1 '),'chars':len(xml),'highlighted_cells':len(style_records)},ensure_ascii=False))

import json,re,html,xml.etree.ElementTree as E
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];R=P/'revisions/2026-09-10-final-polish'
a=json.loads((R/'artifact.json').read_text());imgs=json.loads((R/'images.json').read_text())
def inline(s):
    return ''.join('<b>'+html.escape(p[2:-2])+'</b>' if p.startswith('**') and p.endswith('**') else html.escape(p) for p in re.split(r'(\*\*[^*]+\*\*)',str(s)))
def table(headers,rows):
    cols=len(headers);out=['<table><colgroup>'+''.join(f'<col width="{210 if i==1 else 130}"/>' for i in range(cols))+'</colgroup><thead><tr>'+''.join('<th background-color="light-gray"><p>'+inline(x)+'</p></th>' for x in headers)+'</tr></thead><tbody>']
    peaks={}
    for i,h in enumerate(headers):
        if any(w in h for w in ['留存','衰减','第14日','第60日']):
            vals=[float(str(r[i]).strip('%')) for r in rows if re.fullmatch(r'\d+(?:\.\d+)?%',str(r[i]))]
            if vals:peaks[i]=max(vals)
    for n,row in enumerate(rows):
        text=' '.join(map(str,row));color='light-blue' if 'Android' in text else 'light-green' if 'iOS' in text else 'light-yellow' if 'H5' in text else ('light-gray' if n%2==0 else None)
        cells=[]
        for i,v in enumerate(row):
            peak=i in peaks and re.fullmatch(r'\d+(?:\.\d+)?%',str(v)) and float(str(v).strip('%'))==peaks[i]
            bg='light-yellow' if peak else color
            cells.append('<td'+(f' background-color="{bg}"' if bg else '')+'><p>'+('<b>'+inline(v)+'</b>' if peak else inline(v))+'</p></td>')
        out.append('<tr>'+''.join(cells)+'</tr>')
    return ''.join(out)+'</tbody></table>'
def md(body):
    lines=body.splitlines();out=[];i=0
    while i<len(lines):
        s=lines[i].strip()
        if not s:i+=1;continue
        if s.startswith('|') and i+1<len(lines) and re.match(r'^\|\s*[-:]',lines[i+1]):
            split=lambda x:[t.strip() for t in x.strip().strip('|').split('|')]
            headers=split(s);rows=[];i+=2
            while i<len(lines) and lines[i].startswith('|'):rows.append(split(lines[i]));i+=1
            out.append(table(headers,rows));continue
        if s.startswith('#'):
            level=len(s)-len(s.lstrip('#'));t=re.sub(r'^\d+[｜|.、]\s*','',s[level:].strip());tag='h'+str(max(1,level-1));out.append(f'<{tag} seq="auto">'+inline(t)+f'</{tag}>')
        elif s.startswith('- ') or re.match(r'^\d+\. ',s):
            ordered=not s.startswith('- ');tag='ol' if ordered else 'ul';items=[]
            while i<len(lines) and (re.match(r'^\d+\. ',lines[i]) if ordered else lines[i].startswith('- ')):
                items.append('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',lines[i]))+'</li>');i+=1
            out.append('<'+tag+'>'+''.join(items)+'</'+tag+'>');continue
        else:out.append('<p>'+inline(s)+'</p>')
        i+=1
    return '\n'.join(out)
out=['<title>'+html.escape(a['manifest']['title'])+'</title>'];imagecount=0
for b in a['manifest']['blocks']:
    if b['id']=='title':continue
    if b['type']=='markdown':
        content=md(b['body'])
        if b['id']=='summary':
            h,rest=content.split('</h1>',1);content=h+'</h1><callout background-color="light-blue" border-color="blue">'+rest+'</callout>'
        out.append(content)
    elif b['type']=='table':
        t=next(t for t in a['manifest']['tables'] if t['id']==b['tableId']);headers=[c['label'] for c in t['columns']];rows=[]
        for r in a['snapshot']['datasets'][t['dataset']]:
            values=[]
            for c in t['columns']:
                v=r.get(c['field']);values.append('暂无可比数据' if v is None else f'{v:,.2f}' if isinstance(v,float) else f'{v:,}' if isinstance(v,int) else str(v))
            rows.append(values)
        out.append('<p><b>'+html.escape(t['title'])+'</b></p>'+table(headers,rows))
    elif b['type']=='html' and '<table' in b['body']:
        doc=E.fromstring('<doc>'+b['body']+'</doc>');headers=[''.join(c.itertext()) for c in doc.findall('.//thead/tr/th')];rows=[[''.join(c.itertext()) for c in row.findall('td')] for row in doc.findall('.//tbody/tr')]
        out.append('<p><b>首次付费（历史首充）：6—8月短期留存</b></p>'+table(headers,rows))
    elif b['type'] in ['html','chart']:
        if b['type']=='chart':id=b['chartId']
        else:id='new-decay' if '逐日衰减' in b['body'] else 'first_curve' if '首次付费（历史首充）' in b['body'] else 'new_curve'
        path=Path(imgs[id]).relative_to(ROOT);out.append(f'<img path="@./{path}" width="1000" caption="'+html.escape({'new-decay':'留存率观察值的逐日衰减','first_curve':'首次付费用户活跃留存','new_curve':'新增付费用户活跃留存','paid-rate-chart':'注册当日付费率'}[id])+'"/>');imagecount+=1
out.append('<p>来源：本报告保存的服务端成功付费、账号活跃聚合及独立H5联运生命周期数据；账号留存截至2026年9月3日。本文为最后修改版的阅读整理，未新增线上查询。</p>')
xml='\n'.join(out);assert imagecount==4
(ROOT/'draft_98863e35_folder/draft.xml').write_text(xml)
(R/'lark-release.xml').write_text(xml)
(R/'报告.md').write_text('\n\n'.join(b.get('body','') for b in a['manifest']['blocks'] if b['type']=='markdown'))
print(json.dumps({'tables':xml.count('<table>'),'images':imagecount,'chars':len(xml),'draft':'draft_98863e35_folder/draft.xml'}))

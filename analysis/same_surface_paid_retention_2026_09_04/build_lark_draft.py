"""Render the same canonical narrative/tables to native, readable Lark XML."""
import html
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
DRAFT=PROJECT/'draft_13d5a181_folder/draft.xml'

def inline(s):
    parts=re.split(r'(\*\*.*?\*\*)',str(s))
    return ''.join('<b>'+html.escape(p[2:-2])+'</b>' if p.startswith('**') and p.endswith('**') else html.escape(p) for p in parts)

def body_xml(body):
    out=[]
    for part in body.split('\n\n'):
        lines=part.splitlines()
        if part.startswith('### '):
            title=re.sub(r'^\d+[｜|.、]\s*','',part[4:]);out.append('<h2 seq="auto">'+inline(title)+'</h2>')
        elif part.startswith('## '):
            title=re.sub(r'^\d+[｜|.、]\s*','',part[3:]);out.append('<h1 seq="auto">'+inline(title)+'</h1>')
        elif lines and all(re.match(r'^\d+\. ',x) for x in lines):
            out.append('<ol>'+''.join('<li>'+inline(re.sub(r'^\d+\. ','',x))+'</li>' for x in lines)+'</ol>')
        elif lines and all(x.startswith('- ') for x in lines):
            out.append('<ul>'+''.join('<li>'+inline(x[2:])+'</li>' for x in lines)+'</ul>')
        else:out.append('<p>'+inline(part).replace('\n','<br/>')+'</p>')
    return '\n'.join(out)

def cell(value,column):
    if value is None:return '未成熟／不可计算'
    if column.get('format')=='number' and isinstance(value,(int,float)):
        return f'{value:,}' if isinstance(value,int) else f'{value:,.2f}'
    return str(value)

def main():
    a=json.loads((ROOT/'artifact.json').read_text());m=a['manifest'];ds=a['snapshot']['datasets']
    tables={t['id']:t for t in m['tables']};charts={c['id']:c for c in m['charts']}
    out=['<title>'+html.escape(m['title'])+'</title>','<p>数据观察截至2026年9月3日｜阶段版｜HTML与本文使用同一套数据及口径</p>']
    for b in m['blocks']:
        if b['id']=='title':continue
        if b['type']=='markdown':out.append(body_xml(b['body']))
        elif b['type']=='table':
            t=tables[b['tableId']];cols=t['columns'];rows=ds[t['dataset']]
            out.append('<p><b>'+html.escape(t['title'])+'</b></p>')
            widths=[100]*len(cols)
            if len(cols)>2:widths[1]=200
            out.append('<table><colgroup>'+''.join(f'<col width="{w}"/>' for w in widths)+'</colgroup><thead><tr>'+''.join('<th background-color="light-gray"><p>'+html.escape(c['label'])+'</p></th>' for c in cols)+'</tr></thead><tbody>')
            for row in rows:
                out.append('<tr>'+''.join('<td><p>'+html.escape(cell(row.get(c['field']),c))+'</p></td>' for c in cols)+'</tr>')
            out.append('</tbody></table>')
        elif b['type']=='chart':
            c=charts[b['chartId']];path=ROOT/'charts'/(c['id']+'.png');assert path.exists()
            out.append('<p><b>'+html.escape(c['title'])+'</b></p>')
            out.append(f'<img path="@./{path.relative_to(PROJECT)}" width="1000" caption="'+html.escape(c['title']+'｜来源：BigQuery只读聚合；统计窗口与相邻正文一致')+'"/>')
    out.append('<p>来源：wajenigeria 起源服务端注册与支付成功事件、客户端及网页活跃、账号日活对账；历史背景为6—8月已保存的服务端成功付费与画像首平台聚合。实际端观察仅覆盖9月1—3日，不将日期范围扩大解释为历史已完成。</p>')
    xml='\n'.join(out)
    DRAFT.write_text(xml,encoding='utf-8')
    (ROOT/'lark_release_candidate.xml').write_text(xml,encoding='utf-8')
    print(json.dumps({'draft':str(DRAFT.relative_to(PROJECT)),'tables':xml.count('<table>'),'images':xml.count('<img '),'chars':len(xml)},ensure_ascii=False))

if __name__=='__main__':main()

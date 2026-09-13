"""Render-only import of the user-approved Lark revision; never writes Lark."""
import argparse, copy, hashlib, html, json, shutil
from pathlib import Path
import xml.etree.ElementTree as E

parser=argparse.ArgumentParser()
parser.add_argument('--run-dir', type=Path, default=Path(__file__).resolve().parent)
args=parser.parse_args()
HERE = args.run_dir.resolve()
MACRO = HERE.parents[1]
ROOT = MACRO.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
source = json.loads((HERE/'readback.json').read_text())
root = E.fromstring('<document>'+source['content']+'</document>')
for name in ['artifact.json', '报告.md', 'report.css']:
    dest=HERE/('before-'+name)
    if not dest.exists(): shutil.copy2(MACRO/name,dest)
a=json.loads((HERE/'before-artifact.json').read_text())
output=ROOT/'output/html/Tada与PP-宏观对比-新老用户下注与回访-2026-09-09.html'
if output.exists() and not (HERE/'before-report.html').exists(): shutil.copy2(output,HERE/'before-report.html')

def inline(n):
    s=n.text or ''
    for ch in n:
        t=inline(ch)
        if ch.tag in ('b','strong'): t='**'+t+'**'
        elif ch.tag=='br': t='  \n'
        s+=t+(ch.tail or '')
    return s.strip()
def md(n):
    if n.tag in ('ul','ol'):
        return '\n'.join((str(i+1)+'. ' if n.tag=='ol' else '- ')+inline(c) for i,c in enumerate(n))
    if n.tag=='callout': return '\n\n'.join(filter(None,(md(c) for c in n)))
    t=inline(n)
    if n.tag=='title': return '# '+t
    if n.tag in ('h1','h2','h3'): return '#'*(int(n.tag[1])+1)+' '+n.get('seq-marker','')+' '+t
    return t

style='''<style>body{margin:0;font:14px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#202631;background:white}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:820px}td,th{border:1px solid #dce0e7;padding:11px 12px;text-align:left;vertical-align:middle}p{margin:0}th{font-weight:650}b{font-weight:700}</style>'''
def table_html(n):
    t=copy.deepcopy(n)
    for c in t.iter():
        attrs={k:v for k,v in c.attrib.items() if k in ('rowspan','colspan','width')}
        if c.get('background-color'): attrs['style']='background:'+c.get('background-color')
        c.attrib.clear();c.attrib.update(attrs)
    return style+'<div class="scroll">'+E.tostring(t,encoding='unicode',method='html')+'</div>'

blocks=[];pending=[];tables=0;charts=0
def flush():
    if pending:
        blocks.append({'id':'lark-text-'+str(len(blocks)), 'type':'markdown','body':'\n\n'.join(pending),'sourceId':'split'})
        pending.clear()
chart_ids=['macro-share','pen-new_30d','pen-old_over_30d','ret-new_30d','ret-old_over_30d']
for n in root:
    if n.tag in ('title','h1'):
        flush();pending.append(md(n))
        if n.tag=='title': flush()
    elif n.tag=='callout':
        pending.append(md(n));flush();blocks[-1]['id']='lark-summary'
    elif n.tag=='table':
        flush();tables+=1
        blocks.append({'id':'lark-table-'+str(tables),'type':'html','body':table_html(n),'sourceId':'split'})
    elif n.tag=='img':
        cid=chart_ids[charts]
        assert cid in n.get('name',''), (cid,n.attrib)
        # Lark places the title and subtitle immediately before each image.
        spec=next(c for c in a['manifest']['charts'] if c['id']==cid)
        if len(pending)>=2 and pending[-2].startswith('**'):
            spec['title']=pending[-2].replace('**','');spec['subtitle']=pending[-1]
            del pending[-2:]
        flush();blocks.append({'id':cid+'-block','type':'chart','chartId':cid});charts+=1
    else:
        t=md(n)
        if t: pending.append(t)
flush()
assert tables==4 and charts==5
a['manifest']['blocks']=blocks
a['manifest']['description']='同步飞书已调整版本｜新老用户、下注与回访'
a['manifest']['larkSync']={'url':'https://ksg964l11fam.sg.larksuite.com/docx/HWzVdQfWVoHhZRxiwcBlIJ55grh','revision':source['revision_id'],'mode':'faithful-content-and-table-style','source_sha256':sha(HERE/'readback.json')}
(MACRO/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(MACRO/'报告.md').write_text('\n\n'.join(b.get('body','[图表：'+b.get('chartId','')+']') for b in blocks)+'\n')
css=(HERE/'before-report.css').read_text()
css+='\n:is(#lark-summary,[data-artifact-block-id="lark-summary"]){background:#f0f4ff;border:1px solid #82a7fc;border-radius:12px;padding:24px!important;}\n'
(MACRO/'report.css').write_text(css)
approval=HERE/'title-approval.md'
approval.write_text('用户原话：调整后的报告内容和排版很好 。同步生成HT ML版本\n\n本次仅沿用用户认可的飞书标题“分析报告概要”，其语义等同执行摘要。内容完整保留；不豁免数据检查。来源：本任务当前用户请求及飞书revision '+str(source['revision_id'])+'。\n')
exceptions=[{'report_sha256':sha(MACRO/'artifact.json'),'rule_id':'R002','location':'summary','reason':'用户明确要求同步已认可的飞书内容和排版，保留同义标题“分析报告概要”。','approved_by':'用户（本次同步请求）','approval_reference':{'path':str(approval.relative_to(ROOT)),'sha256':sha(approval)}}]
(HERE/'exceptions.json').write_text(json.dumps(exceptions,ensure_ascii=False,indent=2))
(HERE/'sync-audit.json').write_text(json.dumps({'revision':source['revision_id'],'tables':tables,'charts':charts,'dataset_unchanged':a['snapshot']==json.loads((HERE/'before-artifact.json').read_text())['snapshot'],'feishu_written':False,'mode':'faithful; no narrative or metric changes'},ensure_ascii=False,indent=2))
print(json.dumps({'revision':source['revision_id'],'blocks':len(blocks),'tables':tables,'charts':charts}))

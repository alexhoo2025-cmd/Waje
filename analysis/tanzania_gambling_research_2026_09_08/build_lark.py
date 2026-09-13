"""Create Lark XML from the same canonical report blocks and datasets."""
from pathlib import Path
import json,re,html,hashlib,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
A=json.loads((P/'artifact.json').read_text());M=A['manifest'];D=A['snapshot']['datasets']
def inline(s):
    s=html.escape(str(s),quote=True)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b><span background-color="light-blue">\1</span></b>',s)
    s=re.sub(r'`([^`]+)`',r'<span>\1</span>',s)
    return s
def narrative(s):
    out=[];listing=False
    for para in s.split('\n\n'):
        if para.startswith('# '):continue
        if para.startswith('## '):out.append('<h1>'+inline(para[3:])+'</h1>')
        elif para.startswith('### '):out.append('<h2>'+inline(para[4:])+'</h2>')
        elif re.match(r'\d+\. ',para):out.append('<ol>'+''.join('<li>'+inline(re.sub(r'^\d+\. ','',line))+'</li>' for line in para.splitlines() if line)+'</ol>')
        else:out.append('<p>'+inline(para).replace('\n','<br/>')+'</p>')
    return ''.join(out)
out=['<title>'+html.escape(M['title'])+'</title>'];checks=[]
for b in M['blocks']:
    if b['type']=='markdown':out.append(narrative(b['body']))
    elif b['type']=='chart':
        c=next(c for c in M['charts'] if c['id']==b['chartId']);asset=P/'lark_assets'/f"{c['id']}.png"
        assert asset.is_file(),asset
        out.append(f'<img path="@./{asset.relative_to(ROOT)}" caption="{html.escape(c["title"])}"/>')
        checks.append({'chart':c['id'],'sha256':hashlib.sha256(asset.read_bytes()).hexdigest()})
    elif b['type']=='table':
        t=next(t for t in M['tables'] if t['id']==b['tableId']);cols=t['columns'];rows=D[t['dataset']]
        out.append('<p><b>'+html.escape(t['title'])+'</b></p>')
        width=130 if len(cols)>=6 else 1020//len(cols)
        out.append('<table><colgroup>'+''.join(f'<col width="{width}"/>' for c in cols)+'</colgroup><thead><tr>'+''.join('<th background-color="light-gray"><p>'+inline(c['label'])+'</p></th>' for c in cols)+'</tr></thead><tbody>')
        for row in rows:
            out.append('<tr>')
            for i,c in enumerate(cols):
                v=row[c['field']];text=inline(v)
                if c['field']=='url':text='<a href="'+html.escape(str(v),quote=True)+'">查看原始来源</a>'
                if i==0:text='<b>'+text+'</b>'
                out.append('<td vertical-align="top"><p>'+text+'</p></td>')
            out.append('</tr>')
        out.append('</tbody></table>')
xml='\n'.join(out)
ET.fromstring('<document>'+xml+'</document>')
(ROOT/'draft_fc010586_folder/draft.xml').write_text(xml)
(P/'lark-release.xml').write_text(xml)
(P/'lark-image-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps({'chars':len(xml),'tables':xml.count('<table>'),'images':xml.count('<img '),'draft':'draft_fc010586_folder/draft.xml'},ensure_ascii=False))

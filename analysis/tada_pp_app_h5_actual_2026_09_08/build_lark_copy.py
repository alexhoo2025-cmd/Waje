"""Convert the canonical report and exact shared-renderer charts into Lark XML."""
from pathlib import Path
import json,re,html,subprocess,hashlib,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
DRAFT=ROOT/'draft_bad6327b_folder/draft.xml'
HTML=ROOT/'output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html'
NODE='/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
SHARP='/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'
A=json.loads((P/'artifact.json').read_text());M=A['manifest'];DS=A['snapshot']['datasets']
ASSETS=P/'lark-assets';ASSETS.mkdir(exist_ok=True)
def esc(s):return html.escape(str(s),quote=True)
def inline(s):
    out=[]
    for part in re.split(r'(\*\*.*?\*\*|`[^`]+`|\[[^\]]+\]\([^)]*\))',s):
        if part.startswith('**') and part.endswith('**'):out.append('<b>'+esc(part[2:-2])+'</b>')
        elif part.startswith('`') and part.endswith('`'):out.append(esc(part[1:-1]))
        elif re.fullmatch(r'\[[^\]]+\]\([^)]*\)',part):
            t,u=re.match(r'\[([^\]]+)\]\(([^)]*)\)',part).groups();out.append('<a href="'+esc(u)+'">'+esc(t)+'</a>')
        else:out.append(esc(part))
    return ''.join(out)
def markdown(s):
    result=[]
    for para in re.split(r'\n\s*\n',s.strip()):
        if re.match(r'^#{1,6} ',para):
            prefix,text=para.split(' ',1);level=max(1,len(prefix)-1);text=re.sub(r'^\d+｜','',text)
            result.append(f'<h{level} seq="auto">{inline(text)}</h{level}>')
        elif re.match(r'^\d+\. ',para):
            items=[re.sub(r'^\d+\. ','',x.strip()) for x in para.splitlines() if x.strip()]
            result.append('<ol>'+''.join('<li>'+inline(x)+'</li>' for x in items)+'</ol>')
        elif para.startswith('- '):result.append('<ul>'+''.join('<li>'+inline(x[2:])+'</li>' for x in para.splitlines() if x.startswith('- '))+'</ul>')
        else:result.append('<p>'+inline(' '.join(para.splitlines()))+'</p>')
    return '\n'.join(result)

pattern=r'data-static-chart-block-id="([^"]+)"[^>]*><div class="portable-static-chart-variant portable-static-chart-light"[^>]*>(<svg.*?</svg>)(.*?)(?=<div class="portable-static-chart-variant portable-static-chart-dark")'
matches=re.findall(pattern,HTML.read_text(),re.S)
assert len(matches)==len(M['charts'])==7,(len(matches),len(M['charts']))
images={}
for bid,svg,extra in matches:
    w,h=map(float,re.search(r'<svg width="([\d.]+)" height="([\d.]+)"',svg).groups())
    inner=re.sub(r'^<svg[^>]*>','',svg).removesuffix('</svg>')
    legends=re.findall(r'style="--portable-legend-color:([^"]+)"[^>]*></span><span>(.*?)</span>',extra,re.S)
    outw,outh=int(w+48),int(h+32+(40 if legends else 0))
    out=f'<svg xmlns="http://www.w3.org/2000/svg" width="{outw}" height="{outh}" viewBox="0 0 {outw} {outh}"><rect width="100%" height="100%" fill="white"/><g transform="translate(24,12)">{inner}</g>'
    if legends:
        spans=[max(90,len(html.unescape(t))*15+32) for _,t in legends];x=max(20,(outw-sum(spans))/2)
        for (color,label),span in zip(legends,spans):
            out+=f'<rect x="{x}" y="{h+31}" width="10" height="10" fill="{esc(color)}"/><text x="{x+17}" y="{h+41}" font-family="Arial, PingFang SC, sans-serif" font-size="14" fill="#34465c">{label}</text>';x+=span
    out+='</svg>'
    path=ASSETS/(bid+'.svg');path.write_text(out)
    images[bid]={'svg':str(path),'png':str(path.with_suffix('.png')),'width':outw,'height':outh}
js='const sharp=require(process.argv[1]);const items=JSON.parse(process.argv[2]);Promise.all(items.map(p=>sharp(p.svg,{density:160}).flatten({background:"white"}).png().toFile(p.png))).catch(e=>{console.error(e);process.exitCode=1});'
subprocess.run([NODE,'-e',js,SHARP,json.dumps(list(images.values()))],check=True)
tables={t['id']:t for t in M['tables']};charts={c['id']:c for c in M['charts']}
xml=['<title>'+esc(M['title'])+'</title>'];expected_tables=[]
for b in M['blocks']:
    if b['id']=='title':continue
    if b['type']=='markdown':
        if b['id']=='summary':
            body=re.sub(r'^## 执行摘要\s*','',b['body']);xml.append('<h1 seq="auto">执行摘要</h1><callout background-color="light-blue" border-color="blue">'+markdown(body)+'</callout>')
        else:xml.append(markdown(b['body']))
    elif b['type']=='chart':
        c=charts[b['chartId']];a=images[b['id']]
        xml.extend(['<p><b>'+esc(c['title'])+'</b></p>','<p>'+esc(c.get('subtitle',''))+'</p>',
          '<img path="@./'+esc(str(Path(a['png']).relative_to(ROOT)))+'" width="'+str(a['width'])+'" height="'+str(a['height'])+'" caption="'+esc(c['title'])+'"/>'])
    elif b['type']=='table':
        t=tables[b['tableId']]
        if t['id']=='full-games':
            xml.append('<p><b>附表｜完整共同游戏对照与回访明细</b></p><p>下列附件与HTML附表来自同一份复算结果，便于筛选与复核；正文保留关键游戏和成熟回访结论。</p>')
            for name in ['共同游戏对照.csv','回访分子分母.csv','四组合新老用户.csv']:
                xml.append('<source path="@./'+esc(str((P/name).relative_to(ROOT)))+'" name="'+esc(name)+'"/>')
            continue
        cols=t['columns'];rows=DS[t['dataset']]
        xml.append('<p><b>'+esc(t['title'])+'</b></p>')
        if t.get('subtitle'):xml.append('<p>'+esc(t['subtitle'])+'</p>')
        widths=[int(1000/len(cols))]*len(cols)
        if len(cols)==6 and cols[1]['field']=='游戏':widths=[90,230,170,170,170,170]
        table='<table><colgroup>'+''.join(f'<col width="{w}"/>' for w in widths)+'</colgroup><thead><tr>'
        table+=''.join('<th background-color="light-gray"><p><b>'+esc(c['label'])+'</b></p></th>' for c in cols)+'</tr></thead><tbody>'
        for row in rows:table+='<tr>'+''.join('<td vertical-align="middle"><p>'+inline(str(row.get(c['field'],'')))+'</p></td>' for c in cols)+'</tr>'
        table+='</tbody></table>';xml.append(table);expected_tables.append({'id':t['id'],'rows':len(rows),'columns':len(cols)})
    else:raise ValueError(b['type'])
content='\n\n'.join(xml)+'\n';ET.fromstring('<document>'+content+'</document>')
DRAFT.write_text(content);(P/'lark-source.xml').write_text(content)
receipt={'status':'draft_prepared','draft':str(DRAFT.relative_to(ROOT)),'title':M['title'],
 'html_sha256':hashlib.sha256(HTML.read_bytes()).hexdigest(),'artifact_sha256':hashlib.sha256((P/'artifact.json').read_bytes()).hexdigest(),
 'xml_sha256':hashlib.sha256(content.encode()).hexdigest(),'images':images,'tables':expected_tables,'attachments':3,'chapters':content.count('<h1 ')}
(P/'lark-build-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'draft':str(DRAFT.relative_to(ROOT)),'charts':len(images),'tables':len(expected_tables),'chapters':receipt['chapters'],'attachments':3},ensure_ascii=False))

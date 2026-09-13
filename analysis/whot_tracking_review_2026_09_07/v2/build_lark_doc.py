"""Convert the canonical Whot V2 artifact into native Lark XML."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
ARTIFACT=BASE/'artifact.json'
DRAFT=ROOT/'draft_a1be2d96_folder/draft.xml'

def inline(text: str) -> str:
    parts=re.split(r'(\*\*.*?\*\*|`.*?`)',text)
    out=[]
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            out.append('<b>'+html.escape(part[2:-2])+'</b>')
        elif part.startswith('`') and part.endswith('`'):
            out.append('<code>'+html.escape(part[1:-1])+'</code>')
        else:
            out.append(html.escape(part))
    return ''.join(out)

def parse_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip('|').split('|')]

def table_xml(lines: list[str], *, block_id: str='') -> str:
    header=parse_row(lines[0]);rows=[parse_row(line) for line in lines[2:]]
    count=len(header)
    if count==3: widths=[180,360,300]
    elif count==4: widths=[210,250,260,300]
    elif count==5: widths=[110,100,190,210,130]
    else: widths=[140]*count
    chunks=['<table><colgroup>'+''.join(f'<col width="{w}"/>' for w in widths)+'</colgroup>']
    chunks.append('<thead><tr>'+''.join('<th background-color="light-gray" vertical-align="middle"><p><b>'+inline(c)+'</b></p></th>' for c in header)+'</tr></thead><tbody>')
    for row in rows:
        chunks.append('<tr>')
        for i,cell in enumerate(row):
            color=''
            if block_id=='definitions_1':
                if i==0: color=' background-color="light-blue"'
                elif i==2: color=' background-color="light-green"'
            elif block_id=='scope_index' and i==1:
                color=' background-color="light-blue"' if cell=='一期' else ' background-color="light-green"'
            chunks.append(f'<td{color} vertical-align="top"><p>{inline(cell)}</p></td>')
        chunks.append('</tr>')
    chunks.append('</tbody></table>')
    return ''.join(chunks)

def markdown_xml(body: str, block_id: str) -> str:
    lines=body.splitlines();out=[];i=0
    is_summary=block_id=='summary_0'
    summary_parts=[]
    while i<len(lines):
        line=lines[i]
        if not line.strip(): i+=1;continue
        if line.startswith('# '):
            i+=1;continue
        if line.startswith('## '):
            title=re.sub(r'^\d+[｜|.]\s*','',line[3:])
            out.append('<h1 seq="auto">'+inline(title)+'</h1>');i+=1;continue
        if line.startswith('### '):
            out.append('<h2 seq="auto">'+inline(line[4:])+'</h2>');i+=1;continue
        if line.startswith('|') and i+1<len(lines) and re.match(r'^\|?\s*:?-+',lines[i+1]):
            table=[line,lines[i+1]];i+=2
            while i<len(lines) and lines[i].startswith('|'):
                table.append(lines[i]);i+=1
            out.append(table_xml(table,block_id=block_id));continue
        if re.match(r'^\d+\.\s+',line):
            items=[]
            while i<len(lines) and re.match(r'^\d+\.\s+',lines[i]):
                items.append(re.sub(r'^\d+\.\s+','',lines[i]));i+=1
            out.append('<ol>'+''.join('<li>'+inline(x)+'</li>' for x in items)+'</ol>');continue
        if line.startswith('- '):
            items=[]
            while i<len(lines) and lines[i].startswith('- '):
                items.append(lines[i][2:]);i+=1
            out.append('<ul>'+''.join('<li>'+inline(x)+'</li>' for x in items)+'</ul>');continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('# ','## ','### ','|','- ')) and not re.match(r'^\d+\.\s+',lines[i]):
            para.append(lines[i]);i+=1
        rendered=inline(' '.join(para))
        if is_summary: summary_parts.append('<p>'+rendered+'</p>')
        else: out.append('<p>'+rendered+'</p>')
    if is_summary and summary_parts:
        out.append('<callout emoji="💡" background-color="light-blue" border-color="blue">'+''.join(summary_parts)+'</callout>')
    return ''.join(out)

def native_table(spec: dict, rows: list[dict]) -> str:
    columns=spec['columns'];lines=['| '+' | '.join(c['label'] for c in columns)+' |','| '+' | '.join('---' for _ in columns)+' |']
    for row in rows:
        lines.append('| '+' | '.join(str(row.get(c['field'],'—')) for c in columns)+' |')
    return '<p><b>'+inline(spec['title'])+'</b></p>'+table_xml(lines,block_id='scope_index')

def main() -> None:
    artifact=json.loads(ARTIFACT.read_text());manifest=artifact['manifest'];datasets=artifact['snapshot']['datasets']
    table_map={item['id']:item for item in manifest['tables']}
    chart_map={item['id']:item for item in manifest['charts']}
    blocks=['<title>'+html.escape(manifest['title'])+'</title>']
    for block in manifest['blocks']:
        if block['id']=='title': continue
        if block['type']=='markdown': blocks.append(markdown_xml(block['body'],block['id']))
        elif block['type']=='table':
            spec=table_map[block['tableId']];blocks.append(native_table(spec,datasets[spec['dataset']]))
        elif block['type']=='chart':
            chart=chart_map[block['chartId']]
            blocks.append('<p><b>'+inline(chart['title'])+'</b></p>')
            blocks.append('<img path="@./analysis/whot_tracking_review_2026_09_07/v2/lark_assets/数据指标覆盖的用户旅程阶段.png" width="1000" caption="数据指标覆盖的用户旅程阶段"/>')
    xml=''.join(blocks)
    DRAFT.write_text(xml,encoding='utf-8')
    (BASE/'lark_release_candidate.xml').write_text(xml,encoding='utf-8')
    print(json.dumps({'draft':str(DRAFT.relative_to(ROOT)),'tables':xml.count('<table>'),'images':xml.count('<img '),'headings':xml.count('<h1 ')},ensure_ascii=False))

if __name__=='__main__':main()

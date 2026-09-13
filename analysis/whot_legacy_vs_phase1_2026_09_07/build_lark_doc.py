"""Build a native Lark document from the reviewed comparison Markdown."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
DRAFT=ROOT/'draft_c75bb3ad_folder/draft.xml'

def inline(text: str) -> str:
    out=[]
    for part in re.split(r'(\*\*.*?\*\*|`.*?`)',text):
        if part.startswith('**') and part.endswith('**'):out.append('<b>'+html.escape(part[2:-2])+'</b>')
        elif part.startswith('`') and part.endswith('`'):out.append('<code>'+html.escape(part[1:-1])+'</code>')
        else:out.append(html.escape(part))
    return ''.join(out)

def cells(line: str) -> list[str]:
    return [item.strip() for item in line.strip().strip('|').split('|')]

def table_xml(lines: list[str], section: str) -> str:
    head=cells(lines[0]);rows=[cells(line) for line in lines[2:]]
    widths={3:[180,230,440],4:[160,260,300,230],5:[140,210,240,250,130]}.get(len(head),[170]*len(head))
    out=['<table><colgroup>'+''.join(f'<col width="{w}"/>' for w in widths)+'</colgroup><thead><tr>']
    out.extend('<th background-color="light-gray"><p><b>'+inline(item)+'</b></p></th>' for item in head)
    out.append('</tr></thead><tbody>')
    for row in rows:
        out.append('<tr>')
        for i,item in enumerate(row):
            color=''
            if section=='一期7项需求差异' and i==4:
                color=' background-color="light-green"' if '复用' in item else ' background-color="light-yellow"' if '新增' in item else ' background-color="light-blue"'
            elif section=='指标能力变化' and i==3:
                color=' background-color="light-green"' if '可对齐' in item else ' background-color="light-blue"' if '仅新版' in item else ' background-color="light-yellow"'
            out.append(f'<td{color} vertical-align="top"><p>{inline(item)}</p></td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return ''.join(out)

def content_xml(body: str, section: str) -> str:
    lines=body.splitlines();out=[];summary=[];i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('### '):out.append('<h2 seq="auto">'+inline(line[4:])+'</h2>');i+=1;continue
        if line.startswith('!['):
            match=re.match(r'!\[(.*?)\]\((.*?)\)',line);assert match
            out.append('<img path="@./analysis/whot_legacy_vs_phase1_2026_09_07/old-vs-phase1.png" width="1000" caption="'+html.escape(match.group(1))+'"/>');i+=1;continue
        if line.startswith('|') and i+1<len(lines) and lines[i+1].startswith('|'):
            table=[line,lines[i+1]];i+=2
            while i<len(lines) and lines[i].startswith('|'):table.append(lines[i]);i+=1
            out.append(table_xml(table,section));continue
        if re.match(r'^\d+\. ',line):
            items=[]
            while i<len(lines) and re.match(r'^\d+\. ',lines[i]):items.append(re.sub(r'^\d+\. ','',lines[i]));i+=1
            out.append('<ol>'+''.join('<li>'+inline(item)+'</li>' for item in items)+'</ol>');continue
        if line.startswith('- '):
            items=[]
            while i<len(lines) and lines[i].startswith('- '):items.append(lines[i][2:]);i+=1
            out.append('<ul>'+''.join('<li>'+inline(item)+'</li>' for item in items)+'</ul>');continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('### ','![','|','- ')) and not re.match(r'^\d+\. ',lines[i]):para.append(lines[i]);i+=1
        rendered='<p>'+inline(' '.join(para))+'</p>'
        if section=='执行摘要':summary.append(rendered)
        else:out.append(rendered)
    if summary:out.insert(0,'<callout emoji="💡" background-color="light-blue" border-color="blue">'+''.join(summary)+'</callout>')
    return ''.join(out)

def main():
    markdown=(BASE/'report.md').read_text()
    first,*sections=markdown.split('\n## ')
    title=first.removeprefix('# ').strip()
    xml=['<title>'+html.escape(title)+'</title>']
    for section in sections:
        heading,_,body=section.partition('\n')
        xml.append('<h1 seq="auto">'+inline(heading.strip())+'</h1>')
        xml.append(content_xml(body,heading.strip()))
    result=''.join(xml)
    DRAFT.write_text(result)
    (BASE/'lark_release_candidate.xml').write_text(result)
    print(json.dumps({'draft':str(DRAFT.relative_to(ROOT)),'tables':result.count('<table>'),'images':result.count('<img '),'headings':result.count('<h1 ')},ensure_ascii=False))

if __name__=='__main__':main()

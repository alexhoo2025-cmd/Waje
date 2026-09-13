"""Faithful, editable Lark archive of the approved portable report."""
import hashlib
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
ASSETS = BASE / 'lark-archive-assets'
NODE = '/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
SHARP = '/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'
artifact = json.loads((BASE / 'artifact.json').read_text())
manifest, datasets = artifact['manifest'], artifact['snapshot']['datasets']
report = (BASE / 'report.html').read_text()
ASSETS.mkdir(exist_ok=True)

def esc(s):
    return html.escape(str(s), quote=True)

def inline(s):
    parts = re.split(r'(\*\*.*?\*\*|`[^`]+`|\[[^\]]+\]\([^)]*\))', str(s))
    out = []
    for x in parts:
        if x.startswith('**') and x.endswith('**'):
            out.append('<b>' + esc(x[2:-2]) + '</b>')
        elif x.startswith('`') and x.endswith('`'):
            out.append(esc(x[1:-1]))
        elif re.fullmatch(r'\[[^\]]+\]\([^)]*\)', x):
            label, url = re.match(r'\[([^\]]+)\]\(([^)]*)\)', x).groups()
            out.append('<a href="' + esc(url) + '">' + esc(label) + '</a>')
        else:
            out.append(esc(x))
    return ''.join(out)

table_records = []
def table(headers, rows, identity):
    n = len(headers)
    if n == 7:
        widths = [185, 160, 95, 145, 105, 85, 145]
    elif n == 6:
        widths = [120, 80, 210, 115, 200, 125]
    elif n == 5:
        widths = [240, 120, 130, 170, 110]
    elif n == 4:
        widths = [230, 150, 215, 215]
    elif n == 3:
        widths = [205, 220, 405]
    else:
        widths = [220, 610]
    cols = '<colgroup>' + ''.join(f'<col width="{w}"/>' for w in widths) + '</colgroup>'
    head = '<thead><tr>' + ''.join('<th background-color="light-gray"><p><b>' + inline(v) + '</b></p></th>' for v in headers) + '</tr></thead>'
    body = '<tbody>'
    for row in rows:
        assert len(row) == n, (identity, len(row), n)
        body += '<tr>' + ''.join('<td vertical-align="middle"><p>' + inline(v) + '</p></td>' for v in row) + '</tr>'
    body += '</tbody>'
    table_records.append({'id': identity, 'columns': n, 'rows': len(rows)})
    return '<table>' + cols + head + body + '</table>'

def markdown(s, block_id):
    lines = s.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|') and i + 1 < len(lines) and re.match(r'^\s*\|[\s:|\-]+\|\s*$', lines[i+1]):
            headers = [c.strip() for c in line.strip('|').split('|')]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            out.append(table(headers, rows, block_id))
            continue
        heading = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading:
            level, text = max(1, len(heading[1])-1), heading[2]
            text = re.sub(r'^\d+\.\s*', '', text)
            out.append(f'<h{level} seq="auto">{inline(text)}</h{level}>')
            i += 1
            continue
        if line.startswith('- '):
            items = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                items.append('<li>' + inline(lines[i].strip()[2:]) + '</li>')
                i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||- )', lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append('<p>' + inline(' '.join(para)) + '</p>')
    return '\n'.join(out)

chart_matches = re.findall(r'data-static-chart-block-id="([^"]+)"[^>]*><div class="portable-static-chart-variant portable-static-chart-light"[^>]*>(<svg.*?</svg>)(.*?)(?=<div class="portable-static-chart-variant portable-static-chart-dark")', report, re.S)
assert len(chart_matches) == 7
chart_files = {}
for block_id, svg, extra in chart_matches:
    width, height = map(float, re.search(r'<svg width="([\d.]+)" height="([\d.]+)"', svg).groups())
    # Reuse the exact exported plot, adding only padding and its existing HTML legend.
    inner = re.sub(r'^<svg[^>]*>', '', svg).removesuffix('</svg>')
    inner = re.sub(r'font-family="[^"]*"', 'font-family="Arial, PingFang SC, sans-serif"', inner)
    # The portable SVG fallback leaves two percentage series as raw fractions.
    # Format only labels, preserving every value, point and plotted coordinate.
    if block_id in ('rtp-line-chart', 'category-contribution-chart'):
        category = {r['game_type']: r for r in datasets['category_rollup']}
        contribution_labels = iter([f"{category[g][metric]*100:.2f}%" for metric in ['bet_share', 'net_share'] for g in ['Slot','Fish','Casino']])
        def percent_text(match):
            node = ET.fromstring(match.group(0))
            value = ''.join(node.itertext()).strip()
            if not re.fullmatch(r'\d+(?:\.\d+)?', value):
                return match.group(0)
            if node.attrib.get('text-anchor') == 'end':
                label = f'{float(value)*100:.0f}%'
            elif block_id == 'category-contribution-chart':
                label = next(contribution_labels)
            else:
                return match.group(0)
            return re.sub(r'>[^<>]*</text>$', '>' + label + '</text>', match.group(0))
        inner = re.sub(r'<text\b[^>]*>.*?</text>', percent_text, inner, flags=re.S)
    legends = re.findall(r'style="--portable-legend-color:([^"]+)"[^>]*></span><span>(.*?)</span>', extra, re.S)
    new_w, new_h = int(width+(120 if block_id == 'rtp-line-chart' else 44)), int(height+32+(36 if legends else 0))
    output = f'<svg xmlns="http://www.w3.org/2000/svg" width="{new_w}" height="{new_h}" viewBox="0 0 {new_w} {new_h}"><rect width="100%" height="100%" fill="#fff"/><g transform="translate(20,12)">{inner}</g>'
    if legends:
        spans = [max(82, len(html.unescape(label))*14+28) for _, label in legends]
        x = (new_w - sum(spans))/2
        y = height + 39
        for (color, label), span in zip(legends, spans):
            output += f'<circle cx="{x+5}" cy="{y}" r="4" fill="{esc(color)}"/><text x="{x+17}" y="{y+5}" font-family="Arial, PingFang SC, sans-serif" font-size="14" fill="#43566b">{label}</text>'
            x += span
    output += '</svg>'
    path = ASSETS / f'{block_id}.svg'
    path.write_text(output)
    chart_files[block_id] = {'svg': str(path), 'png': str(path.with_suffix('.png')), 'width': new_w, 'height': new_h}

js = 'const sharp = require(process.argv[1]); const items = JSON.parse(process.argv[2]); Promise.all(items.map(p=>sharp(p.svg,{density:192}).flatten({background:"#ffffff"}).png().toFile(p.png))).catch(e=>{console.error(e);process.exitCode=1});'
subprocess.run([NODE, '-e', js, SHARP, json.dumps(list(chart_files.values()))], check=True)

def formatted(value, column):
    if value is None:
        return 'N/A'
    if isinstance(value, str):
        return value
    if column.get('format') == 'percent':
        return f'{value*100:.2f}%'
    if isinstance(value, (int, float)):
        if value == int(value):
            return f'{value:,.0f}'
        return f'{value:,.2f}'
    return str(value)

tables = {x['id']: x for x in manifest['tables']}
charts = {x['id']: x for x in manifest['charts']}
cards = {x['id']: x for x in manifest['cards']}
title = manifest['title'] + '｜2026-09-04 存档'
xml = ['<title>' + esc(title) + '</title>']
for block in manifest['blocks']:
    kind, bid = block['type'], block['id']
    if bid == 'title':
        continue
    if bid == 'summary':
        body = re.sub(r'^## 汇总结论\s*', '', block['body'])
        xml.append('<p><b>汇总结论</b></p>')
        xml.append('<callout background-color="light-blue" border-color="blue">' + markdown(body, bid) + '</callout>')
    elif kind == 'markdown':
        xml.append(markdown(block['body'], bid))
    elif kind == 'metric-strip':
        ids = block['cardIds']
        for start in range(0, len(ids), 3):
            cols = []
            for cid in ids[start:start+3]:
                c = cards[cid]
                row = datasets[c['dataset']][0]
                metric = c['metrics'][0]
                v = formatted(row[metric['field']], metric)
                cols.append('<column width-ratio="0.3333333333333333"><p>' + esc(metric['label']) + '</p><p><b><span text-color="blue">' + esc(v) + '</span></b></p></column>')
            xml.append('<grid>' + ''.join(cols) + '</grid>')
    elif kind == 'table':
        t = tables[block['tableId']]
        rows = list(datasets[t['dataset']])
        sort = t.get('defaultSort')
        if sort and t['id'] != 'x7-core':
            rows.sort(key=lambda r:r[sort['field']], reverse=sort['direction']=='desc')
        xml.append('<p><b>' + esc(t['title']) + '</b></p>')
        if t.get('subtitle'):
            xml.append('<p>' + esc(t['subtitle']) + '</p>')
        xml.append(table([c['label'] for c in t['columns']], [[formatted(r.get(c['field']),c) for c in t['columns']] for r in rows], t['id']))
    elif kind == 'chart':
        c = charts[block['chartId']]
        asset = chart_files[bid]
        xml.append('<p><b>' + esc(c['title']) + '</b></p>')
        if c.get('subtitle'):
            subtitle = c['subtitle'].replace('完整下注金额可在悬浮提示和数据表查看。', '金额沿用源表单位。')
            xml.append('<p>' + esc(subtitle) + '</p>')
        rel = Path(asset['png']).relative_to(ROOT)
        xml.append(f'<img path="@./{rel}" width="{asset["width"]}" height="{asset["height"]}" caption="{esc(c["title"])}" name="{esc(c["title"])}.png"/>')
    else:
        raise ValueError(kind)

draft = ROOT / sys.argv[1]
assert draft.parent.name == 'draft_c0a87afd_folder'
content = '\n\n'.join(xml) + '\n'
ET.fromstring('<document>' + content + '</document>')
assert content.count('<img ') == 7
assert not any(s in content for s in ['Data access blockers', 'undefined', '剩余工作具体为', '本地游戏字典 CSV 第58行', '<p><b>数据来源</b></p>'])
draft.write_text(content)
receipt = {'title': title, 'status':'draft_prepared', 'source_html_sha256':hashlib.sha256((BASE/'report.html').read_bytes()).hexdigest(), 'artifact_sha256':hashlib.sha256((BASE/'artifact.json').read_bytes()).hexdigest(), 'draft_sha256':hashlib.sha256(content.encode()).hexdigest(), 'charts':chart_files, 'tables':table_records, 'kpi_metrics':6, 'chapter_count':content.count('<h1 '), 'target_space_id':'7672704187443973852', 'target_space_name':'产品数据整理和分析'}
(BASE/'lark-archive-build-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
print(json.dumps({'draft':str(draft),'chapters':receipt['chapter_count'],'charts':len(chart_files),'tables':table_records},ensure_ascii=False,indent=2))

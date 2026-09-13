"""Unified presentation only; values, narrative and order are unchanged."""
import copy,json,re,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-unified-style';R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',P/'report.css',P/'last-approved-version.json',H):
    if not (R/p.name).exists():shutil.copy2(p,R/p.name)
a=json.loads((R/'artifact.json').read_text());before=copy.deepcopy(a)
css=['''
/* Unified semantic emphasis; provider identity is distinct from movement. */
:root{--u-key:#895500;--u-bg:#fff2cd;--u-tada:#155ca8;--u-pp:#a6440c;--u-pos:#137348;--u-neg:#b23030;--u-claim:#153f70;}
@media(prefers-color-scheme:dark){:root{--u-key:#ffe0a0;--u-bg:#493d25;--u-tada:#7cc4ff;--u-pp:#ffb47a;--u-pos:#7bd6ac;--u-neg:#ffaaa6;--u-claim:#b5d9ff;}}
.report-shell .rich-markdown p,.report-shell .rich-markdown li{line-height:1.85;}
.report-shell .rich-markdown strong{color:var(--u-claim);font-weight:700;}
''']
token=re.compile(r'Tada|\bPP\b|[+−-]\d+(?:\.\d+)?(?:个百分点|%)?|\d[\d,]*\.\d+(?:%|个百分点|倍|万|亿)?')
counts={'vendor':0,'key':0,'positive':0,'negative':0}
for b in a['manifest']['blocks']:
    if b['type']!='markdown':continue
    scope=f':is(#{b["id"]},[data-artifact-block-id="{b["id"]}"])'
    out=[];para=0;row=-1
    for line in b['body'].splitlines():
        if line.startswith('|'):
            if re.match(r'^\|\s*[-:]+',line):row=0
            elif row>=0:
                row+=1
                for col,cell in enumerate(line.strip('|').split('|'),1):
                    if b['id']=='sensitivity-table' and col in (4,5):
                        value=float(cell.strip());color='pos' if value>0 else 'neg' if value<0 else 'claim'
                        css.append(f'{scope} tbody tr:nth-child({row}) td:nth-child({col}){{color:var(--u-{color})!important;font-weight:700;}}')
                    if 'Tada' in cell or re.search(r'\bPP\b',cell):
                        color='tada' if 'Tada' in cell else 'pp'
                        css.append(f'{scope} tbody tr:nth-child({row}) td:nth-child({col}){{color:var(--u-{color})!important;font-weight:700;}}')
            out.append(line);continue
        if not line or line.startswith('#') or re.match(r'^(?:- |\d+[.)] )',line):out.append(line);continue
        para+=1;idx=0;parts=[]
        for part in re.split(r'(\*\*[^*]+\*\*)',line):
            bold=part.startswith('**') and part.endswith('**');text=part[2:-2] if bold else part
            start=0
            for m in token.finditer(text):
                prefix=text[start:m.start()]
                if prefix:
                    parts.append('**'+prefix+'**' if bold else prefix)
                    if bold:idx+=1
                value=m.group();parts.append('**'+value+'**');idx+=1
                color='tada' if value=='Tada' else 'pp' if value=='PP' else 'neg' if value[0] in '-−' else 'pos' if value[0]=='+' else 'key'
                counts['vendor' if color in ('tada','pp') else 'negative' if color=='neg' else 'positive' if color=='pos' else 'key']+=1
                extra='background:var(--u-bg);border-radius:3px;padding:0 2px;' if color=='key' else ''
                css.append(f'{scope} .rich-markdown > p:nth-of-type({para}) strong:nth-of-type({idx}){{color:var(--u-{color})!important;{extra}}}')
                start=m.end()
            tail=text[start:]
            if tail:
                parts.append('**'+tail+'**' if bold else tail)
                if bold:idx+=1
        out.append(''.join(parts))
    new='\n'.join(out)
    assert new.replace('**','')==b['body'].replace('**','')
    b['body']=new
assert before['snapshot']==a['snapshot']
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
md=(R/'报告.md').read_text()
for old,new in zip(before['manifest']['blocks'],a['manifest']['blocks']):
    if old.get('body')!=new.get('body'):
        assert old['body'] in md;md=md.replace(old['body'],new['body'],1)
(P/'报告.md').write_text(md)
(P/'report.css').write_text((R/'report.css').read_text()+'\n'+'\n'.join(css))
(R/'change.json').write_text(json.dumps({'text_unchanged':True,'datasets_unchanged':True,'emphasis_tokens':counts,'sign_rule':'Only explicit signed values use green/red; ordinary positive levels are neutral highlights','feishu_updated':False},ensure_ascii=False,indent=2))

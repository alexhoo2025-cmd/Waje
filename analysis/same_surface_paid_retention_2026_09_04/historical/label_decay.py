"""Source-backed SVG annotation fallback for unsupported native line labels."""
import argparse,base64,gzip,json,re,shutil,html
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--retention',action='store_true');parser.add_argument('--first',action='store_true');args=parser.parse_args()
if args.first:args.retention=True
P=Path(__file__).resolve().parent;R=P/('revisions/2026-09-10-retention-labels' if args.retention else 'revisions/2026-09-10-decay-labels');R.mkdir(parents=True,exist_ok=True)
if args.first:R=P/'revisions/2026-09-10-first-labels';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html'
if not (R/'before.html').exists():shutil.copy2(H,R/'before.html')
s=H.read_text();m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S)
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())))
rows=a['snapshot']['datasets']['new_curve' if args.retention else 'new_decay_observed']
if args.first:rows=a['snapshot']['datasets']['first_curve']
if args.retention:rows=[dict(r,decline=r['retention_rate']) for r in rows]
platforms=['Android','iOS','H5（不含PWA候选渠道）'];colors=['#4299e1','#3db9c7','#e9ad23']
def x(d):return 78+(d-2)*80
def y(v):return 425-v*380/(.6 if args.retention else 1)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="510" viewBox="0 0 1100 510" role="img" aria-labelledby="title desc"><title id="title">8月新增付费用户第2至14日逐日衰减率</title><desc id="desc">各节点标注百分比；同日标签错位，细引线对应数据点。第5日起样本日期范围不同，仅为观察值变化。</desc>']
for value in ([0,.15,.30,.45,.6] if args.retention else [0,.25,.5,.75,1]):
    yy=y(value);svg.append(f'<line x1="78" x2="1038" y1="{yy}" y2="{yy}" stroke="var(--grid)"/><text x="62" y="{yy+4}" text-anchor="end" fill="var(--text)" font-size="12">{value*100:.0f}%</text>')
for d in range(2,15):svg.append(f'<text x="{x(d)}" y="456" text-anchor="middle" fill="var(--text)" font-size="12">{d}</text>')
for p,c in zip(platforms,colors):
    rs=sorted([r for r in rows if r['platform']==p],key=lambda r:r['day_number'])
    pts=' '.join(f"{x(r['day_number'])},{y(r['decline'])}" for r in rs)
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2.2"/>')
    for r in rs:svg.append(f'<circle cx="{x(r["day_number"])}" cy="{y(r["decline"])}" r="3.5" fill="{c}" stroke="var(--bg)"/>')
boxes=[]
for d in ([2,3,7,14] if args.retention else range(2,15)):
    points=sorted([(y(r['decline']),platforms.index(r['platform']),r) for r in rows if r['day_number']==d])
    positions=[]
    for yy,idx,r in points:positions.append(max(yy-13,positions[-1]+20 if positions else 20))
    if positions[-1]>412:
        shift=positions[-1]-412;positions=[q-shift for q in positions]
    for (yy,idx,r),ly in zip(points,positions):
        xx=x(d);c=colors[idx];label=f"{r['decline']*100:.1f}%"
        svg.append(f'<line x1="{xx}" y1="{yy}" x2="{xx+10}" y2="{ly-4}" stroke="{c}" stroke-opacity=".65"/><text x="{xx+12}" y="{ly}" fill="{c}" stroke="var(--bg)" stroke-width="3" paint-order="stroke" font-size="12" font-weight="650">{label}</text>')
        boxes.append((xx+12,ly-12,43,15))
for i,b in enumerate(boxes):
    for c in boxes[i+1:]:assert not (b[0]<c[0]+c[2] and c[0]<b[0]+b[2] and b[1]<c[1]+c[3] and c[1]<b[1]+b[3]),'label overlap'
svg.append('<text x="555" y="484" text-anchor="middle" fill="var(--text)" font-size="13">第N个自然日（与前一日比较）</text></svg>')
vector=''.join(svg)
if args.retention:
    vector=vector.replace('8月新增付费用户第2至14日逐日衰减率','8月新增付费用户第2至14日活跃留存率').replace('各节点标注百分比；同日标签错位，细引线对应数据点。第5日起样本日期范围不同，仅为观察值变化。','第2、3、7、14日标注百分比；同日标签错位，细引线对应数据点。各日使用达到统计口径的批次。').replace('第N个自然日（与前一日比较）','第N个自然日')
(R/'labelled-chart.svg').write_text(vector)
style='''<style>:root{--bg:#fff;--text:#29394d;--grid:#dfe5ec}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.6 sans-serif}h3{font-size:20px;margin:0 0 12px}p{margin:8px 0 16px}.scroll{overflow-x:auto;max-width:100%}svg{display:block;width:1100px;height:510px}.legend{display:flex;gap:24px;flex-wrap:wrap}@media(prefers-color-scheme:dark){:root{--bg:#1b293b;--text:#dce7f5;--grid:#354357}}</style>'''
legend='<div class="legend">'+''.join(f'<span style="color:{c}">● {html.escape(p)}</span>' for p,c in zip(platforms,colors))+'</div>'
body=style+'<h3>8月新增付费用户：第2—14日留存率观察值的逐日衰减</h3><p>第2日相对注册当日100%基准；第5日起样本日期范围变化。标签为百分比，细引线对应节点。</p><div class="scroll">'+vector+'</div>'+legend
if args.retention:
    body=style+'<h3>8月新增付费（注册当日付费）：第2—14日活跃留存</h3><p>标注第2、3、7、14日，百分比保留1位小数。各日纳入达到统计口径的用户批次；第7日覆盖8月1—28日，第14日覆盖8月1—21日。</p><div class="scroll">'+vector+'</div>'+legend
if args.first:body=body.replace('新增付费（注册当日付费）','首次付费（历史首充）').replace('新增付费用户','首次付费用户')
b=next(b for b in a['manifest']['blocks'] if b.get('chartId')==('first_curve' if args.first else 'new_curve' if args.retention else 'new-decay'));b.pop('chartId');b.update(type='html',body=body,sourceId='paid-cohorts')
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'report.css').write_text((P/'revisions/2026-09-10-short-table-summary/report.css').read_text())
(R/'qa.json').write_text(json.dumps({'labels':len(boxes),'geometric_overlap':False,'data_unchanged':True,'fallback_reason':'Native Line renderer does not implement labels.values; source-backed static SVG used inside canonical HTML block','interactive_chart_replaced':'new_curve only' if args.retention else 'new-decay only'},indent=2))

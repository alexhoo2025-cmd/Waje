"""Clarify the selected historical report only, using its embedded source."""
import base64,gzip,json,re,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-pwa-title';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html';backup=R/'before.html'
if not backup.exists():shutil.copy2(H,backup)
s=backup.read_text()
m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S);assert m
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())))
title='Waje付费用户留存分析｜APP、H5及PWA候选渠道'
a['manifest']['title']=title
next(b for b in a['manifest']['blocks'] if b['id']=='title')['body']='# '+title
b=next(b for b in a['manifest']['blocks'] if b['id']=='pwa-story')
parts=b['body'].split('\n\n',1)
note='PWA候选渠道按渠道名称筛选，实际运行形态尚待核实，结果暂单列展示。'
b['body']=parts[0]+'\n\n'+note+'\n\n'+parts[1]
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
styles=re.findall(r'<style[^>]*data-waje-reference-theme[^>]*>(.*?)</style>',s,re.S)
(R/'report.css').write_text('\n'.join(styles))
(R/'change.json').write_text(json.dumps({'title':title,'note':note,'historical_report_only':True,'newer_same_surface_report_unchanged':True,'source':'embedded artifact from selected prior_report.html'},ensure_ascii=False,indent=2))

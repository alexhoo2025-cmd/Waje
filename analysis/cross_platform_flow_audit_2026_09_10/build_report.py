"""Package the bounded cross-platform capability assessment; no business data queried."""
from pathlib import Path
import json, hashlib, re
import shutil
import sqlite3
from datetime import datetime
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
now=datetime.now().astimezone().isoformat(timespec='seconds')
text=(BASE/'report.md').read_text()
backup=BASE/'before_html_optimization';backup.mkdir(exist_ok=True)
for name in ['artifact.json','report.md','evidence_receipt.json','html_receipt.json']:
    if (BASE/name).exists() and not (backup/name).exists():shutil.copy2(BASE/name,backup/name)
sources=[{'id':'assessment','label':'APP与H5用户流通证据评估','path':'analysis/cross_platform_flow_audit_2026_09_10/report.md','description':'综合最新Whot方案、历史起源埋点盘点和查询回执；结论为条件支持，当前线上核验受认证阻断。'}]
receipt={'checked_at':now,'business_data_query_executed':False,'bq_mcp':'blocked_authentication','bq_browser':'login_challenge','origin_quality':'redirected_to_login','design_review':'completed','operational_verification':'blocked','external_writes':0,'business_metrics':None,'source_documents':[],'local_sources':[]}
for label in ['whot_phase1','whot_phase2']:
    d=json.loads((BASE/(label+'.json')).read_text())
    receipt['source_documents'].append({'document_id':d['document_id'],'revision':d['revision_id'],'content_sha256':d['content_sha256'],'retrieved_at':d['retrieved_at']})
    sources.append({'id':label,'label':('Whot一期' if label.endswith('1') else 'Whot二期')+'最新飞书方案','url':'https://ksg964l11fam.sg.larksuite.com/docx/'+d['document_id'],'description':'全文读取revision '+str(d['revision_id'])+'；设计不代表生产已上报。'})
paths=['knowledge/02-数据/Waje-H5起源埋点上报全量盘点-2026-08-28.md','knowledge/02-数据/Waje埋点事件与属性字典-2026-08-11.md','knowledge/02-数据/Waje-H5设备与性能补充埋点需求-V3-2026-08-24.md','analysis/whot_hourly_analysis_2026_09_04/source_inventory.json','analysis/whot_hourly_analysis_2026_09_04/quality_checks.json']
for i,path in enumerate(paths):
    receipt['local_sources'].append({'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),'status':'historical_reference'})
    sources.append({'id':'history_'+str(i),'label':Path(path).name,'path':path,'description':'历史来源，日期以文件标题及内容窗口为准，不表示2026年9月10日现状。'})
blocks=[];tables=[];datasets={};lines=text.splitlines();buf=[];i=0
def flush():
    if buf:
        body='\n'.join(buf).strip();buf.clear()
        if body:blocks.append({'id':'text_'+str(len(blocks)),'type':'markdown','body':body})
while i<len(lines):
    line=lines[i]
    if line.startswith('|') and i+1<len(lines) and re.match(r'^\|[\s:|\-]+$',lines[i+1]):
        flush();headers=[c.strip() for c in line.strip('|').split('|')];i+=2;rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            vals=[v.strip() for v in lines[i].strip('|').split('|')]
            assert len(vals)==len(headers)
            rows.append({'c'+str(n):v for n,v in enumerate(vals)});i+=1
        ident='table_'+str(len(tables));datasets[ident]=rows
        tables.append({'id':ident,'title':['跨端分析能力','来源与上报证据','核心指标与计算方式','最小补充项'][len(tables)],'dataset':ident,'sourceId':'assessment','columns':[{'field':'c'+str(n),'label':v,'type':'text'} for n,v in enumerate(headers)]})
        blocks.append({'id':ident,'type':'table','tableId':ident});continue
    if line.startswith('## '):flush()
    buf.append(line);i+=1
flush()
db=sqlite3.connect(':memory:')
for table in tables:
    ident=table['dataset'];fields=[c['field'] for c in table['columns']]
    db.execute('CREATE TABLE '+ident+' (row_order INTEGER, '+', '.join(f+' TEXT' for f in fields)+')')
    db.executemany('INSERT INTO '+ident+' VALUES ('+','.join('?' for _ in range(len(fields)+1))+')',[(n,*(r[f] for f in fields)) for n,r in enumerate(datasets[ident])])
    sql='SELECT '+', '.join(fields)+' FROM '+ident+' ORDER BY row_order;'
    verified=db.execute(sql).fetchall()
    assert verified==[tuple(r[f] for f in fields) for r in datasets[ident]]
    sid=ident+'_source'
    sources.append({'id':sid,'label':table['title']+'｜文档评估整理','path':'analysis/cross_platform_flow_audit_2026_09_10/report.md','query':{'engine':'sqlite','sql':sql,'tables_used':[ident],'description':'对文档评估行在本地内存表中按原顺序读取；不是线上业务查询，未补造经营数值。'}})
    table['sourceId']=sid
db.close()
for block in blocks:
    if block.get('body','').startswith('# '):block['id']='title'
    if block.get('body','').startswith('## 执行摘要'):block['id']='summary'
summary_index=next(i for i,b in enumerate(blocks) if b['id']=='summary')
blocks.insert(summary_index+1,{'id':'flow','type':'html','body':(BASE/'flow.html').read_text(),'sourceId':'assessment'})
artifact={'surface':'report','manifest':{'version':1,'surface':'report','title':text.splitlines()[0][2:],'generatedAt':now,'reportContract':{'type':'mechanism','language':'zh','population':'Waje真人登录账号；APP原生/内嵌H5与外部浏览器H5/PWA分开识别，匿名单列','period':'2026年9月10日设计与证据核查；历史查询窗口为2026年8月28日—9月3日','timezone':'Africa/Lagos；文档核验时间为Asia/Hong_Kong','metrics':[],'assertions':[],'decisions':{},'openQuestions':[]},'sources':sources,'cards':[],'charts':[],'tables':tables,'blocks':blocks},'snapshot':{'version':1,'generatedAt':now,'status':'ready','datasets':datasets},'sources':sources}
(BASE/'artifact.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
(BASE/'evidence_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'tables':len(tables),'blocks':len(blocks),'status':'assessment_complete_live_reporting_blocked'}))

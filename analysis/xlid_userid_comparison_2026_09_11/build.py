from pathlib import Path
from datetime import datetime
import json,re,sqlite3,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
body=(BASE/'report.md').read_text();now=datetime.now().astimezone().isoformat(timespec='seconds')
sources=[{'id':'rules','label':'用户提供的xlid生成与查找规则及截图','path':'analysis/xlid_userid_comparison_2026_09_11/report.md','description':'2026年9月11日用户提供的规则，按文字作机制推演；未验证线上实现。'}]
paths=['analysis/origin_paid_retention_rebuild_2026_09_10/07_key_overlap.sql','analysis/origin_paid_retention_rebuild_2026_09_10/07_key_overlap.result.json','analysis/origin_paid_retention_rebuild_2026_09_10/active-view-definitions.json','analysis/all_platform_cohort_value_2026_09_04/sql/12_paid_retention_2026-08.sql']
for n,path in enumerate(paths):sources.append({'id':'evidence_'+str(n),'label':Path(path).name,'path':path,'description':'只读复用历史证据；未重跑旧SQL、未继承历史任务的扫描额度授权。'})
blocks=[];tables=[];datasets={};buf=[];lines=body.splitlines();i=0;heading=''
def flush():
    if not buf:return
    text='\n'.join(buf).strip();buf.clear()
    if text:blocks.append({'id':'title' if text.startswith('# ') else 'summary' if text.startswith('## 执行摘要') else 'text_'+str(len(blocks)),'type':'markdown','body':text})
while i<len(lines):
    line=lines[i]
    if line.startswith('## '):flush();heading=line[3:]
    if line.startswith('|') and i+1<len(lines) and re.match(r'^\|[\s:|\-]+$',lines[i+1]):
        flush();headers=[s.strip() for s in line.strip('|').split('|')];rows=[];i+=2
        while i<len(lines) and lines[i].startswith('|'):
            cells=[s.strip() for s in lines[i].strip('|').split('|')];assert len(cells)==len(headers)
            rows.append({'c'+str(n):v for n,v in enumerate(cells)});i+=1
        ident='table_'+str(len(tables));datasets[ident]=rows
        fields=['c'+str(n) for n in range(len(headers))];db=sqlite3.connect(':memory:')
        db.execute('CREATE TABLE '+ident+' (row_order INTEGER,'+','.join(f+' TEXT' for f in fields)+')')
        db.executemany('INSERT INTO '+ident+' VALUES ('+','.join('?' for _ in range(len(fields)+1))+')',[(n,*(row[f] for f in fields)) for n,row in enumerate(rows)])
        sql='SELECT '+','.join(fields)+' FROM '+ident+' ORDER BY row_order;'
        assert db.execute(sql).fetchall()==[tuple(row[f] for f in fields) for row in rows];db.close()
        sources.append({'id':ident+'_source','label':heading,'path':'analysis/xlid_userid_comparison_2026_09_11/report.md','query':{'engine':'sqlite','sql':sql,'tables_used':[ident],'description':'文档对照行的本地SQLite排序读取，不是线上用户查询；场景为合成推演，聚合数字另见历史回执。'}})
        tables.append({'id':ident,'title':heading,'dataset':ident,'sourceId':ident+'_source','columns':[{'field':f,'label':h,'type':'text'} for f,h in zip(fields,headers)]})
        blocks.append({'id':ident,'type':'table','tableId':ident});continue
    buf.append(line);i+=1
flush()
contract={'type':'mechanism','language':'zh','population':'用户提供的身份规则；补充app_id=90006指定八渠道画像聚合，非全平台用户','period':'2026年9月11日规则解释；历史画像筛选为8月新增或8月首次付费，截至9月9日','timezone':'机制比较无新增业务日计算；沿用各原报表时区待核','metrics':[],'assertions':[],'decisions':{},'openQuestions':[]}
artifact={'surface':'report','manifest':{'version':1,'surface':'report','title':lines[0][2:],'generatedAt':now,'reportContract':contract,'sources':sources,'blocks':blocks,'tables':tables,'charts':[],'cards':[]},'snapshot':{'version':1,'generatedAt':now,'status':'ready','datasets':datasets},'sources':sources}
(BASE/'artifact.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
rows=json.loads((ROOT/paths[1]).read_text())['rows'];lookup={r['key_type']:r for r in rows}
assert lookup['xl_id']['keys']==696331 and lookup['user_id']['keys']==483568
assert lookup['xl_id']['keys']-lookup['user_id']['keys']==212763
receipt={'status':'rule_analysis_and_historical_aggregate_checked','generated_at':now,'new_online_queries':0,'production_implementation_verified':False,'difference':212763,'difference_is_not_certified_anonymous_count':True,'sources':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths]}
(BASE/'evidence_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'tables':len(tables),'difference_verified':212763,'new_online_queries':0}))

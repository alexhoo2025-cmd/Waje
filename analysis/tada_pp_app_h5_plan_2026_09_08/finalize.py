from pathlib import Path
import json,shutil,re,hashlib,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def load(n):return json.loads((P/n).read_text())
v=load('lark-verification.json');tests=load('test-receipt.json');assert v['status']==tests['status']=='passed'
schema=load('schema.json');schema['input_contracts']['normalized_bets']['fields']['window_id']='STRING；由固定查询参数赋值'
(P/'schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2))
md=(P/'方案.md').read_text().replace('](analysis-flow.png)','](../../analysis/tada_pp_app_h5_plan_2026_09_08/analysis-flow.png)')
dest=ROOT/'knowledge/02-数据/Tada与PP-APP-H5表现差异数据获取与分析方案-2026-09-08.md'
header=f'''---
type: metric-analysis-design
status: design_complete_production_access_pending
updated: 2026-09-08
tags: [Tada, PP, APP, H5, 投注, RTP, TC, 回访, 资源加载]
---

[飞书方案文档]({v['url']}) · [配套字典、接口与测试](../../analysis/tada_pp_app_h5_plan_2026_09_08/README.md)

'''
dest.write_text(header+md)
draft=ROOT/'draft_b3c51a76_folder'
if draft.exists():
 if (draft/'.presentation-decision.json').exists():shutil.copy2(draft/'.presentation-decision.json',P/'presentation-decision.json')
 assert draft.name=='draft_b3c51a76_folder' and (P/'release.xml').is_file()
 shutil.rmtree(draft)
fields=schema['input_contracts']['normalized_bets']['fields'];assert all(f in fields for f in ['window_id','metric_date','user_key','bet_uid','is_human','is_test','provider','settlement_complete','final_payout','net_stake'])
assert all(x['data_state']=='design_only_not_measured' for x in load('metric-dictionary.json'))
assert len(load('metric-dictionary.json'))==13
receipt={'status':'design_delivered','url':v['url'],'revision':v['revision'],'knowledge':str(dest),'metric_groups':13,'tables':8,'schematics':1,'table_cells_verified':v['table_cells'],'logical_contracts':list(schema['input_contracts']),'tests':tests,'production_data_queried':False,'source_metadata_access':load('access-receipt.json')['status'],'independent_review':load('review-receipt.json')['status'],'production_changes':0,'external_messages_sent':0,'sources':7,'source_files_unchanged':all(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256'] for s in load('sources.json')),'remaining_production_prerequisites':['恢复企业BigQuery连接','认证联运下注/结算字段和实际端','确认完整日、产品/包体及币种/资产范围','核验第三方打开与加载链路'],'presentation':'中文、分层标题、浅色重点、原生灰表头；示意图不含业务测量值'}
assert receipt['source_files_unchanged']
(P/'final-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print(json.dumps(receipt,ensure_ascii=False))

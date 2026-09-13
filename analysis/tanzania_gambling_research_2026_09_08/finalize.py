from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def read(n):return json.loads((P/n).read_text())
html=read('html-delivery-receipt.json');lark=read('lark-verification.json');analysis=read('analysis-verification.json');nb=read('复算记录.ipynb')
assert html['ok'] and html['stages']['verification']=='passed'
assert lark['status']=='passed' and analysis['status']=='passed'
assert nb['metadata']['execution']['status']=='passed'
report=ROOT/'output/html/坦桑尼亚博彩行业与产品调研报告-2026-09-08.html'
receipt={'status':'delivered_with_documented_source_gaps','date':'2026-09-08','html':str(report),'html_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'lark':lark['url'],'lark_revision':lark['revision_id'],'scope':{'workbooks':2,'sheets':25,'hidden_sheets':3,'brands':19,'charts':8,'native_tables':19,'lark_cells_verified':1167,'formula_recomputations':265,'cross_version_common_fields':378},'validation':{'analysis':analysis['status'],'html':html['stages'],'lark':lark['status'],'notebook':'sequential Python assertions passed; Jupyter kernel unavailable'},'original_workbooks_unchanged':analysis['checks']['raw_unchanged'],'official_access_gaps':['Premier Bet Cloudflare','SportyBet 451','Betway redirect/Cloudflare','WiBet/Gwala activity text unavailable','Mbet timeout'],'business_gaps':['current comparable GGR and brand market share','dated fieldwork and payment test samples','several current bonus terms and operator mappings'],'source_date_policy':'Historical workbook observations and current verified pages kept separate','side_effects':{'lark_document_created':1,'external_messages_sent':0,'permissions_changed':0},'knowledge_report':'knowledge/03-竞品/专题/2026-09-08-坦桑尼亚博彩行业与产品调研报告.md'}
(P/'final-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
print(json.dumps(receipt,ensure_ascii=False))

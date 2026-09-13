from pathlib import Path
import json,shutil,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
v=json.loads((P/'verification.json').read_text());assert v['status']=='passed'
source=json.loads((P/'source-receipt.json').read_text())
md=(P/'explanation.md').read_text()
for name in ['two-player','four-player']:md=md.replace(f']({name}.png)',f'](../../analysis/whot_robot_explainer_2026_09_08/{name}.png)')
header=f'''---
type: knowledge-explanation
status: source-rules-reviewed
updated: 2026-09-08
tags: [Whot, 机器人, 匹配, 降级, RTP]
source_revision: 16
---

[飞书讲解版]({v['url']}) · [原机制文档]({source['source_url']})

'''
dest=ROOT/'knowledge/01-产品/Whot机器人机制与匹配策略讲解-2026-09-08.md';dest.write_text(header+md)
draft=ROOT/'draft_24935f41_folder'
if draft.exists():
 if (draft/'.presentation-decision.json').exists():shutil.copy2(draft/'.presentation-decision.json',P/'presentation-decision.json')
 assert (P/'release.xml').exists() and draft.name=='draft_24935f41_folder'
 shutil.rmtree(draft)
receipt={'status':'delivered','url':v['url'],'knowledge_file':str(dest),'source':source,'checks':v['checks'],'original_document_modified':False,'messages_sent':0,'new_permissions':False,'interpretation_boundary':'仅原图匹配与补位规则，不声称局内算法、上线效果、100%胜负或实际RTP。','visuals':['two-player.svg','four-player.svg'],'source_rule_nodes':['T0-TN6','BOTCHECK','F0-F38','READY-R2','CANCEL'],'summary':'两人控制/保护/普通路径；四人逐人审核和同意降级；库存、复查、取消边界。'}
(P/'final-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print(json.dumps(receipt,ensure_ascii=False))

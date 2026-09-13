"""Archive only this research; preserve all unrelated workspace artifacts."""
from pathlib import Path
import json,re,shutil
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
dest=ROOT/'knowledge/03-竞品/专题/2026-09-08-坦桑尼亚博彩行业与产品调研报告.md'
# Fix image links for both relative reading roots without changing the narrative.
md=(P/'report.md').read_text().replace('](../../../analysis/tanzania_gambling_research_2026_09_08/lark_assets/','](lark_assets/')
(P/'report.md').write_text(md)
v=json.loads((P/'lark-verification.json').read_text());assert v['status']=='passed'
header=f'''---
type: research-report
status: share-with-caveats
updated: 2026-09-08
tags: [坦桑尼亚, 竞品, 博彩, 支付, 多玩法]
---

交付：[飞书团队阅读版]({v['url']}) · [离线HTML](../../../output/html/坦桑尼亚博彩行业与产品调研报告-2026-09-08.html) · [底稿与复算](../../../analysis/tanzania_gambling_research_2026_09_08/README.md)

'''
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(header+md.replace('](lark_assets/','](../../../analysis/tanzania_gambling_research_2026_09_08/lark_assets/'))
aliases=json.loads((P/'normalized.json').read_text())['aliases']
note=ROOT/'knowledge/03-竞品/专题/2026-09-08-坦桑调研指标与品牌索引.md'
lines=['# 坦桑调研指标与品牌索引','适用：2026年9月8日核验版本；原始调研日期未知。','[完整报告](./2026-09-08-坦桑尼亚博彩行业与产品调研报告.md)','## 指标定义','|指标|定义与边界|','|---|---|','|功能覆盖率|原表明确有 ÷ 明确有与无；命名产品/空白/不明确另列|','|最低存款／提现|具体原表所列门槛，金额TZS；渠道不同不合并|','|门槛比|同品牌最低提现÷最低存款，不代表用户实际支出|','|奖励比例|原单元格百分比格式读取，不与本金倍数混用|','|支付时长|具体秒数单列；即时和未知保持文字；不是本次实测|','|手机钱包活跃订阅|BoT年末前90天至少1笔金额交易的SIM，不是独立人数|','|博彩税收|政府征税，非GGR、NGR或投注额|','## 品牌别名','|规范化键|标准品牌|','|---|---|']
lines += ['|'+k+'|'+v+'|' for k,v in sorted(aliases.items())]
lines += ['## 来源与冲突','[官方核验记录](../../../analysis/tanzania_gambling_research_2026_09_08/external-evidence.json)','[跨版本对账](../../../analysis/tanzania_gambling_research_2026_09_08/cross_version_reconciliation.json)','[各表原值、格式与单元格](../../../analysis/tanzania_gambling_research_2026_09_08/cells.json)','[质量验收](../../../analysis/tanzania_gambling_research_2026_09_08/analysis-verification.json)','[支付及品牌底稿](../../../analysis/tanzania_gambling_research_2026_09_08/normalized.json)','## 复用限制','原表不是当前条款承诺。现金/免费注、线上/线下、品牌/供应商必须分开；缺口不填零。未获核验不代表无牌照。']
note.write_text('\n\n'.join(lines))
print(json.dumps({'report':str(dest),'index':str(note),'lark':v['url']},ensure_ascii=False))
# Preserve the prior generated graph before the scoped knowledge refresh.
backup=P/'graph-before-refresh';backup.mkdir(exist_ok=True)
for name in ['code-graph.json','代码与资产图谱.md']:
 source=ROOT/'knowledge/_generated'/name
 if source.exists() and not (backup/name).exists():shutil.copy2(source,backup/name)
draft=ROOT/'draft_fc010586_folder'
if draft.exists():
 decision=draft/'.presentation-decision.json'
 if decision.exists():shutil.copy2(decision,P/'lark-presentation-decision.json')
 assert draft.name=='draft_fc010586_folder' and (P/'lark-release.xml').exists()
 shutil.rmtree(draft)

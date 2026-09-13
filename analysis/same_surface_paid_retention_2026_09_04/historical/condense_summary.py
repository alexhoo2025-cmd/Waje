"""Condense only the summary and include the previously requested label draft."""
import base64,gzip,json,re,shutil,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-concise-summary';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html'
if not (R/'before.html').exists():shutil.copy2(H,R/'before.html')
s=H.read_text();m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S)
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())));before=copy.deepcopy(a)
b=next(b for b in a['manifest']['blocks'] if b['id']=='summary')
b['body']='''## 执行摘要

**APP付费用户回访水平较高，H5有所改善。** 8月注册当日付费用户的第2日留存为APP **49.5%**、H5 **19.2%**。6至7月完整批次的第14／30日留存均小幅改善，详细数据见正文。

**H5更需关注付费转化和人数下降。** 按本报告注册当日付费口径，7至8月付费率由**15.1%降至10.4%**，新增付费人数减少**24.3%**。回访率提高与付费规模缩小同时发生，建议先核对渠道来源和首日付费路径。

**APP优先排查Android，区分规模与用户质量。** 8月Android贡献APP约**91.7%**的新增付费人数；第2日留存为**49.1%**，低于iOS的**54.6%**。优先按包体、版本及来源渠道复核人数较多的Android群体，平台差异暂作为分析线索。

**回访排查先聚焦付费后的前3天，再跟踪两周表现。** 现有曲线中，第2日下降最大，第3日仍明显下降；可优先检查再次访问入口和首日体验。第5日起样本日期范围变化，后续节点需统一批次再验证。注册当日付费与历史首次付费两类人群分别评估。

统计范围：6—8月起点用户，活跃截止**2026年9月3日**；统计账号在任意端的活跃。H5不含PWA候选渠道，未达到统计口径的数据暂不展示。'''
draft=json.loads((P/'revisions/2026-09-10-retention-labels/artifact.json').read_text())
old_id=next(b['id'] for b in a['manifest']['blocks'] if b.get('chartId')=='new_curve')
replacement=next(b for b in draft['manifest']['blocks'] if b['id']==old_id)
assert replacement['type']=='html'
# Keep the last working chart while its labelled replacement remains unverified.
assert a['snapshot']==before['snapshot']
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'report.css').write_text((P/'revisions/2026-09-10-retention-labels/report.css').read_text())
(R/'change.json').write_text(json.dumps({'summary':'4 findings plus scope; detailed retention preserved in body','prior_label_request_included':False,'prior_label_request_status':'renderer blocked; existing curve preserved','data_unchanged':True,'new_query':False},indent=2))

import base64,gzip,json,re,shutil,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-short-table-summary';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html'
if not (R/'before.html').exists():shutil.copy2(H,R/'before.html')
s=H.read_text();m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S)
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())));before=copy.deepcopy(a)
rows=a['snapshot']['datasets']['new_short']
def row(p,month):return next(r for r in rows if r['platform']==p and r['cohort_month']==month)
ap7,ap8=row('APP（Android+iOS）','2026-07'),row('APP（Android+iOS）','2026-08')
h7,h8=row('H5（不含PWA候选渠道）','2026-07'),row('H5（不含PWA候选渠道）','2026-08')
app_drop=(1-ap8['cohort_users']/ap7['cohort_users'])*100
h5_drop=(1-h8['cohort_users']/h7['cohort_users'])*100
body=f'''### 数据小结：APP规模稳定，H5付费人数减少但次日留存提高

**APP新增付费人数基本稳定，H5在8月明显减少。** APP由7月**83,414人**降至8月**83,208人**，减少**{app_drop:.1f}%**；H5由**48,025人**降至**36,356人**，减少**{h5_drop:.1f}%**。H5需同时关注付费人数和留存，避免仅凭比例上升判断整体改善。

**APP第2日留存缓慢下降，H5连续提高，但两者仍有较大差距。** 6—8月APP为**50.34%→49.81%→49.54%**，H5为**15.52%→16.30%→19.17%**。看完整月份的第7日，6月至7月APP由**18.93%降至18.30%**，H5由**6.39%升至7.09%**；第14日两者分别由**11.14%升至11.42%**、**3.57%升至3.93%**。

**iOS留存高于Android，Android贡献APP的主要人数。** 8月第2日留存为iOS **54.57%**、Android **49.08%**；新增付费人数分别为**6,881人**、**76,327人**。建议优先排查Android早期回访及H5付费人数下降的渠道来源，分组差异作为进一步核查线索。

统计说明：8月第7日仅纳入8月1—28日用户，第14日仅纳入8月1—21日用户；这两项暂不与6、7月完整月份计算环比。H5不含PWA候选渠道，APP总计已包含Android和iOS。'''
idx=next(i for i,b in enumerate(a['manifest']['blocks']) if b.get('tableId')=='new-short-table')
a['manifest']['blocks'].insert(idx+1,{'id':'new-short-summary','type':'markdown','body':body,'sourceId':'paid-cohorts'})
check=copy.deepcopy(a);check['manifest']['blocks'].pop(idx+1);assert check==before
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'report.css').write_text((P/'revisions/2026-09-10-daily-decay-observed/report.css').read_text())
(R/'change.json').write_text(json.dumps({'added_block':'new-short-summary','data_unchanged':True,'app_users_drop_pct':app_drop,'h5_users_drop_pct':h5_drop,'new_query':False},indent=2))

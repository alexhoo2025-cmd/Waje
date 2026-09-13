"""Summarize existing mature long-retention evidence; no new query."""
import base64,gzip,json,re,shutil,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-long-summary';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html'
if not (R/'before.html').exists():shutil.copy2(H,R/'before.html')
s=H.read_text();m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S);assert m
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())));before=copy.deepcopy(a)
def row(ds,month,p):return next(r for r in a['snapshot']['datasets'][ds] if r['cohort_month']==month and r['platform']==p)
platforms=['Android','iOS','H5（不含PWA候选渠道）']
for ds in ['new_long','first_long']:
    for p in platforms:
        for mon,day,end in [('2026-06',30,'2026-06-30'),('2026-07',30,'2026-07-31'),('2026-06',60,'2026-06-30'),('2026-06',90,'2026-06-06')]:
            assert row(ds,mon,p)[f'd{day}_cohort_end']==end
summary=next(b for b in a['manifest']['blocks'] if b['id']=='summary')
summary['body']+='''

**第30日长留：6月至7月，三个平台分组均小幅改善，H5仍低于APP子端。** 新增付费用户的Android为**6.99%→7.09%**、iOS为**8.38%→8.64%**、H5为**2.42%→2.79%**；首次付费用户分别为**7.76%→8.02%**、**8.91%→9.42%**、**3.40%→3.74%**。两个月均覆盖完整起点月份。

**第60日长留：6月完整批次中，iOS最高，Android其次，H5最低。** 按Android／iOS／H5顺序，新增付费用户为**4.41%／5.94%／1.97%**，首次付费用户为**5.00%／6.18%／2.71%**。H5的短期回访改善，还需结合长期回访和付费人数持续评估。

**第90日已有部分成熟样本，保留分组观察。** 6月1—6日起点用户中，新增付费用户为**3.33%／4.16%／1.77%**，首次付费用户为**3.82%／4.85%／2.44%**（顺序同上）。该批次小于第60日的6月完整批次，二者不直接计算流失差值。

长留沿用本历史报告截至**2026年9月3日**的账号任意端活跃数据；H5均不含PWA候选渠道。8月第60／90日尚未到观察日，保留未成熟状态。'''
long=next(b for b in a['manifest']['blocks'] if b['id']=='long-story')
extra='''

### 第60日与第90日：先看同一观察日的平台差异

| 人群 | 平台分组 | 第60日：6月全月批次 | 第60日分母 | 第90日：6月1—6日批次 | 第90日分母 |
| --- | --- | --- | --- | --- | --- |
'''
for ds,label in [('new_long','新增付费'),('first_long','首次付费')]:
    for p in platforms:
        r=row(ds,'2026-06',p)
        extra+=f"| {label} | {p} | {r['d60']} | {r['d60_eligible_users']:,} | {r['d90'].replace('＊','')} | {r['d90_eligible_users']:,} |\n"
extra+='''
**长期回访的平台分组差异在两类付费人群中方向一致：iOS高于Android，H5相对较低。** 首次付费用户的第60／90日比例也均高于注册当日付费用户；两类人群定义不同且存在重叠，应分别评估，不能视为互斥实验组或相加。

**下一步优先验证H5付费用户首周到第30日的持续回访。** 结合来源渠道、游戏参与和付费金额拆解人群构成，再判断改善集中在哪些用户。第90日数据先用于同批次的平台比较，暂不据此推断整月趋势。各组按平台归属划分，回访允许发生在任意端。'''
long['body']+=extra
assert a['snapshot']==before['snapshot']
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'report.css').write_text((P/'revisions/2026-09-10-pwa-title/report.css').read_text())
(R/'verification-notes.json').write_text(json.dumps({'source_cutoff':'2026-09-03','new_query':False,'datasets_unchanged':True,'changed_blocks':['summary','long-story'],'d30_months':'June and July complete','d60':'June complete','d90':'June 1-6 only'},indent=2))

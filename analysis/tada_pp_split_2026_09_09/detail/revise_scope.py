"""Apply the two user-selected narrative edits, with backups and scope checks."""
import copy,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-scope'
R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',H,P/'last-approved-version.json'):
    dest=R/p.name
    if not dest.exists():shutil.copy2(p,dest)
a=json.loads((P/'artifact.json').read_text());before=copy.deepcopy(a)
summary=next(b for b in a['manifest']['blocks'] if b['id']=='summary')['body']
patches={'summary':summary+'''

**统计范围：** 2026年8月1日—9月7日，共38个完整业务日，按拉各斯时间统计。比较Waje真金产品中Tada与PP的有效下注，排除WajeCoin；APP／H5按用户注册渠道划分，金额沿用原报表单位。

**样本说明：** 摘要中的游戏数、人均下注额和RTP覆盖对应渠道的全体下注用户；H5·Tada关联分析选取110款游戏，每款至少有100名下注者、14个有下注记录的业务日。''',
'depth':'''## 01｜Tada的人均下注额更高，下注人数也更多

**在全体下注用户中，Tada的人均下注额为PP的APP约7.02倍、H5约6.39倍。** 两家厂商的下注总额差距更大：Tada分别为PP的28.7倍和19.4倍。Tada的规模优势来自两方面：参与下注的人更多，每位下注用户的平均下注额也更高。

**人均指标按统计期内的累计数据计算：**

- 人均下注额＝该厂商的累计有效下注额÷该厂商的去重下注人数。
- 人均局次＝该厂商的累计有效下注局次÷该厂商的去重下注人数。
- 每项计算均在同一渠道、同一用户类别内进行；同一用户在统计期内多次下注，人数计一次。

**新老用户按下注当天的注册时长划分：** 注册0—29天为新用户，注册满30天为老用户；是否充值均纳入统计。APP和H5表示用户的注册渠道归属。全体用户数据还包括注册日期未知的下注用户。'''}
md=(P/'报告.md').read_text()
for b in a['manifest']['blocks']:
    if b['id'] in patches:
        assert b['body'] in md
        md=md.replace(b['body'],patches[b['id']],1);b['body']=patches[b['id']]
check=copy.deepcopy(a)
for b in check['manifest']['blocks']:
    if b['id'] in patches:b['body']=next(x['body'] for x in before['manifest']['blocks'] if x['id']==b['id'])
assert check==before
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(P/'报告.md').write_text(md)
(R/'change.json').write_text(json.dumps({'changed_blocks':list(patches),'other_content_unchanged':True,'dataset_unchanged':True,'feishu_updated':False},ensure_ascii=False,indent=2))
print('Updated summary and depth only')

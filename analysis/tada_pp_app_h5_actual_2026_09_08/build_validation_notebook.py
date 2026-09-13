"""Execute a local-only notebook over saved aggregates; never resubmit warehouse SQL."""
from pathlib import Path
import json,sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

P=Path(__file__).resolve().parent
md=nbformat.v4.new_markdown_cell;code=nbformat.v4.new_code_cell
cells=[
md('''## tl;dr

本Notebook独立检查Tada／PP报告的38天覆盖、去重、分母、成熟窗口、主要数字及交付结构。所有输入为已保存的聚合结果，**不会重新执行BigQuery查询**。

主要结论：Tada／PP下注额倍数为APP约28.7、H5约19.4；目录资源较小不能证明加载造成差异。到账TC与严格现金/奖励拆分仍缺证据。'''),
md('''## Context & Methods

- 2026年8月1日至9月7日，Africa/Lagos。
- 游戏主口径mode11，排除WajeCoin；渠道归属不等于实际行为端。
- 注册0—29天为新用户，30天起为老用户；回访固定起点账号龄。

### Key Assumptions

游戏金额采用已对账的源单位÷100，未擅自标注币种。结算RTP尚未拆现金与奖励。有效下注局次按业务日、账号、游戏、局和回合去重。'''),
code('''from pathlib import Path
from decimal import Decimal as D
from datetime import date, timedelta
import json, hashlib, collections
P=Path.cwd()
def read(n): return json.loads((P/n).read_text())
def q(n): return read('queries/'+n+'.result.json')
checks={}
raw=q('14_full_core'); corrected=read('core-corrected.json'); analysis=read('analysis-results.json')
receipt_paths=list((P/'queries').glob('*.receipt.json'))
receipts=[json.loads(f.read_text()) for f in receipt_paths]
assert not any(r['status']=='submitted' for r in receipts)
executed=[r for r in receipts if r['status']=='executed']
for r in executed:
    sql=P/r['query']; result=P/'queries'/(sql.stem+'.result.json')
    assert result.exists()
    if 'sql_sha256' in r: assert hashlib.sha256(sql.read_bytes()).hexdigest()==r['sql_sha256']
    if 'result_sha256' in r: assert hashlib.sha256(result.read_bytes()).hexdigest()==r['result_sha256']
    assert r['actual_bytes_processed'] <= 64*1024**3
total_bytes=sum(r['actual_bytes_processed'] for r in executed)
assert total_bytes <= 300*1024**3
checks['query_receipts_and_hashes']=len(executed)
print({'executed_queries':len(executed),'total_scan_gib':round(total_bytes/1024**3,3)})'''),
md('''## Data

### 1. 原始聚合与逐日局标识对账

使用与主汇总独立执行的逐日局标识查询。检查主口径完整日期及去重前后记录数，避免仅凭渲染成功宣布数据正确。'''),
code('''quality=q('19a_round_quality_aug01_19')+q('19b_round_quality_aug20_sep07')
period_dates={date(2026,8,1)+timedelta(days=i) for i in range(38)}
for provider in ['Tada','PP','other_games']:
    rows=[r for r in quality if r['product_mode']=='Waje' and r['provider']==provider]
    assert {date.fromisoformat(r['stat_date']) for r in rows}==period_dates
    for r in rows:
        a=next(x for x in raw if x['time_grain']=='daily' and x['segment_grain']=='all_platforms' and x['product_mode']=='Waje' and x['date_key']==r['stat_date'] and x['provider_group']==provider)
        b=next(x for x in corrected if x['time_grain']=='daily' and x['segment_grain']=='all_platforms' and x['product_mode']=='Waje' and x['date_key']==r['stat_date'] and x['provider_group']==provider)
        assert a['settlement_records']==r['records']
        assert a['settlement_users']==r['users']
        assert b['settlement_records']==r['distinct_user_game_round_keys']
        assert r['missing_round_key_records']==r['missing_log_key_records']==0
checks['independent_daily_round_checks']=114
print('114个厂商×完整业务日检查通过；Waje主口径去重修正与局标识一致。')'''),
md('''### 2. 分子分母与金额守恒'''),
code('''def core(platform,provider,age='all_ages',segment='platform'):
    return next(r for r in corrected if r['product_mode']=='Waje' and r['time_grain']=='period' and r['segment_grain']==segment and r['platform_group']==platform and r['provider_group']==provider and r['age_segment']==age)
for field in ['effective_stake_source_units','settlement_source_units']:
    for platform in ['APP','H5','PWA_named','unmapped']:
        total=D(core(platform,'all_games')[field])
        subtotal=sum(D(core(platform,p)[field]) for p in ['Tada','PP','other_games'])
        assert total==subtotal
    grand=D(core('all_platforms','all_games',segment='all_platforms')[field])
    assert grand==sum(D(core(p,'all_games')[field]) for p in ['APP','H5','PWA_named','unmapped'])
for platform in ['APP','H5']:
    for age in ['all_ages','new_30d','old_over_30d']:
        pair=[r for r in analysis['overview'] if r['platform']==platform and r['age']==age]
        assert abs(sum(r['pair_share'] for r in pair)-1)<1e-12
        assert all(0<=r['all_game_share']<=1 and 0<=r['penetration']<=1 for r in pair)
checks['amount_subtotals_and_share_denominators']='passed'
print('厂商份额、渠道金额汇总及两厂商分母检查通过。')'''),
md('''### 3. 成熟回访与互斥状态'''),
code('''returns=q('18_full_return')
for r in returns:
    assert r['same_provider_return_accounts']+r['other_provider_only_accounts']+r['no_observed_bet_accounts']==r['eligible_accounts']
    assert 0<=r['any_origin_day_game_return_accounts']<=r['same_provider_return_accounts']<=r['eligible_accounts']
    latest_allowed=date(2026,9,7)-timedelta(days=r['observation_day']-1)
    assert date.fromisoformat(r['last_origin_date'])<=latest_allowed
for platform in ['APP','H5']:
    for provider in ['Tada','PP']:
        r=[x for x in returns if x['platform']==platform and x['provider']==provider and x['age_segment']=='all_ages' and x['sample_mode']=='common_30d' and x['cohort_scope']=='summary']
        assert len(r)==5 and len({x['eligible_accounts'] for x in r})==1
        assert all(x['last_origin_date']=='2026-08-09' for x in r)
checks['mature_return_and_state_checks']=len(returns)
print('所有1133行回访状态及成熟范围检查通过；共同范围分母固定。')'''),
md('''## Results

### 4. 关键结论与独立复算'''),
code('''ratios={p:core(p,'Tada')['stake']/core(p,'PP')['stake'] for p in ['APP','H5']}
assert round(ratios['APP'],1)==28.7 and round(ratios['H5'],1)==19.4
for p in ['APP','H5']:
    rows=[r for r in analysis['decomposition'] if r['platform']==p]
    assert abs(sum(r['contribution'] for r in rows)-(core(p,'Tada')['stake']-core(p,'PP')['stake']))<0.001
for r in analysis['return_age_decomposition']:
    assert abs(r['mix_effect']+r['within_age_effect']-r['gap'])<1e-12
final=q('25_final_withdraw_coverage')[0]
assert final['paid_out_status_records']==0
checks['headline_ratios_decomposition_and_tc_gap']='passed'
print({'stake_ratios':ratios,'final_paid_out_status_records':final['paid_out_status_records']})'''),
code('''artifact=read('artifact.json'); delivery=read('delivery-receipt.json')
assert delivery['ok'] and delivery['stages']['verification']=='passed'
assert len(artifact['manifest']['charts'])==7
assert all(len(rows)<=2000 for rows in artifact['snapshot']['datasets'].values())
assert artifact['snapshot']['status']=='partial'
assert '到账TC未计算' in (P/'报告.md').read_text()
assert '注册0' not in artifact['manifest']['title']
checks['report_render_and_required_caveats']='passed'
receipt={'status':'share_with_caveats','checks':checks,'scan_gib':total_bytes/1024**3,
 'required_caveats':['渠道归属而非实际端','游戏币种及现金/奖励拆分未认证','最终到账TC缺失','加载关联不足','均值未按大额用户分位复核','Sonnet独立审查授权缺失'],
 'notebook_execution':'executed_locally_without_cloud_queries'}
(P/'final-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\\n')
print(receipt)'''),
md('''## Takeaways

主下注、渠道份额、有效局次与成熟回访结论通过复算。金额差额分解是算术关系，不是因果效应。最终到账TC、现金与奖励分别计算的严格RTP及真实加载转化仍缺证据；自然／投放、大额用户等更细交叉拆解未完成，正文已明确说明。

SQL与聚合回执位于同目录`sql/`、`queries/`。本Notebook只读取已有结果，常规复算不产生新的BigQuery扫描。''')]
nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Waje analysis (.venv)','language':'python','name':'python3'},'language_info':{'name':'python'}})
nbformat.validate(nb)
km=KernelManager(kernel_name='python3')
km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
NotebookClient(nb,timeout=120,km=km,resources={'metadata':{'path':str(P)}}).execute()
nbformat.write(nb,P/'复算与验收.ipynb')
print(json.dumps({'notebook':'复算与验收.ipynb','status':'executed','code_cells':sum(c.cell_type=='code' for c in nb.cells)},ensure_ascii=False))

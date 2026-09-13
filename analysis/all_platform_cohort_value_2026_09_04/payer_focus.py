"""Payer-retention-first report; explicitly retire order-creation payment claims."""
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEW = '新增付费（注册当日付费）'
FIRST = '首次付费（历史首充）'
H5 = 'H5（不含PWA候选渠道）'
PWA = 'PWA候选渠道（待确认）'
MONTHS = ('2026-06','2026-07','2026-08')


def payer_focus(manifest, snapshot):
    raw, receipts = [], []
    for m in MONTHS:
        path = ROOT/'paid_retention_server_success_v1'/f'13_paid_retention_server_success_{m}.json'
        receipt = json.loads(path.read_text())
        assert receipt['status']=='ok' and receipt['execution']['row_count'] < 3000
        raw.extend(receipt['aggregate_rows']); receipts.append(receipt)
    den_receipt = json.loads((ROOT/'paid_retention_denominators_v1/14_paid_cohort_registration_denominators.json').read_text())
    assert den_receipt['status']=='ok'
    denominator = {(r['cohort_month'],r['platform']):r['registered_users'] for r in den_receipt['aggregate_rows']}
    base = [r for r in raw if r['breakdown']=='平台']
    lookup = {(r['payer_group'],r['cohort_month'],r['platform'],r['day_number']):r for r in base}
    # APP is an exact sum of disjoint first-platform groups, not an average of rates.
    for group in (NEW,FIRST):
        for m in MONTHS:
            for day in (2,3,4,5,6,7,8,9,10,11,12,13,14,30,60,90):
                selected = [lookup[group,m,p,day] for p in ('Android','iOS')]
                r = deepcopy(selected[0]);r['platform']='APP（Android+iOS）'
                for key in ('cohort_users','eligible_users'):
                    r[key]=sum(x[key] for x in selected)
                r['retained_users'] = sum(x['retained_users'] for x in selected) if all(x['retained_users'] is not None for x in selected) else None
                r['retention_rate']=r['retained_users']/r['eligible_users'] if r['eligible_users']>=10 and r['retained_users'] is not None else None
                base.append(r);lookup[group,m,r['platform'],day]=r
    datasets = {'paid_retention_platform':base,
                'paid_retention_packages':[r for r in raw if r['breakdown']=='包与渠道' and not re.search('phx|phoenix|firebase',r['channel'],re.I)],
                'registration_denominators':den_receipt['aggregate_rows']}
    pct=lambda x: '未到观察日' if x is None else f'{x*100:.2f}%'
    def rate(group,month,platform,day):
        return lookup[group,month,platform,day]['retention_rate']
    def values(group,platform,day):
        return ' → '.join(pct(rate(group,m,platform,day)) for m in MONTHS)
    def wide(group,platforms):
        result=[]
        for p in platforms:
            for m in MONTHS:
                r={'payer_group':group,'month_label':str(int(m[-2:]))+'月','cohort_month':m,'platform':p,
                   'cohort_users':lookup[group,m,p,2]['cohort_users']}
                for d in (2,7,14,30,60,90):
                    point=lookup[group,m,p,d]
                    suffix='＊' if 0<point['eligible_users']<point['cohort_users'] else ''
                    r[f'd{d}']=pct(point['retention_rate'])+suffix
                    r[f'd{d}_eligible_users']=point['eligible_users']
                    r[f'd{d}_cohort_end']=point['eligible_cohort_end']
                result.append(r)
        return result
    for group,id_ in ((NEW,'new'),(FIRST,'first')):
        datasets[f'{id_}_short'] = wide(group,('APP（Android+iOS）','Android','iOS',H5))
        datasets[f'{id_}_curve'] = [r for r in base if r['payer_group']==group and r['cohort_month']=='2026-08'
                                    and r['platform'] in ('Android','iOS',H5) and r['day_number']<=14]
        datasets[f'{id_}_long'] = wide(group,('Android','iOS',H5))
    # Candidate PWA codes remain separate; no unverified PWA platform total is shown.
    candidate_rows=[]
    package_rows=datasets['paid_retention_packages']
    keys=sorted({(r['payer_group'],r['cohort_month'],r['package_name'],r['channel']) for r in package_rows if r['platform']==PWA})
    for group,m,pkg,channel in keys:
        selected={r['day_number']:r for r in package_rows if (r['payer_group'],r['cohort_month'],r['package_name'],r['channel'])==(group,m,pkg,channel)}
        r={'payer_group':group,'cohort_month':m,'channel':channel,'package_name':pkg,'cohort_users':selected[2]['cohort_users']}
        for d in (2,14,30,60):
            point=selected[d];r[f'd{d}']=pct(point['retention_rate'])+('＊' if 0<point['eligible_users']<point['cohort_users'] else '')
        candidate_rows.append(r)
    datasets['pwa_candidates']=candidate_rows
    datasets.pop('paid_retention_packages')
    for m in MONTHS:
        datasets['paid_packages_'+m.replace('-','_')]=[r for r in package_rows if r['cohort_month']==m]
    payment=[]
    for p in ('Android','iOS',H5):
        for m in MONTHS:
            count=lookup[NEW,m,p,2]['cohort_users'];den=denominator[m,p]
            payment.append({'platform':p,'cohort_month':m,'registered_users':den,'paid_users':count,'payment_rate':count/den,
                            'payment_rate_display':pct(count/den)})
    datasets['registration_day_payment']=payment
    lifecycle=deepcopy(snapshot['datasets']['h5_lifecycle_source_monthly'])
    datasets['h5_lifecycle_aux']=lifecycle
    ltvsource=deepcopy(next(s for s in manifest['sources'] if s['id']=='h5-lifecycle-source'))
    executed = receipts+[den_receipt]
    sql='\n\n'.join((ROOT.parents[1]/r['sql_file']).read_text() for r in executed)
    source={'id':'paid-cohorts','label':'服务端支付成功与付费用户活跃留存（6—8月）',
            'path':'analysis/all_platform_cohort_value_2026_09_04/paid_retention_server_success_v1/execution_receipt.json',
            'query':{'engine':'Google Cloud BigQuery','language':'SQL','sql':sql,
                     'description':'按历史首平台及注册／首充日统计付费人群；注册日付费率分母为同一画像注册人群。',
                     'tables':['wajenigeria.origin_hfyl.view_metaevent_order','wajenigeria.origin_hfyl.user_events','wajenigeria.origin_hfyl.view_user_version_daily'],
                     'filters':['成功支付：服务端 is_success=pay_success；有效用户与订单号。',
                                '新增付费暂按注册当日完成成功付费，以注册日为第1日。',
                                '首次付费：成功首充标记为真，且支付日与画像历史首充日期一致。',
                                '活跃数据截至2026年9月3日；6—8月批次；每组至少10名用户。'],
                     'metric_definitions':['留存率=在第N个自然日活跃的同批用户数／已到观察日且来源有数据的同批用户数。',
                                          '按首平台分组，回访是Waje账号任意端活跃，不代表只回到原APP／网页。',
                                          'APP先累加Android和iOS分子分母再计算；二者互斥。',
                                          '注册当日付费率=注册当日成功付费用户／同月注册画像用户；不是14日累计付费率。',
                                          '成功首充无法与画像匹配的人群不进入首充留存；未将其视为未留存。']}}
    manifest['sources']=[source,ltvsource]
    manifest['title']='Waje 付费用户留存专题｜APP、H5与PWA待确认渠道'
    manifest['description']='以新增付费、首次付费用户的第2—14日及30／60／90日活跃留存为主线，辅以付费率与LTV。'
    manifest['generatedAt']=datetime.now(ZoneInfo('Asia/Hong_Kong')).isoformat(timespec='seconds')
    manifest['accessIssues']=['PWA渠道映射未获确认：候选渠道分别展示，不输出PWA整体结论。',
                              '新增付费暂按注册当日付费；若业务要求注册后其他付费窗口，需重算。',
                              '本次未计算各端两类付费人群自己的累计LTV；仅保留独立H5联运来源作为辅助。']
    manifest['cards']=[];manifest['charts']=[];manifest['tables']=[];manifest['blocks']=[]
    blocks=manifest['blocks']
    def md(id_,body,src='paid-cohorts'):
        b={'id':id_,'type':'markdown','body':body}
        if src:b['sourceId']=src
        blocks.append(b)
    def col(field,label,fmt=None):
        d={'field':field,'label':label,'type':'number' if fmt else 'text'}
        if fmt:d['format']=fmt
        return d
    def table(id_,title,dataset,columns,subtitle='',src='paid-cohorts'):
        manifest['tables'].append({'id':id_,'title':title,'subtitle':subtitle,'dataset':dataset,'sourceId':src,'layout':'full','density':'spacious','columns':columns})
        blocks.append({'id':id_+'-block','type':'table','tableId':id_})
    def curve(id_,group):
        manifest['charts'].append({'id':id_,'title':f'8月{group}：第2—14日活跃留存','subtitle':'Android、iOS、H5分开显示；各日采用已到观察日的批次。',
          'type':'line','dataset':id_,'sourceId':'paid-cohorts','layout':'full',
          'encodings':{'x':{'field':'day_number','type':'quantitative','label':'第N个自然日'},
                       'y':{'field':'retention_rate','type':'quantitative','format':'percent','label':'活跃留存率'},
                       'color':{'field':'platform','type':'nominal','label':'平台'}},
          'palette':{'kind':'categorical','name':'reference-platform'},'valueFormat':'percent',
          'labels':{'values':'endpoints'},'legend':{'position':'bottom'},'settings':{'showPoints':'always'}})
        blocks.append({'id':id_+'-block','type':'chart','chartId':id_})
    md('title','# '+manifest['title'],None)
    app=values(NEW,'APP（Android+iOS）',2)
    h5count=[lookup[NEW,m,H5,2]['cohort_users'] for m in MONTHS]
    md('summary','## 执行摘要\n\n'
       '**主线改为付费用户留存。** 以下区分“注册当日付费”和“历史首次付费”两类人群；不再用全量新增用户留存代替。PWA渠道映射尚待确认，候选渠道不作为正式PWA整体结论。\n\n'
       f'**APP次日付费留存小幅回落，H5付费回访上升。** 6／7／8月新增付费用户第2日留存：APP **{app}**；H5 **{values(NEW,H5,2)}**。\n\n'
       f'**H5需同时看人数与留存，不能只看回访率上升。** 新增付费人数 **{h5count[0]:,} → {h5count[1]:,} → {h5count[2]:,}**，8月较7月减少 **{(1-h5count[2]/h5count[1])*100:.1f}%**；较少的人完成付费与付费人群构成变化，可能同时影响留存率。\n\n'
       f'**首次付费用户单独判断。** H5第2日首充留存 **{values(FIRST,H5,2)}**；8月第60日尚未成熟，不能下长留改善或恶化的结论。')
    md('definitions','## 01｜人群、平台与留存口径\n\n'
       '- **新增付费用户：** 暂按注册当天完成成功付费；注册日为第1日。如需“注册后7日内付费”等定义，必须重新计算。\n'
       '- **首次付费用户：** 历史首充日期与服务端成功首充事件一致；首充日为第1日，包括非当天注册的用户。两类人群有重叠，不能相加。\n'
       '- **留存：** 同批用户在第N个自然日是否活跃，不要求当天再次付费。按首平台分组，活跃允许发生在Waje任意端；不是同端回访率。\n'
       '- **时间：** 6、7、8月批次，活跃截止9月3日。＊表示部分批次已成熟；未成熟不补零。\n\n'
       '**本次纠正：** 原付费率采用的创建订单事件不能代表支付成功，相关付费率、ARPU与付费人数结论已撤下；下文仅使用服务端支付成功事件。旧审计工件保留，不再作为本专题证据。')
    shortcols=[col('month_label','月份'),col('platform','平台'),col('cohort_users','同批付费人数','number')]+[col(f'd{d}',f'第{d}日留存') for d in (2,7,14)]
    for group,id_,number in ((NEW,'new','02'),(FIRST,'first','03')):
        md(id_+'-story',f'## {number}｜{group}留存\n\n'
           f'**6／7／8月第2日：** Android {values(group,"Android",2)}；iOS {values(group,"iOS",2)}；H5 {values(group,H5,2)}。\n\n'
           '**解读：** 曲线比较8月付费人群第2—14日活跃水平，三个月完整读数见表。8月较长观察日使用较早批次，不能把曲线差异直接解释成产品效果；APP总计与Android／iOS明细也不可重复相加。')
        curve(id_+'_curve',group)
        table(id_+'-short-table',f'{group}：6—8月短期留存',id_+'_short',shortcols)
    md('long-story','## 04｜30／60／90日长留：先看成熟批次\n\n'
       '**6→7月完整月度第30日：** '
       + '；'.join(f'{p}新增付费 {pct(rate(NEW,"2026-06",p,30))} → {pct(rate(NEW,"2026-07",p,30))}，首充 {pct(rate(FIRST,"2026-06",p,30))} → {pct(rate(FIRST,"2026-07",p,30))}' for p in ('Android','iOS',H5))
       + '。三端在这两个完整月度的第30日均小幅上升，但不能据此推出8月也改善。\n\n'
       '**比较边界：** 8月第30日仅覆盖1—5日批次；7月第60日仅覆盖1—6日批次；6月第90日仅覆盖1—6日批次。6月第30／60日与7月第30日覆盖全月。未对齐范围的数值只作观察，不计算整月环比。')
    longcols=[col('month_label','月份'),col('platform','平台')]+[col(f'd{d}',f'第{d}日留存') for d in (30,60,90)]
    table('new-long-table','新增付费用户长留','new_long',longcols)
    table('first-long-table','首次付费用户长留','first_long',longcols)
    md('pwa-story','## 05｜PWA：候选渠道分开列示，等待映射确认\n\n'
       '目前源数据出现 PAWAJEH5PWA、PAWAJEH5PWAT、PAWAJEH5PWW。渠道字典未能消除平台归属歧义，因此下表只陈列这些渠道码的付费留存，**不把它们合并命名为PWA整体**。H5主表暂不含这些候选渠道。确认生产PWA渠道后再汇总；缺少某行可能是人数不足10人，不是零留存。')
    table('pwa-candidate-table','PWA候选渠道：待确认的分组数据','pwa_candidates',
          [col('cohort_month','月份'),col('payer_group','人群'),col('channel','渠道码')]+[col(f'd{d}',f'第{d}日') for d in (2,14,30,60)])
    md('payment-story','## 06｜辅助指标：注册当日付费率\n\n'
       '**这里衡量注册到首次付费的早期转化，不是付费用户留存。** 分母是同月注册画像用户，分子是注册当天成功付费用户；不能与旧版第14日累计指标直接比较。\n\n'
       '**H5 6／7／8月：** '+' → '.join(pct(next(r['payment_rate'] for r in payment if r['platform']==H5 and r['cohort_month']==m)) for m in MONTHS)
       +'。8月早期付费转化下行，而付费人群的次日回访上升；优先检查注册到付费的漏斗与渠道构成，不能把比例变化直接归因于留存机制。')
    manifest['charts'].append({'id':'paid-rate-chart','title':'6—8月注册当日付费率','type':'bar','dataset':'registration_day_payment','sourceId':'paid-cohorts','layout':'full',
      'encodings':{'x':{'field':'platform','type':'nominal','label':'平台'},'y':{'field':'payment_rate','type':'quantitative','format':'percent','label':'注册当日付费率'},'color':{'field':'cohort_month','type':'nominal','label':'注册月'}},'valueFormat':'percent','labels':{'values':'all'},'legend':{'position':'bottom'}})
    blocks.append({'id':'paid-rate-chart-block','type':'chart','chartId':'paid-rate-chart'})
    table('paid-rate-table','注册当日付费率与分母','registration_day_payment',
          [col('cohort_month','月份'),col('platform','平台'),col('registered_users','注册用户','number'),col('paid_users','当日付费用户','number'),col('payment_rate_display','付费率')])
    md('ltv-story','## 07｜辅助指标：H5联运生命周期价值\n\n'
       '这组LTV来自独立联运生命周期数据，**不是上文两类付费人群自己的LTV，也不代表APP或PWA**，仅作为价值趋势背景。\n\n'
       '**7→8月：** 第14日 1707.45 → 1607.46，减少 **99.99（-5.9%）**；第30日 2421.79 → 2190.15，减少 **231.63（-9.6%）**。\n\n'
       '各端新增付费、首充用户的专属LTV尚未计算，不能把这组数复制到各端；后续需按本次人群与起点累计相应收入。', 'h5-lifecycle-source')
    table('ltv-aux-table','H5联运来源：6—8月LTV','h5_lifecycle_aux',
          [col('cohort_month','月份')]+[col(f'ltv_{d}',f'第{d}日LTV','number') for d in (14,30,60,90)],src='h5-lifecycle-source')
    md('actions','## 08｜定位问题与后续核查\n\n'
       '1. **H5先拆转化与回访：** 按包名／渠道比较新增付费人数、当日付费率及第2／7／14日留存，检查8月是否有渠道结构变化。\n'
       '2. **APP分别看两端：** Android关注更大体量下的次日回访，iOS单独追踪；不要将APP总计与子端重复计入。\n'
       '3. **长留看成熟批次：** 保留第30／60／90日读数，按相同注册或首充日期范围做进一步比较，未成熟不判定下滑。\n'
       '4. **确认两项业务定义：** 新增付费是否采用注册当日，以及哪些生产渠道码属于PWA。确认后固化主表；当前PWA归属仍为待确认。\n'
       '5. **补齐辅助价值：** 按新的人群定义重算各端累计付费率、LTV与付费ARPU，不能沿用创建订单口径。',None)
    md('caveats','## 数据边界\n\n'
       '本版是付费留存主线的可核验阶段结果：APP与H5已重算，PWA映射及新增付费窗口待业务确认。首充只纳入服务端成功首充与画像日期相匹配的用户；匹配缺失不等于未留存。'
       '活跃统计使用历史与实时日活联合来源；不是仅凭客户端页面事件，也不把第N日活跃解释为再次付费。各月人群构成不同，当前结果定位差异与趋势，不证明因果。',None)
    snapshot.clear();snapshot.update({'version':1,'generatedAt':manifest['generatedAt'],'status':'partial','datasets':datasets})
    # The report surface uses a bounded snapshot; SQL/raw receipts remain immutable.
    (ROOT/'payer_chart_map.json').write_text(json.dumps([
        {'id':'new_curve','question':'新增付费用户的短期活跃水平','type':'line','points_per_series':13,'series':3,'scope':'8月各观察日成熟批次'},
        {'id':'first_curve','question':'首充用户的短期活跃水平','type':'line','points_per_series':13,'series':3,'scope':'8月各观察日成熟批次'},
        {'id':'paid-rate-chart','question':'注册当日付费率月度比较','type':'grouped bar','months':3,'platforms':3}
    ],ensure_ascii=False,indent=2),encoding='utf-8')

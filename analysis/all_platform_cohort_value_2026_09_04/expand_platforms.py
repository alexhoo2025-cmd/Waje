"""Restore the requested all-platform, three-month reader-facing scope."""
from copy import deepcopy


def expand_platforms(manifest, snapshot, summary):
    datasets = snapshot['datasets']
    rows = [deepcopy(r) for r in summary['platform_retention_monthly']
            if r['platform'] in ('Android', 'iOS', 'H5')]
    lookup = {(r['cohort_month'], r['platform']): r for r in rows}
    months = ('2026-06', '2026-07', '2026-08')
    platforms = ('Android', 'iOS', 'H5')
    pct = lambda v: f'{v * 100:.2f}%'
    datasets['platform_retention_monthly'] = rows

    # Keep exact source rates and denominators in the snapshot; mark incomplete
    # coverage in reader-facing cells rather than pretending it is a full month.
    display = []
    for month in months:
        for platform in platforms:
            r = deepcopy(lookup[month, platform])
            r['month_label'] = f'{int(month[-2:])}月'
            for day in (2, 7, 14, 30, 60, 90):
                value = r.get(f'day_{day}_retention')
                eligible = r.get(f'day_{day}_retention_mature_users')
                suffix = '＊' if eligible and eligible < r['cohort_users'] else ''
                r[f'retention_{day}_display'] = pct(value) + suffix if value is not None else '未到观察日'
            display.append(r)
    datasets['platform_retention_display'] = display

    def col(field, label, fmt=None):
        result = {'field': field, 'label': label, 'type': 'number' if fmt else 'text'}
        if fmt:
            result['format'] = fmt
        return result

    def table(id_, title, subtitle, dataset, source, columns):
        return {'id': id_, 'title': title, 'subtitle': subtitle, 'dataset': dataset,
                'sourceId': source, 'layout': 'full', 'density': 'spacious',
                'columns': columns}

    manifest['tables'] = [t for t in manifest['tables'] if t['id'] != 'platform-retention-key']
    manifest['tables'].extend([
        table('platform-retention-key', '6—8月全平台：新增与短期留存',
              '按首平台注册月汇总；＊表示仅覆盖部分注册批次，不是完整月度留存。',
              'platform_retention_display', 'platform-retention',
              [col('month_label', '注册月'), col('platform', '平台'), col('cohort_users', '新增用户', 'number')]
              + [col(f'retention_{d}_display', f'第{d}日留存') for d in (2, 7, 14)]),
        table('platform-long-retention', '6—8月全平台：30／60／90日留存',
              '各观察日使用各自有效批次；＊为部分批次，未成熟不补零。',
              'platform_retention_display', 'platform-retention',
              [col('month_label', '注册月'), col('platform', '平台')]
              + [col(f'retention_{d}_display', f'第{d}日留存') for d in (30, 60, 90)]),
    ])

    payments = [deepcopy(r) for r in datasets['app_payment_segments'] if r['platform'] in ('Android', 'iOS')]
    datasets['app_payment_visible'] = payments
    pay_lookup = {(r['period'], r['platform']): r for r in payments}
    manifest['tables'].append(table(
        'app-payment-visible', 'APP：6、7月付费用户结构与人均付费',
        '完整月度窗口，仅限能关联首付画像的用户；人群有交集，不相加。',
        'app_payment_visible', 'payment-segmentation', [
            col('period', '月份'), col('platform', '平台'),
            col('unique_paying_users', '付费用户', 'number'),
            col('unique_new_registered_payers', '新增付费', 'number'),
            col('unique_first_payers', '首充付费', 'number'),
            col('unique_old_payers_at_period_start', '期初老付费', 'number'),
            col('payer_arppu', '付费 ARPPU', 'number'),
        ]))

    app_counts = [sum(lookup[m, p]['cohort_users'] for p in ('Android', 'iOS')) for m in months]
    h5_counts = [lookup[m, 'H5']['cohort_users'] for m in months]
    scale_text = ('**新增规模：APP 8月回升，H5同步增长。** '
                  '6／7／8月 APP 新增分别为 ' + ' → '.join(f'{n:,}' for n in app_counts) + '；'
                  'H5 为 ' + ' → '.join(f'{n:,}' for n in h5_counts) + '。'
                  f'8月较7月分别增长 **{(app_counts[2]/app_counts[1]-1)*100:.1f}%**、'
                  f'**{(h5_counts[2]/h5_counts[1]-1)*100:.1f}%**。')
    retention_text = '**规模增长未带来更高留存，Android应优先下钻。** 7→8月第2日留存：' + '；'.join(
        f'{p} {pct(lookup[months[1],p]["day_2_retention"])} → {pct(lookup[months[2],p]["day_2_retention"])}'
        f'（{(lookup[months[2],p]["day_2_retention"]-lookup[months[1],p]["day_2_retention"])*100:+.2f}个百分点）'
        for p in platforms) + '。'
    blocks = {b['id']: b for b in manifest['blocks']}
    original_summary = blocks['summary']['body'].split('\n\n')
    h5_summary = [p for p in original_summary if '付费率下降' in p or '生命周期价值继续下移' in p]
    blocks['summary']['body'] = '\n\n'.join(['## 执行摘要', scale_text, retention_text,
        '**6月不是省略项。** 下文列出三个月各平台的新增和短／长期留存，并补充 APP 6、7月付费分层。6月短期留存仅覆盖部分晚注册批次，不能据此判断6→7月整体改善或恶化。'] + h5_summary)
    manifest['title'] = 'Waje 全平台用户增长与付费分析｜6—8月 · H5自然新增重点'
    manifest['description'] = 'Android、iOS、H5 三个月新增与留存总览、APP付费分层，重点下钻H5自然新增。'
    blocks['title']['body'] = '# ' + manifest['title']

    coverage = ('**读表说明：** 日活源记录从6月30日开始，6月第2／7／14日仅覆盖部分晚注册批次，'
                '不能当作6月整月短期留存；6月第30／60日已覆盖全月注册用户。'
                '7月第60日、6月第90日以及8月长期指标只纳入已到观察日的批次。带＊数据应结合观察范围阅读。')
    blocks['platform-story']['body'] = ('## 01｜6—8月全平台新增与留存\n\n' + scale_text + '\n\n' + coverage)
    app_story = ['## 02｜APP专题：Android与iOS分别看', retention_text]
    june30 = '；'.join(f'{p} {pct(lookup[months[0],p]["day_30_retention"])} → {pct(lookup[months[1],p]["day_30_retention"])}' for p in ('Android','iOS'))
    app_story.append('**6→7月完整批次第30日留存：** ' + june30 + '。两端长期留存变化较小；8月先重点核查Android次日回访下降，不能仅用H5解释全产品变化。')
    manifest['blocks'] = [b for b in manifest['blocks'] if b['id'] not in ('platform-story', 'platform-table')]
    additions = [blocks['platform-story'], blocks['platform-table'],
        {'id':'platform-long-table','type':'table','tableId':'platform-long-retention'},
        {'id':'platform-source','type':'markdown','sourceId':'platform-retention',
         'body':'来源：起源用户画像与日活聚合｜6—8月首平台注册批次｜观察数据截至9月4日。平台未知用户未并入Android、iOS或H5。'},
        {'id':'app-story','type':'markdown','sourceId':'platform-retention','body':'\n\n'.join(app_story)}]
    pay_text = []
    for p in ('Android', 'iOS'):
        before, after = pay_lookup['2026-06',p], pay_lookup['2026-07',p]
        pay_text.append(f'**{p}（6→7月）：** 付费用户 {before["unique_paying_users"]:,} → {after["unique_paying_users"]:,}'
                        f'（{(after["unique_paying_users"]/before["unique_paying_users"]-1)*100:+.1f}%）；'
                        f'新增付费 {before["unique_new_registered_payers"]:,} → {after["unique_new_registered_payers"]:,}；'
                        f'付费 ARPPU {before["payer_arppu"]:,.2f} → {after["payer_arppu"]:,.2f}'
                        f'（{(after["payer_arppu"]/before["payer_arppu"]-1)*100:+.1f}%）。')
    pay_text.append('**解读：** Android 7月付费用户增加但新增付费减少，应拆开新增转化与老用户贡献；iOS付费人数和人均付费均上升。以上是可关联首付画像人群，不是全站所有付费用户。')
    pay_text.append('**8月付费数据边界：** 当前已校验结果尚无APP完整月度去重付费汇总，因此不把两个半月人数相加。APP付费率缺少同口径分母、LTV缺少已验证平台映射，暂不输出；不使用H5值代替。付费 ARPPU＝成功付费金额÷付费用户数，与全部新增用户口径的ARPU不同。')
    additions.extend([
        {'id':'app-payment-story','type':'markdown','sourceId':'payment-segmentation','body':'\n\n'.join(pay_text)},
        {'id':'app-payment-table','type':'table','tableId':'app-payment-visible'},
        {'id':'app-payment-source','type':'markdown','sourceId':'payment-segmentation','body':'来源：6、7月去重成功订单与首付画像聚合｜按首平台汇总。新增付费＝当月注册并付费；首充＝首次付费发生在当月；期初老付费＝月初前已首充且当月付费，不含当月首充用户。'},
    ])
    pos = next(i for i,b in enumerate(manifest['blocks']) if b['id']=='priority')
    manifest['blocks'][pos:pos] = additions
    headings = {'priority':'03｜优先行动','retention-story':'04｜H5自然新增留存',
                'ltv-payment-story':'05｜H5生命周期价值','payment-story':'06｜H5付费率与人均支付',
                'stage-story':'07｜H5付费用户结构'}
    for id_, heading in headings.items():
        blocks[id_]['body'] = '## ' + heading + '\n' + blocks[id_]['body'].split('\n',1)[1]
    blocks['priority']['body'] += '\n3. **Android留存：** 按包名、渠道及版本拆解7→8月第2日下降，核查新增流量结构与首日到次日回访；iOS使用相同维度对照。\n4. **APP付费：** 补齐8月完整月度去重结果后，再评估新增、首充与老付费趋势。'

    # Make June explicit in the focused H5 interpretation as well as its chart.
    ltv = {r['cohort_month']:r for r in summary['h5_lifecycle_source_monthly']}
    blocks['ltv-payment-story']['body'] += '\n\n**6／7／8月完整趋势：** 第14日LTV ' + ' → '.join(f'{ltv[m]["ltv_14"]:,.2f}' for m in months) + '；第30日LTV ' + ' → '.join(f'{ltv[m]["ltv_30"]:,.2f}' for m in months) + '。这组联运来源H5指标持续下行，不用于替代APP或严格H5画像口径。'
    pay = {r['cohort_month']:r for r in datasets['h5_payment_monthly']}
    blocks['payment-story']['body'] += '\n\n**6／7／8月第14日付费率：** ' + ' → '.join(pct(pay[m]['day_14_payment_rate']) for m in months) + '。7月上升、8月回落；应定位8月新增用户从注册到首充的转化损失。'
    blocks['payment-story']['body'] = blocks['payment-story']['body'].replace('付费覆盖','付费率')
    blocks['retention-story']['body'] += '\n\n6月短期留存同样受日活源起始日期限制，曲线只代表有效晚注册批次；不把6→7月曲线差距解释为整月改善。'

    # The landing cards must visibly include APP, not only H5.
    headline = datasets['headline'][0]
    cards = []
    for p in ('Android','iOS'):
        for m,label in (('2026-07','july'),('2026-08','august')):
            headline[f'{p}_{label}_d2'] = lookup[m,p]['day_2_retention']
        cards.append({'id':f'{p}-d2','dataset':'headline','sourceId':'platform-retention',
                      'description':f'{p}首平台注册批次第2日活跃留存',
                      'metrics':[{'label':f'8月 {p} 第2日留存','field':f'{p}_august_d2','format':'percent'},
                                 {'label':'7月对照','field':f'{p}_july_d2','format':'percent'}]})
    manifest['cards'] = cards + [c for c in manifest['cards'] if c['id'] in ('h5-aug-d14-retention','h5-aug-d14-payment')]
    blocks['headline']['cardIds'] = [c['id'] for c in manifest['cards']]

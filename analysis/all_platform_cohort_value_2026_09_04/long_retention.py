"""Source-backed long retention comparisons; no imputation or rate averaging."""
def add_long_retention(manifest, snapshot, daily):
    rows = []
    evidence = []
    for day, months in ((30, ('2026-06', '2026-07', '2026-08')),
                        (60, ('2026-06', '2026-07'))):
        for platform in ('Android', 'iOS', 'H5'):
            valid_days = [
                {r['cohort_date'][-2:] for r in daily
                 if r['platform'] == platform and r['cohort_date'].startswith(month)
                 and r.get(f'day_{day}_retention') is not None}
                for month in months
            ]
            shared = sorted(set.intersection(*valid_days))
            assert shared, 'No mutually observed registration dates'
            row = {'day': day, 'horizon': f'第{day}日', 'platform': platform,
                   'registration_scope': f'各月{int(shared[0])}—{int(shared[-1])}日注册',
                   'matched_days': ','.join(shared), 'august': None}
            for month, label in zip(months, ('june', 'july', 'august')):
                selected = [r for r in daily if r['platform'] == platform
                            and r['cohort_date'].startswith(month) and r['cohort_date'][-2:] in shared]
                denominator = sum(r['cohort_users'] for r in selected)
                # Daily rates were returned from integer active-user counts.
                # Recover and validate those numerators before aggregating.
                numerator = 0
                for item in selected:
                    count = item['cohort_users'] * item[f'day_{day}_retention']
                    assert abs(count-round(count)) < 1e-6
                    numerator += round(count)
                    evidence.append({'day': day, 'platform': platform,
                                     'cohort_date': item['cohort_date'],
                                     'cohort_users': item['cohort_users'], 'retained_users': round(count)})
                row[label] = numerator / denominator
                row[f'{label}_retained_users'] = numerator
                row[f'{label}_cohort_users'] = denominator
                row[f'{label}_display'] = f'{row[label]*100:.2f}%'
            if day == 60:
                row['august_display'] = '未到观察日'
            previous, current = ('july', 'august') if day == 30 else ('june', 'july')
            row['comparison'] = '7→8月' if day == 30 else '6→7月'
            row['change_pp'] = (row[current]-row[previous])*100
            row['relative_change'] = row[current]/row[previous]-1
            row['change_display'] = f'{row["change_pp"]:+.2f}个百分点（{row["relative_change"]*100:+.1f}%）'
            rows.append(row)
    snapshot['datasets']['long_retention_matched'] = rows
    snapshot['datasets']['long_retention_matched_daily'] = evidence

    def text_col(field, label, movement=False):
        result = {'field': field, 'label': label, 'type': 'text'}
        if movement:
            result['movement'] = True
        return result
    manifest['tables'].append({
        'id': 'long-retention-matched', 'title': '长留同范围比较：第30日与第60日',
        'subtitle': '第30日比较各月1—6日注册用户；第60日比较6、7月1—7日注册用户。',
        'dataset': 'long_retention_matched', 'sourceId': 'platform-retention',
        'layout': 'full', 'density': 'spacious',
        'columns': [text_col('horizon', '留存日'), text_col('platform', '平台'),
                    text_col('june_display', '6月'), text_col('july_display', '7月'),
                    text_col('august_display', '8月'), text_col('comparison', '比较月份'),
                    text_col('change_display', '变化：百分点／相对幅度', True)]})
    by_key = {(r['day'],r['platform']):r for r in rows}
    overview = [r for r in snapshot['datasets']['platform_retention_monthly'] if r['cohort_month']=='2026-06']
    june = {r['platform']:r for r in overview}
    baseline = '；'.join(f'{p} **{june[p]["day_30_retention"]*100:.2f}% → {june[p]["day_60_retention"]*100:.2f}%**'
                        for p in ('Android', 'iOS', 'H5'))
    introduction = ('### 第30／60日长留：H5水平低，APP也出现走弱信号\n\n'
        '**先看完整批次的长期水平。** 6月整月注册用户，第30日→第60日留存：' + baseline + '。'
        'H5长期回访水平低于Android和iOS；这是一项平台差异，尚不能直接归因于产品或渠道质量。\n\n'
        '**口径：** 第30／60日留存是注册后第30／60个自然日当天回访的人数占比，不是30／60天内曾回访的比例。'
        '两个留存率的差值也不等于同一批活跃玩家的流失比例。下表保留各月所有已到观察日的有效数据。')
    interpretation = ['### 长留变化分析：对齐注册日期范围后再比较',
        '第30日对齐6、7、8月各月1—6日注册用户；第60日对齐6、7月各月1—7日注册用户。'
        '按各批次注册人数加权，不简单平均每日百分比。此比较用于检查月初批次趋势，不能外推整月；节假日、包名和渠道构成仍可能不同。']
    for p in ('Android','iOS','H5'):
        d30,d60 = by_key[30,p],by_key[60,p]
        interpretation.append(
            f'**{p}：** 第30日7→8月 **{d30["july_display"]} → {d30["august_display"]}**，'
            f'变化 **{d30["change_display"]}**；第60日6→7月 **{d60["june_display"]} → {d60["july_display"]}**，'
            f'变化 **{d60["change_display"]}**。')
    interpretation.append('**定位重点：** Android、iOS在上述月初批次的第30日和第60日均下降，需按包名与渠道检查长期回访；'
        'H5第30日回落、较早批次第60日略升，不能笼统写成所有长留持续恶化。H5应优先拆分自然、投放及其他入口，'
        '继续检查第14→30日各日回访和首充／老付费玩家的长留。以上只定位现象，未验证原因。')
    interpretation.append('**尚不能判断：** 8月注册用户尚未达到第60日，不能给出8月第60日留存或其环比；第90日继续保留已成熟数据。')
    new_blocks = []
    for block in manifest['blocks']:
        if block['id']=='platform-long-table':
            new_blocks.append({'id':'long-retention-levels','type':'markdown','sourceId':'platform-retention','body':introduction})
        new_blocks.append(block)
        if block['id']=='platform-long-table':
            new_blocks.extend([
                {'id':'long-retention-analysis','type':'markdown','sourceId':'platform-retention','body':'\n\n'.join(interpretation)},
                {'id':'long-retention-matched-table','type':'table','tableId':'long-retention-matched'}])
    manifest['blocks'] = new_blocks
    # Supporting source notes explain why a table, not a two-point trend chart.
    source = next(s for s in manifest['sources'] if s['id']=='platform-retention')
    source['query'].setdefault('metric_definitions', []).append(
        '长留同范围比较：每个观察日取所比较月份共同可观测的月内注册日期；从日率与注册人数还原整数回访人数，先加总分子分母后相除。'
        '第30日各月1—6日，第60日6、7月1—7日；保留最大有效批次月表，配对比较单独展示。'
        '只有2—3个可比月份，采用数值与变动表，不绘制暗示连续走势的折线。')

"""Category roll-up for the existing report, based only on reviewed aggregates."""
import json
import re
import sqlite3
from datetime import datetime, timezone


def apply_category_summary(root, run):
    data = json.loads((run / 'analysis-results.json').read_text())
    artifact = json.loads((run / 'artifact.json').read_text())
    games = data['game_rows']
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE reviewed_game_summary (game_type TEXT,total_bet REAL,total_win REAL,net_win REAL,total_count INTEGER)')
    conn.executemany('INSERT INTO reviewed_game_summary VALUES (?,?,?,?,?)',
      [(r['game_type'],r['total_bet'],r['total_win'],r['net_win'],r['total_count']) for r in games])
    sql_path = run / 'sql/03_category_summary.sql'
    sql = sql_path.read_text()
    categories = [dict(r) for r in conn.execute(sql)]
    conn.close()
    pct = lambda x: f'{x*100:.2f}%'
    def share_text(x):
        return '<0.01%' if 0 < x < .0001 else pct(x)
    for row in categories:
        same = sorted([g for g in games if g['game_type']==row['game_type']],key=lambda g:g['total_bet'],reverse=True)
        row['top_game'] = same[0]['game_id'].split('_',1)[-1]
        row['top1_bet_share_within_category'] = same[0]['total_bet']/row['total_bet']
        row['top3_bet_share_within_category'] = sum(g['total_bet'] for g in same[:3])/row['total_bet']
        row.update(bet_share_display=share_text(row['bet_share']),net_share_display=share_text(row['net_share']),
          weighted_rtp_display=pct(row['weighted_rtp']),net_margin_display=pct(row['net_margin']),
          top3_display=pct(row['top3_bet_share_within_category']))
    assert sum(r['games'] for r in categories)==len(games)==161
    errors = {key:sum(r[key] for r in categories)-data['portfolio'][key] for key in ('total_bet','total_win','net_win','total_count')}
    assert all(abs(v)<.01 for v in errors.values()), errors
    assert abs(sum(r['bet_share'] for r in categories)-1)<1e-10
    assert abs(sum(r['net_share'] for r in categories)-1)<1e-10
    bytype = {r['game_type']:r for r in categories}
    slot,fish,casino,card = [bytype[k] for k in ('Slot','Fish','Casino','Card')]
    x7_bet = data['x7_hot']['total_bet']/slot['total_bet']
    x7_net = data['x7_hot']['net_win']/slot['net_win']
    overview = '## 5. Slot、Fish、Casino 品类汇总\n\n按源表Game Type原分类汇总。下注和净赢占比均以全表161款游戏为分母，保留负净赢；加权RTP＝Σ派奖÷Σ下注，净赢率＝Σ净赢÷Σ下注。金额沿用源表单位，业务期间与币种仍待确认。\n'
    scale_rows = '\n'.join(f"| {r['game_type']} | {r['games']} | {r['total_bet']:,.2f} | {r['bet_share_display']} | {r['net_win']:,.2f} | {r['net_share_display']} |" for r in categories)
    efficiency_rows = '\n'.join(f"| {r['game_type']} | {r['weighted_rtp_display']} | {r['net_margin_display']} | {r['top3_display']} |" for r in categories)
    interpretation = f'''### 品类分析

- **Slot是核心规模来源。** 107款游戏贡献{pct(slot['bet_share'])}的下注额与{pct(slot['net_share'])}的净赢，加权RTP为{pct(slot['weighted_rtp'])}，净赢率{pct(slot['net_margin'])}。X7 HOT占Slot下注的{pct(x7_bet)}、净赢的{pct(x7_net)}；它是单款头部游戏，但不能代表整个Slot品类。
- **Fish规模第二，净赢率略低。** 14款贡献{pct(fish['bet_share'])}的下注和{pct(fish['net_share'])}的净赢，RTP为{pct(fish['weighted_rtp'])}，净赢率{pct(fish['net_margin'])}。头部3款占品类下注{fish['top3_display']}，其中Mega Fishing一款占{pct(fish['top1_bet_share_within_category'])}，结果较集中于少数游戏。
- **Casino单位下注净赢率略高，绝对净赢受规模限制。** 35款占下注{pct(casino['bet_share'])}、净赢{pct(casino['net_share'])}；RTP为{pct(casino['weighted_rtp'])}，净赢率{pct(casino['net_margin'])}，比Fish高{(casino['net_margin']-fish['net_margin'])*100:.2f}个百分点。前3款占Casino下注{casino['top3_display']}，需同时观察头部游戏构成。
- **三大品类净赢率差距约0.22个百分点，规模结构对绝对净赢的解释更直接。** 品类汇总是描述性比较，不能据此认定某类游戏应调整RTP，也不能证明推荐或收藏带来增量。

Card作为补充项保留：5款、下注102,200、净赢26,960，仅占全表下注{card['bet_share']*100:.6f}%和净赢{card['net_share']*100:.6f}%；Total Count为{card['total_count']:,}。其RTP{pct(card['weighted_rtp'])}不适合直接与三大高规模品类判断稳定优劣。四类合计已对回全表下注、派奖和Net Win。
'''
    category_md = overview + '\n| 品类 | 游戏数 | Total Bet | 占总下注 | Net Win | 占总净收入 |\n|---|---:|---:|---:|---:|---:|\n' + scale_rows
    category_md += '\n\n| 品类 | 加权RTP | 净赢率 | 前3款占品类下注 |\n|---|---:|---:|---:|\n' + efficiency_rows + '\n\n' + interpretation
    report = (run/'report.md').read_text()
    assert re.search(r'## 5\..*?(?=## 6\.)', report, re.S)
    report = re.sub(r'## 5\..*?(?=## 6\.)',lambda m:category_md+'\n\n',report,flags=re.S)
    (run/'report.md').write_text(report)
    (run/'category-summary.md').write_text(category_md+'\n')
    manifest = artifact['manifest']
    source = {'id':'src-category-rollup','label':'第三方161款游戏的品类聚合',
       'path':str(sql_path.relative_to(root)), 'query':{'engine':'SQLite in-memory over reviewed workbook aggregates','language':'sql','sql':sql,
       'description':'源表原始Game Type分组，排除Total行，累计金额复算RTP及全表下注/净赢贡献；Card保留为余项。',
       'tables_used':['Currency_Summary_Report_2026-09-04_06-41-44.xlsx / Summary!A1:H163'],
       'executed_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
       'metric_definitions':['加权RTP=品类总派奖/品类总下注','净赢率=品类总净赢/品类总下注','下注占比和净赢占比分母为全表161游戏合计，包含负净赢']}}
    manifest['sources']=[s for s in manifest['sources'] if s.get('id')!=source['id']]+[source]
    artifact['snapshot']['datasets']['category_rollup']=categories
    artifact['snapshot']['datasets']['category_contribution']=[{'game_type':r['game_type'],'metric':label,'share':r[key]} for r in categories if r['game_type']!='Card' for label,key in [('下注额占比','bet_share'),('净收入占比','net_share')]]
    tables=[
      {'id':'category-scale','title':'品类下注与净收入汇总','dataset':'category_rollup','sourceId':source['id'],
       'defaultSort':{'field':'total_bet','direction':'desc'},'columns':[
        {'field':'game_type','label':'品类','type':'text'}, {'field':'games','label':'游戏数','type':'number','format':'number'},
        {'field':'total_bet','label':'Total Bet','type':'number','format':'number'}, {'field':'bet_share_display','label':'占总下注','type':'text'},
        {'field':'net_win','label':'Net Win','type':'number','format':'number'}, {'field':'net_share_display','label':'占总净收入','type':'text'}]},
      {'id':'category-efficiency','title':'品类回报、净赢率与头部集中度','dataset':'category_rollup','sourceId':source['id'],
       'defaultSort':{'field':'game_type','direction':'asc'},'columns':[
        {'field':'game_type','label':'品类','type':'text'}, {'field':'weighted_rtp_display','label':'加权RTP','type':'text'},
        {'field':'net_margin_display','label':'净赢率','type':'text'}, {'field':'top3_display','label':'前3款占品类下注','type':'text'}]}
    ]
    manifest['tables']=[t for t in manifest['tables'] if t['id'] not in ('category-scale','category-efficiency')]+tables
    chart={'id':'category-contribution','title':'三大品类下注与净收入贡献','type':'bar','dataset':'category_contribution','sourceId':source['id'],
      'encodings':{'x':{'field':'game_type','type':'nominal','label':'品类'},'y':{'field':'share','type':'quantitative','format':'percent','label':'占全表比例'},
        'color':{'field':'metric','type':'nominal','label':'指标'},'tooltip':[{'field':'game_type','type':'nominal'},{'field':'metric','type':'nominal'},{'field':'share','type':'quantitative','format':'percent'}]}}
    manifest['charts']=[c for c in manifest['charts'] if c['id']!=chart['id']]+[chart]
    ids={'category-overview','category-scale-table','category-efficiency-table','category-contribution-chart','category-analysis'}
    blocks=[b for b in manifest['blocks'] if b['id'] not in ids]
    idx=next(i for i,b in enumerate(blocks) if b['id']=='identity-live')
    blocks[idx:idx]=[
       {'id':'category-overview','type':'markdown','body':overview,'sourceId':source['id']},
       {'id':'category-scale-table','type':'table','tableId':'category-scale'},
       {'id':'category-contribution-chart','type':'chart','chartId':'category-contribution'},
       {'id':'category-efficiency-table','type':'table','tableId':'category-efficiency'},
       {'id':'category-analysis','type':'markdown','body':interpretation,'sourceId':source['id']},
    ]
    manifest['blocks']=blocks
    data['category_summary']=categories
    audit={'status':'passed','input_game_rows':len(games),'category_count':len(categories),'reconciliation_residuals':errors,
      'ratio_method':'ratio of summed amounts','share_denominator':'all 161 games including Card and negative Net Win',
      'x7_share_within_slot':{'bet_share':x7_bet,'net_share':x7_net}}
    for filename,obj in [('artifact.json',artifact),('analysis-results.json',data),('category-summary.json',categories),('category-quality-checks.json',audit)]:
        (run/filename).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


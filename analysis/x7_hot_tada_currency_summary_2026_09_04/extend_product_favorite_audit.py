#!/usr/bin/env python3
"""Extend the reviewed X7 report from local aggregates and bounded source receipts."""
import csv
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
DICT = ROOT / 'analysis/game_code_dictionary_2026_08_31/game_code_name_mapping.csv'
SAMPLE = ROOT / 'analysis/h5_lightgame_first_pay_path_v5_2026_08_28/results/00_current_first_pay_game_summary.csv'
now = datetime.now(timezone.utc).isoformat(timespec='seconds')
backup = RUN / 'revisions' / 'before_product_favorite_audit'
backup.mkdir(parents=True, exist_ok=True)
for name in ('report.md', 'report.html', 'artifact.json', 'analysis-results.json', 'source-receipt.json', 'quality-checks.json'):
    src = RUN / name
    if src.exists() and not (backup / name).exists():
        shutil.copy2(src, backup / name)

def read_json(path):
    return json.loads(path.read_text())

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def norm(value):
    return ' '.join(value.casefold().split())

with DICT.open(newline='') as f:
    catalog = list(csv.DictReader(f))
with SAMPLE.open(newline='') as f:
    sample = list(csv.DictReader(f))
data = read_json(RUN / 'analysis-results.json')
artifact = read_json(RUN / 'artifact.json')
byname = {}
for row in catalog:
    if row['provider'].casefold() == 'tada':
        byname.setdefault(norm(row['game_name']), []).append(row)
byid = {row['game_id']: row for row in sample}
matched = []
for row in data['game_rows']:
    provider_id, name = row['game_id'].split('_', 1)
    candidates = byname.get(norm(name), [])
    ids = sorted(set(r['game_id'] for r in candidates))
    if len(ids) == 1:
        matched.append({'third_party_game_id': provider_id, 'game_name': name,
                        'waje_game_id': ids[0], 'match_status': 'unique_provider_name_match'})
match_by_provider = {r['third_party_game_id']: r for r in matched}
assert match_by_provider['680']['waje_game_id'] == '40163'
x7 = data['x7_hot']
official = 0.9703
actual = x7['total_win'] / x7['total_bet']
expected_net = x7['total_bet'] * (1 - official)
reference_gap = x7['net_win'] - expected_net
comparison = []
for row in data['x7_peers']:
    provider_id, name = row['game_id'].split('_', 1)
    match = match_by_provider.get(provider_id)
    s = byid.get(match['waje_game_id']) if match else None
    comparison.append({'game_name': name, 'waje_game_id': match['waje_game_id'] if match else None,
      'third_party_game_id': provider_id, 'sample_users': int(s['users']) if s else None,
      'cumulative_rounds': int(s['round_count']) if s else None,
      'sample_bet': float(s['bet_amount']) if s else None,
      'rounds_per_user': int(s['round_count']) / int(s['users']) if s else None,
      'bet_per_user': float(s['bet_amount']) / int(s['users']) if s else None,
      'last_update': s['last_update'] if s else None,
      'status': 'provisional_cumulative_snapshot' if s else 'not_available'})
assert len(comparison) == 7
sql_path = RUN / 'sql/02_waje_participation_snapshot.sql'
query = sql_path.read_text()
conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row
conn.execute('CREATE TABLE reviewed_participation_input (game_name TEXT, waje_game_id TEXT, third_party_game_id TEXT, sample_users INTEGER, cumulative_rounds INTEGER, sample_bet REAL, last_update TEXT, status TEXT)')
cols = ['game_name','waje_game_id','third_party_game_id','sample_users','cumulative_rounds','sample_bet','last_update','status']
conn.executemany('INSERT INTO reviewed_participation_input VALUES (?,?,?,?,?,?,?,?)', [[r[k] for k in cols] for r in comparison])
comparison = [dict(r) for r in conn.execute(query)]
conn.close()
assert len(comparison) == 7
xx = next(r for r in comparison if r['waje_game_id'] == '40163')
users_rank = 1 + sum(r['sample_users'] > xx['sample_users'] for r in comparison if r['sample_users'] is not None)
depth_rank = 1 + sum(r['rounds_per_user'] > xx['rounds_per_user'] for r in comparison if r['rounds_per_user'] is not None)

favorite_evidence = [
 {'item':'游戏收藏功能','evidence':'用户截图X7 HOT红心；H5首页PRD revision 2808明定添加/取消喜爱并进入Favorites','status':'function_observed_and_documented'},
 {'item':'专用收藏/取消收藏事件','evidence':'模块表revision168，A2:M87回读84条功能定义；页面表revision91，A1:M41；未检出明确游戏收藏事件','status':'not_found_in_reviewed_registry'},
 {'item':'普通游戏入口点击','evidence':'6kygobdgyi_mc，携带play_id；搜索栏点击6tvs9hfjpe_mc；不能替代收藏结果','status':'definition_observed'},
 {'item':'For You MV/MC','evidence':'H5 wxkp9lm776_mv/mc；APP eittdmb81f_mv/mc。配置存在；收藏动作枚举及生产接收未认证','status':'configured_receipt_only'},
 {'item':'历史收藏引导','evidence':'ne5sydxolh（1/1）与82wyo0hdz6（0/0）为页面配置计数；未证明与游戏红心收藏同义','status':'semantics_unconfirmed'},
 {'item':'疑似收藏数据表','evidence':'ApolloPortalDB.Favorite是配置平台应用收藏；easy_win_fav_casina含sport和competition_id，不能当X7游戏收藏事实','status':'excluded_or_unconfirmed'},
 {'item':'收藏生产聚合','evidence':'BigQuery MCP当前Auth required；起源模块页空白；未获得收藏人数、次数、取消或收藏后游玩聚合','status':'blocked_not_zero'},
]
sources = [
 {'id':'waje-live','url':'https://www.wajegame.com/','observed_at':now,'evidence':'搜索X7 hot返回26项；X7卡面；图片路径/internal/img/NewH5Icon/40163.webp；点击后登录窗口；当前未登录TopGame9项无X7 HOT'},
 {'id':'tada-sheet','url':'https://wbgame.tadagaming.com/All-In-One/production/file/tadaPlusPlayer/pdf/gphkjI4WAnnmGnRtRQgiZX0xzC5cJG5cMEmVKIph-2ea95a26.pdf','observed_at':now,'evidence':'官方名称X7 HOT，ID680，Slot，HTML5，中波动，最高乘数7x、最高奖525x、RTP97.03%；仅作公开参考'},
 {'id':'h5-prd','url':'https://ksg964l11fam.sg.larksuite.com/wiki/Ucmuw1UAsiqee4kUMDkly28ngqc','document_id':'BoeddcpAKoC00WxvH6Ml5R03gSh','revision':2808,'evidence':'添加/取消喜爱→Favorites；最近打开→Recently Played；搜索采用名称模糊/厂商匹配且受用户类型配置影响'},
 {'id':'foryou-prd','url':'https://ksg964l11fam.sg.larksuite.com/wiki/V7yxwT516icdOCkT7wWlyizMg1e','revision':5046,'evidence':'服务端按端、设备、网络、付费及曝光位配置返回排序；前端不重排；设计不能证明X7实际命中'},
 {'id':'module-registry','url':'https://ksg964l11fam.sg.larksuite.com/wiki/JoHBwnONVi15DxkbVZ2lBVWDgse','revision':168,'sheet_id':'Cb1KyM','range':'A2:M87','truncated':False,'definition_rows':84,'explicit_favorite_definition_matches':0},
 {'id':'page-registry','url':'https://ksg964l11fam.sg.larksuite.com/wiki/OdIUweqY0ivlDhk7Xj6ljXvhgGc','revision':91,'sheet_id':'UfeS8F','range':'A1:M41','truncated':False,'explicit_favorite_definition_matches':0},
]
receipt = {'observed_at':now,'status':'partial_gameplay_and_favorite_facts_blocked',
 'identity':{'game_name':'X7 HOT','provider':'TaDa','third_party_game_id':'680','waje_game_id':'40163','catalog_csv_line':58,'catalog_revision':609,
 'matching_method':'provider + normalized exact name, cross-checked by visible Waje card asset ID; not a settlement-ID certification'},
 'mapping_coverage':{'third_party_games':len(data['game_rows']),'unique_name_matches':len(matched)},
 'gameplay':{'waje':'login_gate','official_demo':'dns_and_demo_redirect_load_failure','spins_completed':0,'real_money_actions':0,'experience_basis':'visible entry + official description, not played'},
 'favorite_evidence':favorite_evidence,'sources':sources,
 'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (DICT,SAMPLE)],
 'official_rtp_comparison':{'actual_rtp':actual,'public_reference_rtp':official,'gap_pp':(actual-official)*100,'net_at_public_reference':expected_net,'actual_net':x7['net_win'],'net_gap':reference_gap,'production_configuration_verified':False},
 'local_sample':{'rows':len(sample),'cutoff':'2026-08-28; row update times are not playing dates','population':'historical first-pay analysis preflight sample; full query/cohort selection not certified here','x7':xx,'users_rank_in_7':users_rank,'depth_rank_in_7':depth_rank},
 'favorite_metrics':{'add_users':None,'cancel_users':None,'favorite_state_users':None,'favorite_replay_rate':None,'favorite_bet_contribution':None}}
write_json(RUN/'product-favorite-source-receipt.json', receipt)
write_json(RUN/'game-identity-joins.json', {'coverage':receipt['mapping_coverage'],'matches':matched})
write_json(RUN/'waje-game-participation-comparison.json', comparison)

num = lambda x: 'N/A' if x is None else f'{x:,.2f}'.rstrip('0').rstrip('.')
table = '\n'.join(f"| {r['game_name']} | {r['waje_game_id']} | {r['sample_users']} | {r['cumulative_rounds']:,} | {r['rounds_per_user']:.2f} | {num(r['sample_bet'])} |" for r in comparison)
identity_md = '''## 6. 游戏身份与产品体验核验

**已确认 X7 HOT 的对应关系：TaDa 680 ↔ Waje 40163，展示名称为 X7 HOT。** 全量第三方161款中有139款与Waje目录形成唯一的厂商+标准名称匹配；交易联结仍需使用正式ID映射。

| 字段 | 核验结果 |
|---|---|
| 展示名 / 厂商 | X7 HOT / TaDa；680不是名称的一部分 |
| Waje ID / TaDa ID | 40163 / 680 |
| 类型与资源 | Slot；本地目录资源9.5MB、Classic主题、短连接、非包内（目录属性，非实测加载量） |
| 入口实测 | 未登录Waje搜索返回26个结果，包含X7 HOT；当前TopGame可见9款中未见X7 HOT |
| 试玩状态 | Waje点击后要求登录；官方演示页加载失败；尚未完成模拟旋转 |

官方说明呈现经典水果、BAR/777符号与乘数玩法，最高乘数7x、最高奖525x，中等波动。视觉符号熟悉、交互规则简单，可以作为参与意愿的待验证解释；加载速度、旋转节奏、实际手感、命中频率均未实测。**当前页面的搜索位置不是90天排名，也不代表登录后或App端展示。**
'''
sample_md = f'''## 7. 已关联的 Waje 游戏参与快照

按40163关联到现有首充分析预检快照：X7 HOT有 **367位用户、21,069次累计局数、1,421,775下注额**，人均 **57.41局、3,874.05下注额**。这提供了Waje侧真实参与线索。

| 游戏 | Waje ID | 样本用户 | 累计局数 | 人均局数 | 样本累计下注 |
|---|---:|---:|---:|---:|---:|
{table}

在这7款对照里，X7 HOT样本用户数第{users_rank}、人均局数第{depth_rank}。Fortune Garuda 500为594人、人均104.90局；X15 HOT为228人、人均128.50局。**这份有限样本不支持“X7 HOT的人均参与深度最高”**，也不能推翻第三方全量汇总的下注第一，因为两者人群和期间不同。

备注：文件采集于2026-08-28，X7行最后更新为08:37:56（来源会话记录Africa/Lagos）。原预检指出它是用户×游戏累计快照，update_at不是首次/当日开局时间。完整选人条件未在该CSV中保存，暂称“首充分析预检样本”，不声明为H5全量或首充后新增下注。没有派奖、收藏状态或跨日明细，不能计算本样本RTP、收藏复玩率或D7留存，也不得和第三方下注额相除作贡献率。
'''
favorites_md = '''## 8. 收藏功能、埋点与数据关联结论

**收藏功能有明确产品证据；专用游戏收藏上报与生产聚合尚未核实。** 用户截图中的红心、部门《h5-首页》revision 2808共同支持添加/取消喜爱和Favorites入口。文档还规定Recently Played按最近打开时间排序，说明TopGame之外存在回到游戏的路径。

| 证据层 | 本轮结果 | 对分析的作用 |
|---|---|---|
| 功能 | 卡片添加/取消喜爱，成功后进入Favorites | 确认用户可以收藏游戏 |
| 设计登记 | 模块方案revision168完整A2:M87、84条定义；页面方案revision91完整A1:M41，均未检出专用游戏收藏事件 | 只能说“本次回读范围未登记”，不能说后台绝无上报 |
| 已有入口事件 | 游戏入口点击6kygobdgyi_mc带play_id；搜索栏点击6tvs9hfjpe_mc | 可作为入口诊断候选，未证明点击来自Favorites；不能把play_id直接当40163 |
| 历史收藏提示 | ne5sydxolh、82wyo0hdz6是页面配置；1/1、0/0是配置数量 | 与浏览器收藏/桌面引导可能混淆，不能拿来当游戏收藏量 |
| 通用MC / For You | 可能通过event_id与参数承载动作；For You设计有MV/MC与game_id | 仍需核对favorite/unfavorite动作、操作结果和去重键 |
| 生产数据 | BigQuery MCP认证阻断，起源模块页空白 | 收藏人数、取消人数、收藏后下注/复玩均显示N/A |

元数据中的ApolloPortalDB.Favorite属于配置平台应用收藏；easy_win_fav_casina含sport、competition_id，不是已认证的Slot游戏收藏来源。不能见到Favorite表名就用于X7 HOT。

关联应落实为三步：①以Waje40163筛选添加/取消收藏成功事件并还原当时收藏状态；②把下一次游戏进入区分为Favorites、Recently Played、Search、TopGame、For You和其他入口；③在同日期、端、包、既往参与程度相近的人群中比较次日/7日复玩、下注人数及累计下注。**收藏之后再玩才提供时序支持；收藏用户本就可能更活跃，因此简单组间差异仍不能证明收藏造成提升。**

建议待确认契约：game_id、event_uid、action(add/remove)、result(success/fail)、favorite_state_before/after、entry_source、source_page、module_id、event_time、app/web_version、package/channel。若已在通用MC承载，复用真实事件；若未上报，再补这些字段。受控层内部做用户去重，报告只返回至少10人的聚合组。
'''
rtp_md = f'''## 9. 官方 RTP 参考与收益解释

TaDa官方Game Sheet列出X7 HOT参考RTP **97.03%**；工作簿累计金额复算为 **{actual*100:.6f}%**，高 **{(actual-official)*100:.4f}个百分点**。

| 指标 | 同一X7 HOT下注规模下的值 |
|---|---:|
| Total Bet | {num(x7['total_bet'])} |
| 实际Net Win | {num(x7['net_win'])} |
| 按官方公开97.03%计算的参考Net Win | {num(expected_net)} |
| 实际减参考 | {num(reference_gap)} |

固定下注额时，实际回报较参考更高，对应Net Win比参考少约 **348.63万**。这是金额恒等式对照，不是已发生损失认定，也不是调低RTP的收益预测：生产配置、币种版本、统计期间、局级方差尚未匹配，不能据此判为结算异常。游戏高总下注额从何而来，仍要通过入口、用户结构与跨日行为解释。

对于收藏驱动假设：当前证据链完成了“游戏身份→第三方经营汇总→Waje累计参与样本”，但在“收藏成功→收藏入口进入→后续复玩/下注”处缺少事实。现阶段可认定多入口回访机制存在，无法量化收藏贡献比例。
'''
sources_md = '''## 10. 待补充数据与后续分析

### 数据范围与待补充项

| 项目 | 中文说明 |
|---|---|
| 统计时间范围待确认 | 第三方表格未包含业务日期，文件名仅提供导出时间，尚不能确定它覆盖的统计期间。 |
| 曝光与渠道数据待关联 | 游戏身份已匹配：TaDa 680 ↔ Waje 40163；仍需补充同一期间的端、包体、渠道、展示位置、曝光与点击数据。 |
| 收藏与复玩数据待补充 | 已有Waje累计参与样本，但尚未取得收藏成功、取消收藏、收藏入口进入和跨日复玩数据，暂不能量化收藏的影响。 |
| 大额派奖分布待补充 | 现有数据仅包含累计派奖金额，缺少单局大额派奖分布，暂不能判断少数大奖对整体结果的贡献。 |

'''
audit_md = identity_md + '\n' + sample_md + '\n' + favorites_md + '\n' + rtp_md + '\n' + sources_md
(RUN/'product-favorites-audit.md').write_text('# X7 HOT 产品核验与收藏归因补充\n\n' + audit_md)

report_path = RUN/'report.md'
report = report_path.read_text().split('## 6.')[0]
report = report.replace('不是由异常高 RTP 支撑', '其实际RTP接近官方公开参考')
report = report.replace('完全依赖更大的下注规模', '在本次汇总中由更大的下注规模支撑')
report = report.replace('不是异常高 RTP 极值', '不位于全表RTP最高端，尚不能据此判断生产配置正常与否')
report = report.replace('文件没有业务日期、端、包体、曝光、点击、展示位置、收藏、复玩或 Waje 侧关联键；因此“用户偏好/收藏复玩/推荐算法”仍不能从本文件确认。', '本轮已建立TaDa680与Waje40163映射并关联到367人累计参与样本；曝光、收藏和跨日复玩仍缺同窗事实，尚不能确认偏好或算法驱动。')
report_path.write_text(report.rstrip() + '\n\n' + audit_md)

manifest = artifact['manifest']
src = {'id':'src-x7-product-favorites','label':'X7产品现场、部门PRD与Waje累计参与快照',
       'path':'analysis/x7_hot_tada_currency_summary_2026_09_04/product-favorites-audit.md',
       'query':{'description':'游戏卡片/官方资料核验，已授权部门文档回读，项目CSV按厂商+名称关联后以WajeID接入累计参与样本；无生产收藏查询结果。',
                'executed_at':now,'engine':'browser + Lark user read + local aggregate files',
                'tables_used':[str(DICT.relative_to(ROOT)),str(SAMPLE.relative_to(ROOT))],
                'metric_definitions':['人均局数=累计局数/样本用户数；不是跨日复玩率。','实际RTP=累计派奖/累计下注；官方97.03%尚未匹配生产配置。']}}
manifest['sources'] = [s for s in manifest.get('sources',[]) if s.get('id') != src['id']] + [src]
sample_source = {'id':'src-waje-participation-local-query','label':'Waje累计参与CSV的本地关联与人均指标复算',
 'path':str(sql_path.relative_to(ROOT)), 'query':{'engine':'SQLite in-memory over reviewed aggregate CSV rows',
 'language':'sql','sql':query,'executed_at':now,'description':'按TaDa厂商和标准游戏名关联目录，再以Waje游戏ID关联2026-08-28累计快照；仅输出7款聚合样本。',
 'tables_used':[str(DICT.relative_to(ROOT)),str(SAMPLE.relative_to(ROOT))],
 'metric_definitions':['人均局数=累计局数/样本用户数；不代表跨日复玩。','CSV更新时点不代表投注时间窗口。']}}
manifest['sources'] = [s for s in manifest['sources'] if s.get('id') != sample_source['id']] + [sample_source]
artifact['snapshot']['datasets']['waje_participation'] = comparison
manifest['tables'] = [t for t in manifest['tables'] if t['id'] != 'waje-participation'] + [{
 'id':'waje-participation','title':'已关联Waje累计参与样本（7款）','dataset':'waje_participation','sourceId':sample_source['id'],
 'defaultSort':{'field':'sample_users','direction':'desc'},'columns':[
 {'field':'game_name','label':'游戏','type':'text'},
 {'field':'sample_users','label':'样本人数','type':'number','format':'number'},
 {'field':'rounds_per_user','label':'人均局数','type':'number','format':'number'},
 {'field':'sample_bet','label':'累计下注','type':'number','format':'number'},
 {'field':'waje_game_id','label':'Waje ID','type':'text'}]}]
manifest['charts'] = [c for c in manifest['charts'] if c['id'] != 'waje-depth'] + [{
 'id':'waje-depth','title':'7款游戏样本人均累计局数','type':'bar','dataset':'waje_participation','sourceId':sample_source['id'],
 'encodings':{'x':{'field':'game_name','type':'nominal','label':'游戏'},'y':{'field':'rounds_per_user','type':'quantitative','format':'number','label':'人均累计局数'},
 'tooltip':[{'field':'game_name','type':'nominal'},{'field':'sample_users','type':'quantitative'},{'field':'rounds_per_user','type':'quantitative'},{'field':'last_update','type':'nominal'}]}}]
headline = dict(x7)
headline.update(actual_rtp_display=f'{actual * 100:.4f}%',
                bet_share_display=f"{x7['bet_share'] * 100:.2f}%",
                net_share_display=f"{x7['net_share'] * 100:.2f}%")
artifact['snapshot']['datasets']['x7_headlines'] = [headline]
card_defs = [
 ('stake', '累计下注额', 'total_bet', 'bet_rank'),
 ('payout', '累计派奖额', 'total_win', None),
 ('net', '累计净赢 Net Win', 'net_win', 'net_rank'),
 ('rtp', '实际 RTP', 'actual_rtp_display', None),
 ('stake-share', '下注额占全表', 'bet_share_display', None),
 ('net-share', '净赢占全表', 'net_share_display', None),
]
headline_ids = ['x7-headline-' + x[0] for x in card_defs]
manifest['cards'] = [c for c in manifest.get('cards',[]) if not c['id'].startswith('x7-headline-')]
for key, label, field, rank in card_defs:
    metrics = [{'label':label,'field':field,'format':'number'}]
    if rank:
        metrics.append({'label':'161款游戏中排名','field':rank,'format':'number'})
    manifest['cards'].append({'id':'x7-headline-'+key,'dataset':'x7_headlines',
      'sourceId':'src-currency-summary',
      'source':{'path':'analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql'},
      'description':'第三方工作簿汇总快照；统计期间、币种及金额单位待源方确认。净赢=下注−派奖。',
      'metrics':metrics})
readout = [
 ('游戏名称 / 身份', 'X7 HOT', 'TaDa 680 ↔ Waje 40163'),
 ('累计下注额', num(x7['total_bet']), '第1 / 161；占全表6.35%'),
 ('累计派奖额', num(x7['total_win']), '工作簿Total Win字段'),
 ('累计净赢 Net Win', num(x7['net_win']), '第1 / 161；占全表5.54%'),
 ('实际 RTP', f'{actual*100:.6f}%', '累计派奖÷累计下注'),
 ('净赢率', f"{x7['net_margin']*100:.6f}%", '累计净赢÷累计下注'),
 ('统计次数 Total Count', f"{x7['total_count']:,}", '第2 / 161；不能当作用户数'),
 ('官方参考 RTP', '97.03%', '公开资料参考，生产配置未认证'),
]
artifact['snapshot']['datasets']['x7_metrics_readout'] = [dict(metric=m,value=v,context=c,sort_order=i) for i,(m,v,c) in enumerate(readout)]
for t in manifest['tables']:
    if t['id']=='x7-core':
        t.update(title='X7 HOT 核心数据一览',dataset='x7_metrics_readout',
          defaultSort={'field':'metric','direction':'asc'},columns=[
          {'field':'metric','label':'指标','type':'text'},
          {'field':'value','label':'数值','type':'text'},
          {'field':'context','label':'解释','type':'text'}])
summary_md = '## 汇总结论\n\n' + '\n\n'.join([
 '**X7 HOT在这份161款游戏汇总中，累计下注和净赢均排第1。** 下注2,321,612,200，净赢65,465,600；下注占全表6.35%，净赢占5.54%。',
 '**实际RTP为97.180166%，净赢率为2.819834%。** 高绝对净赢由较大的下注规模与该净赢率共同构成；官方公开参考RTP为97.03%，尚不能据差额判定生产异常。',
 '**已关联Waje历史样本，但“长期领先的原因”尚未确认。** 367位用户累计21,069局，人均57.41局；收藏功能存在，收藏后进入、复玩及投注贡献仍缺生产数据。',
 '数据范围：第三方文件名时间为2026-09-04 06:41:44，业务统计期间和币种/金额单位未明确；Waje样本最后更新于2026-08-28，两者分别解读。'])
cut = next(i for i,b in enumerate(manifest['blocks']) if b['id'] in ('exposure','identity-live'))
blocks = [b for b in manifest['blocks'][:cut] if b['id'] != 'core-headlines']
summary_index = next(i for i,b in enumerate(blocks) if b['id']=='summary')
blocks.insert(summary_index+1, {'id':'core-headlines','type':'metric-strip','cardIds':headline_ids})
blocks += [
 {'id':'identity-live','type':'markdown','body':identity_md,'sourceId':src['id']},
 {'id':'waje-sample','type':'markdown','body':sample_md.split('| 游戏')[0] + '\n备注：2026-08-28首充分析预检的累计快照；update_at不是游玩日，不能声明为H5全量或首充后的新增下注。\n','sourceId':src['id']},
 {'id':'waje-participation-table','type':'table','tableId':'waje-participation'},
 {'id':'waje-depth-chart','type':'chart','chartId':'waje-depth'},
 {'id':'sample-interpretation','type':'markdown','body':f'X7 HOT在7款样本中人数第{users_rank}、人均局数第{depth_rank}。这个样本不支持“人均参与深度最高”；累计局数不能识别收藏用户或跨日留存。两份汇总期间与人群不同，不交叉计算贡献率。','sourceId':src['id']},
 {'id':'favorite-audit','type':'markdown','body':favorites_md,'sourceId':src['id']},
 {'id':'official-reference','type':'markdown','body':rtp_md,'sourceId':src['id']},
 {'id':'product-sources','type':'markdown','body':sources_md},
]
for block in blocks:
    if block.get('id') == 'summary':
        block['body'] = summary_md
    if block.get('id') == 'relationship':
        reg = data['net_win_rtp_regression']
        block['body'] = block['body'].split('\n\n回归方程：')[0]
        block['body'] += f"\n\n回归方程：Net Win = {reg['intercept']:,.2f} + {reg['slope']:,.2f} × RTP百分点（97.18%输入97.18）。直接拟合R²仅{reg['r_squared']*100:.2f}%，不能用正斜率解释提高RTP会增加利润。固定下注额时：ΔNet Win = −Total Bet × ΔRTP；X7每增加1个百分点RTP，净赢减少23,216,122，且这是固定规模情景，不是经营预测。"
manifest['blocks'] = [b for b in blocks if b['id'] not in ('quality', 'quality-table')]
for chart in manifest['charts']:
    if chart['id'] in ('top-bet-games', 'top-bet-share'):
        chart['labels'] = {'values': 'all'}
        chart['valueFormat'] = 'percent' if chart['id'] == 'top-bet-share' else 'compact'
        if chart['id'] == 'top-bet-games':
            chart['subtitle'] = '柱顶金额按亿显示，保留两位小数；完整下注金额可在悬浮提示和数据表查看。'
            if not any(x.get('field') == 'bet_share' for x in chart['encodings'].get('tooltip', [])):
                chart['encodings']['tooltip'].append({'field':'bet_share','type':'quantitative','format':'percent'})
        else:
            chart['subtitle'] = '柱顶显示各游戏占全表161款游戏总下注的比例。'
    if chart['id'] == 'rtp-net-scatter':
        chart['encodings']['x'].update(domain=[0.5,1.2], ticks=[0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2], format='percent')
        outside = sum(not 0.5 <= r['reported_rtp'] <= 1.2 for r in data['game_rows'])
        chart['subtitle'] = f'横轴50%—120%；{outside}款区间外游戏不在图窗内。相关系数仍基于全部161款游戏：Pearson r=0.133，Spearman ρ=0.268。'
# Keep engineering checks in their audit JSON files, not in the reader payload.
manifest['tables'] = [t for t in manifest['tables'] if t['id'] != 'quality-checks']
artifact['snapshot']['datasets'].pop('quality_checks', None)
report = report_path.read_text()
report_path.write_text(report[:report.index('## ')] + summary_md + '\n\n' + report[report.index('## 1. X7 HOT 的核心结果'):])
manifest['generatedAt'] = now
artifact['snapshot']['generatedAt'] = now
artifact['snapshot'].pop('accessIssues',None)
# Reconcile sensitivity actual row with unrounded observed amounts.
for r in artifact['snapshot']['datasets'].get('x7_rtp_sensitivity',[]):
    if r.get('scenario') == 'X7 HOT实际RTP':
        r.update(rtp=actual, expected_net_win=x7['net_win'], delta_vs_actual=0)
data['product_favorite_audit'] = receipt
data['waje_participation_comparison'] = comparison
data['waje_exposure_context'].update(x7_game_id='40163', third_party_game_id='680',
   x7_mapping_status='matched_catalog_and_live_card', x7_exposure_reason='游戏身份已匹配；仍未取得同窗曝光、收藏操作与来源入口事实。')
write_json(RUN/'analysis-results.json',data)
write_json(RUN/'artifact.json',artifact)
quality=read_json(RUN/'quality-checks.json')
quality['product_favorite_checks']={'catalog_unique_x7':True,'live_card_id_matches':True,'third_party_id_official':True,
 'local_sample_joined':True,'peers':7,'favorite_metrics_proven':False,'demo_completed':False,'public_rtp_is_production_config':False}
write_json(RUN/'quality-checks.json',quality)
(ROOT/'knowledge/02-数据/X7-HOT游戏身份与收藏上报核验-2026-09-04.md').write_text('# X7 HOT 游戏身份、参与快照与收藏上报核验\n\n' + audit_md)
from category_summary import apply_category_summary
apply_category_summary(ROOT, RUN)
print(json.dumps({'mapping':receipt['identity'],'matching_games':len(matched),'local_sample':xx,
 'favorite_status':'not_verified','demo_completed':False,'report':str(RUN/'report.html')},ensure_ascii=False))

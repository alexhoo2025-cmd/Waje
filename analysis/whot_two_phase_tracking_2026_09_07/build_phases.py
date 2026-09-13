#!/usr/bin/env python3
"""Partition the reviewed 15-topic contract; render all surfaces from one section model."""
import argparse
import copy
import hashlib
import html
import json
import re
from pathlib import Path
from datetime import datetime
import sqlite3

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
SOURCE=ROOT/'analysis/whot_tracking_review_2026_09_07/v2/requirements_contract.json'
TEMPLATE=ROOT/'analysis/whot_tracking_review_2026_09_07/v2/artifact.json'
STAMP=datetime.now().astimezone().isoformat(timespec='seconds')
COMMON=[
 '所有指标以真人为主，机器人和身份未知单列。用户分组为新/老×付费/非付费；一期定义的分组、端、包和规则版本在二期沿用。',
 '新用户建议为注册当日，老用户为此前注册；首次玩Whot另设维度。最终天数规则需策划签字，二期不得另起一套定义。',
 '人数按窗口去重用户；次数按曝光ID、动作ID或业务尝试ID去重。传输重试复用事件UID。局数按整桌ID，人局数按牌局ID＋参与者；四人一桌是1局、4个人局。',
 'UTC存储、Africa/Lagos展示；匹配按受理时间归属。业务等待时间和入库缓冲均结束后才进入统计；未知结果保留在分母并单列占比。缓冲建议5分钟，其他加载/购买/归因窗口分别配置并签字。',
 'APP和H5使用同一服务端玩法事实。端/包/网页/APP/规则版本独立记录；共享桌按端统计可能重叠，不能直接把两端桌数相加。',
 '分母为0显示N/A；曝光、接受、购买、充值、提现各阶段分别记录。小于10人的报表分组隐藏或合并，明细关联仅留受控数据层。'
]
FIELDS=[
 ('event_uid / event_version','string / string','每条事件必填','同一业务事件重传复用UID；新schema升级版本'),
 ('event_name / action / source','string / enum / enum','每条事件必填','逻辑名映射平台实际event_id；client/server/ledger区分'),
 ('event_time / received_at / server_seq','timestamp / timestamp / int64','时间必填；seq服务状态必填','存UTC；服务端顺序用于乱序修正，客户端耗时用本地单调时钟'),
 ('user_key / participant_key','string','用户事件必填；参与者在局内必填','使用既有受控身份关联键，不上传直接身份信息'),
 ('client_type / package_name / app_version / web_version','enum / string','按端条件必填','APP/H5、Android/iOS和版本分别可查；非适用版本可空'),
 ('game_family / client_game_id / server_game_id / play_id / ruleset_version','string','映射与版本必填','6001/9006和玩法ID关系由研发确认；规则版本不可仅靠game_id推断'),
 ('platform_tenure / whot_experience / payer_state_at_event','enum','每个用户事件必填或unknown','新/老、首次/非首次Whot、付费/非付费分别记录'),
 ('analysis_segment_at_entry / cohort_rule_version','enum / string','旅程开始时冻结','漏斗分组沿用入口状态；实际付费状态可随事件变化'),
 ('root_match_id / match_attempt_id','string','匹配请求和后续结果必填','自动重试同attempt；重新受理新attempt，迁移保留前后关联'),
 ('requested_mode / actual_count','int enum','请求时前者必填；组桌后后者必填','请求只允许2/4；实际人数允许2/3/4；未组桌不能填0伪造结果'),
 ('room_id / payer_pool / pool_id','string / enum / string','服务端受理后必填','手动请求房间与服务端resolved_room_id分别保存'),
 ('queue_epoch / offer_id / offer_stage','int64 / string / enum','降级建议和响应必填','N1/N2独立；人员变化使旧offer失效；stage限N1/N2等签字值'),
 ('game_round_id / human_count / robot_count','string / int64 / int64','GAMESTART及局事实必填','同桌只生成一局；sum人机席位数等于actual_count'),
 ('exposure_id / action_id','string','展示/点击条件必填','一可见实例一exposure；每次真实点击一action，接受展示数另去重'),
 ('result / reason / config_version','enum / enum / string','有业务结果时必填','结果与失败原因分列；未定义枚举留unknown并告警')
]
PHASE2_FIELDS=[
 ('state_transition_id / auto_episode_id','string','托管/恢复','一段托管可含多个动作；恢复手动按服务端成功转换'),
 ('last_card_window_id / penalty_id','string','宣告/抓罚/处罚','同一窗口允许多个抓罚请求，只有一个处罚ID有效'),
 ('tracker_funnel_id / purchase_attempt_id / entitlement_id','string','购买与权益','购买方式展示→提交→结果→权益关联，不按回调条数计成功'),
 ('method_code / sku_id / effective_round_id','enum / string','记牌器按条件必填','购买方式来自后台真实枚举；当局购买下一局生效需校验'),
 ('tie_break_id / draw_round_no','string / int64','同分抽牌','重复抽牌递增轮号；同分局数只按game_round_id计一次'),
 ('disconnect_episode_id / reconnect_attempt_id / snapshot_version','string','断线/重连','一段断线可有多次重试；恢复完整快照才算恢复成功'),
 ('settlement_id / currency / asset_type / amount_unit','string / enum','资金结算必填','有效下注、派奖、退款、费用分别存；跨币种不直接合并'),
 ('guide_exposure_id / guide_type / guide_id / guide_version','string / enum','资金引导','deposit/withdraw分开；一期的exposure_id规则沿用'),
 ('attribution_window / destination','配置值 / enum','引导归因','窗口和多触点规则需签字；一个业务成功只归给一个符合规则的引导')
]

def p(text):return '<p>'+html.escape(str(text))+'</p>'
def table_xml(headers,rows):
    head='<thead><tr>'+''.join('<th background-color="light-blue">'+p(h)+'</th>' for h in headers)+'</tr></thead>'
    return '<table>'+head+'<tbody>'+''.join('<tr>'+''.join('<td>'+p(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'
def table_md(headers,rows):return '| '+' | '.join(headers)+' |\n|'+ '|'.join('---' for _ in headers)+'|\n'+''.join('| '+' | '.join(str(v).replace('|','／').replace('\n','；') for v in row)+' |\n' for row in rows)
def sections_for(phase,groups):
    first=phase==1
    sec=[]
    def heading(level,text):sec.append(('h',level,text))
    def para(text):sec.append(('p',text))
    def note(text):sec.append(('note',text))
    def table(headers,rows):sec.append(('table',headers,rows))
    heading(1,'总体方案')
    para('一期目标：沿进入到开局的用户路径，回答谁进入、引导是否接受、加载是否完成、选择哪种模式和房间、是否匹配成功及四人降级能否挽回开局。' if first else '二期目标：在一期身份、匹配和开局链路上，补齐局内体验、新规则、恢复、购买权益、结算展示和资金引导，定位开局后的流失与转化。')
    note('分期依据：采用截图最后“先做前七项、局内放二期”的建议。新人引导纳入一期；截图较早提到的Last Card、结算、充值引导按最终分期放入二期。')
    table(['原需求编号','场景','本期交付'],[[f"需求{g['requirement_id']:02d}",g['name'],g['takeaway']] for g in groups])
    heading(2,'实施路径与期际依赖')
    para('用户分组 → 新人引导 → 进入与加载 → 选择2/4人 → 选房/快速匹配 → 受理与排队 → 降级建议与响应 → 服务端匹配结果 → 最小GAMESTART回执。' if first else '沿用一期GAMESTART及身份 → 托管/手动/退出 → Last Card与同分决胜 → 断线重连 → 记牌器购买和使用 → GAMEEND及资金结算 → 结算展示/再玩 → 充值和提现引导。图示顺序是分析路径，局内动作不必按此顺序全部发生。')
    note('一期最小依赖：GAMESTART的attempt、round、participant、requested_mode、actual_count、人机组成与版本必须一起落地，才能统计局数和开局率；这是需求04/06/07的基础，二期再扩展GAMEEND、结算展示与资金分析。如果新版本没有此回执，一期只能验收匹配结果，开局率标记暂不可用。' if first else '二期启动条件：一期共用身份、game_load_id、match_attempt_id、game_round_id、规则版本及端包映射已验收。沿用既有GAMESTART事件与命名，不新建重复开局来源。二期的局内托管/重连不同于一期匹配时的断线终态；两者按阶段区分。')
    heading(2,'范围边界与交付物')
    para('交付：本期字段与事件合同、服务端/客户端映射表、聚合指标表、端到端验收用例和入库回读结果。本文为实施评审方案，实际平台event_id由埋点管理员创建后回填；当前未执行生产发布。')
    para('一期保留匹配阶段断线、风控拒绝和建桌失败原因；完整局内网络诊断、记牌器、Last Card、同分、结算、充值/提现引导在二期。' if first else '二期新增08—15的详细行为；01—07的分组、请求分母、房间和匹配来源作为依赖复用，不算二期重复实施范围。')
    heading(1,'核心数据指标及算法')
    heading(2,'统计规则')
    for text in COMMON:para(text)
    heading(2,'优先查看的核心指标')
    table(['指标','分子／统计值','分母／条件','用途'],[
      ['匹配后开局率','已关联GAMESTART的受理真人attempt数','统计观察期已结束的受理真人attempt数','能否真正开始玩'],
      ['四人原模式兑现率','请求4人并实际开4人attempt数','统计观察期已结束的4人请求数','用户所选模式兑现'],
      ['开局等待P95','成功者的started_at－accepted_at的95分位','成功样本，并同时看失败/取消/未知比例','响应体验'],
      ['加载成功率','达到真实ready的load数','统计观察期已结束的load start数','入口损失'],
      ['新人引导接受率','被接受的引导展示数','已展示引导实例数','引导吸引力']
    ] if first else [
      ['对局完成率','正常结束的真人人局数','统计观察期已结束的已开始真人人局数','局内体验；异常退出单列'],
      ['最终结算覆盖率','有唯一服务端最终结算的真人人局数','应结算且观察期已结束的真人人局数','结算可靠性'],
      ['结算展示覆盖率','看到结算的真人人局数','已完成结算真人人局数','用户收到结果'],
      ['引导接受率','被接受的引导展示实例数','对应deposit或withdraw展示实例数','触达转化；两种引导分开'],
      ['同币种RTP','最终有效派奖之和','最终有效下注之和；剔除取消、重复、未结算，退款按确认规则处理','金额加权，不平均个人RTP']])
    heading(2,'按需求逐项计算')
    for g in groups:
      heading(3,f"需求{g['requirement_id']:02d}｜{g['name']}")
      table(['统计对象／动作','指标及算法'],[[e['logical_event'],e['metric_definition']] for e in g['events']])
    heading(2,'数据质量监控')
    para('结果成功、失败、取消、超时、失效和未知按业务层级分别统计。比例展示分子和分母；任何字段缺失、样本不足和观察时间不足都不填0。跨端、跨用户分组UV可能重复，汇总重新去重。')
    para('匹配终态率与开局率分开：matched是桌位分配完成，GAMESTART是牌局真正开始。共同5/10/15秒开局率使用全部观察期结束的受理请求；不把45秒等待上限缩放成15秒。' if first else '充值引导接受仅代表点击，记牌器成功仅代表服务端购买完成，提现还需分别看申请/审核/到账。资金指标依赖最终账本，不以score或净输赢字段替代派奖。')
    heading(1,'具体埋点实现')
    heading(2,'公共字段及复用规范')
    table(['字段','类型','填写条件','定义与校验'],FIELDS if first else FIELDS[:8]+FIELDS[12:]+PHASE2_FIELDS)
    para('所有以下事件名为逻辑合同：event_name与action拆列，映射既有MC/MV/PV或专用事件时只能选择一条权威统计链。前端意图与服务端结果可各报一次，但必须标记source、关联同一action_id，聚合时不得合并相加。')
    heading(2,'逐项事件与触发实现')
    for g in groups:
      heading(3,f"需求{g['requirement_id']:02d}｜{g['name']}")
      para(g['takeaway'])
      table(['事件／动作','上报责任','触发条件','专属字段'],[[e['logical_event'],e['source'],e['trigger'],e['fields']] for e in g['events']])
    heading(2,'关键状态及跨事件连接')
    for text in ([
      '引导：show→accept/close；accept可继续step_complete/complete。离开或切后台单列，未完成不能推断主动关闭。引导资格、步骤和完成条件待策划定稿。',
      '加载：start→ready/fail/timeout/abandon；bet_ready为另一个能力到达点，不当作第二次load成功。重载新load_id，阶段内重试保留关联。',
      '降级：issued→shown→accept/reject/timeout；人员变化走invalidated，不能计作拒绝/超时。N1/N2重新生成offer_id与同意集合；Keep Waiting是拒绝替代开局，不是取消匹配。',
      '匹配：accepted→matched/failed/cancelled；队列迁移记录migrated＋next_attempt_id，不能归为业务失败。matched继续关联GAMESTART。取消先于建桌则取消，建桌先行则取消未生效；每attempt最终唯一裁决。',
      '一期数据流：用户和客户端上下文→点击/加载→服务端受理及建议→响应与结果→GAMESTART参与事实→小时/日聚合。建议批次按offer_id，用户响应按offer_id＋用户，局数按round。'
    ] if first else [
      '托管与退出：auto_enter→manual_resume或牌局终止，auto_episode_id贯穿；exit_request→exit_result，退出可能转托管而不结束整桌。',
      'Last Card：opportunity→declared或missed→catch_success/catch_fail→penalty或expired。抓罚失败需真实请求，没人抓罚只是窗口失效。同一窗口多请求只允许一次处罚；20 WHOT先完成图案选择。',
      '记牌器：entry_click→methods_show→method_select→purchase_submit→success/failed/cancelled/pending→effective→open_used。已有权益直接使用另列；购买方式来自后台实际枚举，下一局生效通过effective_round_id校验。',
      '同分：started→draw_round→resolved或下一draw_round；无论抽几轮，同分局数按game_round_id计一次。',
      '网络：一个disconnect_episode_id下可多个reconnect_attempt_id；网络连接成功还需完整快照恢复成功。异常退出区分客户端确认与服务端超时推断。',
      '结算：GAMEEND→最终BETREWARD/ASSET→WHOT_SETTLEMENT show→play_again/back_rooms；实际复玩需next_root_match_id关联后续GAMESTART。',
      '资金引导：show→accept/close→业务后续；按guide_exposure_id关联，归因窗建议同会话或30分钟、并由业务签字。多个引导触达同一成功订单只能按确定规则归一次；提现到账需独立长窗口。'
    ]):para(text)
    heading(2,'本期验收与上线顺序')
    table(['负责人','交付','通过条件'],[
      ['策划','人群/模式/房间/时序/结果枚举签字','新用户规则、引导资格、N1/N2与游戏ID映射明确' if first else 'Last Card、购买方式、下一局、引导场景及资金口径明确'],
      ['客户端','可见展示、意图及体验事件','重复点击/重试不误计；APP/H5可定位'],
      ['服务端／业务服务','唯一结果与幂等关联','服务端终态、开局或权益/资金结果可回查'],
      ['数据开发','分层聚合与指标计算','分子分母、UTC/Lagos、观察期截止和未知状态一致'],
      ['测试','端到端回放与双端验收','必测场景100%通过；错误定位到事件和字段']])
    para('必测：新老付费四组、引导接受/关闭/完成、冷/热缓存和弱网、默认模式与真实点击、多房间及余额不足、N1/N2全部响应组合与人员变化、取消/建桌竞争、跨队列迁移、最小GAMESTART关联。' if first else '必测：超时/断线托管恢复、多对手并发抓罚只一次处罚、无人抓罚无处罚、20选图案顺序、各真实购买方式失败重试及下一局权益、重复同分、重连状态恢复、重复结算回调、多次结算展示、再玩关联、两类资金引导及多触点归因。')
    note('发布质量目标（建议，待签字）：关键关联覆盖≥99.5%，必填缺失<0.1%，同一业务事实重复计数为0；应有结果而未知的请求单列。二期资金未解释差额必须为0。先完成测试回放，再灰度观察，最后按同口径发布报表。')
    heading(2,'待确认事项与来源')
    para('本期需定稿：平台新用户天数与首次Whot定义、新人引导步骤和资格、6001/9006/play_id、匹配成功/开局服务节点、N1/N2及超时配置、入库缓冲。' if first else '本期需定稿：Last Card的3秒与回合机会规则、记牌器购买方式和生效局、退出后的托管处理、最终派奖是否含本金、充值/提现引导场景与接受动作、充值归因窗与提现到账观察窗。')
    para('来源：用户15项需求清单与本轮分期截图最终建议；策划方案最近已核验版本revision 5738；原V2完整合同。当前文档为设计计划，不表示事件已经实现。')
    return sec

def build(phase,draft):
    original=json.loads(SOURCE.read_text())['groups']
    groups=[g for g in original if (g['requirement_id']<=7)==(phase==1)]
    label='一期' if phase==1 else '二期'
    title=f'新版Whot{label}埋点计划｜'+('进入、选择与匹配' if phase==1 else '局内体验、结算与资金引导')
    folder=BASE/f'phase{phase}';folder.mkdir(exist_ok=True)
    sections=sections_for(phase,groups)
    xml=['<title>'+html.escape(title)+'</title>']
    md=['# '+title]
    blocks=[{'id':'title','type':'markdown','body':'# '+title}]
    for i,s in enumerate(sections):
      typ=s[0]
      if typ=='h':
        level,text=s[1:];xml.append(f'<h{level} seq="auto">{html.escape(text)}</h{level}>');body='#'*(level+1)+' '+text
      elif typ=='table':xml.append(table_xml(s[1],s[2]));body=table_md(s[1],s[2])
      elif typ=='note':xml.append('<callout background-color="light-yellow" border-color="orange">'+p(s[1])+'</callout>');body='> '+s[1]
      else:xml.append(p(s[1]));body=s[1]
      md.append(body);blocks.append({'id':f'content_{i:03d}','type':'markdown','body':body})
    # Header fragments are kept with their following paragraph/table in HTML.
    merged=[]
    for b in blocks:
      if merged and (merged[-1]['body'].startswith('#') and '\n\n' not in merged[-1]['body']):merged[-1]['body']+='\n\n'+b['body']
      else:merged.append(b)
    xml_text='\n'.join(xml)
    (ROOT/draft).write_text(xml_text,encoding='utf-8')
    (folder/'report.xml').write_text(xml_text,encoding='utf-8')
    (folder/'report.md').write_text('\n\n'.join(md)+'\n',encoding='utf-8')
    (folder/'requirements.json').write_text(json.dumps({'phase':phase,'groups':groups,'shared_dependencies':['user_context','GAMESTART','match_attempt_id','game_round_id','ruleset_version']},ensure_ascii=False,indent=2)+'\n')
    # Use the reviewed canonical source experience; only this phase's scope is counted.
    src=[{'id':'reviewed','label':'用户确认的15项需求及两期安排','path':f'analysis/whot_two_phase_tracking_2026_09_07/phase{phase}/requirements.json','description':'一期01—07；二期08—15。采用用户截图最后建议，GAMESTART作为一期最小依赖。'}]
    artifact={'surface':'report','manifest':{'version':1,'surface':'report','title':title,'generatedAt':STAMP,'sources':src,'cards':[],'charts':[],'tables':[],'blocks':merged},'snapshot':{'version':1,'generatedAt':STAMP,'status':'ready','datasets':{}},'sources':src}
    # The report renderer requires a native chart. Show contract coverage, not fabricated operations.
    dataset=[{'topic':g['name'],'entries':len(g['events'])} for g in groups]
    db=sqlite3.connect(':memory:');db.execute('CREATE TABLE requirements(topic TEXT, entries INTEGER)');db.executemany('INSERT INTO requirements VALUES (:topic,:entries)',dataset)
    sql='SELECT topic, SUM(entries) AS entries FROM requirements GROUP BY topic;'
    db.execute(sql).fetchall();db.close()
    src.append({'id':'phase_scope','label':f'{label}合同条目覆盖','query':{'engine':'sqlite','sql':sql,'description':'按已审核需求合同统计条目，数量不是事件编码数量、研发工作量或业务发生量。','tables_used':['requirements']}})
    artifact['snapshot']['datasets']={'scope':dataset}
    artifact['manifest']['charts']=[{'id':'scope','title':f'{label}需求合同覆盖','type':'bar','dataset':'scope','sourceId':'phase_scope','encodings':{'x':{'field':'topic','type':'nominal'},'y':{'field':'entries','type':'quantitative'}},'yAxisTitle':'合同条目数'}]
    insert=next(i for i,b in enumerate(merged) if b['body'].startswith('## 核心数据指标'))
    merged[insert:insert]=[{'id':'scope_explain','type':'markdown','body':'### 本期覆盖概览\n\n下图只表示各需求的合同条目数量，便于核对覆盖；不表示研发工作量或线上数据。详细内容见下方指标及实施表。'},{'id':'scope_chart','type':'chart','chartId':'scope'}]
    (folder/'artifact.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
    return {'phase':phase,'title':title,'requirement_ids':[g['requirement_id'] for g in groups],'entry_count':sum(len(g['events']) for g in groups),'draft_path':draft,'section_headings':[s[2] for s in sections if s[0]=='h' and s[1]==1]}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--draft1',required=True);ap.add_argument('--draft2',required=True);a=ap.parse_args()
    phases=[build(1,a.draft1),build(2,a.draft2)]
    ids=sum([p['requirement_ids'] for p in phases],[])
    assert sorted(ids)==list(range(1,16)) and len(ids)==len(set(ids))
    assert all(p['section_headings']==['总体方案','核心数据指标及算法','具体埋点实现'] for p in phases)
    receipt={'status':'passed','generated_at':STAMP,'source_hash':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'phases':phases,'coverage':'15/15, disjoint requirement ownership','allocation_basis':'用户截图最后建议前七项一期，08—15二期','schema_state':'proposed_not_deployed'}
    (BASE/'split_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))

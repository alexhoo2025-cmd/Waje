#!/usr/bin/env python3
"""Fifteen requirement groups, one canonical source for Markdown/HTML/contracts."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'v2'
OUT.mkdir(exist_ok=True)
STAMP=datetime.now().astimezone().isoformat(timespec='seconds')
TITLE='新版 Whot 埋点与数据指标｜15项需求评审版'
SOURCE='https://ksg964l11fam.sg.larksuite.com/wiki/WjLww2oliipOPzkJMHil0yvbglc'

# Each row: logical event/action, source, exact trigger, fields, metric/denominator.
GROUPS=[
('用户群体','将新老用户与付费状态交叉拆分；用户群体作为所有事件的公共维度。',[
('用户画像快照','服务端','事件发生时附加注册日、首次付费日期、首次玩Whot时间和当前付费状态','registration_date, first_pay_date, first_whot_started_at, payer_state_at_event, cohort_rule_version','人数=时间窗内去重真人；新老和付费两轴分别汇总，再交叉成四组'),
('新老口径','数据层','统计日期当天注册为新用户，其他为老用户；首次玩Whot单独标记','platform_tenure, whot_experience, analysis_segment_at_entry','四组：新付费、新非付费、老付费、老非付费；无法识别的用户单列')]),
('新人引导','区分看到引导、接受引导与完成引导；没有展示就没有接受率分母。',[
('WHOT_TUTORIAL / show','客户端','引导真正可见时，一次展示只报一次','tutorial_id, tutorial_version, exposure_id, step_id','展示次数=去重exposure_id；展示人数=去重用户'),
('WHOT_TUTORIAL / accept, close','客户端','点击开始引导或显式关闭','exposure_id, action_id, action, close_reason','接受率=被接受展示数/展示数；关闭率=被关闭展示数/展示数'),
('WHOT_TUTORIAL / step_complete, complete','客户端；规则完成由服务端校验','完成步骤和全部引导；切后台不当作主动关闭','tutorial_run_id, step_id, completion_source','完成率=完成run数/接受run数；按步骤看流失。引导是否真人匹配/模拟局需明确')]),
('进入游戏与加载','加载成功、画面可操作和可下注分别确认，才能找到首局入口损失。',[
('WHOT_LOAD / start','客户端主框架','进入Whot并开始加载，失败前也必须有开始事件','game_load_id, entry_source, cache_state, platform','加载次数=去重load_id；加载人数=去重用户'),
('WHOT_LOAD / ready, fail, timeout, abandon','客户端/游戏桥','游戏真实ready或错误、超时、离开终态','game_load_id, stage, duration_ms, error_code, downloaded_bytes','成功率=ready load数/统计观察期已结束的start load数；P50/P95耗时；放弃和未知终态单列'),
('WHOT_LOAD / bet_ready','游戏桥+服务端条件','余额、房间权限、连接、操作控件均可用','game_load_id, ready_source, readiness_reason','可下注到达率=bet_ready load数/start load数；H5复用既有H5_GAME_*并映射，不能双计')]),
('对局选择','选择2/4人与实际开2/3/4人分别统计；点击量不代表实际开局量。',[
('WHOT_MODE_SELECT / click','客户端','用户点击人数选择控件；默认预选不算点击','action_id, selection_id, requested_mode, selection_origin','点击次数=去重action_id；点击人数=去重用户；同时报告有效模式切换次数'),
('GAMESTART / player participation','服务端','牌局真正开始，为每位参与者生成参与记录','game_round_id, participant_key, requested_mode, actual_count, match_attempt_id','局数=去重game_round_id；人数=去重真人；人局数=去重round+participant；按选择模式追踪2→2、4→4/3/2')]),
('房间选择','快速匹配和手动进房分别看，保留系统推荐房间与最终受理房间。',[
('WHOT_ROOM / list_show','客户端','可见房间列表及推荐卡片展示','room_list_view_id, config_version, recommended_room_id, visible_room_ids','列表触达人数与次数；只上报可见房间ID，不上传完整配置'),
('WHOT_ROOM / quick_click, enter_click','客户端','点击Quick Match或某房间Enter','action_id, room_list_view_id, requested_mode, requested_room_id, entry_method','各方式点击人数/次数；房间点击率=点击该房间的列表展示数/该房间可见列表展示数'),
('WHOT_ROOM_RESULT / accepted, rejected','服务端','校验资产和房间权限，并选定真实房间','action_id, match_attempt_id, resolved_room_id, rejection_reason, payer_pool','受理率=被受理进房请求数/收到进房请求数；客户端点击到受理另看关联率')]),
('匹配情况','受理尝试、组桌成功和真正开局是三个阶段，取消由服务端裁决。',[
('WHOT_MATCH_REQUEST / accepted','服务端','一次匹配请求受理入队','root_match_id, match_attempt_id, requested_mode, payer_pool, pool_id, deadline_at','请求次数=去重attempt；匹配人数=去重真人'),
('WHOT_MATCH_END / matched, failed, cancelled','服务端','每个attempt唯一终态，成功定义为有效桌位已分配','match_attempt_id, table_id, actual_count, reason, accepted_at, ended_at','匹配成功率=matched attempts/统计观察期已结束的受理attempts；失败率/取消率同分母；未知终态不删除'),
('WHOT_MATCH_CANCEL / request, result','客户端请求+服务端结果','取消点击与取消是否生效分报，建桌先完成则拒绝取消','action_id, match_attempt_id, cancel_result, reason','取消成功率=确认取消attempts/有取消请求attempts；建桌竞争单列'),
('GAMESTART / linked start','服务端','已匹配用户真正进入开始状态','match_attempt_id, game_round_id, actual_count','开局率=关联GAMESTART attempts/受理attempts；匹配后未开局率；开局耗时与取消耗时分开看')]),
('4人局降级建议','建议送达、展示和最终响应分开；N1/N2必须有独立的建议与同意状态。',[
('WHOT_MATCH_OFFER / issued, shown','服务端签发+客户端可见','每个queue_epoch中生成建议；客户端实际可见时回执','offer_id, queue_epoch, stage, target_count, other_human_count, expires_at','建议批次数=去重offer_id；建议触达次数=去重offer_id+用户。多人共用offer不能乘成多批'),
('WHOT_MATCH_RESPONSE / accept, reject, timeout','服务端','校验用户响应；超时由服务端到期结算，未展示另标记','offer_id, participant_key, response, response_at, validation_result','接受/拒绝/超时次数=去重offer+用户的有效终态；接受率=接受机会数/已展示且统计观察期已结束的有效机会数'),
('WHOT_MATCH_OFFER / invalidated','服务端','人员加入离开、取消、断线使建议失效；清空旧同意','offer_id, queue_epoch, invalidated_reason','失效次数单列，不记为拒绝或超时；N1接受不能继承到N2'),
('GAMESTART / downgrade','服务端','明确同意的用户实际开2/3人局','requested_mode, actual_count, offer_id, consent_version, robot_count','4人兑现率=4→4开局attempts/4人受理attempts；降级开局率=4→2/3开局attempts/4人受理attempts')]),
('对局过程','玩家退出、超时托管和断线托管分别记录；恢复手动以服务端状态为准。',[
('WHOT_PLAY_STATE / auto_enter','服务端','从手动进入托管，一次状态改变报一次','game_round_id, participant_key, state_transition_id, reason','托管次数=进入转换数；托管人数=用户去重；托管人局率=托管人局/已开局真人参与人局'),
('WHOT_PLAY_STATE / manual_resume','服务端','用户恢复操作请求被接受并恢复手动','state_transition_id, auto_episode_id, reason','恢复次数/人数；恢复率=已恢复托管段/已结束托管段；仍进行中的段单列'),
('WHOT_PLAY_STATE / exit_request, exit_result','客户端+服务端','主动退出点击及服务端执行结果','action_id, game_round_id, exit_reason, continued_by_auto','退出请求和确认退出分开；退出人局率=确认退出人局/已开局真人人局；退出不必然等于牌局结束')]),
('Last Card','宣告成功、漏宣告与抓罚失败要用同一机会窗口关联，避免并发和重连重复计数。',[
('WHOT_LAST_CARD / opportunity, declared, missed','服务端','产生单牌机会、有效宣告、正式进入漏宣告状态','last_card_window_id, actor_key, ruleset_version, state_seq','宣告成功率=成功宣告窗口/统计观察期已结束的可宣告窗口；漏宣告次数=missed窗口；无人抓罚不自动罚牌'),
('WHOT_LAST_CARD / catch_request, catch_success, catch_fail','服务端','校验抓罚请求的胜出或失败结果','action_id, last_card_window_id, catcher_key, fail_reason','抓罚成功/失败次数=请求ID终态去重；成功率=成功请求/已终结抓罚请求；并发败选也属于失败原因'),
('WHOT_LAST_CARD / penalty, expired','服务端','唯一罚抽执行或所有对手机会用完','penalty_id, last_card_window_id, added_cards, expiry_reason','罚抽执行率=有效penalty/抓罚成功窗口；一个窗口最多一次罚抽2张；失效后重新宣告用新机会标识')]),
('记牌器','完整记录入口→方式展示→选择→购买结果→权益生效→打开使用。',[
('WHOT_TRACKER / entry_click, methods_show','客户端','入口点击；购买方式实际可见','action_id, tracker_funnel_id, exposure_id, placement, offered_method_codes','入口点击人数/次数；方式展示人数/次数；已有权益用户直接使用单列'),
('WHOT_TRACKER / method_select, purchase_submit','客户端','选择后端返回的购买方式；提交购买','tracker_funnel_id, purchase_attempt_id, method_code, sku_id, price, asset_type','各方式选择次数/人数；提交率=已提交funnel/已选择funnel。购买方式枚举待策划，不假定广告或现金'),
('WHOT_TRACKER_PURCHASE / success, failed, cancelled, pending','服务端/支付或权益服务','购买尝试达到对应业务状态；回调幂等','purchase_attempt_id, method_code, entitlement_id, result, error_code','成功率=成功attempts/统计观察期已结束的已提交attempts；失败/取消/待定分别报告；不能用客户端成功页替代'),
('WHOT_TRACKER / effective, open_used','服务端生效+客户端真实展开','权益真正生效；有效面板实际展开','entitlement_id, purchase_round_id, effective_round_id, tracker_view_id','购买后使用率=归因窗内使用的成功购买权益数/统计观察期已结束的成功购买权益数；当局购买下一局生效必须验收')]),
('同分抽牌','计数单位是发生同分的牌局，重复抽牌轮次作为另一个指标。',[
('WHOT_TIE_BREAK / started, draw_round, resolved','服务端','最低点多人相同进入决胜；每轮抽牌及最终结果','game_round_id, tie_break_id, draw_round_no, participant_count, result','同分局数=去重game_round_id；同分率=同分局/已终局牌局；条件同分率=同分局/牌堆耗尽局；决胜轮次不当局数')]),
('网络异常','断线、重连尝试和异常退出各有唯一标识，可追踪重试与恢复失败。',[
('WHOT_NETWORK / disconnected, reconnect_start','客户端；服务端可有独立观测','连接失效；每次重连开始','disconnect_episode_id, reconnect_attempt_id, game_round_id, network_type','断线次数=去重episode；重连次数=去重attempt；断线人数=用户去重'),
('WHOT_NETWORK / reconnect_success, reconnect_failed','客户端+服务端确认恢复','连接恢复且牌局快照应用成功；或重连失败','reconnect_attempt_id, snapshot_version, duration_ms, restored_state, error_code','重连成功率=成功attempts/统计观察期已结束的start attempts；段级恢复率=最终恢复episode/统计观察期已结束的断线episode'),
('WHOT_NETWORK / abnormal_exit','客户端尽力+服务端会话超时推断','崩溃、连接持续失效或进程退出导致离开','episode_id, exit_reason, observation_source, inference_rule_version','确认异常退出与推断分开；没有客户端退出事件不能自动认定主动退出')]),
('对局结算','游戏结束、服务端结算完成与客户端看见结算是不同事实。',[
('GAMEEND / ended','服务端','整桌结束与每位玩家结束记录分粒度','game_round_id, participant_key, end_reason, actual_count, duration_ms','对局结束局数=整桌round去重；玩家人局=round+用户；按正常出完/比点/决胜/异常分类'),
('BETREWARD + ASSET / final','服务端/账本','最终有效扣款、派奖、退款、抽成','settlement_id, game_round_id, currency, asset_type, amount_unit, final_stake, payout, fee, refund','下注/派奖按同币种有效终态加总；RTP=payout/final_stake；平台收益按账本口径，净输赢不能冒充派奖'),
('WHOT_SETTLEMENT / show','客户端','结算信息在任一结束页面实际可见','settlement_view_id, game_round_id, participant_key, surface, settlement_state','展示次数=去重view_id；展示覆盖率=已展示结算人局/已完成结算真人人局；重连新视图只增加PV'),
('WHOT_SETTLEMENT / play_again, back_rooms','客户端','点击再来一局或返回房间列表','action_id, settlement_view_id, next_root_match_id','点击次数/人数；再玩意向率=有再玩点击的结算人局/展示结算人局；实际复玩需关联后续GAMESTART')]),
('充值引导','统计引导触达、接受与后续支付；接受仅代表点击主按钮。',[
('WHOT_GUIDE / show; guide_type=deposit','客户端','充值引导真正展示','guide_exposure_id, guide_id, guide_version, scene, game_round_id','引导次数=去重exposure；人数=用户去重；场景区分破产/余额不足/结算等实际配置值'),
('WHOT_GUIDE / accept, close; guide_type=deposit','客户端','点击引导主按钮或关闭','guide_exposure_id, action_id, destination','接受次数=被接受exposure数；接受人数=用户去重；接受率=接受exposure/展示exposure'),
('充值后续归因','支付服务端','关联订单创建和成功付款','guide_exposure_id, payment_attempt_id（仅受控服务内部）, attribution_window','另报引导后充值人数/金额')]),
('提现引导','与充值引导复用结构，但申请、审核和到账必须分开。',[
('WHOT_GUIDE / show; guide_type=withdraw','客户端','提现引导实际展示','guide_exposure_id, guide_id, guide_version, scene, eligibility_state','引导次数=去重exposure；人数=用户去重'),
('WHOT_GUIDE / accept, close; guide_type=withdraw','客户端','点击进入提现或关闭','guide_exposure_id, action_id, destination','接受次数=被接受exposure；接受人数=用户去重；接受率=接受exposure/展示exposure'),
('提现后续归因','提现服务端','用户提交申请、审核结束及到账','guide_exposure_id, withdrawal_attempt_id（仅受控服务内部）, status, attribution_window','统计提现申请率和到账率；点击引导不代表提现成功')])]

COMMON='''## 统计口径

- **人数**：同一真人在统计期内只算1人；无法确认身份的用户单列。
- **次数**：每次请求或操作只算1次；重复上报不重复计算。
- **局数**：一桌牌算1局；每位玩家参加一局算1个人局。APP与H5同桌时，整桌只算1局。
- **用户分组**：统计日期当天注册为新用户，其他为老用户；再区分付费和非付费，首次玩Whot单独标记。
- **统计时间**：统一按拉各斯时间出报表。只统计已经结束等待的请求，结果未知的请求单列。
- **分析维度**：先看APP/H5、房间、请求人数、实际人数和付费状态，再按包名、版本、入口和小时下钻。
- **数据边界**：真人和机器人以服务端席位为准；虚拟在线人数不进入统计。游戏ID和规则版本确认后，才能比较新旧版本。

## 核心指标

| 指标 | 怎么算 | 解决什么问题 |
|---|---|---|
| **匹配后开局率** | 真正开局的匹配请求 ÷ 已结束等待的匹配请求 | **用户最终有没有玩上** |
| **四人模式兑现率** | 请求4人且实际开4人的请求 ÷ 已结束等待的4人请求 | **用户选择的模式有没有兑现** |
| **开局等待P95** | 95%的成功开局请求，其等待时间不超过该值 | **大多数用户最长要等多久** |
| **超时与取消** | 分别统计超时率、取消率和未知结果占比 | **用户为什么没有开局** |
| **完局与结算** | 同时看完局率、结算覆盖、RTP和重连失败率 | **开局改善后，对局和资金是否正常** |

5、10、15、30、45秒内开局率统一按已结束等待的请求计算。比较新旧版本时，固定房间、时段、付费状态和端；共享匹配池需分房间或分时测试。
'''

LINKS='''## 关联键与重复上报规则

| 键 | 生命周期 | 去重规则 |
|---|---|---|
| event_uid＋event_version | 一条事件事实 | 传输重试复用UID；保留来源client/server |
| user_key / participant_key | 用户、牌桌参与 | 仅在受控数据层关联；报告只输出聚合 |
| game_load_id | 一次进入加载 | 重载新ID，阶段切换沿用ID |
| root_match_id | 一次连续匹配旅程 | 自动降级/迁移沿用根ID；显式新发起定义需签字 |
| match_attempt_id | 一名用户的一次受理入队 | HTTP重试复用；手动重新排队新ID；旧attempt以migrated终结时关联后继，不归为失败 |
| queue_epoch＋offer_id | 一次稳定候选组及其建议 | N1/N2新offer；人员变化invalidate旧offer，禁止复用旧同意 |
| game_round_id＋participant_key | 整桌与玩家参与 | GAMESTART/GAMEEND分清table/player粒度，不能把双方上报相加 |
| exposure_id＋action_id | 引导/购买方式/结算展示和点击 | 曝光按可见实例，点击按动作ID；接受展示数与原始点击数分开 |
| purchase_attempt_id＋entitlement_id | 购买尝试与权益 | 回调重复不增购买成功；重试是否新尝试由业务服务确认 |
| last_card_window_id＋action_id | 宣告/抓罚机会 | 同窗多个请求只一个成功处罚，其余保留失败原因 |
| disconnect_episode_id＋reconnect_attempt_id | 一段断线及多次重试 | 同一断线可多次重连；段恢复率与尝试成功率分列 |

通用字段还包括event_time、received_at、server_seq、source、client_type、package_name、ruleset_version、room_id、payer_pool、currency/asset_type/amount_unit及schema_version。所有键是设计字段，须映射实际接口后创建；不可把本方案的逻辑名当作已存在Ares event_id。

## 匹配状态与降级计数必须这样闭环

**受理入队 → 队列变化 → N1/N2建议 → 用户响应 → 服务端组桌结果 → GAMESTART。** 取消、超时、拒绝、人员变化都要有可解释的出口。

- 一名真人在4人队列中：当前PRD允许准备快速2人候选并征求同意；不要写成“只差1人”。
- 两名真人：双方同意才开2人。三名真人：第4人加入优先4人，全同意可开3人，窗口到期仅两人同意可让同意者开2人；剩余用户状态由服务端明确记录。
- 响应层：accepted/rejected/timeout/invalidated/delivery_unknown分列。Keep Waiting映射为拒绝替代建议，但不等于取消整个匹配。
- 建桌成功不等于GAMESTART；取消请求被建桌先行拒绝不是取消成功。终态按服务端顺序裁决，退款与未扣款的要求按最终结果验收。
- 新增client offer shown确认：服务端issued不代表客户端已看到。多人建议同意率按offer×用户机会，桌级建议成功率按offer批次，禁止混用分母。
'''

QA='''## 上线验收与交付分工

| 验收组 | 必测场景 | 必须通过的检查 |
|---|---|---|
| 四组用户 | 新/老×付费/非付费；当天首次充值前后 | 入口分组保持进入时状态；首次付费后的变化另行记录 |
| 引导与加载 | 接受、关闭、完成、后台中断；冷/热缓存、弱网、超时 | 后台中断单列；每次加载都有开始和结束状态 |
| 模式和房间 | 默认选中/用户点击；快速匹配/手动进入；余额不足 | 默认选中单独记录；最终房间与用户请求正确关联 |
| 匹配与降级 | 1/2/3/4真人、N1/N2、人员变化、拒绝/超时、跨队列 | 建议状态按规则更新；实际人数正确；剩余用户去向明确 |
| 取消竞争 | 取消先于建桌、建桌先于取消、已回列表再拉入局 | 取消结果由服务端唯一确认；每次请求只有一个终态 |
| 托管和退出 | 超时/断线托管、恢复手动、退出被拒绝 | 玩家状态和整桌状态分别正确；退出只影响对应玩家 |
| Last Card | 普通/特殊牌→单牌，20选图案，漏宣告、多对手抓罚、无人抓罚 | 每个机会最多执行一次处罚；3秒和回合机会使用同一规则版本 |
| 记牌器 | 各实际购买方式、失败/取消/重试、已有权益、下一局生效 | 购买结果与权益生效分别记录；权益从下一局开始使用 |
| 同分和网络 | 多轮决胜、重连恢复抓罚/决胜/结算、异常退出 | 每个同分牌局记1局；断线段与重连次数分别统计 |
| 结算及引导 | 不同结束原因、重复展示、再玩/回房、充值/提现引导 | 结算覆盖到每位玩家；引导接受、支付和到账分别统计 |

**分工建议**：策划确认业务口径与枚举；客户端负责可见展示、意图和性能；游戏服务端负责匹配/玩法终态；支付和权益服务负责购买/账本；数据团队负责去重、四组切片及回读；测试负责端到端回放。

## 评审前需要定稿的6项

1. 新用户采用注册当日还是注册后N天；首次玩Whot单独定义；是否包含游客和引导模拟局。
2. 新人引导何时出现、是否可跳过、步骤和完成标准；与Rules主动查看区分。
3. 记牌器有哪些实际购买方式及SKU；当局购买下一局生效在换房/断线后如何判断。
4. 充值/提现引导的场景、主按钮去向、接受定义和归因窗；事件仅保留代码不采集支付或身份详情。
5. 6001/9006/play_id和新旧规则版本映射；匹配成功与GAMESTART具体服务节点；终态延迟宽限。
6. Last Card时序、4人机器人资格、N1/N2重置、正式派奖是否含本金。PRD结算公式与示例差异在签字前维持待核。

'''

def main():
    sections=[('summary','## 执行摘要\n\n**完整覆盖15项需求，沿用户旅程逐项验收。** 从四类用户、引导和加载到匹配、局内行为、结算及资金引导，逐项给出事件、触发、字段和指标分母。\n\n**先补展示和尝试，再统计接受和成功。** 建议签发不等于展示，取消点击不等于取消生效，记牌器购买成功不等于权益已生效；这些节点分别记录。\n\n**上线前重点打通匹配、结算和关键新规则。** 四人模式同时看原模式兑现率、降级开局率和失败/取消；宣告抓罚与同分决胜以服务端唯一结果为准。\n\n**状态：待评审的实施设计。**'),('definitions',COMMON)]
    for i,(name,takeaway,events) in enumerate(GROUPS,1):
        if i==1:
            sections.append(('phase_1','## 一期｜基础体验与匹配\n\n覆盖需求01—07：用户分群、新人引导、进入与加载、对局和房间选择，以及匹配与等待。'))
        elif i==8:
            sections.append(('phase_2','## 二期｜局内体验与资金引导\n\n覆盖需求08—15：局内操作、牌局规则、托管与重连、辅助功能、结算，以及充值和提现引导。'))
        body=f'## {i:02d}｜{name}\n\n**{takeaway}**\n\n| 事件 / 动作（逻辑名） | 来源与触发 | 关键字段 | 指标与算法 |\n|---|---|---|---|\n'
        for e,source,trigger,fields,metric in events:
            body+=f'| {e} | {source}：{trigger} | {fields} | {metric} |\n'
        sections.append((f'requirement_{i:02}',body))
    for prefix,body in [('links',LINKS),('qa',QA)]:
        for j,part in enumerate(body.split('\n## ')):
            sections.append((f'{prefix}_{j}',part if j==0 else '## '+part))
    # Split definition peer headings so each remains an independent reader segment.
    normalized=[]
    for key,body in sections:
        for j,part in enumerate(body.split('\n## ')):
            normalized.append((f'{key}_{j}',part if j==0 else '## '+part))
    markdown='# '+TITLE+'\n\n'+'\n\n'.join(b for _,b in normalized)
    (OUT/'report.md').write_text(markdown+'\n',encoding='utf-8')
    groups=[{'requirement_id':i,'name':n,'takeaway':t,'events':[{'logical_event':e,'source':s,'trigger':tr,'fields':f,'metric_definition':m} for e,s,tr,f,m in rows]} for i,(n,t,rows) in enumerate(GROUPS,1)]
    (OUT/'requirements_contract.json').write_text(json.dumps({'status':'review_ready','planner_revision':5738,'definition_version':'whot_tracking_v2_15','groups':groups},ensure_ascii=False,indent=2)+'\n')
    source=[{'id':'planner','label':'Whot新版策划方案','href':SOURCE,'description':'2026-09-07回读revision 5738；规则参考，实施状态待验收'}, {'id':'user_requirements','label':'用户确认的15项埋点需求','description':'本会话用户提供的15项需求，作为覆盖与验收主合同'}, {'id':'design','label':'新版Whot埋点与数据指标V2','path':'analysis/whot_tracking_review_2026_09_07/v2/report.md','description':'逐项事件、触发条件、字段、分母和验收设计，无生产结果'}]
    artifact={'surface':'report','manifest':{'version':1,'surface':'report','title':TITLE,'generatedAt':STAMP,'sources':source,'cards':[],'charts':[],'tables':[],'blocks':[{'id':'title','type':'markdown','body':'# '+TITLE}]+[{'id':k,'type':'markdown','body':b} for k,b in normalized]},'snapshot':{'version':1,'generatedAt':STAMP,'status':'ready','datasets':{}},'sources':source}
    scope_rows=[{'topic':g['name'],'requirement':'需求%02d'%g['requirement_id'],'phase':('一期' if g['requirement_id']<=7 else '二期'),'stage':('进入与选择' if g['requirement_id']<=5 else '匹配与降级' if g['requirement_id']<=7 else '局内玩法与恢复' if g['requirement_id']<=12 else '结算与资金引导'),'action_count':len(g['events'])} for g in groups]
    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE contract_scope (requirement TEXT, topic TEXT, phase TEXT, stage TEXT, action_count INTEGER)')
    db.executemany('INSERT INTO contract_scope VALUES (:requirement,:topic,:phase,:stage,:action_count)',scope_rows)
    scope_sql='SELECT stage, SUM(action_count) AS action_count FROM contract_scope GROUP BY stage ORDER BY MIN(requirement);'
    scope_chart=[{'stage':r[0],'action_count':r[1]} for r in db.execute(scope_sql)]
    db.close()
    (OUT/'contract_scope.json').write_text(json.dumps(scope_rows,ensure_ascii=False,indent=2)+'\n')
    scope_source={'id':'scope','label':'15项数据指标覆盖统计','path':'analysis/whot_tracking_review_2026_09_07/v2/contract_scope.json','query':{'engine':'sqlite','sql':scope_sql,'description':'按用户旅程阶段汇总15项数据指标需求。','tables_used':['contract_scope'],'executed_at':STAMP}}
    source.append(scope_source)
    artifact['snapshot']['datasets']={'contract_scope':scope_rows,'scope_chart':scope_chart}
    artifact['manifest']['charts']=[{'id':'scope_chart','title':'数据指标覆盖的用户旅程阶段','type':'bar','dataset':'scope_chart','sourceId':'scope','encodings':{'x':{'field':'stage','type':'ordinal','label':'旅程阶段'},'y':{'field':'action_count','type':'quantitative','label':'数据记录项数'}},'yAxisTitle':'数据记录项数'}]
    artifact['manifest']['tables']=[{'id':'scope_table','title':'15项数据指标与实施阶段','dataset':'contract_scope','sourceId':'scope','defaultSort':{'field':'requirement','direction':'asc'},'columns':[{'field':'requirement','label':'需求编号','type':'text'},{'field':'phase','label':'实施阶段','type':'text'},{'field':'topic','label':'场景','type':'text'},{'field':'stage','label':'旅程阶段','type':'text'},{'field':'action_count','label':'数据记录项数','type':'number','format':'number'}]}]
    artifact['manifest']['blocks'][2:2]=[{'id':'scope_intro','type':'markdown','body':'## 数据指标覆盖范围\n\n下图展示15项数据指标覆盖的用户旅程。需求01—07为一期，需求08—15为二期。'},{'id':'scope_visual','type':'chart','chartId':'scope_chart'},{'id':'scope_index','type':'table','tableId':'scope_table'}]
    (OUT/'artifact.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
    assert len(groups)==15 and [g['requirement_id'] for g in groups]==list(range(1,16))
    (OUT/'coverage_receipt.json').write_text(json.dumps({'status':'passed','generated_at':STAMP,'requirement_count':15,'requirement_ids':list(range(1,16)),'all_have_trigger_fields_metrics':all(len(g['events'])>0 and all(all(e.values()) for e in g['events']) for g in groups),'schema_state':'proposed_not_deployed','production_query':'not_run','planner_revision':5738,'visual_decision':'按15项顺序展示精确合同表；没有业务数据，不制作虚构漏斗图'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','groups':15,'event_action_rows':sum(len(g['events']) for g in groups),'artifact':str(OUT/'artifact.json')},ensure_ascii=False))
if __name__=='__main__':main()

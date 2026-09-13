# 新版Whot一期埋点计划｜进入、选择与匹配

## 总体方案

一期目标：沿进入到开局的用户路径，回答谁进入、引导是否接受、加载是否完成、选择哪种模式和房间、是否匹配成功及四人降级能否挽回开局。

> 分期依据：采用截图最后“先做前七项、局内放二期”的建议。新人引导纳入一期；截图较早提到的Last Card、结算、充值引导按最终分期放入二期。

| 原需求编号 | 场景 | 本期交付 |
|---|---|---|
| 需求01 | 用户群体 | 将新老用户与付费状态交叉拆分；用户群体作为所有事件的公共维度。 |
| 需求02 | 新人引导 | 区分看到引导、接受引导与完成引导；没有展示就没有接受率分母。 |
| 需求03 | 进入游戏与加载 | 加载成功、画面可操作和可下注分别确认，才能找到首局入口损失。 |
| 需求04 | 对局选择 | 选择2/4人与实际开2/3/4人分别统计；点击量不代表实际开局量。 |
| 需求05 | 房间选择 | 快速匹配和手动进房分别看，保留系统推荐房间与最终受理房间。 |
| 需求06 | 匹配情况 | 受理尝试、组桌成功和真正开局是三个阶段，取消由服务端裁决。 |
| 需求07 | 4人局降级建议 | 建议送达、展示和最终响应分开；N1/N2必须有独立的建议与同意状态。 |


### 实施路径与期际依赖

用户分组 → 新人引导 → 进入与加载 → 选择2/4人 → 选房/快速匹配 → 受理与排队 → 降级建议与响应 → 服务端匹配结果 → 最小GAMESTART回执。

> 一期最小依赖：GAMESTART的attempt、round、participant、requested_mode、actual_count、人机组成与版本必须一起落地，才能统计局数和开局率；这是需求04/06/07的基础，二期再扩展GAMEEND、结算展示与资金分析。如果新版本没有此回执，一期只能验收匹配结果，开局率标记暂不可用。

### 范围边界与交付物

交付：本期字段与事件合同、服务端/客户端映射表、聚合指标表、端到端验收用例和入库回读结果。本文为实施评审方案，实际平台event_id由埋点管理员创建后回填；当前未执行生产发布。

一期保留匹配阶段断线、风控拒绝和建桌失败原因；完整局内网络诊断、记牌器、Last Card、同分、结算、充值/提现引导在二期。

## 核心数据指标及算法

### 统计规则

所有指标以真人为主，机器人和身份未知单列。用户分组为新/老×付费/非付费；一期定义的分组、端、包和规则版本在二期沿用。

新用户建议为注册当日，老用户为此前注册；首次玩Whot另设维度。最终天数规则需策划签字，二期不得另起一套定义。

人数按窗口去重用户；次数按曝光ID、动作ID或业务尝试ID去重。传输重试复用事件UID。局数按整桌ID，人局数按牌局ID＋参与者；四人一桌是1局、4个人局。

UTC存储、Africa/Lagos展示；匹配按受理时间归属。业务等待时间和入库缓冲均结束后才进入统计；未知结果保留在分母并单列占比。缓冲建议5分钟，其他加载/购买/归因窗口分别配置并签字。

APP和H5使用同一服务端玩法事实。端/包/网页/APP/规则版本独立记录；共享桌按端统计可能重叠，不能直接把两端桌数相加。

分母为0显示N/A；曝光、接受、购买、充值、提现各阶段分别记录。小于10人的报表分组隐藏或合并，明细关联仅留受控数据层。

### 优先查看的核心指标

| 指标 | 分子／统计值 | 分母／条件 | 用途 |
|---|---|---|---|
| 匹配后开局率 | 已关联GAMESTART的受理真人attempt数 | 统计观察期已结束的受理真人attempt数 | 能否真正开始玩 |
| 四人原模式兑现率 | 请求4人并实际开4人attempt数 | 统计观察期已结束的4人请求数 | 用户所选模式兑现 |
| 开局等待P95 | 成功者的started_at－accepted_at的95分位 | 成功样本，并同时看失败/取消/未知比例 | 响应体验 |
| 加载成功率 | 达到真实ready的load数 | 统计观察期已结束的load start数 | 入口损失 |
| 新人引导接受率 | 被接受的引导展示数 | 已展示引导实例数 | 引导吸引力 |


### 按需求逐项计算

#### 需求01｜用户群体

| 统计对象／动作 | 指标及算法 |
|---|---|
| 用户画像快照 | 人数=时间窗内去重真人；新老和付费两轴分别汇总，再交叉成四组 |
| 新老口径 | 四组：新付费、新非付费、老付费、老非付费；未知单列。新用户天数规则待签字 |


#### 需求02｜新人引导

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_TUTORIAL / show | 展示次数=去重exposure_id；展示人数=去重用户 |
| WHOT_TUTORIAL / accept, close | 接受率=被接受展示数/展示数；关闭率=被关闭展示数/展示数 |
| WHOT_TUTORIAL / step_complete, complete | 完成率=完成run数/接受run数；按步骤看流失。引导是否真人匹配/模拟局需明确 |


#### 需求03｜进入游戏与加载

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_LOAD / start | 加载次数=去重load_id；加载人数=去重用户 |
| WHOT_LOAD / ready, fail, timeout, abandon | 成功率=ready load数/统计观察期已结束的start load数；P50/P95耗时；放弃和未知终态单列 |
| WHOT_LOAD / bet_ready | 可下注到达率=bet_ready load数/start load数；H5复用既有H5_GAME_*并映射，不能双计 |


#### 需求04｜对局选择

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_MODE_SELECT / click | 点击次数=去重action_id；点击人数=去重用户；同时报告有效模式切换次数 |
| GAMESTART / player participation | 局数=去重game_round_id；人数=去重真人；人局数=去重round+participant；按选择模式追踪2→2、4→4/3/2 |


#### 需求05｜房间选择

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_ROOM / list_show | 列表触达人数与次数；只上报可见房间ID，不上传完整配置 |
| WHOT_ROOM / quick_click, enter_click | 各方式点击人数/次数；房间点击率=点击该房间的列表展示数/该房间可见列表展示数 |
| WHOT_ROOM_RESULT / accepted, rejected | 受理率=被受理进房请求数/收到进房请求数；客户端点击到受理另看关联率 |


#### 需求06｜匹配情况

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_MATCH_REQUEST / accepted | 请求次数=去重attempt；匹配人数=去重真人 |
| WHOT_MATCH_END / matched, failed, cancelled | 匹配成功率=matched attempts/统计观察期已结束的受理attempts；失败率/取消率同分母；未知终态不删除 |
| WHOT_MATCH_CANCEL / request, result | 取消成功率=确认取消attempts/有取消请求attempts；建桌竞争单列 |
| GAMESTART / linked start | 开局率=关联GAMESTART attempts/受理attempts；匹配后未开局率；开局耗时与取消耗时分开看 |


#### 需求07｜4人局降级建议

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_MATCH_OFFER / issued, shown | 建议批次数=去重offer_id；建议触达次数=去重offer_id+用户。多人共用offer不能乘成多批 |
| WHOT_MATCH_RESPONSE / accept, reject, timeout | 接受/拒绝/超时次数=去重offer+用户的有效终态；接受率=接受机会数/已展示且统计观察期已结束的有效机会数 |
| WHOT_MATCH_OFFER / invalidated | 失效次数单列，不记为拒绝或超时；N1接受不能继承到N2 |
| GAMESTART / downgrade | 4人兑现率=4→4开局attempts/4人受理attempts；降级开局率=4→2/3开局attempts/4人受理attempts |


### 数据质量监控

结果成功、失败、取消、超时、失效和未知按业务层级分别统计。比例展示分子和分母；任何字段缺失、样本不足和观察时间不足都不填0。跨端、跨用户分组UV可能重复，汇总重新去重。

匹配终态率与开局率分开：matched是桌位分配完成，GAMESTART是牌局真正开始。共同5/10/15秒开局率使用全部观察期结束的受理请求；不把45秒等待上限缩放成15秒。

## 具体埋点实现

### 公共字段及复用规范

| 字段 | 类型 | 填写条件 | 定义与校验 |
|---|---|---|---|
| event_uid / event_version | string / string | 每条事件必填 | 同一业务事件重传复用UID；新schema升级版本 |
| event_name / action / source | string / enum / enum | 每条事件必填 | 逻辑名映射平台实际event_id；client/server/ledger区分 |
| event_time / received_at / server_seq | timestamp / timestamp / int64 | 时间必填；seq服务状态必填 | 存UTC；服务端顺序用于乱序修正，客户端耗时用本地单调时钟 |
| user_key / participant_key | string | 用户事件必填；参与者在局内必填 | 使用既有受控身份关联键，不上传直接身份信息 |
| client_type / package_name / app_version / web_version | enum / string | 按端条件必填 | APP/H5、Android/iOS和版本分别可查；非适用版本可空 |
| game_family / client_game_id / server_game_id / play_id / ruleset_version | string | 映射与版本必填 | 6001/9006和玩法ID关系由研发确认；规则版本不可仅靠game_id推断 |
| platform_tenure / whot_experience / payer_state_at_event | enum | 每个用户事件必填或unknown | 新/老、首次/非首次Whot、付费/非付费分别记录 |
| analysis_segment_at_entry / cohort_rule_version | enum / string | 旅程开始时冻结 | 漏斗分组沿用入口状态；实际付费状态可随事件变化 |
| root_match_id / match_attempt_id | string | 匹配请求和后续结果必填 | 自动重试同attempt；重新受理新attempt，迁移保留前后关联 |
| requested_mode / actual_count | int enum | 请求时前者必填；组桌后后者必填 | 请求只允许2/4；实际人数允许2/3/4；未组桌不能填0伪造结果 |
| room_id / payer_pool / pool_id | string / enum / string | 服务端受理后必填 | 手动请求房间与服务端resolved_room_id分别保存 |
| queue_epoch / offer_id / offer_stage | int64 / string / enum | 降级建议和响应必填 | N1/N2独立；人员变化使旧offer失效；stage限N1/N2等签字值 |
| game_round_id / human_count / robot_count | string / int64 / int64 | GAMESTART及局事实必填 | 同桌只生成一局；sum人机席位数等于actual_count |
| exposure_id / action_id | string | 展示/点击条件必填 | 一可见实例一exposure；每次真实点击一action，接受展示数另去重 |
| result / reason / config_version | enum / enum / string | 有业务结果时必填 | 结果与失败原因分列；未定义枚举留unknown并告警 |


所有以下事件名为逻辑合同：event_name与action拆列，映射既有MC/MV/PV或专用事件时只能选择一条权威统计链。前端意图与服务端结果可各报一次，但必须标记source、关联同一action_id，聚合时不得合并相加。

### 逐项事件与触发实现

#### 需求01｜用户群体

将新老用户与付费状态交叉拆分；用户群体作为所有事件的公共维度。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| 用户画像快照 | 服务端 | 事件发生时附加注册日、首次Whot开始时间及截至此刻的历史充值状态 | registration_date, first_whot_started_at, payer_state_at_event, cohort_rule_version |
| 新老口径 | 数据层 | 建议平台注册当日为平台新用户，注册日前于业务日为老用户；另记首次玩Whot，避免混淆 | platform_tenure, whot_experience, analysis_segment_at_entry |


#### 需求02｜新人引导

区分看到引导、接受引导与完成引导；没有展示就没有接受率分母。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_TUTORIAL / show | 客户端 | 引导真正可见时，一次展示只报一次 | tutorial_id, tutorial_version, exposure_id, step_id |
| WHOT_TUTORIAL / accept, close | 客户端 | 点击开始引导或显式关闭 | exposure_id, action_id, action, close_reason |
| WHOT_TUTORIAL / step_complete, complete | 客户端；规则完成由服务端校验 | 完成步骤和全部引导；切后台不当作主动关闭 | tutorial_run_id, step_id, completion_source |


#### 需求03｜进入游戏与加载

加载成功、画面可操作和可下注分别确认，才能找到首局入口损失。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_LOAD / start | 客户端主框架 | 进入Whot并开始加载，失败前也必须有开始事件 | game_load_id, entry_source, cache_state, platform |
| WHOT_LOAD / ready, fail, timeout, abandon | 客户端/游戏桥 | 游戏真实ready或错误、超时、离开终态 | game_load_id, stage, duration_ms, error_code, downloaded_bytes |
| WHOT_LOAD / bet_ready | 游戏桥+服务端条件 | 余额、房间权限、连接、操作控件均可用 | game_load_id, ready_source, readiness_reason |


#### 需求04｜对局选择

选择2/4人与实际开2/3/4人分别统计；点击量不代表实际开局量。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_MODE_SELECT / click | 客户端 | 用户点击人数选择控件；默认预选不算点击 | action_id, selection_id, requested_mode, selection_origin |
| GAMESTART / player participation | 服务端 | 牌局真正开始，为每位参与者生成参与记录 | game_round_id, participant_key, requested_mode, actual_count, match_attempt_id |


#### 需求05｜房间选择

快速匹配和手动进房分别看，保留系统推荐房间与最终受理房间。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_ROOM / list_show | 客户端 | 可见房间列表及推荐卡片展示 | room_list_view_id, config_version, recommended_room_id, visible_room_ids |
| WHOT_ROOM / quick_click, enter_click | 客户端 | 点击Quick Match或某房间Enter | action_id, room_list_view_id, requested_mode, requested_room_id, entry_method |
| WHOT_ROOM_RESULT / accepted, rejected | 服务端 | 校验资产和房间权限，并选定真实房间 | action_id, match_attempt_id, resolved_room_id, rejection_reason, payer_pool |


#### 需求06｜匹配情况

受理尝试、组桌成功和真正开局是三个阶段，取消由服务端裁决。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_MATCH_REQUEST / accepted | 服务端 | 一次匹配请求受理入队 | root_match_id, match_attempt_id, requested_mode, payer_pool, pool_id, deadline_at |
| WHOT_MATCH_END / matched, failed, cancelled | 服务端 | 每个attempt唯一终态，成功定义为有效桌位已分配 | match_attempt_id, table_id, actual_count, reason, accepted_at, ended_at |
| WHOT_MATCH_CANCEL / request, result | 客户端请求+服务端结果 | 取消点击与取消是否生效分报，建桌先完成则拒绝取消 | action_id, match_attempt_id, cancel_result, reason |
| GAMESTART / linked start | 服务端 | 已匹配用户真正进入开始状态 | match_attempt_id, game_round_id, actual_count |


#### 需求07｜4人局降级建议

建议送达、展示和最终响应分开；N1/N2必须有独立的建议与同意状态。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_MATCH_OFFER / issued, shown | 服务端签发+客户端可见 | 每个queue_epoch中生成建议；客户端实际可见时回执 | offer_id, queue_epoch, stage, target_count, other_human_count, expires_at |
| WHOT_MATCH_RESPONSE / accept, reject, timeout | 服务端 | 校验用户响应；超时由服务端到期结算，未展示另标记 | offer_id, participant_key, response, response_at, validation_result |
| WHOT_MATCH_OFFER / invalidated | 服务端 | 人员加入离开、取消、断线使建议失效；清空旧同意 | offer_id, queue_epoch, invalidated_reason |
| GAMESTART / downgrade | 服务端 | 明确同意的用户实际开2/3人局 | requested_mode, actual_count, offer_id, consent_version, robot_count |


### 关键状态及跨事件连接

引导：show→accept/close；accept可继续step_complete/complete。离开或切后台单列，未完成不能推断主动关闭。引导资格、步骤和完成条件待策划定稿。

加载：start→ready/fail/timeout/abandon；bet_ready为另一个能力到达点，不当作第二次load成功。重载新load_id，阶段内重试保留关联。

降级：issued→shown→accept/reject/timeout；人员变化走invalidated，不能计作拒绝/超时。N1/N2重新生成offer_id与同意集合；Keep Waiting是拒绝替代开局，不是取消匹配。

匹配：accepted→matched/failed/cancelled；队列迁移记录migrated＋next_attempt_id，不能归为业务失败。matched继续关联GAMESTART。取消先于建桌则取消，建桌先行则取消未生效；每attempt最终唯一裁决。

一期数据流：用户和客户端上下文→点击/加载→服务端受理及建议→响应与结果→GAMESTART参与事实→小时/日聚合。建议批次按offer_id，用户响应按offer_id＋用户，局数按round。

### 本期验收与上线顺序

| 负责人 | 交付 | 通过条件 |
|---|---|---|
| 策划 | 人群/模式/房间/时序/结果枚举签字 | 新用户规则、引导资格、N1/N2与游戏ID映射明确 |
| 客户端 | 可见展示、意图及体验事件 | 重复点击/重试不误计；APP/H5可定位 |
| 服务端／业务服务 | 唯一结果与幂等关联 | 服务端终态、开局或权益/资金结果可回查 |
| 数据开发 | 分层聚合与指标计算 | 分子分母、UTC/Lagos、观察期截止和未知状态一致 |
| 测试 | 端到端回放与双端验收 | 必测场景100%通过；错误定位到事件和字段 |


必测：新老付费四组、引导接受/关闭/完成、冷/热缓存和弱网、默认模式与真实点击、多房间及余额不足、N1/N2全部响应组合与人员变化、取消/建桌竞争、跨队列迁移、最小GAMESTART关联。

> 发布质量目标（建议，待签字）：关键关联覆盖≥99.5%，必填缺失<0.1%，同一业务事实重复计数为0；应有结果而未知的请求单列。二期资金未解释差额必须为0。先完成测试回放，再灰度观察，最后按同口径发布报表。

### 待确认事项与来源

本期需定稿：平台新用户天数与首次Whot定义、新人引导步骤和资格、6001/9006/play_id、匹配成功/开局服务节点、N1/N2及超时配置、入库缓冲。

来源：用户15项需求清单与本轮分期截图最终建议；策划方案最近已核验版本revision 5738；原V2完整合同。当前文档为设计计划，不表示事件已经实现。

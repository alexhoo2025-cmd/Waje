# 新版Whot二期埋点计划｜局内体验、结算与资金引导

## 总体方案

二期目标：在一期身份、匹配和开局链路上，补齐局内体验、新规则、恢复、购买权益、结算展示和资金引导，定位开局后的流失与转化。

> 分期依据：采用截图最后“先做前七项、局内放二期”的建议。新人引导纳入一期；截图较早提到的Last Card、结算、充值引导按最终分期放入二期。

| 原需求编号 | 场景 | 本期交付 |
|---|---|---|
| 需求08 | 对局过程 | 玩家退出、超时托管和断线托管分别记录；恢复手动以服务端状态为准。 |
| 需求09 | Last Card | 宣告成功、漏宣告与抓罚失败要用同一机会窗口关联，避免并发和重连重复计数。 |
| 需求10 | 记牌器 | 完整记录入口→方式展示→选择→购买结果→权益生效→打开使用。 |
| 需求11 | 同分抽牌 | 计数单位是发生同分的牌局，重复抽牌轮次作为另一个指标。 |
| 需求12 | 网络异常 | 断线、重连尝试和异常退出各有唯一标识，可追踪重试与恢复失败。 |
| 需求13 | 对局结算 | 游戏结束、服务端结算完成与客户端看见结算是不同事实。 |
| 需求14 | 充值引导 | 统计引导触达、接受与后续支付；接受仅代表点击主按钮。 |
| 需求15 | 提现引导 | 与充值引导复用结构，但申请、审核和到账必须分开。 |


### 实施路径与期际依赖

沿用一期GAMESTART及身份 → 托管/手动/退出 → Last Card与同分决胜 → 断线重连 → 记牌器购买和使用 → GAMEEND及资金结算 → 结算展示/再玩 → 充值和提现引导。图示顺序是分析路径，局内动作不必按此顺序全部发生。

> 二期启动条件：一期共用身份、game_load_id、match_attempt_id、game_round_id、规则版本及端包映射已验收。沿用既有GAMESTART事件与命名，不新建重复开局来源。二期的局内托管/重连不同于一期匹配时的断线终态；两者按阶段区分。

### 范围边界与交付物

交付：本期字段与事件合同、服务端/客户端映射表、聚合指标表、端到端验收用例和入库回读结果。本文为实施评审方案，实际平台event_id由埋点管理员创建后回填；当前未执行生产发布。

二期覆盖原需求08—15，并新增需求16“机器人胜负偏离与整局回放”；01—07的分组、请求分母、房间和匹配来源作为依赖复用，不算二期重复实施范围。

### 新增需求16｜机器人胜负偏离与整局回放

目标：识别“必赢机器人最终输局”和“必输机器人最终赢局”，从开局发牌到最终裁决逐步回放真人与机器人的全部操作，定位规则执行、策略执行、状态同步或结果统计问题。作为二期新增第9项需求，原需求08—15继续保留。

“必赢／必输”沿用策划的策略名称，代表配置的目标，不代表已经实现100%／0%胜率。按服务端实际下发并确认生效的目标判断；配置名、客户端表现、下注净输赢均不能单独决定目标或牌局胜负。本需求交付诊断数据与审计能力，策略变更须另行评审。

| 分析问题 | 可交付结果 | 证据要求 |
| --- | --- | --- |
| 哪些局偏离目标 | 必赢输局、必输赢局两类名单与发生率 | 机器人席位、开局目标与版本、最终游戏裁决；全量摘要作分母 |
| 为什么发生 | 按首个状态差异、策略执行异常和最终结束原因分类 | 初始状态＋按序动作＋服务端状态变化＋最终结果 |
| 能否重现 | 一局一条回放时间线，标出关键回合与校验状态 | 真人与机器人完整轨迹，缺帧、版本缺失等明确提示 |

采集路径：开局固化席位与策略 → 全程记录状态变化及动作 → 服务端裁决识别偏离 → 固化整局轨迹 → 回放校验 → 按版本和结束原因复盘。必须从开局采集；结束时才开始记录无法补回先前的摸牌和出牌。

范围：所有经服务端确认含机器人的新版Whot牌局。机器人席位是本模块统计主体；真人手动、真人托管、机器人控制分别记录。请求人数2/4与实际人数2/3/4独立保存；多人局或多机器人组合是否允许该策略，由版本化适用范围确认。超出适用范围仍保留记录，并标记scope_conflict。

依赖复用：需求08托管/退出、09 Last Card、11同分抽牌、12网络恢复、13结束与结算，通过game_round_id、seat_id、cause_event_uid关联到同一轨迹；沿用一期端、包、模式、房间、付费池、规则版本。普通运营报表继续真人为主，本模块的机器人指标另列，避免混用分母。

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
| 对局完成率 | 正常结束的真人人局数 | 统计观察期已结束的已开始真人人局数 | 局内体验；异常退出单列 |
| 最终结算覆盖率 | 有唯一服务端最终结算的真人人局数 | 应结算且观察期已结束的真人人局数 | 结算可靠性 |
| 结算展示覆盖率 | 看到结算的真人人局数 | 已完成结算真人人局数 | 用户收到结果 |
| 引导接受率 | 被接受的引导展示实例数 | 对应deposit或withdraw展示实例数 | 触达转化；两种引导分开 |
| 同币种RTP | 最终有效派奖之和 | 最终有效下注之和；剔除取消、重复、未结算，退款按确认规则处理 | 金额加权，不平均个人RTP |


### 按需求逐项计算

#### 需求08｜对局过程

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_PLAY_STATE / auto_enter | 托管次数=进入转换数；托管人数=用户去重；托管人局率=托管人局/已开局真人参与人局 |
| WHOT_PLAY_STATE / manual_resume | 恢复次数/人数；恢复率=已恢复托管段/已结束托管段；仍进行中的段单列 |
| WHOT_PLAY_STATE / exit_request, exit_result | 退出请求和确认退出分开；退出人局率=确认退出人局/已开局真人人局；退出不必然等于牌局结束 |


#### 需求09｜Last Card

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_LAST_CARD / opportunity, declared, missed | 宣告成功率=成功宣告窗口/统计观察期已结束的可宣告窗口；漏宣告次数=missed窗口；无人抓罚不自动罚牌 |
| WHOT_LAST_CARD / catch_request, catch_success, catch_fail | 抓罚成功/失败次数=请求ID终态去重；成功率=成功请求/已终结抓罚请求；并发败选也属于失败原因 |
| WHOT_LAST_CARD / penalty, expired | 罚抽执行率=有效penalty/抓罚成功窗口；一个窗口最多一次罚抽2张；失效后重新宣告用新机会标识 |


#### 需求10｜记牌器

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_TRACKER / entry_click, methods_show | 入口点击人数/次数；方式展示人数/次数；已有权益用户直接使用单列 |
| WHOT_TRACKER / method_select, purchase_submit | 各方式选择次数/人数；提交率=已提交funnel/已选择funnel。购买方式枚举待策划，不假定广告或现金 |
| WHOT_TRACKER_PURCHASE / success, failed, cancelled, pending | 成功率=成功attempts/统计观察期已结束的已提交attempts；失败/取消/待定分别报告；不能用客户端成功页替代 |
| WHOT_TRACKER / effective, open_used | 购买后使用率=归因窗内使用的成功购买权益数/统计观察期已结束的成功购买权益数；当局购买下一局生效必须验收 |


#### 需求11｜同分抽牌

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_TIE_BREAK / started, draw_round, resolved | 同分局数=去重game_round_id；同分率=同分局/已终局牌局；条件同分率=同分局/牌堆耗尽局；决胜轮次不当局数 |


#### 需求12｜网络异常

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_NETWORK / disconnected, reconnect_start | 断线次数=去重episode；重连次数=去重attempt；断线人数=用户去重 |
| WHOT_NETWORK / reconnect_success, reconnect_failed | 重连成功率=成功attempts/统计观察期已结束的start attempts；段级恢复率=最终恢复episode/统计观察期已结束的断线episode |
| WHOT_NETWORK / abnormal_exit | 确认异常退出与推断分开；没有客户端退出事件不能自动认定主动退出 |


#### 需求13｜对局结算

| 统计对象／动作 | 指标及算法 |
|---|---|
| GAMEEND / ended | 对局结束局数=整桌round去重；玩家人局=round+用户；按正常出完/比点/决胜/异常分类 |
| BETREWARD + ASSET / final | 下注/派奖按同币种有效终态加总；RTP=payout/final_stake；平台收益按账本口径，净输赢不能冒充派奖 |
| WHOT_SETTLEMENT / show | 展示次数=去重view_id；展示覆盖率=已展示结算人局/已完成结算真人人局；重连新视图只增加PV |
| WHOT_SETTLEMENT / play_again, back_rooms | 点击次数/人数；再玩意向率=有再玩点击的结算人局/展示结算人局；实际复玩需关联后续GAMESTART |


#### 需求14｜充值引导

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_GUIDE / show; guide_type=deposit | 引导次数=去重exposure；人数=用户去重；场景区分破产/余额不足/结算等实际配置值 |
| WHOT_GUIDE / accept, close; guide_type=deposit | 接受次数=被接受exposure数；接受人数=用户去重；接受率=接受exposure/展示exposure |
| 充值后续归因 | 另报引导后充值人数/金额；建议同会话或30分钟归因，窗长待签字；支付成功不合并到引导接受 |


#### 需求15｜提现引导

| 统计对象／动作 | 指标及算法 |
|---|---|
| WHOT_GUIDE / show; guide_type=withdraw | 引导次数=去重exposure；人数=用户去重 |
| WHOT_GUIDE / accept, close; guide_type=withdraw | 接受次数=被接受exposure；接受人数=用户去重；接受率=接受exposure/展示exposure |
| 提现后续归因 | 另报申请率/到账率；不因点击引导就记录提现成功；不在事件中上传银行卡/KYC详情 |


### 数据质量监控

结果成功、失败、取消、超时、失效和未知按业务层级分别统计。比例展示分子和分母；任何字段缺失、样本不足和观察时间不足都不填0。跨端、跨用户分组UV可能重复，汇总重新去重。

充值引导接受仅代表点击，记牌器成功仅代表服务端购买完成，提现还需分别看申请/审核/到账。资金指标依赖最终账本，不以score或净输赢字段替代派奖。

### 需求16｜统计对象、核心指标及算法

统计对象分为整桌牌局与机器人席位局。整桌键为game_round_id；机器人席位局键为game_round_id＋seat_id，同一机器人账号跨局不合并。按开局时间归属Lagos业务日／小时，保存截至时间；牌局终结与日志入库缓冲结束后计算。未终结、作废、结果未知单列。

可判定集合E：已终结有效牌局，机器人身份明确，服务端策略在开局前或首个策略动作前生效，目标为win/lose且全局未切换，规则及策略适用范围明确，存在唯一最终胜者。回放缺失不从E中删除；它影响诊断能力，不应使发生率变低。

| 核心指标 | 算法与分母 | 解释与来源 |
| --- | --- | --- |
| 必赢机器人输局率 | E中目标win且该席位result=lose的席位局数 ÷ E中目标win的席位局数 | 来自策略生效记录＋最终裁决；同时展示分子分母 |
| 必输机器人赢局率 | E中目标lose且该席位result=win的席位局数 ÷ E中目标lose的席位局数 | 胜负按游戏裁决；不以派奖金额正负判断 |
| 偏离局完整回放通过率 | 两类偏离涉及的去重牌局中，完整性与状态重放均通过的局数 ÷ 全部两类偏离的去重牌局数 | 分母含归档失败、缺帧和缺版本的局；不能只用已打开回放的局 |

| 辅助指标 | 算法／展示方式 |
| --- | --- |
| 偏离牌局数与偏离席位局数 | 前者按round去重，后者按round＋seat去重；一桌多机器人可能同时触发两类，两类牌局数不能相加当总局数 |
| 目标可判定覆盖率 | E席位局数 ÷ 已终结有效的已知机器人席位局数；目标未知、未生效、切换、scope_conflict及结果缺失分别计数 |
| 异常与未完成覆盖 | 按已开始机器人牌局统计未终结／作废／结果未知占比，并展示时间窗；不得静默剔除后声称策略稳定 |
| 归档完整率与重放一致率 | 完整归档局／全部偏离局；重放一致局／实际执行重放局，并列未运行数。核心指标仍使用全部偏离局作分母 |
| 原因分布 | 按偏离牌局的首个已证实差异原因归类；未定位单列，其他并存线索用辅助标签，避免重复累计 |
| 规则与执行差异 | 服务端拒绝／失败动作、策略计划未执行、非法状态变化、终局与展示不一致分别统计；单次偏离不能自动归因于算法 |

分类规则：actual_result=win当且仅当该席位为服务端唯一最终胜者；有另一位唯一胜者时为lose。同分决胜尚未完成为pending，取消退款为void，多个胜者或裁决缺失为unknown。中途换策略保留segment轨迹，但整局单列policy_changed，不用最后一次目标回写开局目标。若策略目标实际指“指定真人输赢”而非机器人自己，需记录target_subject与目标席位并另算，不能套用本表。

必选维度：robot_policy_version、config_version、ruleset_version、服务端版本、目标、实际人数、人机组成、房间、付费池、结束原因、Lagos小时。APP/H5按同桌真人端组合展示；按参与端展开会重复桌数，汇总重新去重。真人新老／付费分组沿用一期。概率配置按该局生效快照分析，不把策略文档默认概率硬编码为生产事实。

三条终局路径分别分析：手牌出完；牌堆耗尽且最低积分唯一；最低同分后抽牌决胜。没有唯一结果、规则映射不明或分母为0时显示N/A。需要展示真人群体的聚合结果时，少于10人的分组隐藏或合并；受控回放用席位代号，不公开账户或设备标识。

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
| game_round_id / human_count / robot_count | string / int64 / int64 | GAMESTART及局事实必填 | 同桌只生成一局；sum人机席位数等于actual_count |
| exposure_id / action_id | string | 展示/点击条件必填 | 一可见实例一exposure；每次真实点击一action，接受展示数另去重 |
| result / reason / config_version | enum / enum / string | 有业务结果时必填 | 结果与失败原因分列；未定义枚举留unknown并告警 |
| state_transition_id / auto_episode_id | string | 托管/恢复 | 一段托管可含多个动作；恢复手动按服务端成功转换 |
| last_card_window_id / penalty_id | string | 宣告/抓罚/处罚 | 同一窗口允许多个抓罚请求，只有一个处罚ID有效 |
| tracker_funnel_id / purchase_attempt_id / entitlement_id | string | 购买与权益 | 购买方式展示→提交→结果→权益关联，不按回调条数计成功 |
| method_code / sku_id / effective_round_id | enum / string | 记牌器按条件必填 | 购买方式来自后台真实枚举；当局购买下一局生效需校验 |
| tie_break_id / draw_round_no | string / int64 | 同分抽牌 | 重复抽牌递增轮号；同分局数只按game_round_id计一次 |
| disconnect_episode_id / reconnect_attempt_id / snapshot_version | string | 断线/重连 | 一段断线可有多次重试；恢复完整快照才算恢复成功 |
| settlement_id / currency / asset_type / amount_unit | string / enum | 资金结算必填 | 有效下注、派奖、退款、费用分别存；跨币种不直接合并 |
| guide_exposure_id / guide_type / guide_id / guide_version | string / enum | 资金引导 | deposit/withdraw分开；一期的exposure_id规则沿用 |
| attribution_window / destination | 配置值 / enum | 引导归因 | 窗口和多触点规则需签字；一个业务成功只归给一个符合规则的引导 |


所有以下事件名为逻辑合同：event_name与action拆列，映射既有MC/MV/PV或专用事件时只能选择一条权威统计链。前端意图与服务端结果可各报一次，但必须标记source、关联同一action_id，聚合时不得合并相加。

### 逐项事件与触发实现

#### 需求08｜对局过程

玩家退出、超时托管和断线托管分别记录；恢复手动以服务端状态为准。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_PLAY_STATE / auto_enter | 服务端 | 从手动进入托管，一次状态改变报一次 | game_round_id, participant_key, state_transition_id, reason |
| WHOT_PLAY_STATE / manual_resume | 服务端 | 用户恢复操作请求被接受并恢复手动 | state_transition_id, auto_episode_id, reason |
| WHOT_PLAY_STATE / exit_request, exit_result | 客户端+服务端 | 主动退出点击及服务端执行结果 | action_id, game_round_id, exit_reason, continued_by_auto |


#### 需求09｜Last Card

宣告成功、漏宣告与抓罚失败要用同一机会窗口关联，避免并发和重连重复计数。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_LAST_CARD / opportunity, declared, missed | 服务端 | 产生单牌机会、有效宣告、正式进入漏宣告状态 | last_card_window_id, actor_key, ruleset_version, state_seq |
| WHOT_LAST_CARD / catch_request, catch_success, catch_fail | 服务端 | 校验抓罚请求的胜出或失败结果 | action_id, last_card_window_id, catcher_key, fail_reason |
| WHOT_LAST_CARD / penalty, expired | 服务端 | 唯一罚抽执行或所有对手机会用完 | penalty_id, last_card_window_id, added_cards, expiry_reason |


#### 需求10｜记牌器

完整记录入口→方式展示→选择→购买结果→权益生效→打开使用。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_TRACKER / entry_click, methods_show | 客户端 | 入口点击；购买方式实际可见 | action_id, tracker_funnel_id, exposure_id, placement, offered_method_codes |
| WHOT_TRACKER / method_select, purchase_submit | 客户端 | 选择后端返回的购买方式；提交购买 | tracker_funnel_id, purchase_attempt_id, method_code, sku_id, price, asset_type |
| WHOT_TRACKER_PURCHASE / success, failed, cancelled, pending | 服务端/支付或权益服务 | 购买尝试达到对应业务状态；回调幂等 | purchase_attempt_id, method_code, entitlement_id, result, error_code |
| WHOT_TRACKER / effective, open_used | 服务端生效+客户端真实展开 | 权益真正生效；有效面板实际展开 | entitlement_id, purchase_round_id, effective_round_id, tracker_view_id |


#### 需求11｜同分抽牌

计数单位是发生同分的牌局，重复抽牌轮次作为另一个指标。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_TIE_BREAK / started, draw_round, resolved | 服务端 | 最低点多人相同进入决胜；每轮抽牌及最终结果 | game_round_id, tie_break_id, draw_round_no, participant_count, result |


#### 需求12｜网络异常

断线、重连尝试和异常退出各有唯一标识，可追踪重试与恢复失败。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_NETWORK / disconnected, reconnect_start | 客户端；服务端可有独立观测 | 连接失效；每次重连开始 | disconnect_episode_id, reconnect_attempt_id, game_round_id, network_type |
| WHOT_NETWORK / reconnect_success, reconnect_failed | 客户端+服务端确认恢复 | 连接恢复且牌局快照应用成功；或重连失败 | reconnect_attempt_id, snapshot_version, duration_ms, restored_state, error_code |
| WHOT_NETWORK / abnormal_exit | 客户端尽力+服务端会话超时推断 | 崩溃、连接持续失效或进程退出导致离开 | episode_id, exit_reason, observation_source, inference_rule_version |


#### 需求13｜对局结算

游戏结束、服务端结算完成与客户端看见结算是不同事实。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| GAMEEND / ended | 服务端 | 整桌结束与每位玩家结束记录分粒度 | game_round_id, participant_key, end_reason, actual_count, duration_ms |
| BETREWARD + ASSET / final | 服务端/账本 | 最终有效扣款、派奖、退款、抽成 | settlement_id, game_round_id, currency, asset_type, amount_unit, final_stake, payout, fee, refund |
| WHOT_SETTLEMENT / show | 客户端 | 结算信息在任一结束页面实际可见 | settlement_view_id, game_round_id, participant_key, surface, settlement_state |
| WHOT_SETTLEMENT / play_again, back_rooms | 客户端 | 点击再来一局或返回房间列表 | action_id, settlement_view_id, next_root_match_id |


#### 需求14｜充值引导

统计引导触达、接受与后续支付；接受仅代表点击主按钮。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_GUIDE / show; guide_type=deposit | 客户端 | 充值引导真正展示 | guide_exposure_id, guide_id, guide_version, scene, game_round_id |
| WHOT_GUIDE / accept, close; guide_type=deposit | 客户端 | 点击引导主按钮或关闭 | guide_exposure_id, action_id, destination |
| 充值后续归因 | 支付服务端 | 关联订单创建和成功付款 | guide_exposure_id, payment_attempt_id（仅受控服务内部）, attribution_window |


#### 需求15｜提现引导

与充值引导复用结构，但申请、审核和到账必须分开。

| 事件／动作 | 上报责任 | 触发条件 | 专属字段 |
|---|---|---|---|
| WHOT_GUIDE / show; guide_type=withdraw | 客户端 | 提现引导实际展示 | guide_exposure_id, guide_id, guide_version, scene, eligibility_state |
| WHOT_GUIDE / accept, close; guide_type=withdraw | 客户端 | 点击进入提现或关闭 | guide_exposure_id, action_id, destination |
| 提现后续归因 | 提现服务端 | 用户提交申请、审核结束及到账 | guide_exposure_id, withdrawal_attempt_id（仅受控服务内部）, status, attribution_window |


### 关键状态及跨事件连接

托管与退出：auto_enter→manual_resume或牌局终止，auto_episode_id贯穿；exit_request→exit_result，退出可能转托管而不结束整桌。

Last Card：opportunity→declared或missed→catch_success/catch_fail→penalty或expired。抓罚失败需真实请求，没人抓罚只是窗口失效。同一窗口多请求只允许一次处罚；20 WHOT先完成图案选择。

记牌器：entry_click→methods_show→method_select→purchase_submit→success/failed/cancelled/pending→effective→open_used。已有权益直接使用另列；购买方式来自后台实际枚举，下一局生效通过effective_round_id校验。

同分：started→draw_round→resolved或下一draw_round；无论抽几轮，同分局数按game_round_id计一次。

网络：一个disconnect_episode_id下可多个reconnect_attempt_id；网络连接成功还需完整快照恢复成功。异常退出区分客户端确认与服务端超时推断。

结算：GAMEEND→最终BETREWARD/ASSET→WHOT_SETTLEMENT show→play_again/back_rooms；实际复玩需next_root_match_id关联后续GAMESTART。

资金引导：show→accept/close→业务后续；按guide_exposure_id关联，归因窗建议同会话或30分钟、并由业务签字。多个引导触达同一成功订单只能按确定规则归一次；提现到账需独立长窗口。

### 本期验收与上线顺序

| 负责人 | 交付 | 通过条件 |
|---|---|---|
| 策划 | 人群/模式/房间/时序/结果枚举签字 | Last Card、购买方式、下一局、引导场景及资金口径明确 |
| 客户端 | 可见展示、意图及体验事件 | 重复点击/重试不误计；APP/H5可定位 |
| 服务端／业务服务 | 唯一结果与幂等关联 | 服务端终态、开局或权益/资金结果可回查 |
| 数据开发 | 分层聚合与指标计算 | 分子分母、UTC/Lagos、观察期截止和未知状态一致 |
| 测试 | 端到端回放与双端验收 | 必测场景100%通过；错误定位到事件和字段 |


必测：超时/断线托管恢复、多对手并发抓罚只一次处罚、无人抓罚无处罚、20选图案顺序、各真实购买方式失败重试及下一局权益、重复同分、重连状态恢复、重复结算回调、多次结算展示、再玩关联、两类资金引导及多触点归因。

> 发布质量目标（建议，待签字）：关键关联覆盖≥99.5%，必填缺失<0.1%，同一业务事实重复计数为0；应有结果而未知的请求单列。二期资金未解释差额必须为0。先完成测试回放，再灰度观察，最后按同口径发布报表。

### 待确认事项与来源

本期需定稿：Last Card的3秒与回合机会规则、记牌器购买方式和生效局、退出后的托管处理、最终派奖是否含本金、充值/提现引导场景与接受动作、充值归因窗与提现到账观察窗。

来源：用户15项需求清单与本轮分期截图最终建议；策划方案最近已核验版本revision 5738；原V2完整合同。当前文档为设计计划，不表示事件已经实现。

### 需求16｜机器人胜负偏离与整局回放实现

以下为新增逻辑事件合同，最终event_id由埋点管理员映射。完整手牌、牌堆顺序与决策轨迹进入服务端受控回放存储；分析层仅接收牌局摘要、结果分类与replay_id。客户端不承载完整对手手牌。已存在的二期事件关联复用，不重复上报同一状态事实。

| 事件 | 责任与触发 | 专属字段 | 幂等与校验 |
| --- | --- | --- | --- |
| WHOT_ROUND_SNAPSHOT | 牌局服务端；发牌前后、首个可操作状态、关键检查点及最终裁决时 | snapshot_id、snapshot_stage、state_version、ruleset_version、engine_build、card_dictionary_version、seat_map、hands_ref、deck_ref、discard_ref、current_seat、current_pattern、effect_state、state_hash | 按round＋snapshot_id唯一；初始全状态及换牌前后必须可取回。cards用实例ID而非仅点数，避免同牌歧义 |
| WHOT_BOT_POLICY | 策略服务；assigned/applied/changed/disabled各状态生效时 | seat_id、policy_assignment_id、policy_segment_id、expected_outcome、target_subject、target_seat、applicability、policy_version、config_snapshot_ref、effective_seq、reason | 保存目标下发与实际生效两件事；局中切换不覆盖历史，未生效不冒充实际策略 |
| WHOT_BOT_DECISION | 策略引擎；每次决策完成或失败时 | decision_id、seat_id、policy_segment_id、input_state_hash、observation_scope、planned_action、executed_action_id、result、reason_code、duration_ms、decision_trace_ref | 可区分输入错误、决策异常与执行失败；相同版本及输入才可复验决策。记录真实日志，不反推当时意图 |
| WHOT_ROUND_ACTION | 牌局服务端；每个请求裁决及自动动作生效时 | action_id、cause_event_uid、server_seq、turn_no、actor_seat、actor_type、control_mode、action_type、target_seats、card_refs、draw_reason、result、before_hash、after_hash | play/draw/choose_pattern/skip/pass及特殊牌效果；请求与结果关联。重试复用action_id，拒绝动作不改状态，批次保留每张摸牌及其顺序 |
| WHOT_STATE_MUTATION | 牌局服务端；洗牌、发牌修正、手牌或牌堆顺序变动时 | mutation_id、cause_decision_id、mutation_type、affected_zones、before_state_ref、after_state_ref、rng_draw_ref、server_seq、result、reason | 记录实际洗牌、换牌和牌堆变化，含结算展示前的额外变化；仅记录种子或仅记录最终手牌不足以还原 |
| WHOT_BOT_ROUND_RESULT | 结束服务端／数据层；最终裁决或更正后 | game_round_id、seat_id、policy_assignment_id、target_at_start、result、end_reason、winner_seat、outcome_revision、eligibility_state、deviation_type、replay_id | 每席位局＋结果版本幂等；聚合采用最新有效裁决。重用GAMEEND与最终账本关联，不能重复计算结算 |
| WHOT_REPLAY_AUDIT | 归档与回放服务；归档及重放任务状态变化时 | replay_id、manifest_version、expected_seq_end、observed_seq_count、gap_ranges、checksum_status、replay_status、first_mismatch_seq、reason、replay_engine_version | archiving/complete/incomplete/failed/expired与passed/mismatch/not_run分列；可打开文件不等于回放通过 |

| 公共字段组 | 类型与必填条件 | 用途 |
| --- | --- | --- |
| event_uid / schema_version / source | string，每事件必填 | 上报重试复用UID；版本、client/server分列 |
| game_round_id / seat_id / participant_key | string；整桌事件seat可空，席位事件必填 | 身份保持同一席位；participant仅受控层关联，报表不返回实际标识 |
| is_robot / actor_type / control_mode | bool或unknown；enum | human＋manual/auto与robot＋policy分开；机器人模拟离线与真人网络断线不同 |
| server_seq / state_version / cause_event_uid | int64／string；状态日志必填 | 一个round共享全序；跨服务由牌局权威序号连接，不依赖客户端时间排序 |
| event_time / received_at / data_cutoff_at | UTC timestamp | 入库延迟和Lagos时段；终结超时/缓冲按规则配置 |
| ruleset_version / engine_build / bot_policy_version / config_version | string；相应事实必填 | 服务端代码、规则、策略、配置分别定位，不用APP版本代替 |
| requested_mode / actual_count / human_count / robot_count / client_mix | int与enum；开局事实必填 | 实际2/3/4人及跨端共享桌，席位组成总和核对 |
| replay_id / manifest_version / trace_ref / capture_state | string；回放摘要必填 | 仅内部对象引用，不写长期公开URL、凭据或直接身份信息 |

### 需求16｜按Whot机制还原完整牌局

| 机制 | 必须还原的内容 | 诊断判定 |
| --- | --- | --- |
| 洗牌、发牌与起始牌 | 完整牌集合、牌实例、原始牌堆顺序、发牌顺序、修正前后手牌、起始牌及当前图案 | PRD为2/3人各5张、4人各4张，起始牌普通牌；按该局规则版本校验 |
| 普通出牌与摸牌 | 动作前手牌、合法动作判断、真实选择、被拒原因；每张摸牌的牌堆位置、牌面、接收席位及顺序 | 无牌可出和主动选择摸牌均可能合法，不能将“有牌却摸牌”直接判为bug |
| 1/2/8/14/20功能牌 | 功能牌生效、目标席位、连出计数、回合转移、2罚摸累计／反弹、14影响席位、20图案选择 | 按规则版本回放；多人8跳过等行为不可硬套双人规则。实际换牌与控顶变化独立留痕 |
| Last Card宣告／抓罚 | 2→1手牌变化、特殊效果生效、20选图案、窗口开启、每对手机会、宣告、放弃、抓罚裁决及唯一罚抽 | 特殊效果及20选图案先完成；并发只一次罚抽。区分真实生效时间与动画延迟，机器人配置概率按生效快照 |
| 真人托管、退出、机器人状态与重连 | 动作发起者与控制模式、托管起止、服务端超时、状态快照版本、重试去重、模拟离线标记 | 真人托管仍是真人；动画离线不作为真实网络异常证据 |
| 牌堆耗尽比分 | 耗尽前牌堆、每席位最终手牌、逐牌计分、总分、淘汰与最低同分集合 | 星形双倍、20为20分按规则快照核对；只比较最低分集合 |
| 同分抽牌决胜 | 每轮参与席位、回收弃牌、洗牌后顺序、每席位抽牌、亮牌、再次同分与最终胜者 | PRD为最高点数胜、1最小20最大、不触发功能牌；不得把每轮决胜计成新牌局 |
| 终局与结算展示 | 游戏裁决时真实手牌、最终胜者、结算引用、展示快照以及两者间全部状态变化 | 结算展示快照不可覆盖历史真实手牌；胜负偏离与金额/RTP分开诊断 |

### 需求16｜采集、存储与回放流程

1. 开局为全部含机器人牌局分配replay_id并开启完整服务端轨迹，异步写入可靠队列或事务outbox；每条状态变化带同一牌局序号和前后hash。需要提前固定顺序的洗牌/RNG结果、外部响应及实际状态变动一并保存。日志失败记录并告警，不要求客户端等待回放归档。

2. 持久化层将整局日志按序分块，生成包含起止序号、总事件数、分块校验和、规则与引擎版本的manifest。初始状态＋所有变化量足以重建，每个关键阶段加检查点。断线恢复只引用检查点；时间戳、手牌数量或最终截图均不能替代状态日志。

3. 终局生成所有机器人席位局的全量摘要，先分类偏离再决定长期留存。两类偏离及目标未知／策略冲突／执行失败的局建议100%保留；正常对照按策略版本×实际人数×结束原因固定分层抽样，记录sample_rate及seed。所有比率用全量摘要，不能用异常回放库算发生率。

4. 短期轨迹从开局持续保留至终局判定与归档确认完成，异常长局不得被TTL提前删除；未收到归档成功回执时重试并标记缺口。建议待确认的留存配置：普通完整轨迹7天、偏离与对照回放30天；结果更正若已过保留期，更新分类并标记replay_expired，不能补造轨迹。

5. 回放校验分两层：结构完整性（无断序、重复计数、缺快照、校验和错误）与状态重放（按该局引擎/规则重放后每步hash及最终胜者一致）。策略决策复验为独立状态，依赖策略版本、决策输入与随机输出；不能仅凭动作重放成功就认定策略正确。

6. 研发回放页建议：顶部显示偏离类型、目标与实际结果、版本、结束原因和完整性；中部按席位显示手牌/牌堆/弃牌及逐步时间线；侧栏显示决策、实际执行、状态变化和首个差异。支持播放、暂停、步进、跳转Last Card/决胜/首差异；数据不完整时显示缺口位置。只读复盘不调用生产动作或资金接口。

### 需求16｜原因分类与评审验收

| 原因类别 | 可以确认的证据 | 处理建议 |
| --- | --- | --- |
| 目标或适用范围问题 | 下发与生效不一致、局中切换、多机器人互相冲突、2人策略用于3/4人 | 先校正配置与统计口径，冲突局单列 |
| 规则执行差异 | 首次状态hash分歧可定位到功能牌、抓罚、计分或决胜步骤 | 研发按具体规则与输入重现 |
| 策略执行异常 | 决策失败、计划未执行、API失败或超时的真实回执 | 按策略版本排查调用和落地过程；偏离率本身不证明策略算法错误 |
| 日志与结果问题 | 序号缺口、重复结算、展示状态覆盖真实状态 | 先修复证据链，原因标记unknown或data_gap |
| 未发现执行差异 | 完整回放通过且未证实异常 | 保留为策略结果偏离待分析；不直接判定根因或调整玩家输赢 |

必测：必赢输/赢、必输赢/输、目标未知、下发未生效、中途切换、同桌多机器人两类同时命中；2/3/4人合法与不适用组合；三种终局路径及多轮同分；20图案与宣告时序；2反弹链、14、1/8连出；多对手并发抓罚只罚一次；真人托管恢复、模拟离线与真实断线；牌库变化及展示前手牌变化；传输重复/乱序/缺片、服务重启、归档失败重试、过期更正与结果版本升级。

验收例：一桌A为win目标机器人但输、B为lose目标机器人却赢，统计为2个偏离席位局、1个偏离牌局；3局偏离中2局完整重放通过、1局缺片，核心回放通过率为2/3。若win目标有效席位局10个、输2个，其中1个回放缺失，输局率仍为2/10。以上均为合成验收例，不是线上数据。

上线验收建议：固定测试牌局100%可重放且最终结果一致，偏离分类与人工裁决一致，同一业务事实重复计数为0；生产缺帧、未归档和未知原因持续单列。策划确认目标主体、多人适用范围和策略冲突优先级，服务端确认权威状态与版本快照，数据团队验收分母及更正逻辑，测试验收双端表现与单一服务端事实。

来源与待确认：2026年9月8日用户新增需求；《Whot 6001 真金博彩机器人策略》revision 69与新版玩法需求revision 5738已重新读取。策略文档参数表未作为线上生效证据；新版本适用规则、目标主体、运行配置、日志现有覆盖和留存期限需研发／策划确认。本文是埋点及回放设计，尚未采集任何真实牌局或部署服务。


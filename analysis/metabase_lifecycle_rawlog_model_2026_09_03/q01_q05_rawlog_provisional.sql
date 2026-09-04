-- Saved Metabase Questions Q01-Q05
-- Shared source: {{#240-model-lifecycle-v2-joint-daily-rawlog-provisional}} AS m
-- All outputs are aggregate-only. date_start/date_end are optional Metabase date variables.
-- Reader-facing aliases intentionally follow the established Chinese Lifecycle workbook headers.
-- game_id is retained only as a technical grouping key and is never projected in a report.

-- Q01｜原始数据总数（原始日志试运行）
SELECT
  MIN(m.business_date) AS `开始日期`,
  MAX(m.business_date) AS `结束日期`,
  SUM(m.base_bet) AS `总基础下注额`,
  SUM(m.entire_bet) AS `总完全下注额`,
  SUM(m.base_actual_profit) AS `总基础实际盈利`,
  SUM(m.actual_profit) AS `查询期完全盈利`,
  CASE WHEN SUM(m.base_bet) = 0 THEN NULL ELSE 1 - SUM(m.base_actual_profit) / SUM(m.base_bet) END AS `总基础真实回报比`,
  CASE WHEN SUM(m.entire_bet) = 0 THEN NULL ELSE 1 - SUM(m.actual_profit) / SUM(m.entire_bet) END AS `总完全真实回报比`,
  SUM(m.expected_rtp_ratio * m.base_bet) / NULLIF(SUM(m.base_bet), 0) AS `总基础预期回报比`,
  SUM(m.expected_rtp_ratio * m.entire_bet) / NULLIF(SUM(m.entire_bet), 0) AS `总完全预期回报比`,
  NULL AS `总人数`,
  MAX(m.data_cutoff_at) AS `数据截止时间`,
  MAX(m.data_status) AS `数据状态`,
  MAX(m.metric_version) AS `口径版本`,
  '查询期去重用户数未由原始日志认证；总览从游戏聚合行重算，未使用空的 game_id=0 汇总行' AS `数据边界`
FROM {{#240-model-lifecycle-v2-joint-daily-rawlog-provisional}} AS m
WHERE m.row_scope = 'game'
  AND m.display_lifecycle BETWEEN 0 AND 4
  [[AND m.business_date >= {{date_start}}]]
  [[AND m.business_date <= {{date_end}}]];

-- Q02｜原始详细奖池（原始日志试运行）
WITH game_rows AS (
  SELECT
    m.business_date,
    m.display_lifecycle,
    m.game_id,
    m.base_bet,
    m.base_actual_profit,
    m.base_expected_profit,
    m.bankruptcy_profit,
    m.control_profit,
    m.entire_bet,
    m.actual_profit,
    m.entire_expected_profit,
    m.expected_rtp_ratio,
    m.data_cutoff_at,
    m.data_status,
    m.metric_version,
    CASE m.game_id
      WHEN 1 THEN '厂商汇总：PG'
      WHEN 2 THEN '厂商汇总：KooGame'
      WHEN 3 THEN '厂商汇总：Spribe'
      WHEN 4 THEN '厂商汇总：Tada'
      WHEN 5 THEN '厂商汇总：PP'
      WHEN 6 THEN '厂商汇总：OMG'
      WHEN 7 THEN '厂商汇总：BetCSports'
      WHEN 1003 THEN '红绿'
      WHEN 1004 THEN '足球'
      WHEN 2001 THEN '转盘'
      WHEN 2002 THEN '新转盘'
      WHEN 2003 THEN '转瓶子'
      WHEN 2004 THEN '21点'
      WHEN 2005 THEN '弹球游戏（Plinko 圣诞）'
      WHEN 2006 THEN '五张牌'
      WHEN 2007 THEN '五张牌红黑'
      WHEN 2008 THEN '拼奈拉（NairaSlots）'
      WHEN 3001 THEN '捕鱼'
      WHEN 6001 THEN 'Whot'
      WHEN 6002 THEN '骰子'
      WHEN 6005 THEN '百人Whot'
      WHEN 6007 THEN '对决'
      WHEN 9001 THEN 'CoinFlip'
      WHEN 9003 THEN 'ColorDice'
      WHEN 9008 THEN 'Limbo'
      WHEN 9010 THEN 'Keno'
      WHEN 9011 THEN 'Hilo'
      WHEN 9013 THEN 'Tower'
      WHEN 9016 THEN 'Plinko'
      WHEN 9998 THEN 'EasyWin'
      WHEN 9999 THEN '厂商汇总：betcCasino'
      ELSE CONCAT('待映射（ID ', CAST(m.game_id AS CHAR), '）')
    END AS game_display_name
  FROM {{#240-model-lifecycle-v2-joint-daily-rawlog-provisional}} AS m
  WHERE m.row_scope = 'game'
    AND m.display_lifecycle BETWEEN 0 AND 4
    [[AND m.business_date >= {{date_start}}]]
    [[AND m.business_date <= {{date_end}}]]
)
SELECT
  business_date AS `日期`,
  display_lifecycle AS `生命周期`,
  game_display_name AS `游戏`,
  SUM(base_bet) AS `基础下注额`,
  SUM(base_expected_profit) AS `基础预期盈利`,
  SUM(base_actual_profit) AS `基础实际盈利`,
  CASE WHEN SUM(base_bet) = 0 THEN NULL ELSE 1 - SUM(base_actual_profit) / SUM(base_bet) END AS `基础真实回报比`,
  SUM(expected_rtp_ratio * base_bet) / NULLIF(SUM(base_bet), 0) AS `基础预期回报比`,
  SUM(bankruptcy_profit) AS `总破产保护金额`,
  SUM(control_profit) AS `总个人盈利控制金额`,
  SUM(entire_bet) AS `完全下注额`,
  SUM(entire_expected_profit) AS `完全预期盈利`,
  SUM(actual_profit) AS `完全实际盈利`,
  CASE WHEN SUM(entire_bet) = 0 THEN NULL ELSE 1 - SUM(actual_profit) / SUM(entire_bet) END AS `完全真实回报比`,
  SUM(expected_rtp_ratio * entire_bet) / NULLIF(SUM(entire_bet), 0) AS `完全预期回报比`,
  CASE WHEN SUM(entire_bet) = 0 THEN NULL ELSE (1 - SUM(actual_profit) / SUM(entire_bet)) - SUM(expected_rtp_ratio * entire_bet) / NULLIF(SUM(entire_bet), 0) END AS `完全回报比差距`,
  MAX(data_cutoff_at) AS `数据截止时间`,
  MAX(data_status) AS `数据状态`,
  MAX(metric_version) AS `口径版本`
FROM game_rows
GROUP BY business_date, display_lifecycle, game_id, game_display_name
ORDER BY business_date DESC, `完全下注额` DESC
LIMIT 100;

-- Q03｜生命周期奖池分游戏汇总（原始日志试运行）
WITH game_rows AS (
  SELECT
    m.business_date,
    m.game_id,
    m.base_bet,
    m.base_actual_profit,
    m.base_expected_profit,
    m.bankruptcy_profit,
    m.control_profit,
    m.entire_bet,
    m.actual_profit,
    m.entire_expected_profit,
    m.expected_rtp_ratio,
    m.data_cutoff_at,
    m.data_status,
    m.metric_version,
    CASE m.game_id
      WHEN 1 THEN '厂商汇总：PG'
      WHEN 2 THEN '厂商汇总：KooGame'
      WHEN 3 THEN '厂商汇总：Spribe'
      WHEN 4 THEN '厂商汇总：Tada'
      WHEN 5 THEN '厂商汇总：PP'
      WHEN 6 THEN '厂商汇总：OMG'
      WHEN 7 THEN '厂商汇总：BetCSports'
      WHEN 1003 THEN '红绿'
      WHEN 1004 THEN '足球'
      WHEN 2001 THEN '转盘'
      WHEN 2002 THEN '新转盘'
      WHEN 2003 THEN '转瓶子'
      WHEN 2004 THEN '21点'
      WHEN 2005 THEN '弹球游戏（Plinko 圣诞）'
      WHEN 2006 THEN '五张牌'
      WHEN 2007 THEN '五张牌红黑'
      WHEN 2008 THEN '拼奈拉（NairaSlots）'
      WHEN 3001 THEN '捕鱼'
      WHEN 6001 THEN 'Whot'
      WHEN 6002 THEN '骰子'
      WHEN 6005 THEN '百人Whot'
      WHEN 6007 THEN '对决'
      WHEN 9001 THEN 'CoinFlip'
      WHEN 9003 THEN 'ColorDice'
      WHEN 9008 THEN 'Limbo'
      WHEN 9010 THEN 'Keno'
      WHEN 9011 THEN 'Hilo'
      WHEN 9013 THEN 'Tower'
      WHEN 9016 THEN 'Plinko'
      WHEN 9998 THEN 'EasyWin'
      WHEN 9999 THEN '厂商汇总：betcCasino'
      ELSE CONCAT('待映射（ID ', CAST(m.game_id AS CHAR), '）')
    END AS game_display_name
  FROM {{#240-model-lifecycle-v2-joint-daily-rawlog-provisional}} AS m
  WHERE m.row_scope = 'game'
    AND m.display_lifecycle BETWEEN 0 AND 4
    [[AND m.business_date >= {{date_start}}]]
    [[AND m.business_date <= {{date_end}}]]
)
SELECT
  game_display_name AS `游戏`,
  COUNT(DISTINCT business_date) AS `有效数据天数`,
  SUM(base_bet) AS `基础下注额`,
  SUM(base_expected_profit) AS `基础预期盈利`,
  SUM(base_actual_profit) AS `基础实际盈利`,
  CASE WHEN SUM(base_bet) = 0 THEN NULL ELSE 1 - SUM(base_actual_profit) / SUM(base_bet) END AS `基础真实回报比`,
  SUM(expected_rtp_ratio * base_bet) / NULLIF(SUM(base_bet), 0) AS `基础预期回报比`,
  CASE WHEN SUM(base_bet) = 0 THEN NULL ELSE (1 - SUM(base_actual_profit) / SUM(base_bet)) - SUM(expected_rtp_ratio * base_bet) / NULLIF(SUM(base_bet), 0) END AS `基础回报比差距`,
  SUM(bankruptcy_profit) AS `总破产保护金额`,
  SUM(control_profit) AS `总个人盈利控制金额`,
  SUM(entire_bet) AS `完全下注额`,
  SUM(entire_expected_profit) AS `完全预期盈利`,
  SUM(actual_profit) AS `完全实际盈利`,
  CASE WHEN SUM(entire_bet) = 0 THEN NULL ELSE 1 - SUM(actual_profit) / SUM(entire_bet) END AS `完全真实回报比`,
  SUM(expected_rtp_ratio * entire_bet) / NULLIF(SUM(entire_bet), 0) AS `完全预期回报比`,
  CASE WHEN SUM(entire_bet) = 0 THEN NULL ELSE (1 - SUM(actual_profit) / SUM(entire_bet)) - SUM(expected_rtp_ratio * entire_bet) / NULLIF(SUM(entire_bet), 0) END AS `完全回报比差距`,
  MAX(data_cutoff_at) AS `数据截止时间`,
  MAX(data_status) AS `数据状态`,
  MAX(metric_version) AS `口径版本`
FROM game_rows
GROUP BY game_id, game_display_name
ORDER BY `完全下注额` DESC
LIMIT 100;

-- Q04｜原始数据活跃周期-回报（原始日志试运行）
SELECT
  m.business_date AS `日期`,
  m.display_lifecycle AS `生命周期`,
  SUM(m.base_bet) AS `基础下注额`,
  SUM(m.base_expected_profit) AS `基础预期盈利`,
  SUM(m.base_actual_profit) AS `基础实际盈利`,
  CASE WHEN SUM(m.base_bet) = 0 THEN NULL ELSE 1 - SUM(m.base_actual_profit) / SUM(m.base_bet) END AS `基础真实回报比`,
  SUM(m.expected_rtp_ratio * m.base_bet) / NULLIF(SUM(m.base_bet), 0) AS `基础预期回报比`,
  CASE WHEN SUM(m.base_bet) = 0 THEN NULL ELSE (1 - SUM(m.base_actual_profit) / SUM(m.base_bet)) - SUM(m.expected_rtp_ratio * m.base_bet) / NULLIF(SUM(m.base_bet), 0) END AS `基础回报比差距`,
  SUM(m.bankruptcy_profit) AS `总破产保护金额`,
  SUM(m.control_profit) AS `总个人盈利控制金额`,
  SUM(m.entire_bet) AS `完全下注额`,
  SUM(m.entire_expected_profit) AS `完全预期盈利`,
  SUM(m.actual_profit) AS `完全实际盈利`,
  CASE WHEN SUM(m.entire_bet) = 0 THEN NULL ELSE 1 - SUM(m.actual_profit) / SUM(m.entire_bet) END AS `完全真实回报比`,
  SUM(m.expected_rtp_ratio * m.entire_bet) / NULLIF(SUM(m.entire_bet), 0) AS `完全预期回报比`,
  CASE WHEN SUM(m.entire_bet) = 0 THEN NULL ELSE (1 - SUM(m.actual_profit) / SUM(m.entire_bet)) - SUM(m.expected_rtp_ratio * m.entire_bet) / NULLIF(SUM(m.entire_bet), 0) END AS `完全回报比差距`,
  NULL AS `人均实际盈利`,
  MAX(m.data_cutoff_at) AS `数据截止时间`,
  MAX(m.data_status) AS `数据状态`,
  MAX(m.metric_version) AS `口径版本`,
  '从游戏聚合行按生命周期重算；查询期去重用户与人均盈利未由原始日志认证' AS `数据边界`
FROM {{#240-model-lifecycle-v2-joint-daily-rawlog-provisional}} AS m
WHERE m.row_scope = 'game'
  AND m.display_lifecycle BETWEEN 0 AND 4
  [[AND m.business_date >= {{date_start}}]]
  [[AND m.business_date <= {{date_end}}]]
GROUP BY m.business_date, m.display_lifecycle
ORDER BY m.business_date, m.display_lifecycle
LIMIT 500;

-- Q05｜原始数据活跃周期-付费（原始日志试运行）
SELECT
  m.business_date AS `日期`,
  m.display_lifecycle AS `生命周期`,
  NULL AS `总人数`,
  SUM(m.recharge_count) AS `充值次数`,
  SUM(m.recharge_amount) AS `当日充值总金额`,
  SUM(m.repeat_recharge_count) AS `复充次数`,
  SUM(m.repeat_recharge_amount) AS `当日复充总金额`,
  SUM(m.withdraw_count) AS `提现次数`,
  SUM(m.withdraw_amount) AS `TX总金额`,
  SUM(m.recharge_amount) - SUM(m.withdraw_amount) AS `收支差额（非账务营收）`,
  SUM(m.controlled_user_count) AS `受控人数`,
  SUM(m.controlled_count) AS `受控次数`,
  SUM(m.absolute_bankrupt_user_count) AS `绝对破产人数`,
  SUM(m.absolute_bankrupt_count) AS `绝对破产次数`,
  SUM(m.retention_user_count) AS `留存人数`,
  SUM(m.upgrade_user_count) AS `升级人数`,
  NULL AS `TC比`,
  NULL AS `平均流充比`,
  NULL AS `折损系数`,
  MAX(m.data_cutoff_at) AS `数据截止时间`,
  MAX(m.data_status) AS `数据状态`,
  MAX(m.metric_version) AS `口径版本`,
  '查询期去重用户、TC、流充比和折损系数未由原始日志认证；收支差额=充值金额-提现金额，不等同账务营收' AS `数据边界`
FROM {{#240-model-lifecycle-v2-joint-daily-rawlog-provisional}} AS m
WHERE m.row_scope = 'summary'
  AND m.display_lifecycle BETWEEN 0 AND 4
  [[AND m.business_date >= {{date_start}}]]
  [[AND m.business_date <= {{date_end}}]]
GROUP BY m.business_date, m.display_lifecycle
ORDER BY m.business_date, m.display_lifecycle
LIMIT 500;

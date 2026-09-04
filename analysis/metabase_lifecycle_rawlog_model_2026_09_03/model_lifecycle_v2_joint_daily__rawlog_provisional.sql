-- Waje Lifecycle V2 (Joint) raw-log aggregate model.
-- Metabase Model: model_lifecycle_v2_joint_daily__rawlog_provisional
-- Status: provisional_raw_log
-- Scope: business dates from 2026-08-01 inclusive; aggregate-only.
-- This query deliberately exposes no user, account, order, KYC, or raw-log rows.

WITH raw_snapshot AS (
  SELECT
    DATE(DATE_SUB(FROM_UNIXTIME(src.time), INTERVAL 1 DAY)) AS business_date,
    src.game_type AS game_id,
    src.lifecycle - 1 AS display_lifecycle,
    src.pool_type,
    src.data,
    FROM_UNIXTIME(src.time) AS snapshot_time
  FROM whot_center.stat_lifecycle_pool_v2_log AS src
  WHERE src.change_type = 3
    AND src.data_type = 1
    AND src.time >= UNIX_TIMESTAMP('2026-08-02 00:00:00')
), daily_pivot AS (
  SELECT
    business_date,
    game_id,
    display_lifecycle,
    MAX(CASE WHEN pool_type = 1 THEN data END) AS real_profit_raw,
    MAX(CASE WHEN pool_type = 2 THEN data END) AS expected_profit_raw,
    MAX(CASE WHEN pool_type = 3 THEN data END) AS adjusted_profit_raw,
    MAX(CASE WHEN pool_type = 4 THEN data END) AS entire_bet_raw,
    MAX(CASE WHEN pool_type = 5 THEN data END) AS bankruptcy_bet_raw,
    MAX(CASE WHEN pool_type = 6 THEN data END) AS bankruptcy_profit_raw,
    MAX(CASE WHEN pool_type = 7 THEN data END) AS control_bet_raw,
    MAX(CASE WHEN pool_type = 8 THEN data END) AS control_profit_raw,
    MAX(CASE WHEN pool_type = 12 THEN data END) AS expected_rtp_bps,
    MAX(CASE WHEN pool_type = 22 THEN data END) AS real_reserved_raw,
    MAX(CASE WHEN pool_type = 23 THEN data END) AS expected_reserved_raw,
    MAX(CASE WHEN pool_type = 1001 THEN data END) AS recharge_count,
    MAX(CASE WHEN pool_type = 1002 THEN data END) AS recharge_amount_raw,
    MAX(CASE WHEN pool_type = 1003 THEN data END) AS repeat_recharge_count,
    MAX(CASE WHEN pool_type = 1004 THEN data END) AS repeat_recharge_amount_raw,
    MAX(CASE WHEN pool_type = 1005 THEN data END) AS withdraw_count,
    MAX(CASE WHEN pool_type = 1006 THEN data END) AS withdraw_amount_raw,
    MAX(CASE WHEN pool_type = 1007 THEN data END) AS controlled_user_count,
    MAX(CASE WHEN pool_type = 1008 THEN data END) AS controlled_count,
    MAX(CASE WHEN pool_type = 1009 THEN data END) AS absolute_bankrupt_user_count,
    MAX(CASE WHEN pool_type = 1010 THEN data END) AS absolute_bankrupt_count,
    MAX(CASE WHEN pool_type = 1011 THEN data END) AS retention_user_count,
    MAX(CASE WHEN pool_type = 1024 THEN data END) AS upgrade_user_count,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT pool_type) AS pool_type_coverage,
    MAX(snapshot_time) AS data_cutoff_at
  FROM raw_snapshot
  GROUP BY business_date, game_id, display_lifecycle
)
SELECT
  business_date,
  'joint' AS data_scope,
  'all' AS population_type,
  display_lifecycle,
  game_id,
  /*
     展示名称以已验收的游戏代码字典（revision 609）和 Lifecycle 原始工作簿交叉核验。
     9008/9010 采用技术映射：Limbo=9008、Keno=9010；不沿用产品表中已知的颠倒关系。
     1–7、9999 是原始 Lifecycle 表中的厂商/平台汇总行，不伪装成单款游戏。
  */
  CASE game_id
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
    ELSE CONCAT('待映射（ID ', CAST(game_id AS CHAR), '）')
  END AS game_name,
  CASE
    WHEN game_id IN (1, 2, 3, 4, 5, 6, 7, 9999) THEN 'provider_rollup'
    WHEN game_id IN (1003, 1004, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 3001, 6001, 6002, 6005, 6007, 9001, 9003, 9008, 9010, 9011, 9013, 9016, 9998) THEN 'mapped_game'
    ELSE 'pending_mapping'
  END AS game_mapping_status,
  CAST(game_id AS CHAR) AS game_type,
  'not_available' AS provider,
  1 AS is_joint,
  NULL AS is_self_developed,
  CASE WHEN game_id = 0 THEN 'summary' ELSE 'game' END AS row_scope,
  'not_available' AS app_version,
  'not_available' AS package_id,
  'not_available' AS distribution_channel_id,
  'not_available' AS attribution_media_id,
  'not_available' AS attribution_channel_id,
  real_profit_raw / 100.0 AS real_profit,
  expected_profit_raw / 100.0 AS expected_profit,
  adjusted_profit_raw / 100.0 AS adjusted_profit,
  entire_bet_raw / 100.0 AS entire_bet,
  bankruptcy_bet_raw / 100.0 AS bankruptcy_bet,
  bankruptcy_profit_raw / 100.0 AS bankruptcy_profit,
  control_bet_raw / 100.0 AS control_bet,
  control_profit_raw / 100.0 AS control_profit,
  expected_rtp_bps / 10000.0 AS expected_rtp_ratio,
  (real_profit_raw - real_reserved_raw) / 100.0 AS actual_profit,
  (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) / 100.0 AS base_bet,
  (real_profit_raw - real_reserved_raw - bankruptcy_profit_raw - control_profit_raw) / 100.0 AS base_actual_profit,
  CASE
    WHEN entire_bet_raw = 0 OR entire_bet_raw IS NULL THEN NULL
    ELSE 1 - (real_profit_raw - real_reserved_raw) / entire_bet_raw
  END AS entire_actual_rtp_ratio,
  CASE
    WHEN (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) = 0
      OR (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) IS NULL THEN NULL
    ELSE 1 - (real_profit_raw - real_reserved_raw - bankruptcy_profit_raw - control_profit_raw)
      / (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw)
  END AS base_actual_rtp_ratio,
  CASE
    WHEN expected_rtp_bps IS NULL THEN NULL
    ELSE entire_bet_raw * (10000 - expected_rtp_bps) / 10000.0 / 100.0
  END AS entire_expected_profit,
  CASE
    WHEN expected_rtp_bps IS NULL THEN NULL
    ELSE (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw)
      * (10000 - expected_rtp_bps) / 10000.0 / 100.0
  END AS base_expected_profit,
  recharge_count,
  recharge_amount_raw / 100.0 AS recharge_amount,
  repeat_recharge_count,
  repeat_recharge_amount_raw / 100.0 AS repeat_recharge_amount,
  withdraw_count,
  withdraw_amount_raw / 100.0 AS withdraw_amount,
  controlled_user_count,
  controlled_count,
  absolute_bankrupt_user_count,
  absolute_bankrupt_count,
  retention_user_count,
  upgrade_user_count,
  NULL AS user_count,
  NULL AS tc_ratio,
  NULL AS flow_recharge_ratio,
  NULL AS loss_coefficient,
  source_row_count,
  pool_type_coverage,
  data_cutoff_at,
  'provisional_raw_log' AS data_status,
  'rawlog_v0_20260801' AS metric_version,
  '历史版本、包体、渠道、归因、查询期去重用户、TC、流充比和折损系数未由原始日志认证' AS metric_limitations
FROM daily_pivot
ORDER BY business_date, game_id, display_lifecycle;

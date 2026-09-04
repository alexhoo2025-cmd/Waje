-- Idempotent D+1 refresh template for Africa/Lagos business dates.
-- Initial load: SET @start_business_date = '2026-08-01';
-- Daily refresh: reset only the most recent three complete business dates.

SET @start_business_date = '2026-08-01';
SET @end_business_date = '2026-09-02';

START TRANSACTION;

DELETE FROM whot_center.mart_lifecycle_v2_joint_daily_rawlog
WHERE business_date BETWEEN @start_business_date AND @end_business_date;

INSERT INTO whot_center.mart_lifecycle_v2_joint_daily_rawlog (
  business_date, game_id, display_lifecycle, data_scope, population_type, row_scope,
  game_name, game_type, provider, is_joint, is_self_developed,
  app_version, package_id, distribution_channel_id, attribution_media_id, attribution_channel_id,
  real_profit, expected_profit, adjusted_profit, entire_bet, bankruptcy_bet, bankruptcy_profit,
  control_bet, control_profit, expected_rtp_ratio, actual_profit, base_bet, base_actual_profit,
  entire_actual_rtp_ratio, base_actual_rtp_ratio, entire_expected_profit, base_expected_profit,
  recharge_count, recharge_amount, repeat_recharge_count, repeat_recharge_amount,
  withdraw_count, withdraw_amount, controlled_user_count, controlled_count,
  absolute_bankrupt_user_count, absolute_bankrupt_count, retention_user_count, upgrade_user_count,
  user_count, tc_ratio, flow_recharge_ratio, loss_coefficient, source_row_count,
  pool_type_coverage, data_cutoff_at, data_status, metric_version, metric_limitations
)
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
    AND src.time >= UNIX_TIMESTAMP(DATE_ADD(@start_business_date, INTERVAL 1 DAY))
    AND src.time < UNIX_TIMESTAMP(DATE_ADD(@end_business_date, INTERVAL 2 DAY))
), daily_pivot AS (
  SELECT
    business_date, game_id, display_lifecycle,
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
  business_date, game_id, display_lifecycle, 'joint', 'all',
  CASE WHEN game_id = 0 THEN 'summary' ELSE 'game' END,
  CONCAT('游戏ID ', CAST(game_id AS CHAR)), CAST(game_id AS CHAR), 'not_available', 1, NULL,
  'not_available', 'not_available', 'not_available', 'not_available', 'not_available',
  real_profit_raw / 100.0, expected_profit_raw / 100.0, adjusted_profit_raw / 100.0,
  entire_bet_raw / 100.0, bankruptcy_bet_raw / 100.0, bankruptcy_profit_raw / 100.0,
  control_bet_raw / 100.0, control_profit_raw / 100.0, expected_rtp_bps / 10000.0,
  (real_profit_raw - real_reserved_raw) / 100.0,
  (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) / 100.0,
  (real_profit_raw - real_reserved_raw - bankruptcy_profit_raw - control_profit_raw) / 100.0,
  CASE WHEN entire_bet_raw = 0 OR entire_bet_raw IS NULL THEN NULL ELSE 1 - (real_profit_raw - real_reserved_raw) / entire_bet_raw END,
  CASE WHEN (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) = 0 OR (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) IS NULL THEN NULL ELSE 1 - (real_profit_raw - real_reserved_raw - bankruptcy_profit_raw - control_profit_raw) / (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) END,
  CASE WHEN expected_rtp_bps IS NULL THEN NULL ELSE entire_bet_raw * (10000 - expected_rtp_bps) / 10000.0 / 100.0 END,
  CASE WHEN expected_rtp_bps IS NULL THEN NULL ELSE (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) * (10000 - expected_rtp_bps) / 10000.0 / 100.0 END,
  recharge_count, recharge_amount_raw / 100.0, repeat_recharge_count, repeat_recharge_amount_raw / 100.0,
  withdraw_count, withdraw_amount_raw / 100.0, controlled_user_count, controlled_count,
  absolute_bankrupt_user_count, absolute_bankrupt_count, retention_user_count, upgrade_user_count,
  NULL, NULL, NULL, NULL, source_row_count, pool_type_coverage, data_cutoff_at,
  'provisional_raw_log', 'rawlog_v0_20260801',
  '历史版本、包体、渠道、归因、查询期去重用户、TC、流充比和折损系数未由原始日志认证'
FROM daily_pivot;

COMMIT;

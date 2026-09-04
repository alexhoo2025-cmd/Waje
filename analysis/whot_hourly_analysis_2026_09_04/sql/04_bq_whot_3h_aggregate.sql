-- The 3-hour table must deduplicate users at 3-hour grain.
-- This template intentionally does not sum hourly user counts.
WITH certified_settlement AS (
  SELECT
    DATE(TIMESTAMP_MILLIS(SAFE_CAST(server_time AS INT64)), 'Africa/Lagos') AS metric_date_lagos,
    EXTRACT(HOUR FROM TIMESTAMP_MILLIS(SAFE_CAST(server_time AS INT64)) AT TIME ZONE 'Africa/Lagos') AS hour_lagos,
    NULLIF(CAST(user_id AS STRING), '') AS user_key,
    NULLIF(CAST(unique_id AS STRING), '') AS round_id,
    SAFE_CAST(bet_num AS NUMERIC) AS bet_amount,
    SAFE_CAST(cash_settlement AS NUMERIC) AS player_payout_amount,
    LOWER(CAST(is_robot AS STRING)) IN ('1', 'true', 'robot') AS robot_flag
  FROM `wajenigeria.origin_hfyl.realtime_event_server`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-03'
    AND target_day IS NOT NULL
    AND play_id = '9116001'
    AND LOWER(CAST(event_type AS STRING)) = 'gameend'
),
valid_rounds AS (
  SELECT
    metric_date_lagos,
    DIV(hour_lagos, 3) * 3 AS period_start_hour,
    user_key,
    round_id,
    bet_amount,
    player_payout_amount,
    robot_flag
  FROM certified_settlement
  WHERE user_key IS NOT NULL
    AND round_id IS NOT NULL
)
SELECT
  metric_date_lagos,
  CONCAT(LPAD(CAST(period_start_hour AS STRING), 2, '0'), ':00—', LPAD(CAST(period_start_hour + 2 AS STRING), 2, '0'), ':59') AS period_3h,
  'Whot' AS game_scope,
  COUNT(DISTINCT IF(NOT robot_flag AND bet_amount > 0, user_key, NULL)) AS bet_users,
  COUNT(DISTINCT IF(NOT robot_flag AND bet_amount > 0, round_id, NULL)) AS bet_rounds,
  SUM(IF(NOT robot_flag AND bet_amount > 0, bet_amount, 0)) AS bet_amount,
  SUM(IF(NOT robot_flag AND bet_amount > 0, player_payout_amount, 0)) AS player_payout_amount,
  SUM(IF(NOT robot_flag AND bet_amount > 0, bet_amount - player_payout_amount, 0)) AS house_profit_amount,
  SAFE_DIVIDE(
    SUM(IF(NOT robot_flag AND bet_amount > 0, player_payout_amount, 0)),
    SUM(IF(NOT robot_flag AND bet_amount > 0, bet_amount, 0))
  ) AS weighted_rtp,
  COUNT(DISTINCT IF(robot_flag AND bet_amount > 0, user_key, NULL)) AS robot_users,
  SUM(IF(robot_flag AND bet_amount > 0, bet_amount, 0)) AS robot_bet_amount,
  7 AS observed_days,
  CURRENT_TIMESTAMP() AS data_cutoff_at,
  'provisional_server_gameend' AS data_state,
  '3-hour users are deduplicated directly, entry is sparse and cash settlement/unit remain provisional' AS missing_reason
FROM valid_rounds
GROUP BY metric_date_lagos, period_start_hour
ORDER BY metric_date_lagos, period_start_hour
LIMIT 3000;

-- Aggregate template for the observed Whot server feed.
-- Exact Whot mapping: play_id='9116001' (dictionary game_id=6001).
-- Amounts remain source integer units; cash_settlement is a payout proxy pending certification.
WITH settled_rounds AS (
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
hourly AS (
  SELECT
    metric_date_lagos,
    hour_lagos,
    COUNT(DISTINCT IF(NOT robot_flag AND bet_amount > 0, user_key, NULL)) AS bet_users,
    COUNT(DISTINCT IF(NOT robot_flag AND bet_amount > 0, round_id, NULL)) AS bet_rounds,
    SUM(IF(NOT robot_flag AND bet_amount > 0, bet_amount, 0)) AS bet_amount,
    SUM(IF(NOT robot_flag AND bet_amount > 0, player_payout_amount, 0)) AS player_payout_amount,
    COUNT(DISTINCT IF(robot_flag AND bet_amount > 0, user_key, NULL)) AS robot_users,
    SUM(IF(robot_flag AND bet_amount > 0, bet_amount, 0)) AS robot_bet_amount
  FROM settled_rounds
  WHERE user_key IS NOT NULL
    AND round_id IS NOT NULL
  GROUP BY metric_date_lagos, hour_lagos
)
SELECT
  metric_date_lagos,
  hour_lagos,
  'Whot' AS game_scope,
  CAST(NULL AS INT64) AS entry_users,
  CAST(NULL AS INT64) AS gamestart_users,
  bet_users,
  bet_rounds,
  bet_amount,
  player_payout_amount,
  bet_amount - player_payout_amount AS house_profit_amount,
  SAFE_DIVIDE(player_payout_amount, bet_amount) AS weighted_rtp,
  CAST(NULL AS FLOAT64) AS entry_to_bet_rate,
  CAST(NULL AS STRING) AS rtp_band,
  robot_users,
  robot_bet_amount,
  7 AS observed_days,
  CURRENT_TIMESTAMP() AS data_cutoff_at,
  'provisional_server_gameend' AS data_state,
  'PV entry is sparse, cash_settlement and source integer unit require business certification' AS missing_reason
FROM hourly
ORDER BY metric_date_lagos, hour_lagos
LIMIT 3000;

-- User keys are used only inside this query and never returned.
-- At least 3 settled rounds per user-hour; suppress an hour if fewer than 10 users qualify.
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
user_hour AS (
  SELECT
    metric_date_lagos,
    hour_lagos,
    user_key,
    COUNT(DISTINCT round_id) AS settled_rounds,
    SUM(bet_amount) AS bet_amount,
    SUM(player_payout_amount) AS player_payout_amount
  FROM settled_rounds
  WHERE NOT robot_flag
    AND user_key IS NOT NULL
    AND round_id IS NOT NULL
    AND bet_amount > 0
  GROUP BY metric_date_lagos, hour_lagos, user_key
  HAVING COUNT(DISTINCT round_id) >= 3
),
banded AS (
  SELECT
    metric_date_lagos,
    hour_lagos,
    CASE
      WHEN SAFE_DIVIDE(player_payout_amount, bet_amount) < 0.90 THEN '<90%'
      WHEN SAFE_DIVIDE(player_payout_amount, bet_amount) < 0.95 THEN '90%—95%'
      WHEN SAFE_DIVIDE(player_payout_amount, bet_amount) < 1.00 THEN '95%—100%'
      WHEN SAFE_DIVIDE(player_payout_amount, bet_amount) < 1.05 THEN '100%—105%'
      WHEN SAFE_DIVIDE(player_payout_amount, bet_amount) < 1.10 THEN '105%—110%'
      ELSE '≥110%'
    END AS rtp_band
  FROM user_hour
  WHERE bet_amount > 0
),
hour_counts AS (
  SELECT metric_date_lagos, hour_lagos, COUNT(*) AS rtp_eligible_users
  FROM banded
  GROUP BY metric_date_lagos, hour_lagos
)
SELECT
  banded.metric_date_lagos,
  banded.hour_lagos,
  'Whot' AS game_scope,
  CASE WHEN hour_counts.rtp_eligible_users < 10 THEN '样本不足/已隐藏' ELSE banded.rtp_band END AS rtp_band,
  CASE WHEN hour_counts.rtp_eligible_users < 10 THEN NULL ELSE COUNT(*) END AS rtp_band_users,
  CASE WHEN hour_counts.rtp_eligible_users < 10 THEN NULL ELSE SAFE_DIVIDE(COUNT(*), hour_counts.rtp_eligible_users) END AS rtp_band_share,
  hour_counts.rtp_eligible_users,
  'provisional_server_user_rtp, minimum_3_settled_rounds, groups_under_10_suppressed' AS data_state
FROM banded
JOIN hour_counts USING (metric_date_lagos, hour_lagos)
GROUP BY banded.metric_date_lagos, banded.hour_lagos, banded.rtp_band, hour_counts.rtp_eligible_users
HAVING hour_counts.rtp_eligible_users >= 10
ORDER BY banded.metric_date_lagos, banded.hour_lagos, rtp_band
LIMIT 3000;

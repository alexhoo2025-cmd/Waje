-- MySQL/Metabase fallback only. Run only against an owner-approved narrow view
-- or after a cost guard proves the time filter is indexed. Do not call rows "rounds"
-- unless a stable round key and final settlement semantics are certified.
SELECT
  DATE(FROM_UNIXTIME(time)) AS metric_date_lagos,
  HOUR(FROM_UNIXTIME(time)) AS hour_lagos,
  COUNT(DISTINCT user_id) AS bet_users,
  SUM(bet) / 100.0 AS candidate_bet_amount,
  SUM(reward) / 100.0 AS candidate_payout_amount,
  SUM(reward) / NULLIF(SUM(bet), 0) AS candidate_weighted_rtp,
  'candidate_record_rows_not_rounds' AS round_status,
  'provisional_until_bet_reward_units_are_certified' AS data_state
FROM whot_center.game_record
WHERE game = 'Whot'
  AND time >= UNIX_TIMESTAMP('2026-08-28 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-09-04 00:00:00')
GROUP BY metric_date_lagos, hour_lagos
ORDER BY metric_date_lagos, hour_lagos;

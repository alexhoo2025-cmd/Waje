-- TEMPLATE ONLY: activate the authorized view before execution.
SELECT
  event_date,
  game_id,
  play_id,
  surface_type,
  package_id,
  currency_type,
  SUM(effective_stake) AS effective_stake,
  SUM(final_payout) AS final_payout,
  SUM(valid_rounds) AS valid_rounds,
  SAFE_DIVIDE(SUM(final_payout), NULLIF(SUM(effective_stake), 0)) AS actual_rtp,
  MAX(data_cutoff) AS data_cutoff,
  LOGICAL_AND(complete_day) AS complete_day
FROM `wajenigeria.agent_analytics.vw_game_rtp_daily_safe`
WHERE event_date BETWEEN @start_date AND @end_date
GROUP BY event_date, game_id, play_id, surface_type, package_id, currency_type
HAVING SUM(valid_rounds) >= 10
LIMIT 3000;

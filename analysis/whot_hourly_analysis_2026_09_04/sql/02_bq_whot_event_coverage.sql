-- Execute only after q00/q01 and the exact Whot game_type/game_id are certified.
-- Replace the marked exact-match predicate if the dictionary resolves Whot to a numeric key.
SELECT
  target_day AS metric_date_lagos,
  CAST(event_type AS STRING) AS event_type,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(NULLIF(CAST(user_id AS STRING), '')) AS approx_user_count,
  COUNTIF(LOWER(CAST(game_type AS STRING)) = 'whot') AS candidate_whot_event_count,
  COUNTIF(LOWER(CAST(event_type AS STRING)) = 'pv') AS entry_candidate_events,
  COUNTIF(LOWER(CAST(event_type AS STRING)) = 'gamestart') AS gamestart_events,
  COUNTIF(LOWER(CAST(event_type AS STRING)) = 'gameend') AS gameend_events,
  COUNTIF(LOWER(CAST(event_type AS STRING)) = 'betreward') AS betreward_events,
  COUNTIF(NULLIF(CAST(user_id AS STRING), '') IS NULL) AS null_user_events,
  COUNTIF(NULLIF(CAST(play_id AS STRING), '') IS NULL) AS null_play_events
FROM `wajenigeria.origin_hfyl.history_event_client`
WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-03'
GROUP BY metric_date_lagos, event_type
ORDER BY metric_date_lagos, event_type
LIMIT 3000;

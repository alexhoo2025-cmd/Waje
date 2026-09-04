WITH base AS (
  SELECT
    event_name,
    user_id,
    event_params
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
)
SELECT
  COUNT(*) AS total_events,
  COUNTIF(user_id IS NOT NULL AND user_id != '') AS events_with_user_id,
  APPROX_COUNT_DISTINCT(IF(user_id IS NOT NULL AND user_id != '', user_id, NULL)) AS identified_users,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(game_load|game_ready|bet_ready|game_start|place_bet|settlement|game_end)')) AS game_process_named_events,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(web[_-]?vital|lcp|inp|cls|fcp|ttfb|page[_-]?load|js[_-]?error|frontend[_-]?error|exception)')) AS performance_named_events,
  COUNTIF(EXISTS (
    SELECT 1 FROM UNNEST(event_params) ep
    WHERE REGEXP_CONTAINS(LOWER(ep.key), r'(game_id|play_id|round_id|session_id|release_id|h5_build|lcp|inp|cls|fcp|ttfb)')
  )) AS events_with_target_keys
FROM base;

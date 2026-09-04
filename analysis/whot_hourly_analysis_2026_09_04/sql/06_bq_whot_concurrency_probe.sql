-- Probe only: no Whot-scoped online/session intervals were found in the observed schema.
-- APPONLINE without Whot scope is not concurrency; this query remains intentionally blocked.
SELECT
  DATE(TIMESTAMP_MILLIS(SAFE_CAST(server_time AS INT64)), 'Africa/Lagos') AS metric_date_lagos,
  EXTRACT(HOUR FROM TIMESTAMP_MILLIS(SAFE_CAST(server_time AS INT64)) AT TIME ZONE 'Africa/Lagos') AS hour_lagos,
  COUNT(DISTINCT NULLIF(CAST(user_id AS STRING), '')) AS online_user_proxy,
  CAST(NULL AS NUMERIC) AS min_observed_duration,
  CAST(NULL AS NUMERIC) AS max_observed_duration,
  'proxy_only_until_session_intervals_are_certified' AS data_state
FROM `wajenigeria.origin_hfyl.realtime_event_server`
WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-03'
  AND target_day IS NOT NULL
  AND play_id = '9116001'
  AND FALSE
GROUP BY metric_date_lagos, hour_lagos
ORDER BY metric_date_lagos, hour_lagos
LIMIT 3000;

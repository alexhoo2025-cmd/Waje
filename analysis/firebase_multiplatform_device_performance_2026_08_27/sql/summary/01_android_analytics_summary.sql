-- Compact Android Analytics window summary. Event names are grouped into
-- safe categories; no event_params or user-level rows are returned.
SELECT
  'android' AS endpoint,
  COALESCE(NULLIF(app_info.id, ''), 'unknown') AS app_package,
  'all_versions' AS app_version,
  CASE
    WHEN event_name IN ('session_start', 'first_open', 'first_visit', 'user_engagement') THEN 'lifecycle'
    WHEN event_name IN ('page_view', 'screen_view') THEN 'page_or_screen'
    WHEN STARTS_WITH(event_name, 'notification_') THEN 'notification'
    WHEN event_name IN ('register', 'recharge', 'withdraw', 'firstCharge') THEN 'behavior_signal'
    ELSE 'other'
  END AS event_category,
  COUNT(*) AS event_count,
  COUNT(DISTINCT _TABLE_SUFFIX) AS covered_days
FROM `wajenigeria.waje_ng_firebase_android.events_*`
WHERE _TABLE_SUFFIX BETWEEN '__APP_START_YYYYMMDD__' AND '__APP_END_YYYYMMDD__'
GROUP BY endpoint, app_package, app_version, event_category
ORDER BY app_package, event_count DESC
LIMIT 500;

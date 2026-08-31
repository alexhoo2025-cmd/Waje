-- Android Firebase Analytics behavior aggregates.
-- Event counts are not users or unique sessions. No event_params are expanded.
WITH analytics_events AS (
  SELECT
    'android' AS endpoint,
    COALESCE(NULLIF(app_info.id, ''), 'unknown') AS app_package,
    'all_versions' AS app_version,
    SAFE.PARSE_DATE('%Y%m%d', event_date) AS metric_date_lagos,
    event_name
  FROM `wajenigeria.waje_ng_firebase_android.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '__APP_START_YYYYMMDD__' AND '__APP_END_YYYYMMDD__'
)
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  'all_versions' AS app_version,
  CASE
    WHEN event_name IN ('session_start', 'first_open', 'first_visit', 'user_engagement') THEN 'lifecycle'
    WHEN event_name IN ('page_view', 'screen_view') THEN 'page_or_screen'
    WHEN STARTS_WITH(event_name, 'notification_') THEN 'notification'
    WHEN event_name IN ('register', 'recharge', 'withdraw', 'firstCharge') THEN 'behavior_signal'
    ELSE 'other'
  END AS event_category,
  'category_total' AS event_name_bucket,
  COUNT(*) AS event_count
FROM analytics_events
WHERE metric_date_lagos IS NOT NULL
GROUP BY metric_date_lagos, endpoint, app_package, event_category
ORDER BY metric_date_lagos, endpoint, app_package, event_count DESC
LIMIT 500;

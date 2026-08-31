-- H5 Firebase Analytics behavior aggregates.
-- H5 has a separate coverage window because the current source does not yet
-- have the same complete days as native Analytics.
SELECT
  SAFE.PARSE_DATE('%Y%m%d', event_date) AS metric_date_lagos,
  'h5' AS endpoint,
  'waje_ng_firebase_h5' AS app_package,
  'unknown' AS app_version,
  CASE
    WHEN event_name IN ('session_start', 'first_visit', 'user_engagement') THEN 'lifecycle'
    WHEN event_name = 'page_view' THEN 'page_or_screen'
    WHEN STARTS_WITH(event_name, 'notification_') THEN 'notification'
    ELSE 'other'
  END AS event_category,
  event_name AS event_name_bucket,
  COUNT(*) AS event_count,
  COUNT(DISTINCT _TABLE_SUFFIX) AS covered_days
FROM `wajenigeria.waje_ng_firebase_h5.events_*`
WHERE _TABLE_SUFFIX BETWEEN '__H5_START_YYYYMMDD__' AND '__H5_END_YYYYMMDD__'
GROUP BY metric_date_lagos, endpoint, app_package, app_version, event_category, event_name_bucket
ORDER BY metric_date_lagos, event_count DESC
LIMIT 500;

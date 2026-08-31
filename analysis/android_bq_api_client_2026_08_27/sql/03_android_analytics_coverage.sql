-- Low-cardinality Android Analytics coverage check.
-- This query is intentionally separate from the device/event mix query so that
-- LIMIT 3000 cannot hide a package or date from the coverage conclusion.
SELECT
  PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS metric_date_lagos,
  COALESCE(NULLIF(app_info.id, ''), 'unknown') AS app_package,
  COUNT(*) AS event_count,
  COUNT(DISTINCT NULLIF(app_info.version, '')) AS app_version_count,
  COUNT(DISTINCT NULLIF(stream_id, '')) AS stream_count,
  COUNTIF(event_name = 'session_start') AS session_start_event_count
FROM `wajenigeria.waje_ng_firebase_android.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
  AND platform = 'ANDROID'
  AND app_info.id IN (
    'com.hfhy.waje.special',
    'com.hfhy.wajecasino.palmgame',
    'com.hfhy.wajecasino.game'
  )
GROUP BY metric_date_lagos, app_package
ORDER BY metric_date_lagos, app_package
LIMIT 100;

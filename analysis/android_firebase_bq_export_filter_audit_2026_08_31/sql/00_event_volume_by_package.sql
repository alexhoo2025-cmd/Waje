-- Read-only aggregate validation.
-- Candidate path from the 2026-08-27 local preparation pack; replace only after
-- the actual Firebase Analytics events_* table is verified in BigQuery.
SELECT
  PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS event_day,
  COALESCE(NULLIF(app_info.id, ''), 'unknown') AS app_package,
  COALESCE(NULLIF(app_info.version, ''), 'unknown') AS app_version,
  event_name,
  COUNT(*) AS event_count
FROM `wajenigeria.waje_ng_firebase_android.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
  AND platform = 'ANDROID'
GROUP BY event_day, app_package, app_version, event_name
HAVING COUNT(*) >= 10
ORDER BY event_day, app_package, event_count DESC
LIMIT 3000;

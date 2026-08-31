-- Crashlytics aggregate counts for the three Android packages.
-- event_id and issue_id are used only within COUNT(DISTINCT); diagnostic
-- payloads, custom keys, installation IDs and stack fields are not selected.
WITH crash_events AS (
  SELECT 'android_main' AS endpoint, 'com.hfhy.waje.special' AS app_package, event_timestamp, is_fatal, issue_id, event_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__STABILITY_START__' AND DATE '__STABILITY_END__'
  UNION ALL
  SELECT 'android_transsion_old', 'com.hfhy.wajecasino.palmgame', event_timestamp, is_fatal, issue_id, event_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__STABILITY_START__' AND DATE '__STABILITY_END__'
  UNION ALL
  SELECT 'android_transsion_new', 'com.hfhy.wajecasino.game', event_timestamp, is_fatal, issue_id, event_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__STABILITY_START__' AND DATE '__STABILITY_END__'
)
SELECT
  DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
  endpoint, app_package,
  'all_versions' AS app_version,
  IF(is_fatal, 'fatal', 'non_fatal') AS error_type,
  COUNT(*) AS export_record_count,
  COUNT(DISTINCT event_id) AS dedup_event_count,
  COUNT(DISTINCT issue_id) AS issue_count,
  MAX(event_timestamp) AS data_cutoff_at
FROM crash_events
GROUP BY metric_date_lagos, endpoint, app_package, error_type
ORDER BY metric_date_lagos, endpoint, export_record_count DESC
LIMIT 500;

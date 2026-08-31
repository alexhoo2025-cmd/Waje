-- Compact Crashlytics window summary: one row per Android package/error type.
-- event_id and issue_id are used only inside aggregate functions.
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
  endpoint,
  app_package,
  IF(is_fatal, 'fatal', 'non_fatal') AS error_type,
  COUNT(*) AS export_record_count,
  COUNT(DISTINCT event_id) AS dedup_event_count,
  COUNT(DISTINCT issue_id) AS issue_count,
  MAX(event_timestamp) AS data_cutoff_at
FROM crash_events
GROUP BY endpoint, app_package, error_type
ORDER BY endpoint, error_type
LIMIT 500;

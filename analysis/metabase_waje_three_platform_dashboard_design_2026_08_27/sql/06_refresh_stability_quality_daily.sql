-- Admin-run scheduled query. Counts only; no crash rate until schema and denominator are certified.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE OR REPLACE TABLE `wajenigeria.waje_device_performance_mart.mart_stability_quality_daily`
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, app_version, issue_type
AS
WITH crashes AS (
  SELECT 'android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package, event_timestamp, application.display_version AS app_version, is_fatal, issue_id, event_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', event_timestamp, application.display_version, is_fatal, issue_id, event_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', event_timestamp, application.display_version, is_fatal, issue_id, event_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
)
SELECT
  DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
  endpoint,
  platform,
  app_package,
  COALESCE(NULLIF(app_version, ''), 'unknown') AS app_version,
  CASE WHEN is_fatal THEN 'fatal' ELSE 'nonfatal_or_anr' END AS issue_type,
  COUNT(*) AS event_count,
  COUNT(DISTINCT issue_id) AS issue_count,
  COUNT(DISTINCT event_id) AS distinct_event_id_count,
  MAX(event_timestamp) AS data_cutoff_at,
  metric_date_lagos < CURRENT_DATE('Africa/Lagos') AS complete_day,
  'provisional_event_dedup_and_denominator' AS quality_status,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM crashes
GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version, issue_type;

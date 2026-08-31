-- D+1 Crashlytics aggregation. No exception, stack, title, subtitle, custom-key,
-- installation or session identifier is selected into the mart.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.mart_stability_daily` (
  metric_date_lagos DATE NOT NULL,
  endpoint STRING NOT NULL,
  platform STRING NOT NULL,
  app_package STRING NOT NULL,
  app_version STRING NOT NULL,
  device_manufacturer STRING NOT NULL,
  device_model STRING NOT NULL,
  os_name STRING NOT NULL,
  os_version STRING NOT NULL,
  crashlytics_export_record_count INT64 NOT NULL,
  fatal_event_count INT64,
  nonfatal_event_count INT64,
  issue_count INT64,
  data_cutoff_at TIMESTAMP,
  complete_day BOOL NOT NULL,
  quality_status STRING NOT NULL,
  quality_note STRING NOT NULL,
  metric_definition_version STRING NOT NULL,
  refreshed_at TIMESTAMP NOT NULL
)
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, app_version, device_manufacturer
OPTIONS(description = 'Aggregate-only Android Crashlytics daily facts. Event and issue counts are provisional; no crash rate is calculated until event-id uniqueness and session denominator coverage are certified.');

DELETE FROM `wajenigeria.waje_device_performance_mart.mart_stability_daily`
WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date;

INSERT INTO `wajenigeria.waje_device_performance_mart.mart_stability_daily`
WITH raw_export AS (
  SELECT 'android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package,
    event_timestamp, application.display_version AS app_version, device.manufacturer AS device_manufacturer,
    device.model AS device_model, operating_system.name AS os_name,
    operating_system.display_version AS os_version, is_fatal, event_id, issue_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', event_timestamp, application.display_version,
    device.manufacturer, device.model, operating_system.name, operating_system.display_version, is_fatal, event_id, issue_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', event_timestamp, application.display_version,
    device.manufacturer, device.model, operating_system.name, operating_system.display_version, is_fatal, event_id, issue_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
)
SELECT
  DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
  endpoint,
  platform,
  app_package,
  COALESCE(NULLIF(app_version, ''), 'unknown') AS app_version,
  COALESCE(NULLIF(device_manufacturer, ''), 'unknown') AS device_manufacturer,
  COALESCE(NULLIF(device_model, ''), 'unknown') AS device_model,
  COALESCE(NULLIF(os_name, ''), 'unknown') AS os_name,
  COALESCE(NULLIF(os_version, ''), 'unknown') AS os_version,
  COUNT(*) AS crashlytics_export_record_count,
  COUNT(DISTINCT IF(is_fatal, event_id, NULL)) AS fatal_event_count,
  COUNT(DISTINCT IF(NOT is_fatal, event_id, NULL)) AS nonfatal_event_count,
  COUNT(DISTINCT issue_id) AS issue_count,
  MAX(event_timestamp) AS data_cutoff_at,
  DATE(event_timestamp, 'Africa/Lagos') < CURRENT_DATE('Africa/Lagos') AS complete_day,
  'provisional_event_dedup_and_denominator' AS quality_status,
  'Fatal/non-fatal event counts and issue count are safe aggregates. Do not calculate crash rate, ANR rate, impacted-user count or error-free session rate until event-id uniqueness and Sessions linkage are certified.' AS quality_note,
  'v1' AS metric_definition_version,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM raw_export
GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version, device_manufacturer, device_model, os_name, os_version, complete_day;

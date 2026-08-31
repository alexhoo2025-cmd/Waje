-- Admin-run scheduled query. Aggregates source coverage in BigQuery before Metabase reads it.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE OR REPLACE TABLE `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily`
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, source_name
AS
WITH coverage AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    'android_main' AS endpoint,
    'Android' AS platform,
    'com.hfhy.waje.special' AS app_package,
    'firebase_performance' AS source_name,
    COUNT(*) AS source_record_count,
    0 AS distinct_session_count,
    COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
    MAX(event_timestamp) AS data_cutoff_at
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos

  UNION ALL
  SELECT DATE(event_timestamp, 'Africa/Lagos'), 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', 'firebase_performance', COUNT(*), 0, COUNTIF(event_type = 'NETWORK_REQUEST'), MAX(event_timestamp)
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos

  UNION ALL
  SELECT DATE(event_timestamp, 'Africa/Lagos'), 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', 'firebase_performance', COUNT(*), 0, COUNTIF(event_type = 'NETWORK_REQUEST'), MAX(event_timestamp)
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos

  UNION ALL
  SELECT DATE(event_timestamp, 'Africa/Lagos'), 'android_main', 'Android', 'com.hfhy.waje.special', 'firebase_sessions', COUNT(*), COUNT(DISTINCT session_id), 0, MAX(event_timestamp)
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos

  UNION ALL
  SELECT DATE(event_timestamp, 'Africa/Lagos'), 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', 'firebase_sessions', COUNT(*), COUNT(DISTINCT session_id), 0, MAX(event_timestamp)
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos

  UNION ALL
  SELECT DATE(event_timestamp, 'Africa/Lagos'), 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', 'firebase_sessions', COUNT(*), COUNT(DISTINCT session_id), 0, MAX(event_timestamp)
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos

  UNION ALL
  SELECT PARSE_DATE('%Y%m%d', _TABLE_SUFFIX),
    CASE app_info.id WHEN 'com.hfhy.waje.special' THEN 'android_main' WHEN 'com.hfhy.wajecasino.palmgame' THEN 'android_transsion_old' WHEN 'com.hfhy.wajecasino.game' THEN 'android_transsion_new' ELSE 'android_unmapped' END,
    'Android', app_info.id, 'firebase_analytics', COUNT(*), 0, 0, MAX(TIMESTAMP_MICROS(event_timestamp))
  FROM `wajenigeria.waje_ng_firebase_android.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)
    AND platform = 'ANDROID'
  GROUP BY metric_date_lagos, endpoint, app_info.id

  UNION ALL
  SELECT PARSE_DATE('%Y%m%d', _TABLE_SUFFIX), 'ios_existing', 'iOS', COALESCE(NULLIF(app_info.id, ''), 'com.wajegame.wajegame'), 'firebase_analytics', COUNT(*), 0, 0, MAX(TIMESTAMP_MICROS(event_timestamp))
  FROM `wajenigeria.waje_ng_firebase_ios.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)
  GROUP BY metric_date_lagos, app_info.id

  UNION ALL
  SELECT PARSE_DATE('%Y%m%d', _TABLE_SUFFIX), 'h5', 'H5', 'waje_ng_firebase_h5', 'firebase_analytics', COUNT(*), 0, 0, MAX(TIMESTAMP_MICROS(event_timestamp))
  FROM `wajenigeria.waje_ng_firebase_h5.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)
  GROUP BY metric_date_lagos
)
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  source_name,
  source_record_count,
  distinct_session_count,
  network_request_count,
  data_cutoff_at,
  metric_date_lagos < CURRENT_DATE('Africa/Lagos') AS complete_day,
  CASE WHEN source_record_count = 0 THEN 'data_gap' WHEN metric_date_lagos >= CURRENT_DATE('Africa/Lagos') - 6 THEN 'immature' ELSE 'provisional' END AS quality_status,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM coverage;

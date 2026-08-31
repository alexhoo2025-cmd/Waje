-- D+1 source coverage and freshness. This is the first page's primary guardrail.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily` (
  metric_date_lagos DATE NOT NULL,
  endpoint STRING NOT NULL,
  platform STRING NOT NULL,
  app_package STRING NOT NULL,
  source_name STRING NOT NULL,
  source_record_count INT64 NOT NULL,
  distinct_session_count INT64,
  session_start_event_count INT64,
  event_name_count INT64,
  data_cutoff_at TIMESTAMP,
  source_freshness_lag_minutes INT64,
  complete_day BOOL NOT NULL,
  quality_status STRING NOT NULL,
  quality_note STRING NOT NULL,
  metric_definition_version STRING NOT NULL,
  refreshed_at TIMESTAMP NOT NULL
)
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, source_name
OPTIONS(description = 'Source availability, completeness and freshness guardrail. Counts from distinct source products are not directly comparable.');

DELETE FROM `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily`
WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date;

INSERT INTO `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily`
WITH analytics_coverage AS (
  SELECT
    metric_date_lagos, endpoint, platform, app_package,
    'firebase_analytics' AS source_name,
    SUM(event_count) AS source_record_count,
    CAST(NULL AS INT64) AS distinct_session_count,
    SUM(session_start_event_count) AS session_start_event_count,
    COUNT(DISTINCT event_name) AS event_name_count,
    MAX(event_data_cutoff_at) AS data_cutoff_at,
    LOGICAL_AND(complete_day) AS complete_day,
    MAX(quality_status) AS quality_status,
    'Analytics event counts are behavior signals. session_start is an event count, not a unique-session count.' AS quality_note
  FROM `wajenigeria.waje_device_performance_mart.mart_event_session_daily`
  WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos, endpoint, platform, app_package
), performance_coverage AS (
  SELECT
    metric_date_lagos, endpoint, platform, app_package,
    'firebase_performance' AS source_name,
    SUM(performance_record_count) AS source_record_count,
    CAST(NULL AS INT64) AS distinct_session_count,
    CAST(NULL AS INT64) AS session_start_event_count,
    CAST(NULL AS INT64) AS event_name_count,
    MAX(data_cutoff_at) AS data_cutoff_at,
    LOGICAL_AND(complete_day) AS complete_day,
    MAX(quality_status) AS quality_status,
    'Performance coverage is authoritative for native trace presence; Sessions flags are not used as a substitute.' AS quality_note
  FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`
  WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos, endpoint, platform, app_package
), sessions_coverage AS (
  SELECT 'android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package,
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos, COUNT(*) AS source_record_count,
    COUNT(DISTINCT session_id) AS distinct_session_count, MAX(event_timestamp) AS data_cutoff_at
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos
  UNION ALL
  SELECT 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', DATE(event_timestamp, 'Africa/Lagos'), COUNT(*), COUNT(DISTINCT session_id), MAX(event_timestamp)
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos
  UNION ALL
  SELECT 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', DATE(event_timestamp, 'Africa/Lagos'), COUNT(*), COUNT(DISTINCT session_id), MAX(event_timestamp)
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos
), crashlytics_coverage AS (
  SELECT
    metric_date_lagos, endpoint, platform, app_package,
    'firebase_crashlytics' AS source_name,
    crashlytics_export_record_count AS source_record_count,
    CAST(NULL AS INT64) AS distinct_session_count,
    CAST(NULL AS INT64) AS session_start_event_count,
    CAST(NULL AS INT64) AS event_name_count,
    data_cutoff_at,
    complete_day,
    quality_status,
    quality_note
  FROM `wajenigeria.waje_device_performance_mart.mart_stability_daily`
  WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date
)
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  source_name,
  source_record_count,
  distinct_session_count,
  session_start_event_count,
  event_name_count,
  data_cutoff_at,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), data_cutoff_at, MINUTE) AS source_freshness_lag_minutes,
  complete_day,
  quality_status,
  quality_note,
  'v1' AS metric_definition_version,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM analytics_coverage
UNION ALL
SELECT
  metric_date_lagos, endpoint, platform, app_package, source_name, source_record_count,
  distinct_session_count, session_start_event_count, event_name_count, data_cutoff_at,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), data_cutoff_at, MINUTE), complete_day,
  quality_status, quality_note, 'v1', CURRENT_TIMESTAMP()
FROM performance_coverage
UNION ALL
SELECT
  metric_date_lagos, endpoint, platform, app_package, 'firebase_sessions', source_record_count,
  distinct_session_count, CAST(NULL AS INT64), CAST(NULL AS INT64), data_cutoff_at,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), data_cutoff_at, MINUTE),
  metric_date_lagos < CURRENT_DATE('Africa/Lagos'),
  'provisional',
  'Distinct session count is valid only within Firebase Sessions and is not cross-end comparable to Analytics session_start.',
  'v1', CURRENT_TIMESTAMP()
FROM sessions_coverage
UNION ALL
SELECT
  metric_date_lagos, endpoint, platform, app_package, source_name, source_record_count,
  distinct_session_count, session_start_event_count, event_name_count, data_cutoff_at,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), data_cutoff_at, MINUTE), complete_day,
  quality_status, quality_note, 'v1', CURRENT_TIMESTAMP()
FROM crashlytics_coverage;

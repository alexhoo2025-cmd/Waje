-- 15-minute freshness diagnostic. It is a source-lag monitor until observed source lag is consistently below 45 minutes.
DECLARE refresh_start_timestamp TIMESTAMP DEFAULT TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 72 HOUR);

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.mart_native_performance_15m` (
  bucket_start_utc TIMESTAMP NOT NULL,
  endpoint STRING NOT NULL,
  platform STRING NOT NULL,
  app_package STRING NOT NULL,
  app_version STRING NOT NULL,
  trace_category STRING NOT NULL,
  performance_record_count INT64 NOT NULL,
  duration_trace_count INT64 NOT NULL,
  network_request_count INT64 NOT NULL,
  network_response_count INT64 NOT NULL,
  network_success_count INT64 NOT NULL,
  latest_event_timestamp TIMESTAMP,
  source_freshness_lag_minutes INT64,
  freshness_status STRING NOT NULL,
  metric_definition_version STRING NOT NULL,
  refreshed_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(bucket_start_utc)
CLUSTER BY endpoint, app_package, app_version, trace_category
OPTIONS(description = 'Aggregate-only 15-minute native Performance freshness diagnostic. Do not treat as real-time product performance when freshness_status is delayed.');

DELETE FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_15m`
WHERE bucket_start_utc >= refresh_start_timestamp;

INSERT INTO `wajenigeria.waje_device_performance_mart.mart_native_performance_15m`
WITH raw_performance AS (
  SELECT 'android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package, event_timestamp, app_display_version, event_type, network_info.response_code AS response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID` WHERE event_timestamp >= refresh_start_timestamp
  UNION ALL
  SELECT 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', event_timestamp, app_display_version, event_type, network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID` WHERE event_timestamp >= refresh_start_timestamp
  UNION ALL
  SELECT 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', event_timestamp, app_display_version, event_type, network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID` WHERE event_timestamp >= refresh_start_timestamp
  UNION ALL
  SELECT 'ios_existing', 'iOS', 'com.wajegame.wajegame', event_timestamp, app_display_version, event_type, network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS` WHERE event_timestamp >= refresh_start_timestamp
)
SELECT
  TIMESTAMP_SECONDS(DIV(UNIX_SECONDS(event_timestamp), 900) * 900) AS bucket_start_utc,
  endpoint,
  platform,
  app_package,
  COALESCE(NULLIF(app_display_version, ''), 'unknown') AS app_version,
  CASE event_type
    WHEN 'DURATION_TRACE' THEN 'duration_trace'
    WHEN 'SCREEN_TRACE' THEN 'screen_trace'
    WHEN 'NETWORK_REQUEST' THEN 'network_request'
    WHEN 'TRACE_METRIC' THEN 'trace_metric'
    ELSE 'other'
  END AS trace_category,
  COUNT(*) AS performance_record_count,
  COUNTIF(event_type = 'DURATION_TRACE') AS duration_trace_count,
  COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
  COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL) AS network_response_count,
  COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399) AS network_success_count,
  MAX(event_timestamp) AS latest_event_timestamp,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(event_timestamp), MINUTE) AS source_freshness_lag_minutes,
  IF(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(event_timestamp), MINUTE) <= 45, 'fresh', 'delayed') AS freshness_status,
  'v1' AS metric_definition_version,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM raw_performance
GROUP BY bucket_start_utc, endpoint, platform, app_package, app_version, trace_category;

-- Admin-run 15-minute diagnostic query. It emits aggregate freshness/volume only.
DECLARE refresh_start_timestamp TIMESTAMP DEFAULT TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR);

CREATE OR REPLACE TABLE `wajenigeria.waje_device_performance_mart.mart_native_performance_15m`
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, event_bucket
AS
WITH source AS (
  SELECT 'android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package, event_timestamp, event_type, network_info.response_code AS response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE event_timestamp >= refresh_start_timestamp
  UNION ALL
  SELECT 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', event_timestamp, event_type, network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE event_timestamp >= refresh_start_timestamp
  UNION ALL
  SELECT 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', event_timestamp, event_type, network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE event_timestamp >= refresh_start_timestamp
  UNION ALL
  SELECT 'ios_existing', 'iOS', 'com.wajegame.wajegame', event_timestamp, event_type, network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS`
  WHERE event_timestamp >= refresh_start_timestamp
)
SELECT
  DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
  TIMESTAMP_SECONDS(DIV(UNIX_SECONDS(event_timestamp), 900) * 900) AS bucket_start_at,
  endpoint,
  platform,
  app_package,
  event_type AS event_bucket,
  COUNT(*) AS performance_record_count,
  COUNTIF(response_code IS NOT NULL) AS response_code_count,
  COUNTIF(response_code BETWEEN 200 AND 399) AS network_success_count,
  MAX(event_timestamp) AS data_cutoff_at,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM source
GROUP BY metric_date_lagos, bucket_start_at, endpoint, platform, app_package, event_bucket;

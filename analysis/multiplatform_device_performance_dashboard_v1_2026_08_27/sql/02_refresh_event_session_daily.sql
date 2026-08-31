-- D+1 rolling refresh: 30 Lagos business days. Run after 01_create_dimensions.sql.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.mart_event_session_daily` (
  metric_date_lagos DATE NOT NULL,
  endpoint STRING NOT NULL,
  platform STRING NOT NULL,
  app_package STRING NOT NULL,
  firebase_stream_id STRING,
  app_version STRING NOT NULL,
  event_name STRING NOT NULL,
  event_category STRING NOT NULL,
  core_role STRING NOT NULL,
  include_in_engagement BOOL NOT NULL,
  include_in_client_behavior_funnel BOOL NOT NULL,
  event_count INT64 NOT NULL,
  session_start_event_count INT64 NOT NULL,
  event_data_cutoff_at TIMESTAMP,
  complete_day BOOL NOT NULL,
  quality_status STRING NOT NULL,
  metric_definition_version STRING NOT NULL,
  source_name STRING NOT NULL,
  refreshed_at TIMESTAMP NOT NULL
)
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, app_version, event_category
OPTIONS(description = 'Aggregate-only cross-platform Firebase Analytics event and session-start facts. session_start is an event count, not a unique-session count.');

DELETE FROM `wajenigeria.waje_device_performance_mart.mart_event_session_daily`
WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date;

INSERT INTO `wajenigeria.waje_device_performance_mart.mart_event_session_daily`
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS metric_date_lagos,
    'h5' AS endpoint,
    'H5' AS platform,
    'waje_ng_firebase_h5' AS app_package,
    stream_id AS firebase_stream_id,
    'unknown' AS app_version,
    event_name,
    event_timestamp
  FROM `wajenigeria.waje_ng_firebase_h5.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)

  UNION ALL

  SELECT
    PARSE_DATE('%Y%m%d', _TABLE_SUFFIX),
    'ios_existing',
    'iOS',
    COALESCE(NULLIF(app_info.id, ''), 'com.wajegame.wajegame'),
    stream_id,
    COALESCE(NULLIF(app_info.version, ''), 'unknown'),
    event_name,
    event_timestamp
  FROM `wajenigeria.waje_ng_firebase_ios.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)

  UNION ALL

  SELECT
    PARSE_DATE('%Y%m%d', event_date),
    CASE app_info.id
      WHEN 'com.hfhy.waje.special' THEN 'android_main'
      WHEN 'com.hfhy.wajecasino.palmgame' THEN 'android_transsion_old'
      WHEN 'com.hfhy.wajecasino.game' THEN 'android_transsion_new'
      ELSE 'android_unmapped'
    END,
    'Android',
    COALESCE(NULLIF(app_info.id, ''), 'unknown'),
    stream_id,
    COALESCE(NULLIF(app_info.version, ''), 'unknown'),
    event_name,
    event_timestamp
  FROM `wajenigeria.waje_ng_firebase_android.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)
)
SELECT
  raw.metric_date_lagos,
  raw.endpoint,
  raw.platform,
  raw.app_package,
  raw.firebase_stream_id,
  raw.app_version,
  raw.event_name,
  COALESCE(taxonomy.event_category, 'unclassified') AS event_category,
  COALESCE(taxonomy.core_role, 'unclassified') AS core_role,
  COALESCE(taxonomy.include_in_engagement, FALSE) AS include_in_engagement,
  COALESCE(taxonomy.include_in_client_behavior_funnel, FALSE) AS include_in_client_behavior_funnel,
  COUNT(*) AS event_count,
  COUNTIF(raw.event_name = 'session_start') AS session_start_event_count,
  MAX(TIMESTAMP_MICROS(raw.event_timestamp)) AS event_data_cutoff_at,
  raw.metric_date_lagos < CURRENT_DATE('Africa/Lagos') AS complete_day,
  CASE
    WHEN raw.endpoint = 'h5' THEN 'provisional_behavior_only'
    WHEN raw.metric_date_lagos >= CURRENT_DATE('Africa/Lagos') - 6 THEN 'immature'
    ELSE 'provisional'
  END AS quality_status,
  'v1' AS metric_definition_version,
  'firebase_analytics' AS source_name,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM raw_events AS raw
LEFT JOIN `wajenigeria.waje_device_performance_mart.dim_event_taxonomy` AS taxonomy
  USING (event_name)
GROUP BY
  metric_date_lagos, endpoint, platform, app_package, firebase_stream_id, app_version,
  event_name, event_category, core_role, include_in_engagement,
  include_in_client_behavior_funnel, complete_day, quality_status;

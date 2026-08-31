-- Admin-run scheduled query. Client event counts and Sessions counts remain separate measures.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE OR REPLACE TABLE `wajenigeria.waje_device_performance_mart.mart_event_session_daily`
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, app_version, event_category
AS
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS metric_date_lagos,
    CASE app_info.id WHEN 'com.hfhy.waje.special' THEN 'android_main' WHEN 'com.hfhy.wajecasino.palmgame' THEN 'android_transsion_old' WHEN 'com.hfhy.wajecasino.game' THEN 'android_transsion_new' ELSE 'android_unmapped' END AS endpoint,
    'Android' AS platform,
    COALESCE(NULLIF(app_info.id, ''), 'unknown') AS app_package,
    COALESCE(NULLIF(app_info.version, ''), 'unknown') AS app_version,
    event_name,
    event_timestamp
  FROM `wajenigeria.waje_ng_firebase_android.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)
    AND platform = 'ANDROID'
    AND app_info.id IN ('com.hfhy.waje.special', 'com.hfhy.wajecasino.palmgame', 'com.hfhy.wajecasino.game')

  UNION ALL
  SELECT PARSE_DATE('%Y%m%d', _TABLE_SUFFIX), 'ios_existing', 'iOS', COALESCE(NULLIF(app_info.id, ''), 'com.wajegame.wajegame'), COALESCE(NULLIF(app_info.version, ''), 'unknown'), event_name, event_timestamp
  FROM `wajenigeria.waje_ng_firebase_ios.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)

  UNION ALL
  SELECT PARSE_DATE('%Y%m%d', _TABLE_SUFFIX), 'h5', 'H5', 'waje_ng_firebase_h5', 'unknown', event_name, event_timestamp
  FROM `wajenigeria.waje_ng_firebase_h5.events_*`
  WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', refresh_start_date) AND FORMAT_DATE('%Y%m%d', refresh_end_date)
), classified AS (
  SELECT
    metric_date_lagos,
    endpoint,
    platform,
    app_package,
    app_version,
    event_name,
    event_timestamp,
    CASE
      WHEN STARTS_WITH(LOWER(event_name), 'notification') THEN 'notification'
      WHEN event_name IN ('session_start', 'first_open', 'first_visit') THEN 'lifecycle'
      WHEN REGEXP_CONTAINS(LOWER(event_name), r'(register|recharge|withdraw|firstcharge)') THEN 'business_behavior'
      WHEN event_name IN ('screen_view', 'page_view', 'user_engagement') THEN 'engagement'
      ELSE 'other'
    END AS event_category
  FROM raw_events
)
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  app_version,
  event_name,
  event_category,
  COUNT(*) AS event_count,
  COUNTIF(event_name = 'session_start') AS session_start_event_count,
  MAX(TIMESTAMP_MICROS(event_timestamp)) AS event_data_cutoff_at,
  metric_date_lagos < CURRENT_DATE('Africa/Lagos') AS complete_day,
  CASE WHEN metric_date_lagos >= CURRENT_DATE('Africa/Lagos') - 6 THEN 'immature' ELSE 'provisional' END AS quality_status,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM classified
GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version, event_name, event_category;

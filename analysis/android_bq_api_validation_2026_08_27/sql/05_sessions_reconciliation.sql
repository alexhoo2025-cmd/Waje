-- Android Sessions reconciliation. session_id is used only inside COUNT(DISTINCT) and never returned.
WITH sessions AS (
  SELECT
    'android_main' AS endpoint,
    'com.hfhy.waje.special' AS app_package,
    event_timestamp,
    session_id,
    performance_data_collection_enabled,
    crashlytics_data_collection_enabled
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'

  UNION ALL

  SELECT
    'android_transsion_old',
    'com.hfhy.wajecasino.palmgame',
    event_timestamp,
    session_id,
    performance_data_collection_enabled,
    crashlytics_data_collection_enabled
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'

  UNION ALL

  SELECT
    'android_transsion_new',
    'com.hfhy.wajecasino.game',
    event_timestamp,
    session_id,
    performance_data_collection_enabled,
    crashlytics_data_collection_enabled
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
), grouped AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint,
    app_package,
    COUNT(*) AS session_record_count,
    COUNT(DISTINCT session_id) AS distinct_session_count,
    COUNTIF(performance_data_collection_enabled IS TRUE) AS performance_flag_true_count,
    COUNTIF(crashlytics_data_collection_enabled IS TRUE) AS crashlytics_flag_true_count,
    MAX(event_timestamp) AS data_cutoff_at
  FROM sessions
  GROUP BY metric_date_lagos, endpoint, app_package
)
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  session_record_count,
  distinct_session_count,
  SAFE_DIVIDE(performance_flag_true_count, session_record_count) AS performance_flag_share,
  SAFE_DIVIDE(crashlytics_flag_true_count, session_record_count) AS crashlytics_flag_share,
  data_cutoff_at,
  IF(
    performance_flag_true_count = 0 AND session_record_count > 0,
    'quality_warning_check_performance_table',
    'observed'
  ) AS quality_status
FROM grouped
ORDER BY metric_date_lagos, endpoint
LIMIT 3000;

-- Compact Android Sessions window summary. session_id is only used inside
-- COUNT(DISTINCT) and is never returned.
WITH sessions AS (
  SELECT 'android_main' AS endpoint, 'com.hfhy.waje.special' AS app_package, event_timestamp, session_id, performance_data_collection_enabled, crashlytics_data_collection_enabled
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__SESSIONS_START__' AND DATE '__SESSIONS_END__'
  UNION ALL
  SELECT 'android_transsion_old', 'com.hfhy.wajecasino.palmgame', event_timestamp, session_id, performance_data_collection_enabled, crashlytics_data_collection_enabled
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__SESSIONS_START__' AND DATE '__SESSIONS_END__'
  UNION ALL
  SELECT 'android_transsion_new', 'com.hfhy.wajecasino.game', event_timestamp, session_id, performance_data_collection_enabled, crashlytics_data_collection_enabled
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__SESSIONS_START__' AND DATE '__SESSIONS_END__'
)
SELECT
  endpoint,
  app_package,
  COUNT(DISTINCT session_id) AS distinct_session_count,
  COUNT(*) AS session_event_count,
  SAFE_DIVIDE(COUNTIF(performance_data_collection_enabled), COUNT(*)) AS performance_collection_flag_share,
  SAFE_DIVIDE(COUNTIF(crashlytics_data_collection_enabled), COUNT(*)) AS crashlytics_collection_flag_share
FROM sessions
GROUP BY endpoint, app_package
ORDER BY endpoint
LIMIT 500;

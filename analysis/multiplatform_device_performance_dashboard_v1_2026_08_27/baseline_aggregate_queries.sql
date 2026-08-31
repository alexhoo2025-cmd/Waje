-- Reviewed aggregate-only baseline queries. Execute each statement separately in europe-west4.
-- Do not add user, device, URL, request body, response body, stack or order fields.

-- A. Android/iOS native Performance coverage by package.
SELECT 'android_main' AS endpoint, MIN(DATE(event_timestamp, 'Africa/Lagos')) AS first_day, MAX(DATE(event_timestamp, 'Africa/Lagos')) AS last_day, COUNT(*) AS performance_record_count, COUNTIF(event_type = 'DURATION_TRACE') AS duration_trace_count, COUNTIF(event_type = 'SCREEN_TRACE') AS screen_trace_count, COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count, COUNT(DISTINCT app_display_version) AS app_version_count
FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-13' AND DATE '2026-08-27'
UNION ALL
SELECT 'android_transsion_old', MIN(DATE(event_timestamp, 'Africa/Lagos')), MAX(DATE(event_timestamp, 'Africa/Lagos')), COUNT(*), COUNTIF(event_type = 'DURATION_TRACE'), COUNTIF(event_type = 'SCREEN_TRACE'), COUNTIF(event_type = 'NETWORK_REQUEST'), COUNT(DISTINCT app_display_version)
FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-13' AND DATE '2026-08-27'
UNION ALL
SELECT 'android_transsion_new', MIN(DATE(event_timestamp, 'Africa/Lagos')), MAX(DATE(event_timestamp, 'Africa/Lagos')), COUNT(*), COUNTIF(event_type = 'DURATION_TRACE'), COUNTIF(event_type = 'SCREEN_TRACE'), COUNTIF(event_type = 'NETWORK_REQUEST'), COUNT(DISTINCT app_display_version)
FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-13' AND DATE '2026-08-27'
UNION ALL
SELECT 'ios_existing', MIN(DATE(event_timestamp, 'Africa/Lagos')), MAX(DATE(event_timestamp, 'Africa/Lagos')), COUNT(*), COUNTIF(event_type = 'DURATION_TRACE'), COUNTIF(event_type = 'SCREEN_TRACE'), COUNTIF(event_type = 'NETWORK_REQUEST'), COUNT(DISTINCT app_display_version)
FROM `wajenigeria.waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS`
WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-13' AND DATE '2026-08-27';

-- B. H5 Firebase event coverage and dictionary.
SELECT event_name, COUNT(*) AS event_count, COUNT(DISTINCT _TABLE_SUFFIX) AS covered_days
FROM `wajenigeria.waje_ng_firebase_h5.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260814' AND '20260821'
GROUP BY event_name
ORDER BY event_count DESC;

-- C. Android Firebase Sessions coverage. Session IDs are counted only inside the aggregate.
SELECT 'android_main' AS endpoint, COUNT(DISTINCT session_id) AS distinct_session_count, SAFE_DIVIDE(COUNTIF(performance_data_collection_enabled), COUNT(*)) AS performance_collection_flag_share, SAFE_DIVIDE(COUNTIF(crashlytics_data_collection_enabled), COUNT(*)) AS crashlytics_collection_flag_share
FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID`
WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-18' AND DATE '2026-08-26'
UNION ALL
SELECT 'android_transsion_old', COUNT(DISTINCT session_id), SAFE_DIVIDE(COUNTIF(performance_data_collection_enabled), COUNT(*)), SAFE_DIVIDE(COUNTIF(crashlytics_data_collection_enabled), COUNT(*))
FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID`
WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-18' AND DATE '2026-08-26'
UNION ALL
SELECT 'android_transsion_new', COUNT(DISTINCT session_id), SAFE_DIVIDE(COUNTIF(performance_data_collection_enabled), COUNT(*)), SAFE_DIVIDE(COUNTIF(crashlytics_data_collection_enabled), COUNT(*))
FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID`
WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-18' AND DATE '2026-08-26';

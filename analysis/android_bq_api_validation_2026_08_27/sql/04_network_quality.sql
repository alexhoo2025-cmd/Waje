-- Android NETWORK_REQUEST quality and latency. No URL or request name is returned.
WITH raw_requests AS (
  SELECT
    'android_main' AS endpoint,
    'com.hfhy.waje.special' AS app_package,
    event_timestamp,
    COALESCE(NULLIF(app_display_version, ''), 'unknown') AS app_version,
    network_info.response_code AS response_code,
    SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0) AS response_completed_ms
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
    AND event_type = 'NETWORK_REQUEST'

  UNION ALL

  SELECT
    'android_transsion_old',
    'com.hfhy.wajecasino.palmgame',
    event_timestamp,
    COALESCE(NULLIF(app_display_version, ''), 'unknown'),
    network_info.response_code,
    SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0)
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
    AND event_type = 'NETWORK_REQUEST'

  UNION ALL

  SELECT
    'android_transsion_new',
    'com.hfhy.wajecasino.game',
    event_timestamp,
    COALESCE(NULLIF(app_display_version, ''), 'unknown'),
    network_info.response_code,
    SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0)
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
    AND event_type = 'NETWORK_REQUEST'
), grouped AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint,
    app_package,
    app_version,
    COUNT(*) AS network_request_count,
    COUNTIF(response_code IS NOT NULL) AS response_code_count,
    COUNTIF(response_code IS NULL) AS missing_response_code_count,
    COUNTIF(response_code BETWEEN 200 AND 399) AS network_success_count,
    COUNTIF(response_code >= 400) AS http_error_count,
    COUNTIF(response_completed_ms >= 0) AS latency_sample_count,
    IF(
      COUNTIF(response_completed_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(response_completed_ms >= 0, response_completed_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(90)],
      NULL
    ) AS network_p90_ms,
    MAX(event_timestamp) AS data_cutoff_at
  FROM raw_requests
  GROUP BY metric_date_lagos, endpoint, app_package, app_version
  HAVING COUNT(*) >= 10
)
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  app_version,
  network_request_count,
  response_code_count,
  missing_response_code_count,
  SAFE_DIVIDE(missing_response_code_count, network_request_count) AS missing_response_code_rate,
  network_success_count,
  http_error_count,
  SAFE_DIVIDE(network_success_count, response_code_count) AS network_success_rate,
  latency_sample_count,
  network_p90_ms,
  data_cutoff_at,
  IF(latency_sample_count >= 500, 'p90_eligible', 'p90_sample_too_small') AS quality_status
FROM grouped
ORDER BY metric_date_lagos, endpoint, app_version
LIMIT 3000;

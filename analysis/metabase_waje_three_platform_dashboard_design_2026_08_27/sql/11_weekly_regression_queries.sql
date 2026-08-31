-- Read-only weekly regression query. P90 is recalculated from raw events in BigQuery;
-- it is never averaged from daily P90 values.
DECLARE current_start DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 7 DAY);
DECLARE current_end DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);
DECLARE prior_start DATE DEFAULT DATE_SUB(current_start, INTERVAL 7 DAY);
DECLARE prior_end DATE DEFAULT DATE_SUB(current_start, INTERVAL 1 DAY);

WITH raw AS (
  SELECT 'android_main' AS endpoint, 'com.hfhy.waje.special' AS app_package, event_timestamp, event_type, SAFE_DIVIDE(trace_info.duration_us, 1000.0) AS duration_ms, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0) AS network_ms, network_info.response_code AS response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN prior_start AND current_end
  UNION ALL
  SELECT 'android_transsion_old', 'com.hfhy.wajecasino.palmgame', event_timestamp, event_type, SAFE_DIVIDE(trace_info.duration_us, 1000.0), SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN prior_start AND current_end
  UNION ALL
  SELECT 'android_transsion_new', 'com.hfhy.wajecasino.game', event_timestamp, event_type, SAFE_DIVIDE(trace_info.duration_us, 1000.0), SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN prior_start AND current_end
), periods AS (
  SELECT 'current_7d' AS period, endpoint, app_package, duration_ms, network_ms, response_code, event_type
  FROM raw
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN current_start AND current_end
  UNION ALL
  SELECT 'prior_7d', endpoint, app_package, duration_ms, network_ms, response_code, event_type
  FROM raw
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN prior_start AND prior_end
)
SELECT
  period,
  endpoint,
  app_package,
  COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) AS duration_sample_count,
  IF(COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) >= 500, APPROX_QUANTILES(IF(event_type = 'DURATION_TRACE' AND duration_ms >= 0, duration_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(90)], NULL) AS duration_p90_ms,
  COUNTIF(event_type = 'NETWORK_REQUEST' AND network_ms >= 0) AS network_sample_count,
  IF(COUNTIF(event_type = 'NETWORK_REQUEST' AND network_ms >= 0) >= 500, APPROX_QUANTILES(IF(event_type = 'NETWORK_REQUEST' AND network_ms >= 0, network_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(90)], NULL) AS network_p90_ms,
  SAFE_DIVIDE(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399), COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL)) AS network_success_rate,
  IF(period = 'current_7d', current_start, prior_start) AS period_start,
  IF(period = 'current_7d', current_end, prior_end) AS period_end,
  CASE WHEN COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) < 500 OR COUNTIF(event_type = 'NETWORK_REQUEST' AND network_ms >= 0) < 500 THEN 'immature_for_full_p90_comparison' ELSE 'eligible' END AS quality_status
FROM periods
GROUP BY period, endpoint, app_package, period_start, period_end
ORDER BY period, endpoint
LIMIT 3000;

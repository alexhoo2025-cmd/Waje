-- Read-only downstream aggregate from the native performance mart.
CREATE OR REPLACE TABLE `wajenigeria.waje_device_performance_mart.mart_network_quality_daily`
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, app_version
AS
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  app_version,
  SUM(network_request_count) AS network_request_count,
  SUM(network_response_count) AS network_response_count,
  SUM(network_success_count) AS network_success_count,
  SUM(network_request_count - network_response_count) AS missing_response_code_count,
  SAFE_DIVIDE(SUM(network_success_count), SUM(network_response_count)) AS network_success_rate,
  COUNTIF(network_p90_ms IS NOT NULL) AS p90_eligible_dimension_count,
  MIN(network_p90_ms) AS network_p90_min_ms,
  MAX(network_p90_ms) AS network_p90_max_ms,
  MAX(data_cutoff_at) AS data_cutoff_at,
  LOGICAL_AND(complete_day) AS complete_day,
  CASE WHEN COUNTIF(network_p90_ms IS NOT NULL) = 0 THEN 'p90_unavailable' WHEN LOGICAL_AND(complete_day) THEN 'provisional' ELSE 'immature' END AS quality_status,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`
WHERE metric_date_lagos BETWEEN DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY) AND DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY)
GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version;

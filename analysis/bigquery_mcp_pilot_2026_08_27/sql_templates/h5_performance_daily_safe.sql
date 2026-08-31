-- TEMPLATE ONLY: activate the authorized view before execution.
SELECT
  event_date,
  page_id,
  web_version,
  device_tier,
  browser,
  network_type,
  SUM(sample_size) AS sample_size,
  AVG(p50_load_ms) AS p50_load_ms,
  AVG(p95_load_ms) AS p95_load_ms,
  AVG(error_rate) AS error_rate,
  MAX(data_cutoff) AS data_cutoff,
  LOGICAL_AND(complete_day) AS complete_day
FROM `wajenigeria.agent_analytics.vw_h5_performance_daily_safe`
WHERE event_date BETWEEN @start_date AND @end_date
GROUP BY event_date, page_id, web_version, device_tier, browser, network_type
HAVING SUM(sample_size) >= 10
LIMIT 3000;

-- Read-only quality checks for Metabase pre-publish validation.
WITH expected_dates AS (
  SELECT day AS metric_date_lagos
  FROM UNNEST(GENERATE_DATE_ARRAY(DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 7 DAY), DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY))) AS day
), observed AS (
  SELECT metric_date_lagos, endpoint, COUNT(*) AS row_count
  FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`
  WHERE metric_date_lagos BETWEEN DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY)
  GROUP BY metric_date_lagos, endpoint
)
SELECT
  dates.metric_date_lagos,
  endpoints.endpoint,
  COALESCE(observed.row_count, 0) AS aggregate_row_count,
  CASE WHEN observed.row_count IS NULL THEN 'data_gap' ELSE 'observed' END AS quality_status
FROM expected_dates AS dates
CROSS JOIN UNNEST(['android_main', 'android_transsion_old', 'android_transsion_new', 'ios_existing']) AS endpoints(endpoint)
LEFT JOIN observed USING (metric_date_lagos, endpoint)
ORDER BY dates.metric_date_lagos, endpoints.endpoint
LIMIT 3000;

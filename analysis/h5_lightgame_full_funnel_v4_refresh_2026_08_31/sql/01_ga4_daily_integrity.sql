SELECT
  PARSE_DATE('%Y%m%d', event_date) AS stat_date,
  COUNT(*) AS event_rows,
  COUNT(DISTINCT event_name) AS event_types,
  APPROX_COUNT_DISTINCT(user_pseudo_id) AS users,
  COUNTIF(platform != 'WEB') AS non_web_rows,
  COUNTIF(event_timestamp IS NULL) AS missing_timestamp_rows
FROM `waje-analytics-readonly.analytics_504208609.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
GROUP BY stat_date
ORDER BY stat_date;

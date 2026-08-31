SELECT
  event_date,
  COUNT(*) AS event_count,
  COUNT(DISTINCT event_name) AS event_types,
  COUNTIF(event_timestamp IS NULL) AS null_timestamp_events,
  COUNTIF(platform != 'WEB' OR platform IS NULL) AS non_web_events,
  COUNTIF(stream_id IS NULL OR stream_id = '') AS missing_stream_events,
  COUNTIF(device.category IS NULL OR device.category = '') AS missing_device_category_events,
  COUNTIF(device.operating_system IS NULL OR device.operating_system = '') AS missing_os_events,
  COUNTIF(COALESCE(device.web_info.browser, device.browser) IS NULL) AS missing_browser_events,
  COUNTIF(geo.country IS NULL OR geo.country = '') AS missing_country_events
FROM `waje-analytics-readonly.analytics_504208609.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
GROUP BY event_date
ORDER BY event_date;

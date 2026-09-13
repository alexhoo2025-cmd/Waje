WITH events AS (
 SELECT target_day AS cohort_date,app_id,user_id,client_type,event_type,custom,
  timezone_offset,SAFE_CAST(time AS INT64) AS event_time_number
 FROM `wajenigeria.origin_hfyl.view_event_client`
 WHERE target_day BETWEEN DATE '2026-09-01' AND DATE '2026-09-03'
), counters AS (
 SELECT cohort_date,app_id,client_type,event_type,
 COUNT(*) AS events,COUNT(DISTINCT user_id) AS users,
 COUNTIF(custom IS NOT NULL AND custom NOT IN ('','{}','null')) AS with_custom,
 COUNTIF(JSON_VALUE(custom,'$.is_pwa') IS NOT NULL) AS is_pwa_count,
 COUNTIF(JSON_VALUE(custom,'$.display_mode') IS NOT NULL) AS display_mode_count,
 COUNTIF(JSON_VALUE(custom,'$.standalone') IS NOT NULL) AS standalone_count,
 COUNTIF(JSON_VALUE(custom,'$.is_webview') IS NOT NULL) AS webview_count,
 MIN(timezone_offset) AS min_timezone_offset,MAX(timezone_offset) AS max_timezone_offset,
 COUNTIF(event_time_number BETWEEN 1788220800000 AND 1788566400000) AS timestamp_millis_in_window
 FROM events
 WHERE cohort_date BETWEEN DATE '2026-09-01' AND DATE '2026-09-03'
 GROUP BY cohort_date,app_id,client_type,event_type
 HAVING COUNT(DISTINCT user_id)>=10
)
SELECT cohort_date,app_id,client_type,event_type,events,users,with_custom,is_pwa_count,display_mode_count,standalone_count,webview_count,min_timezone_offset,max_timezone_offset,timestamp_millis_in_window
FROM counters
ORDER BY events DESC
LIMIT 3000;

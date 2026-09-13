SELECT
  table_name,
  SAFE.PARSE_DATE('%Y%m%d', partition_id) AS biz_date,
  SUM(total_rows) AS total_rows,
  MAX(last_modified_time) AS last_modified_time
FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'realtime_event_server'
  AND SAFE.PARSE_DATE('%Y%m%d', partition_id) BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
GROUP BY 1,2
ORDER BY biz_date
LIMIT 100;

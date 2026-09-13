SELECT table_name, SAFE.PARSE_DATE('%Y%m%d', partition_id) AS partition_date,
SUM(total_rows) AS total_rows, MAX(last_modified_time) AS last_modified_time
FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name IN ('realtime_event_server','realtime_event_client','realtime_event_web','user_events')
AND SAFE.PARSE_DATE('%Y%m%d', partition_id) BETWEEN DATE '2026-08-01' AND DATE '2026-09-09'
GROUP BY table_name, partition_date
ORDER BY table_name, partition_date
LIMIT 200;

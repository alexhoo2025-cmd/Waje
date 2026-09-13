SELECT table_name, partition_id, total_rows, total_logical_bytes, last_modified_time
FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name IN ('realtime_event_server','realtime_event_client','realtime_event_web','user_xlid','realtime_edw_user_version_daily')
  AND (partition_id BETWEEN '20260801' AND '20260908' OR partition_id IS NULL)
ORDER BY table_name,partition_id
LIMIT 1000;

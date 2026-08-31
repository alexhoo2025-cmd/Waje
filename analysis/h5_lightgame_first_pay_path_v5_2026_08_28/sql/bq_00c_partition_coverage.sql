SELECT
  partition_id,
  total_rows,
  total_logical_bytes,
  last_modified_time
FROM `wajenigeria.pubwaje.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'user_events'
ORDER BY partition_id;


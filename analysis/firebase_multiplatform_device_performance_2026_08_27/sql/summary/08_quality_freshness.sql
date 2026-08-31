-- Compact Firebase table/schema metadata. No business rows.
SELECT
  t.table_schema AS dataset_id,
  t.table_name,
  t.table_type,
  t.creation_time,
  COUNT(c.field_path) AS field_path_count
FROM `wajenigeria`.`region-europe-west4`.INFORMATION_SCHEMA.TABLES AS t
LEFT JOIN `wajenigeria`.`region-europe-west4`.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS AS c
  ON c.table_schema = t.table_schema AND c.table_name = t.table_name
WHERE STARTS_WITH(t.table_schema, 'waje_ng_firebase_')
GROUP BY t.table_schema, t.table_name, t.table_type, t.creation_time
ORDER BY t.table_schema, t.table_name
LIMIT 500;

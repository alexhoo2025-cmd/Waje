-- Metadata-only check. Run in europe-west4 after BigQuery API authentication is restored.
SELECT
  table_schema,
  table_name,
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM `wajenigeria`.`region-europe-west4`.INFORMATION_SCHEMA.COLUMNS
WHERE table_schema IN (
  'waje_ng_firebase_android',
  'waje_ng_firebase_android_performance',
  'waje_ng_firebase_android_sessions'
)
ORDER BY table_schema, table_name, ordinal_position
LIMIT 3000;

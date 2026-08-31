-- Metadata-only API smoke test. Execute in europe-west4.
SELECT
  table_schema,
  COUNT(*) AS column_count
FROM `wajenigeria`.`region-europe-west4`.INFORMATION_SCHEMA.COLUMNS
WHERE table_schema IN (
  'waje_ng_firebase_android',
  'waje_ng_firebase_android_performance',
  'waje_ng_firebase_android_sessions'
)
GROUP BY table_schema
ORDER BY table_schema
LIMIT 100;

-- Compact Firebase source inventory. Metadata only; no business rows.
SELECT
  table_schema AS dataset_id,
  COUNT(*) AS object_count,
  COUNTIF(table_type = 'BASE TABLE') AS base_table_count,
  COUNTIF(table_type = 'VIEW') AS view_count,
  COUNTIF(table_type = 'MATERIALIZED VIEW') AS materialized_view_count
FROM `wajenigeria`.`region-europe-west4`.INFORMATION_SCHEMA.TABLES
WHERE STARTS_WITH(table_schema, 'waje_ng_firebase_')
GROUP BY table_schema
ORDER BY table_schema
LIMIT 500;

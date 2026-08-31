-- Firebase-only metadata inventory for the enterprise Waje project.
-- No business rows or field values are read. The query is intentionally
-- regional so a missing Firebase dataset appears as an inventory result rather
-- than making the whole query fail on a guessed physical table name.
SELECT
  table_schema AS dataset_id,
  COUNT(*) AS object_count,
  COUNTIF(table_type = 'BASE TABLE') AS base_table_count,
  COUNTIF(table_type = 'VIEW') AS view_count,
  COUNTIF(table_type = 'MATERIALIZED VIEW') AS materialized_view_count,
  MIN(creation_time) AS first_object_created_at,
  MAX(creation_time) AS last_object_created_at
FROM `wajenigeria`.`region-europe-west4`.INFORMATION_SCHEMA.TABLES
WHERE STARTS_WITH(table_schema, 'waje_ng_firebase_')
GROUP BY table_schema
ORDER BY table_schema
LIMIT 500;

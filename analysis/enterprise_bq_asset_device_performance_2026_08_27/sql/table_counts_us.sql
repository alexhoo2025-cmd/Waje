-- Read-only metadata inventory: US datasets only.
SELECT '90006' AS dataset_id,
       COUNT(*) AS table_or_view_count,
       COUNTIF(table_type = 'BASE TABLE') AS base_table_count,
       COUNTIF(table_type = 'VIEW') AS view_count,
       COUNTIF(table_type = 'MATERIALIZED VIEW') AS materialized_view_count
FROM `wajenigeria.90006.INFORMATION_SCHEMA.TABLES`
UNION ALL
SELECT 'waje_ng_firebase_ios_imported_segments', COUNT(*),
       COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW')
FROM `wajenigeria.waje_ng_firebase_ios_imported_segments.INFORMATION_SCHEMA.TABLES`
ORDER BY dataset_id;

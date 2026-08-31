-- Read-only metadata inventory. Returns table names and field paths only; no table rows.
SELECT '90006' AS dataset_id, t.table_name, t.table_type, t.creation_time,
       c.field_path, c.data_type, c.description
FROM `wajenigeria.90006.INFORMATION_SCHEMA.TABLES` AS t
LEFT JOIN `wajenigeria.90006.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` AS c
USING (table_name)
UNION ALL
SELECT 'waje_ng_firebase_ios_imported_segments', t.table_name, t.table_type, t.creation_time,
       c.field_path, c.data_type, c.description
FROM `wajenigeria.waje_ng_firebase_ios_imported_segments.INFORMATION_SCHEMA.TABLES` AS t
LEFT JOIN `wajenigeria.waje_ng_firebase_ios_imported_segments.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` AS c
USING (table_name)
ORDER BY dataset_id, table_name, field_path;

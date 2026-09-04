-- Enterprise BigQuery metadata check for the H5 Firebase export.
-- Metadata only: table names and creation timestamps, no event rows.
SELECT
  table_name,
  table_type,
  creation_time
FROM `wajenigeria.waje_ng_firebase_h5.INFORMATION_SCHEMA.TABLES`
WHERE STARTS_WITH(table_name, 'events_')
ORDER BY table_name;

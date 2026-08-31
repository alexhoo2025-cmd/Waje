-- Read-only metadata and aggregate audit template.
-- Target: waje-analytics-readonly (BigQuery Sandbox).
-- This file is intentionally not executed by the restricted wajenigeria MCP.
-- First discover the actual Firebase Performance dataset/table names in the UI.

-- 1) Dataset/table inventory after export appears.
SELECT
  table_name,
  table_type,
  creation_time
FROM `waje-analytics-readonly.firebase_performance.INFORMATION_SCHEMA.TABLES`
ORDER BY table_name;

-- 2) Partition freshness and row volume.
SELECT
  table_name,
  partition_id,
  total_rows,
  total_logical_bytes
FROM `waje-analytics-readonly.firebase_performance.INFORMATION_SCHEMA.PARTITIONS`
WHERE partition_id IS NOT NULL
ORDER BY partition_id DESC, table_name;

-- 3) After get_table_info confirms the schema, replace only the documented
-- column names below. Do not SELECT * or return row-level device/app data.
-- SELECT event_date, app_id, event_type, COUNT(*) AS event_count
-- FROM `waje-analytics-readonly.firebase_performance.<verified_table>`
-- WHERE event_date BETWEEN DATE 'YYYY-MM-DD' AND DATE 'YYYY-MM-DD'
-- GROUP BY event_date, app_id, event_type
-- ORDER BY event_date, app_id, event_type;

-- 4) Compare daily aggregate volumes with the Firebase/Performance console
-- only after the table schema and timezone are confirmed. Flag data_gap,
-- delayed partitions, unknown app IDs, duplicates and missing versions.

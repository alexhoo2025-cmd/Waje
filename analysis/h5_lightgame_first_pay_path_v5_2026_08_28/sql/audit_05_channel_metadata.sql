SELECT
  table_schema,
  table_name,
  column_name,
  data_type
FROM `wajenigeria.region-europe-west4.INFORMATION_SCHEMA.COLUMNS`
WHERE REGEXP_CONTAINS(LOWER(column_name), r'(channel|media|campaign|package|source|client_type|device_type)')
  AND table_schema IN ('origin_hfyl', 'pubwaje', 'track_hfyl')
ORDER BY table_schema, table_name, column_name;

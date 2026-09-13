-- Design only: not executed. Metadata access must be restored first.
-- Current existence and semantic suitability of candidate views is NOT certified.
SELECT table_name, table_type, creation_time
FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.TABLES`
WHERE REGEXP_CONTAINS(LOWER(table_name), r'(game|bet|reward|event|user|order|pay|withdraw|asset)')
ORDER BY table_name;

SELECT table_name, column_name, data_type, is_nullable
FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.COLUMNS`
WHERE REGEXP_CONTAINS(LOWER(table_name), r'(game|bet|reward|event|user|order|pay|withdraw|asset)')
ORDER BY table_name, ordinal_position;

-- Metadata only. Run before any game-event data query.
SELECT
  table_name,
  table_type,
  creation_time
FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.TABLES`
WHERE REGEXP_CONTAINS(
  LOWER(table_name),
  r'(game|event|session|online|asset|pay|action|user|record)'
)
ORDER BY table_name
LIMIT 3000;

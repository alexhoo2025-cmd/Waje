-- Aggregate-only inventory of current user attribute names and coverage.
SELECT
  COALESCE(NULLIF(field_name, ''), '(blank)') AS field_name,
  COUNT(*) AS attribute_row_count,
  APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count
FROM `wajenigeria.origin_hfyl.user_fields_explode`
WHERE create_time IS NOT NULL
GROUP BY field_name
HAVING APPROX_COUNT_DISTINCT(user_id) >= 10
ORDER BY attribute_row_count DESC
LIMIT 500;

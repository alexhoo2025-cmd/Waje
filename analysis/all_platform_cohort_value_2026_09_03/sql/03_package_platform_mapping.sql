-- Aggregate-only package/platform mapping for current active user facts.
WITH user_events_base AS (
  SELECT
    target_day AS cohort_date,
    app_id,
    first_package_name,
    package_name,
    first_client_type,
    client_type,
    user_id
  FROM `wajenigeria.origin_hfyl.user_events`
)
SELECT
  app_id,
  COALESCE(NULLIF(first_package_name, ''), '(blank)') AS first_package_name,
  COALESCE(NULLIF(package_name, ''), '(blank)') AS observed_package_name,
  first_client_type,
  client_type,
  COUNT(*) AS snapshot_rows,
  APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count
FROM user_events_base
WHERE cohort_date BETWEEN DATE '2026-08-27' AND DATE '2026-09-02'
GROUP BY app_id, first_package_name, observed_package_name, first_client_type, client_type
HAVING APPROX_COUNT_DISTINCT(user_id) >= 10
ORDER BY approx_subject_count DESC
LIMIT 500;

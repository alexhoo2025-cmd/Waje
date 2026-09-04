-- Aggregate-only coverage check for current cohort, payment, LTV, and activity facts.
-- No user, order, transaction, or device rows are returned.
WITH ltv_base AS (
  SELECT target_day AS cohort_date
  FROM `wajenigeria.track_hfyl.user_ltv`
), activity_base AS (
  SELECT target_day AS cohort_date
  FROM `wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel`
)
SELECT
  'track_hfyl.user_ltv' AS source_name,
  MIN(cohort_date) AS min_target_day,
  MAX(cohort_date) AS max_target_day,
  COUNT(*) AS row_count,
  CAST(NULL AS INT64) AS approx_subject_count
FROM ltv_base
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-02'
UNION ALL
SELECT
  'ares_hfyl.user_activety_indicators_downloadchannel' AS source_name,
  MIN(cohort_date) AS min_target_day,
  MAX(cohort_date) AS max_target_day,
  COUNT(*) AS row_count,
  CAST(NULL AS INT64) AS approx_subject_count
FROM activity_base
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-02'
ORDER BY source_name;

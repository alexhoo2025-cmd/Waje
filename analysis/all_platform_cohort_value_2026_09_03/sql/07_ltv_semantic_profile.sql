-- Aggregate-only LTV field-semantic profile. It checks data-type coverage and nonzero lifecycle values.
WITH ltv_base AS (
  SELECT
    target_day AS cohort_date,
    app_id,
    data_type,
    ltv_1,
    ltv_7,
    ltv_14,
    ltv_30,
    ltv_60,
    ltv_90
  FROM `wajenigeria.track_hfyl.user_ltv`
)
SELECT
  app_id,
  data_type,
  MIN(cohort_date) AS min_target_day,
  MAX(cohort_date) AS max_target_day,
  COUNT(*) AS source_rows,
  COUNTIF(COALESCE(ltv_1, 0) != 0) AS nonzero_ltv_1_rows,
  COUNTIF(COALESCE(ltv_7, 0) != 0) AS nonzero_ltv_7_rows,
  COUNTIF(COALESCE(ltv_14, 0) != 0) AS nonzero_ltv_14_rows,
  COUNTIF(COALESCE(ltv_30, 0) != 0) AS nonzero_ltv_30_rows,
  COUNTIF(COALESCE(ltv_60, 0) != 0) AS nonzero_ltv_60_rows,
  COUNTIF(COALESCE(ltv_90, 0) != 0) AS nonzero_ltv_90_rows
FROM ltv_base
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-02'
GROUP BY app_id, data_type
ORDER BY app_id, data_type;

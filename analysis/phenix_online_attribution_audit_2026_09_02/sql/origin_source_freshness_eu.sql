-- Metadata-like aggregate freshness check for the Europe-region Origin cohort tables.
-- The wide date range is only used to expose min/max loaded dates; no detail rows are returned.
WITH date_bounds AS (
  SELECT DATE '2000-01-01' AS event_date
)
SELECT 'daily_new_user_retention' AS source_table, MIN(target_day) AS min_target_day, MAX(target_day) AS max_target_day, COUNT(*) AS source_rows
FROM `wajenigeria.bigdata.daily_new_user_retention`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2100-01-01'
UNION ALL
SELECT 'first_pay_retention', MIN(target_day), MAX(target_day), COUNT(*)
FROM `wajenigeria.bigdata.first_pay_retention`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2100-01-01'

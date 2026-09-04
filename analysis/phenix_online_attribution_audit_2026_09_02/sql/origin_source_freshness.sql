-- Metadata-like aggregate freshness check for the US-region Origin source table.
-- The wide date range is only used to expose min/max loaded dates; no detail rows are returned.
WITH date_bounds AS (
  SELECT DATE '2000-01-01' AS event_date
)
SELECT 'campaign_conversion_cost' AS source_table, MIN(target_day) AS min_target_day, MAX(target_day) AS max_target_day, COUNT(*) AS source_rows
FROM `wajenigeria.90006.campaign_conversion_cost`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2100-01-01'

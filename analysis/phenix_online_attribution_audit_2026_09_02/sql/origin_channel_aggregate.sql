-- Origin channel aggregate cross-check for the Phenix window.
-- Only aggregated channel totals are returned; no campaign rows or user details.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
)
SELECT
  target_day,
  download_channel,
  SUM(cost_amount) AS spend_amount,
  SUM(new_users_today) AS new_users,
  SUM(register_users) AS registered_users,
  SUM(pay_users_count) AS paying_users,
  SUM(first_pay_users) AS first_paying_users,
  COUNT(*) AS source_row_count
FROM `wajenigeria.90006.campaign_conversion_cost`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2026-09-02'
GROUP BY target_day, download_channel
ORDER BY target_day, download_channel

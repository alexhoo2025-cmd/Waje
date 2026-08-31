-- TEMPLATE ONLY — do not execute until the authorised V2 Joint model is live.
-- Purpose: reproduce the aggregate-only “game × display lifecycle 1–4 × week”
-- RTP validation used by the local export-based report.
-- Expected source: certified model_lifecycle_v2_joint_daily.

WITH scoped AS (
  SELECT
    business_date,
    game_id,
    game_name,
    display_lifecycle,
    entire_bet,
    entire_actual_profit,
    entire_expected_profit
  FROM model_lifecycle_v2_joint_daily
  WHERE business_date BETWEEN DATE '2026-08-14' AND DATE '2026-08-27'
    AND data_scope = 'joint'
    AND population_type = 'all'
    AND display_lifecycle IN (1, 2, 3, 4)
    AND data_status = 'complete'
), weekly AS (
  SELECT
    CASE
      WHEN business_date BETWEEN DATE '2026-08-14' AND DATE '2026-08-20' THEN 'week_1'
      ELSE 'week_2'
    END AS period,
    game_id,
    game_name,
    display_lifecycle,
    COUNT(DISTINCT CASE WHEN entire_bet > 0 THEN business_date END) AS active_days,
    SUM(entire_bet) AS entire_bet,
    SUM(entire_actual_profit) AS entire_actual_profit,
    SUM(entire_expected_profit) AS entire_expected_profit,
    1 - SUM(entire_actual_profit) / NULLIF(SUM(entire_bet), 0) AS weighted_actual_rtp,
    1 - SUM(entire_expected_profit) / NULLIF(SUM(entire_bet), 0) AS weighted_expected_rtp
  FROM scoped
  GROUP BY 1, 2, 3, 4
)
SELECT *
FROM weekly
ORDER BY game_name, display_lifecycle, period;

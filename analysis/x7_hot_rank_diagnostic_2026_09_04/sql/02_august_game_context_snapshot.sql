-- RERUN CONTRACT / MATERIALIZED SNAPSHOT REFERENCE.
-- The shipped chart rows are the reviewed local output from the August
-- Lifecycle V2 Joint aggregation, not a new live query in this run.
-- Re-run after the certified lifecycle model is available.

SELECT
  game_name AS game,
  SUM(entire_bet) AS bet_amount,
  SUM(entire_actual_profit) AS actual_profit,
  1 - SAFE_DIVIDE(SUM(entire_actual_profit), SUM(entire_bet)) AS actual_rtp,
  SAFE_DIVIDE(SUM(entire_bet), SUM(SUM(entire_bet)) OVER ()) AS bet_share
FROM model_lifecycle_v2_joint_daily -- target model to be confirmed
WHERE business_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
  AND data_scope = 'joint'
  AND population_type = 'all'
  AND display_lifecycle IN (1, 2, 3, 4)
  AND data_status = 'complete'
GROUP BY game_name
ORDER BY bet_amount DESC;

-- Post-refresh checks. Every query returns aggregate metadata only.

-- 1. Mart freshness and business-date coverage.
SELECT
  MIN(business_date) AS first_business_date,
  MAX(business_date) AS last_business_date,
  COUNT(*) AS aggregate_row_count,
  MAX(data_cutoff_at) AS data_cutoff_at,
  MAX(refreshed_at) AS refreshed_at
FROM whot_center.mart_lifecycle_v2_joint_daily_rawlog;

-- 2. Unique grain must hold because it is the mart primary key.
SELECT business_date, game_id, display_lifecycle, COUNT(*) AS duplicate_count
FROM whot_center.mart_lifecycle_v2_joint_daily_rawlog
GROUP BY business_date, game_id, display_lifecycle
HAVING COUNT(*) > 1;

-- 3. Date filter must use the materialized index path.
EXPLAIN SELECT
  game_id,
  SUM(entire_bet) AS entire_bet
FROM whot_center.mart_lifecycle_v2_joint_daily_rawlog
WHERE business_date BETWEEN '2026-09-01' AND '2026-09-02'
  AND row_scope = 'game'
  AND display_lifecycle BETWEEN 0 AND 4
GROUP BY game_id
ORDER BY entire_bet DESC
LIMIT 20;

-- 4. Compare raw-log and mart totals for a selected stable window.
-- Use the existing aggregate-only Model SQL as the raw comparator; compare only
-- the same business-date, game, and lifecycle grain before publishing.

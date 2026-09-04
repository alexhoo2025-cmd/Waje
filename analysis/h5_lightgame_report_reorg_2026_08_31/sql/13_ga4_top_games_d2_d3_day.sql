-- Waje business-day convention:
-- D1 Day = cohort day; D2 Day = cohort + 1 calendar day;
-- D3 Day = cohort + 2 calendar days.
-- This query intentionally does not reuse the legacy GA4 label "D3"
-- which used cohort + 3 days and is a D4 Day result under this convention.
WITH first_visits AS (
  SELECT
    user_pseudo_id,
    MIN(PARSE_DATE('%Y%m%d', event_date)) AS first_visit_date
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name = 'first_visit'
  GROUP BY user_pseudo_id
),
game_entries AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS entry_date,
    user_pseudo_id,
    REGEXP_EXTRACT(
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
      r'/game/(6001|9008|9001|9010|9003|9011|9016|9013|2003)(?:/|$)'
    ) AS game_id
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name = 'page_view'
),
new_game_users AS (
  SELECT DISTINCT e.entry_date, e.user_pseudo_id, e.game_id
  FROM game_entries e
  JOIN first_visits f USING (user_pseudo_id)
  WHERE e.entry_date = f.first_visit_date
    AND e.game_id IS NOT NULL
),
active_days AS (
  SELECT DISTINCT
    PARSE_DATE('%Y%m%d', event_date) AS active_date,
    user_pseudo_id
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name IN ('session_start', 'user_engagement', 'page_view')
)
SELECT
  game_id,
  COUNT(DISTINCT IF(entry_date <= DATE '2026-08-26', user_pseudo_id, NULL)) AS d2_day_den,
  COUNT(DISTINCT IF(
    entry_date <= DATE '2026-08-26'
    AND EXISTS (
      SELECT 1 FROM active_days a
      WHERE a.user_pseudo_id = g.user_pseudo_id
        AND a.active_date = DATE_ADD(g.entry_date, INTERVAL 1 DAY)
    ),
    user_pseudo_id,
    NULL
  )) AS d2_day_num,
  COUNT(DISTINCT IF(entry_date <= DATE '2026-08-25', user_pseudo_id, NULL)) AS d3_day_den,
  COUNT(DISTINCT IF(
    entry_date <= DATE '2026-08-25'
    AND EXISTS (
      SELECT 1 FROM active_days a
      WHERE a.user_pseudo_id = g.user_pseudo_id
        AND a.active_date = DATE_ADD(g.entry_date, INTERVAL 2 DAY)
    ),
    user_pseudo_id,
    NULL
  )) AS d3_day_num
FROM new_game_users g
GROUP BY game_id
ORDER BY game_id;

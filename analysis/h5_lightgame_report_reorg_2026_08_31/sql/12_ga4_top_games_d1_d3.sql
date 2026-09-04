WITH first_visits AS (
  SELECT
    user_pseudo_id,
    MIN(PARSE_DATE('%Y%m%d', event_date)) AS first_visit_date
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name = 'first_visit'
  GROUP BY user_pseudo_id
), game_entries AS (
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
), new_game_users AS (
  SELECT DISTINCT e.entry_date, e.user_pseudo_id, e.game_id
  FROM game_entries e
  JOIN first_visits f USING (user_pseudo_id)
  WHERE e.entry_date = f.first_visit_date
    AND e.game_id IS NOT NULL
), active_days AS (
  SELECT DISTINCT
    PARSE_DATE('%Y%m%d', event_date) AS active_date,
    user_pseudo_id
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name IN ('session_start', 'user_engagement', 'page_view')
)
SELECT
  g.game_id,
  COUNTIF(g.entry_date <= DATE '2026-08-26') AS d1_den,
  COUNTIF(
    g.entry_date <= DATE '2026-08-26'
    AND EXISTS (
      SELECT 1 FROM active_days a
      WHERE a.user_pseudo_id = g.user_pseudo_id
        AND a.active_date = DATE_ADD(g.entry_date, INTERVAL 1 DAY)
    )
  ) AS d1_num,
  COUNTIF(g.entry_date <= DATE '2026-08-24') AS d3_den,
  COUNTIF(
    g.entry_date <= DATE '2026-08-24'
    AND EXISTS (
      SELECT 1 FROM active_days a
      WHERE a.user_pseudo_id = g.user_pseudo_id
        AND a.active_date = DATE_ADD(g.entry_date, INTERVAL 3 DAY)
    )
  ) AS d3_num
FROM new_game_users g
GROUP BY g.game_id
ORDER BY g.game_id;

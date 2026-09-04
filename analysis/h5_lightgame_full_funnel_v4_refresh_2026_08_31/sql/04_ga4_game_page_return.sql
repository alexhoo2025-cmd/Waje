WITH first_visits AS (
  SELECT
    user_pseudo_id,
    MIN(PARSE_DATE('%Y%m%d', event_date)) AS first_visit_date
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
    AND event_name = 'first_visit'
  GROUP BY user_pseudo_id
),
game_entries AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS entry_date,
    user_pseudo_id,
    REGEXP_EXTRACT(
      REGEXP_EXTRACT(
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
        r'https?://[^/]+([^?#]*)'
      ),
      r'/game/(9003|9008|9010|9011|9016)(?:/|$)'
    ) AS game_id
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
    AND event_name = 'page_view'
),
new_game_users AS (
  SELECT DISTINCT
    e.entry_date,
    e.user_pseudo_id,
    e.game_id
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
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
    AND event_name IN ('session_start', 'user_engagement', 'page_view')
)
SELECT
  g.entry_date,
  g.game_id,
  COUNT(*) AS new_game_users,
  COUNTIF(EXISTS (
    SELECT 1 FROM active_days a
    WHERE a.user_pseudo_id = g.user_pseudo_id
      AND a.active_date = DATE_ADD(g.entry_date, INTERVAL 1 DAY)
  )) AS return_d1_users,
  COUNTIF(EXISTS (
    SELECT 1 FROM active_days a
    WHERE a.user_pseudo_id = g.user_pseudo_id
      AND a.active_date = DATE_ADD(g.entry_date, INTERVAL 3 DAY)
  )) AS return_d3_users,
  COUNTIF(EXISTS (
    SELECT 1 FROM active_days a
    WHERE a.user_pseudo_id = g.user_pseudo_id
      AND a.active_date = DATE_ADD(g.entry_date, INTERVAL 7 DAY)
  )) AS return_d7_users
FROM new_game_users g
GROUP BY g.entry_date, g.game_id
HAVING new_game_users >= 10
ORDER BY g.entry_date, g.game_id;

WITH first_visits AS (
  SELECT
    user_pseudo_id,
    MIN(PARSE_DATE('%Y%m%d', event_date)) AS first_visit_date
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name = 'first_visit'
  GROUP BY user_pseudo_id
), game_pages AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS stat_date,
    user_pseudo_id,
    REGEXP_EXTRACT(
      REGEXP_EXTRACT(
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
        r'https?://[^/]+([^?#]*)'
      ),
      r'/game/(9003|9008|9010|9011|9016)(?:/|$)'
    ) AS game_id
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name = 'page_view'
)
SELECT
  p.stat_date,
  p.game_id,
  COUNT(*) AS page_views,
  APPROX_COUNT_DISTINCT(p.user_pseudo_id) AS all_visitors,
  APPROX_COUNT_DISTINCT(IF(f.first_visit_date = p.stat_date, p.user_pseudo_id, NULL)) AS new_visitors
FROM game_pages p
LEFT JOIN first_visits f USING (user_pseudo_id)
WHERE p.game_id IS NOT NULL
GROUP BY p.stat_date, p.game_id
HAVING all_visitors >= 10
ORDER BY p.stat_date, p.game_id;

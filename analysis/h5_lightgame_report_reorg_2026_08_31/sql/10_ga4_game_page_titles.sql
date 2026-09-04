SELECT
  REGEXP_EXTRACT(
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
    r'/game/([^/?#]+)'
  ) AS game_slug,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_title') AS page_title,
  COUNT(*) AS page_views
FROM `waje-analytics-readonly.analytics_504208609.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
  AND event_name = 'page_view'
  AND REGEXP_CONTAINS(
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
    r'/game/'
  )
GROUP BY game_slug, page_title
HAVING page_views >= 10
ORDER BY page_views DESC
LIMIT 100;

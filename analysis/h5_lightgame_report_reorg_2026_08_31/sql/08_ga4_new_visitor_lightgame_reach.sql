WITH first_visits AS (
  SELECT
    user_pseudo_id,
    MIN(PARSE_DATE('%Y%m%d', event_date)) AS first_visit_date,
    ANY_VALUE(LOWER(COALESCE(traffic_source.source, '(direct)'))) AS source,
    ANY_VALUE(LOWER(COALESCE(traffic_source.medium, '(none)'))) AS medium
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name = 'first_visit'
  GROUP BY user_pseudo_id
),
game_pages AS (
  SELECT DISTINCT
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
  f.first_visit_date,
  CASE
    WHEN REGEXP_CONTAINS(f.source, r'facebook|fb') THEN 'Facebook'
    WHEN REGEXP_CONTAINS(f.source, r'google|adwords') THEN 'Google'
    WHEN f.source = '(direct)' OR f.medium IN ('(none)', 'organic', 'referral') THEN 'Natural/Direct'
    ELSE 'Other'
  END AS source_group,
  COUNT(*) AS new_visitors,
  COUNTIF(EXISTS (
    SELECT 1 FROM game_pages p
    WHERE p.user_pseudo_id = f.user_pseudo_id
      AND p.stat_date = f.first_visit_date
      AND p.game_id IS NOT NULL
  )) AS lightgame_page_users
FROM first_visits f
GROUP BY f.first_visit_date, source_group
HAVING new_visitors >= 30
ORDER BY f.first_visit_date, new_visitors DESC;

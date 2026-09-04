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
page_views AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS stat_date,
    user_pseudo_id,
    REGEXP_EXTRACT(
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
      r'https?://[^/]+([^?#]*)'
    ) AS page_path,
    device.operating_system AS os,
    device.web_info.browser AS browser,
    device.mobile_brand_name AS brand
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
    AND event_name = 'page_view'
),
joined AS (
  SELECT
    p.stat_date,
    CASE
      WHEN REGEXP_CONTAINS(f.source, r'facebook|fb') THEN 'Facebook'
      WHEN REGEXP_CONTAINS(f.source, r'google|adwords') THEN 'Google'
      WHEN f.source = '(direct)' OR f.medium IN ('(none)', 'organic', 'referral') THEN 'Natural/Direct'
      ELSE 'Other'
    END AS source_group,
    REGEXP_EXTRACT(p.page_path, r'/game/(9003|9008|9010|9011|9016)(?:/|$)') AS game_id,
    p.os,
    p.browser,
    p.brand,
    p.user_pseudo_id
  FROM page_views p
  JOIN first_visits f USING (user_pseudo_id)
  WHERE p.stat_date = f.first_visit_date
)
SELECT
  stat_date,
  source_group,
  game_id,
  os,
  browser,
  brand,
  COUNT(*) AS page_views,
  APPROX_COUNT_DISTINCT(user_pseudo_id) AS new_visitors
FROM joined
WHERE game_id IS NOT NULL
GROUP BY stat_date, source_group, game_id, os, browser, brand
HAVING new_visitors >= 10
ORDER BY stat_date, game_id, new_visitors DESC
LIMIT 3000;

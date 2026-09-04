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
events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS stat_date,
    user_pseudo_id,
    event_name
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
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
    SELECT 1 FROM events e
    WHERE e.user_pseudo_id = f.user_pseudo_id
      AND e.stat_date = f.first_visit_date
      AND e.event_name = 'page_view'
  )) AS page_view_users,
  COUNTIF(EXISTS (
    SELECT 1 FROM events e
    WHERE e.user_pseudo_id = f.user_pseudo_id
      AND e.stat_date = DATE_ADD(f.first_visit_date, INTERVAL 1 DAY)
  )) AS return_d1_users,
  COUNTIF(EXISTS (
    SELECT 1 FROM events e
    WHERE e.user_pseudo_id = f.user_pseudo_id
      AND e.stat_date = DATE_ADD(f.first_visit_date, INTERVAL 3 DAY)
  )) AS return_d3_users
FROM first_visits f
GROUP BY f.first_visit_date, source_group
HAVING new_visitors >= 30
ORDER BY f.first_visit_date, new_visitors DESC;

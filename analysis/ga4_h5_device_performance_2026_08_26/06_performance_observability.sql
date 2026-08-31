WITH base AS (
  SELECT event_name, event_params
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
)
SELECT
  COUNT(*) AS total_events,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(web[_-]?vitals|lcp|inp|cls|fcp|ttfb|page[_-]?load|js[_-]?error|frontend[_-]?error|exception|network[_-]?error)')) AS performance_named_events,
  COUNTIF(EXISTS (
    SELECT 1
    FROM UNNEST(event_params) AS ep
    WHERE REGEXP_CONTAINS(LOWER(ep.key), r'(web[_-]?vitals|lcp|inp|cls|fcp|ttfb|page[_-]?load|js[_-]?error|frontend[_-]?error|network)')
  )) AS performance_parameter_events
FROM base;

SELECT
  ep.key AS parameter_key,
  COUNT(*) AS parameter_occurrences,
  COUNT(DISTINCT event_name) AS event_type_coverage
FROM `waje-analytics-readonly.analytics_504208609.events_*`,
UNNEST(event_params) AS ep
WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
GROUP BY parameter_key
ORDER BY parameter_occurrences DESC, parameter_key;

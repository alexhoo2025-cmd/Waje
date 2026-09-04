-- Controlled quality audit. Return only counts of parameter presence and
-- restricted-key candidates; do not export raw key names or values.
SELECT
  PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS event_day,
  event_name,
  COUNT(*) AS event_count,
  COUNTIF(ARRAY_LENGTH(event_params) > 0) AS events_with_params,
  COUNTIF(ARRAY_LENGTH(user_properties) > 0) AS events_with_user_properties,
  COUNTIF(REGEXP_CONTAINS(
    TO_JSON_STRING(event_params),
    r'(?i)(user|phone|email|token|device|advert|account|bank|id_card|face|biometric)'
  )) AS restricted_parameter_candidate_events
FROM `wajenigeria.waje_ng_firebase_android.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
  AND platform = 'ANDROID'
GROUP BY event_day, event_name
ORDER BY event_day, event_count DESC
LIMIT 3000;

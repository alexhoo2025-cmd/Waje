-- Focused audit for the exact URL marker p=h5phx in the legacy H5 export.
-- Parameter keys are returned for diagnosis; parameter values and URLs are not returned.
SELECT
  event_params.key AS marker_parameter_key,
  event_name,
  COALESCE(NULLIF(traffic_source.source, ''), '(blank)') AS first_source,
  COALESCE(NULLIF(traffic_source.medium, ''), '(blank)') AS first_medium,
  COUNT(*) AS matched_parameter_count,
  APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) AS approx_matched_subject_count
FROM `wajenigeria.waje_ng_firebase_h5.events_20260827`, UNNEST(event_params) AS event_params
WHERE event_date = '20260827'
  AND REGEXP_CONTAINS(LOWER(COALESCE(event_params.value.string_value, '')), r'(^|[?&])p=h5phx([&#]|$)')
GROUP BY marker_parameter_key, event_name, first_source, first_medium
HAVING APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) >= 10
ORDER BY matched_parameter_count DESC, marker_parameter_key, event_name
LIMIT 3000

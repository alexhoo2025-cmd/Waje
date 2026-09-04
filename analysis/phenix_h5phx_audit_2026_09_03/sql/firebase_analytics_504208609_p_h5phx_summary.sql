-- Aggregate summary for p=h5phx embedded in Firebase URL parameters.
-- No URL or parameter values are returned.
WITH base AS (
  SELECT
    event_name,
    user_pseudo_id,
    traffic_source.source AS first_source,
    traffic_source.medium AS first_medium,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE p.key = 'page_location'
        AND REGEXP_CONTAINS(LOWER(COALESCE(p.value.string_value, '')), r'(^|[?&])p=h5phx([&#]|$)')
    ) AS page_location_marker,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE p.key = 'page_referrer'
        AND REGEXP_CONTAINS(LOWER(COALESCE(p.value.string_value, '')), r'(^|[?&])p=h5phx([&#]|$)')
    ) AS page_referrer_marker,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE p.key = 'form_destination'
        AND REGEXP_CONTAINS(LOWER(COALESCE(p.value.string_value, '')), r'(^|[?&])p=h5phx([&#]|$)')
    ) AS form_destination_marker,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE LOWER(COALESCE(p.key, '')) = 'p'
        AND LOWER(COALESCE(p.value.string_value, '')) = 'h5phx'
    ) AS exact_p_key
  FROM `wajenigeria.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260828' AND '20260901'
    AND event_date BETWEEN '20260828' AND '20260901'
)
SELECT
  'analytics_504208609' AS dataset_id,
  COUNTIF(page_location_marker) AS page_location_marker_event_count,
  APPROX_COUNT_DISTINCT(IF(page_location_marker, user_pseudo_id, NULL)) AS page_location_marker_subjects_approx,
  COUNTIF(page_location_marker AND event_name = 'first_visit') AS first_visit_marker_event_count,
  APPROX_COUNT_DISTINCT(IF(page_location_marker AND event_name = 'first_visit', user_pseudo_id, NULL)) AS first_visit_marker_subjects_approx,
  COUNTIF(page_location_marker AND event_name = 'page_view') AS page_view_marker_event_count,
  APPROX_COUNT_DISTINCT(IF(page_location_marker AND event_name = 'page_view', user_pseudo_id, NULL)) AS page_view_marker_subjects_approx,
  COUNTIF(page_referrer_marker) AS page_referrer_marker_event_count,
  COUNTIF(form_destination_marker) AS form_destination_marker_event_count,
  COUNTIF(exact_p_key) AS exact_p_key_event_count,
  COUNTIF(page_location_marker AND LOWER(COALESCE(first_source, '')) = '(direct)' AND LOWER(COALESCE(first_medium, '')) = '(none)') AS direct_first_source_marker_event_count,
  COUNTIF(page_location_marker AND REGEXP_CONTAINS(LOWER(COALESCE(first_medium, '')), r'(paid|cpc|cpm|display|social)')) AS paid_medium_marker_event_count
FROM base

-- Exact p=h5phx aggregate audit for one complete Firebase day.
-- No event rows, URL values, parameter values or identifiers are returned.
WITH base AS (
  SELECT
    platform,
    app_info.id AS app_id,
    app_info.version AS app_version,
    device.web_info.hostname AS hostname,
    event_name,
    user_pseudo_id,
    traffic_source.source AS first_source,
    traffic_source.medium AS first_medium,
    collected_traffic_source.manual_source AS manual_source,
    collected_traffic_source.manual_medium AS manual_medium,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE LOWER(COALESCE(p.key, '')) = 'p'
    ) AS p_key_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE LOWER(COALESCE(p.key, '')) = 'p'
        AND LOWER(COALESCE(p.value.string_value, '')) = 'h5phx'
    ) AS p_exact_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(LOWER(COALESCE(p.value.string_value, '')), r'(^|[?&])p=h5phx([&#]|$)')
    ) AS p_url_marker_present,
    EXISTS (
      SELECT 1 FROM UNNEST(user_properties) p
      WHERE LOWER(COALESCE(p.key, '')) = 'p'
        AND LOWER(COALESCE(p.value.string_value, '')) = 'h5phx'
    ) AS user_property_p_exact_present,
    REGEXP_CONTAINS(
      LOWER(CONCAT(
        COALESCE(app_info.id, ''), '|', COALESCE(app_info.version, ''), '|',
        COALESCE(device.web_info.hostname, ''), '|', COALESCE(traffic_source.source, ''), '|',
        COALESCE(traffic_source.medium, ''), '|', COALESCE(collected_traffic_source.manual_source, ''), '|',
        COALESCE(collected_traffic_source.manual_medium, '')
      )),
      r'(h5phx|phenix)'
    ) AS package_or_source_marker_present,
    REGEXP_CONTAINS(
      LOWER(CONCAT(COALESCE(event_name, ''), '|', COALESCE(app_info.version, ''))),
      r'(h5phx|phenix)'
    ) AS event_or_version_marker_present,
    traffic_source.source IS NOT NULL AND traffic_source.source != '' AS first_source_present,
    collected_traffic_source.manual_source IS NOT NULL
      AND collected_traffic_source.manual_source != '' AS manual_source_present
  FROM `wajenigeria.analytics_517134955.events_20260829`
  WHERE event_date = '20260829'
), normalized AS (
  SELECT
    platform,
    app_id,
    app_version,
    hostname,
    event_name,
    user_pseudo_id,
    CASE
      WHEN manual_source IS NOT NULL AND manual_source != '' THEN manual_source
      WHEN first_source IS NOT NULL AND first_source != '' THEN first_source
      ELSE '(blank)'
    END AS observed_source,
    CASE
      WHEN manual_medium IS NOT NULL AND manual_medium != '' THEN manual_medium
      WHEN first_medium IS NOT NULL AND first_medium != '' THEN first_medium
      ELSE '(blank)'
    END AS observed_medium,
    p_key_present,
    p_exact_present,
    p_url_marker_present,
    user_property_p_exact_present,
    package_or_source_marker_present,
    event_or_version_marker_present,
    first_source_present,
    manual_source_present
  FROM base
)
SELECT
  platform,
  COALESCE(app_id, '(blank)') AS app_id,
  COALESCE(hostname, '(blank)') AS hostname,
  COALESCE(observed_source, '(blank)') AS observed_source,
  COALESCE(observed_medium, '(blank)') AS observed_medium,
  event_name,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) AS approx_subject_count,
  COUNTIF(p_key_present) AS p_key_present_count,
  COUNTIF(p_exact_present) AS p_exact_count,
  COUNTIF(p_url_marker_present) AS p_url_marker_count,
  COUNTIF(user_property_p_exact_present) AS user_property_p_exact_count,
  COUNTIF(package_or_source_marker_present) AS package_or_source_marker_count,
  COUNTIF(event_or_version_marker_present) AS event_or_version_marker_count,
  COUNTIF(first_source_present) AS first_source_present_count,
  COUNTIF(manual_source_present) AS manual_source_present_count,
  COUNTIF(event_name = 'first_visit') AS first_visit_event_count,
  COUNTIF(event_name = 'first_open') AS first_open_event_count,
  COUNTIF(event_name = 'session_start') AS session_start_event_count,
  COUNTIF(event_name = 'page_view') AS page_view_event_count
FROM normalized
GROUP BY platform, app_id, hostname, observed_source, observed_medium, event_name
HAVING APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) >= 10
ORDER BY event_count DESC, observed_source, event_name
LIMIT 3000

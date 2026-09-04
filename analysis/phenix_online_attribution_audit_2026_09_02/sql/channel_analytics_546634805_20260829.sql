-- Aggregate-only Firebase attribution audit.
-- Date is a complete event day; no event rows or parameter values are returned.
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
    traffic_source.source IS NOT NULL AND traffic_source.source != '' AS first_source_present,
    collected_traffic_source.manual_source IS NOT NULL
      AND collected_traffic_source.manual_source != '' AS manual_source_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(LOWER(COALESCE(p.key, '')), r'(package|bundle|app[_-]?id)')
    ) AS package_key_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(LOWER(COALESCE(p.key, '')), r'(channel|media|source|medium|referrer)')
    ) AS channel_key_present,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(LOWER(COALESCE(p.key, '')), r'(campaign|utm_)')
    ) AS campaign_key_present,
    REGEXP_CONTAINS(
      LOWER(CONCAT(
        COALESCE(app_info.id, ''), '|',
        COALESCE(app_info.version, ''), '|',
        COALESCE(device.web_info.hostname, ''), '|',
        COALESCE(traffic_source.source, ''), '|',
        COALESCE(traffic_source.medium, '')
      )),
      r'(wajeh5phx|waje5phx|phenix)'
    )
    OR EXISTS (
      SELECT 1 FROM UNNEST(event_params) p
      WHERE REGEXP_CONTAINS(
        LOWER(CONCAT(COALESCE(p.key, ''), '=', COALESCE(p.value.string_value, ''))),
        r'(wajeh5phx|waje5phx|phenix)'
      )
    )
    OR EXISTS (
      SELECT 1 FROM UNNEST(user_properties) p
      WHERE REGEXP_CONTAINS(
        LOWER(CONCAT(COALESCE(p.key, ''), '=', COALESCE(p.value.string_value, ''))),
        r'(wajeh5phx|waje5phx|phenix)'
      )
    ) AS phx_marker_present
  FROM `wajenigeria.analytics_546634805.events_20260829`
  WHERE event_date = '20260829'
), normalized AS (
  SELECT
    platform,
    app_id,
    app_version,
    hostname,
    event_name,
    user_pseudo_id,
    first_source,
    first_medium,
    manual_source,
    manual_medium,
    first_source_present,
    manual_source_present,
    package_key_present,
    channel_key_present,
    campaign_key_present,
    phx_marker_present,
    CASE
      WHEN manual_source_present OR (manual_medium IS NOT NULL AND manual_medium != '') THEN 'manual_collected'
      WHEN first_source_present OR (first_medium IS NOT NULL AND first_medium != '') THEN 'first_user_traffic'
      ELSE 'unattributed'
    END AS attribution_basis,
    CASE
      WHEN manual_source_present OR (manual_medium IS NOT NULL AND manual_medium != '') THEN
        CONCAT(COALESCE(NULLIF(manual_source, ''), '(not_set)'), ' / ', COALESCE(NULLIF(manual_medium, ''), '(not_set)'))
      WHEN first_source_present OR (first_medium IS NOT NULL AND first_medium != '') THEN
        CONCAT(COALESCE(NULLIF(first_source, ''), '(not_set)'), ' / ', COALESCE(NULLIF(first_medium, ''), '(not_set)'))
      ELSE '(unattributed)'
    END AS channel_key
  FROM base
)
SELECT
  'channel' AS row_scope,
  COALESCE(platform, '(blank)') AS platform,
  COALESCE(app_id, '(blank)') AS app_id,
  COALESCE(hostname, '(blank)') AS hostname,
  COALESCE(attribution_basis, '(all)') AS attribution_basis,
  COALESCE(channel_key, '(all)') AS channel_key,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) AS approx_subject_count,
  COUNT(DISTINCT event_name) AS distinct_event_name_count,
  COUNTIF(event_name = 'page_view') AS page_view_event_count,
  COUNTIF(event_name = 'session_start') AS session_start_event_count,
  COUNTIF(event_name = 'first_visit') AS first_visit_event_count,
  COUNTIF(event_name = 'first_open') AS first_open_event_count,
  COUNTIF(event_name = 'user_engagement') AS user_engagement_event_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(register|recharge|purchase|withdraw|payment|login|pay)')) AS business_event_candidate_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(game|bet|round|settle|reward|play)')) AS game_event_candidate_count,
  COUNTIF(first_source_present) AS first_source_present_count,
  COUNTIF(manual_source_present) AS manual_source_present_count,
  COUNTIF(package_key_present) AS package_key_present_count,
  COUNTIF(channel_key_present) AS channel_key_present_count,
  COUNTIF(campaign_key_present) AS campaign_key_present_count,
  COUNTIF(phx_marker_present) AS phx_marker_count,
  APPROX_COUNT_DISTINCT(NULLIF(app_version, '')) AS approx_version_count,
  APPROX_TOP_COUNT(event_name, 50) AS top_event_names
FROM normalized
GROUP BY platform, app_id, hostname, attribution_basis, channel_key
HAVING APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NULL OR user_pseudo_id = '', NULL, user_pseudo_id)) >= 10
ORDER BY event_count DESC, channel_key

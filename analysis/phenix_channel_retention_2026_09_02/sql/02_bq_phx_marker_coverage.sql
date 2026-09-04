-- Aggregate-only check for the Phenix package/source marker.
-- No event names, parameter keys, parameter values or identifiers are returned.
SELECT
  _TABLE_SUFFIX AS event_table_day,
  COUNT(*) AS total_event_count,
  COUNT(DISTINCT event_name) AS distinct_event_name_count,
  COUNTIF(event_name = 'page_view') AS page_view_event_count,
  COUNTIF(event_name = 'session_start') AS session_start_event_count,
  COUNTIF(event_name = 'first_visit') AS first_visit_event_count,
  COUNTIF(event_name = 'user_engagement') AS user_engagement_event_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(register|recharge|purchase|withdraw|payment|login|pay)')) AS business_event_candidate_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_name), r'(game[_-]?ready|bet[_-]?ready|game[_-]?start|game[_-]?end|settlement)')) AS game_event_candidate_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(COALESCE(app_info.id, '')), r'(phx|phenix)')) AS app_id_marker_event_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(COALESCE(app_info.version, '')), r'(phx|phenix)')) AS app_version_marker_event_count,
  COUNTIF(traffic_source.source IS NOT NULL AND traffic_source.source != '') AS traffic_source_present_count,
  COUNTIF(collected_traffic_source.manual_source IS NOT NULL AND collected_traffic_source.manual_source != '') AS collected_source_present_count,
  COUNTIF(EXISTS (
    SELECT 1 FROM UNNEST(event_params) ep
    WHERE ep.key = 'package_name'
  )) AS package_param_present_count,
  COUNTIF(EXISTS (
    SELECT 1 FROM UNNEST(event_params) ep
    WHERE ep.key = 'channel'
  )) AS channel_param_present_count,
  COUNTIF(EXISTS (
    SELECT 1 FROM UNNEST(event_params) ep
    WHERE ep.key = 'attribution_media'
  )) AS attribution_media_param_present_count,
  COUNTIF(EXISTS (
    SELECT 1 FROM UNNEST(event_params) ep
    WHERE ep.key = 'campaign_id'
  )) AS campaign_param_present_count,
  COUNTIF(EXISTS (
    SELECT 1 FROM UNNEST(event_params) ep
    WHERE ep.key IN ('package_name', 'channel', 'attribution_media', 'campaign_id')
      AND LOWER(COALESCE(ep.value.string_value, '')) IN ('wajeh5phx', 'phenix')
  )) AS phx_param_marker_event_count,
  COUNTIF(user_pseudo_id IS NOT NULL AND user_pseudo_id != '') AS pseudo_id_present_count,
  APPROX_COUNT_DISTINCT(IF(user_pseudo_id IS NOT NULL AND user_pseudo_id != '', user_pseudo_id, NULL)) AS approximate_pseudo_id_count
FROM `wajenigeria.waje_ng_firebase_h5.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260827' AND '20260827'
GROUP BY event_table_day;

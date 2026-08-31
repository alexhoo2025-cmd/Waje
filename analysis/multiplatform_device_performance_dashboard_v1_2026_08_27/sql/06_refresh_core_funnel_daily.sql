-- V1 keeps client behavior, server-observed events and business-success facts separate.
-- Origin source mapping currently lacks a certified app-package mapping, so server stages remain origin_unmapped.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 7 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.mart_core_funnel_daily` (
  metric_date_lagos DATE NOT NULL,
  endpoint STRING NOT NULL,
  platform STRING NOT NULL,
  app_package STRING NOT NULL,
  app_version STRING NOT NULL,
  funnel_stage STRING NOT NULL,
  stage_kind STRING NOT NULL,
  stage_event_count INT64,
  source_is_server BOOL NOT NULL,
  business_success_confirmed BOOL NOT NULL,
  data_cutoff_at TIMESTAMP,
  complete_day BOOL NOT NULL,
  quality_status STRING NOT NULL,
  quality_note STRING NOT NULL,
  metric_definition_version STRING NOT NULL,
  refreshed_at TIMESTAMP NOT NULL
)
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, app_version, funnel_stage
OPTIONS(description = 'Client behavior and Origin server-event aggregate stages. Neither client attempt nor server event is automatically a business-success metric.');

DELETE FROM `wajenigeria.waje_device_performance_mart.mart_core_funnel_daily`
WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date;

INSERT INTO `wajenigeria.waje_device_performance_mart.mart_core_funnel_daily`
WITH client_behavior AS (
  SELECT
    metric_date_lagos,
    endpoint,
    platform,
    app_package,
    app_version,
    CASE core_role
      WHEN 'session_start' THEN 'session_start'
      WHEN 'page_view' THEN 'page_or_screen_view'
      WHEN 'screen_view' THEN 'page_or_screen_view'
      WHEN 'register_behavior' THEN 'register_behavior'
      WHEN 'recharge_behavior' THEN 'recharge_behavior'
    END AS funnel_stage,
    SUM(event_count) AS stage_event_count,
    MAX(event_data_cutoff_at) AS data_cutoff_at,
    LOGICAL_AND(complete_day) AS complete_day,
    MAX(quality_status) AS quality_status
  FROM `wajenigeria.waje_device_performance_mart.mart_event_session_daily`
  WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date
    AND include_in_client_behavior_funnel
    AND core_role IN ('session_start', 'page_view', 'screen_view', 'register_behavior', 'recharge_behavior')
  GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version, funnel_stage
), origin_register AS (
  SELECT
    target_day AS metric_date_lagos,
    COUNT(*) AS stage_event_count
  FROM `wajenigeria.origin_hfyl.view_event_register`
  WHERE target_day BETWEEN refresh_start_date AND refresh_end_date
  GROUP BY metric_date_lagos
), origin_server AS (
  SELECT
    target_day AS metric_date_lagos,
    event_type,
    COUNT(*) AS stage_event_count
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN refresh_start_date AND refresh_end_date
    AND event_type IN ('LOGIN', 'GAMESTART', 'GAMEEND')
  GROUP BY metric_date_lagos, event_type
), server_stages AS (
  SELECT metric_date_lagos, 'server_register_event' AS funnel_stage, stage_event_count FROM origin_register
  UNION ALL
  SELECT metric_date_lagos,
    CASE event_type WHEN 'LOGIN' THEN 'server_login_event' WHEN 'GAMESTART' THEN 'server_game_start_event' WHEN 'GAMEEND' THEN 'server_game_end_event' END,
    stage_event_count
  FROM origin_server
)
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  app_version,
  funnel_stage,
  'client_behavior' AS stage_kind,
  stage_event_count,
  FALSE AS source_is_server,
  FALSE AS business_success_confirmed,
  data_cutoff_at,
  complete_day,
  quality_status,
  'Client event count only. It indicates behavior or attempt, not a server-confirmed business result.' AS quality_note,
  'v1' AS metric_definition_version,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM client_behavior
UNION ALL
SELECT
  metric_date_lagos,
  'origin_unmapped' AS endpoint,
  'Origin' AS platform,
  'unknown' AS app_package,
  'unknown' AS app_version,
  funnel_stage,
  'server_event' AS stage_kind,
  stage_event_count,
  TRUE AS source_is_server,
  FALSE AS business_success_confirmed,
  NULL AS data_cutoff_at,
  metric_date_lagos < CURRENT_DATE('Africa/Lagos') AS complete_day,
  'provisional_source_mapping' AS quality_status,
  'Server event is observed from Origin but app-package mapping and is_success semantics are not yet certified. It is not presented as a business-success rate.' AS quality_note,
  'v1' AS metric_definition_version,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM server_stages;

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.mart_metric_status` (
  metric_date_lagos DATE NOT NULL,
  endpoint STRING NOT NULL,
  metric_domain STRING NOT NULL,
  metric_name STRING NOT NULL,
  status STRING NOT NULL,
  reason STRING NOT NULL,
  owner_action STRING NOT NULL,
  refreshed_at TIMESTAMP NOT NULL
)
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, metric_domain, status
OPTIONS(description = 'Explicit non-numeric status facts. Use to represent data_gap, blocked, delayed and immature metrics without fabricating zeroes.');

DELETE FROM `wajenigeria.waje_device_performance_mart.mart_metric_status`
WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date;

INSERT INTO `wajenigeria.waje_device_performance_mart.mart_metric_status`
SELECT
  calendar_day AS metric_date_lagos,
  endpoint,
  metric_domain,
  metric_name,
  status,
  reason,
  owner_action,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM UNNEST(GENERATE_DATE_ARRAY(refresh_start_date, refresh_end_date)) AS calendar_day
CROSS JOIN UNNEST([
  STRUCT('h5' AS endpoint, 'performance' AS metric_domain, 'h5_web_vitals' AS metric_name, 'data_gap' AS status,
    'Current H5 Firebase Analytics contains only standard behavior events; no Web Vitals, route ready, core request latency or front-end error event is ingested.' AS reason,
    'Implement the approved H5 V2 RUM event contract before enabling H5 performance cards.' AS owner_action),
  STRUCT('h5', 'core_funnel', 'game_ready_and_bet_ready', 'blocked',
    'No H5 game-ready, bet-ready or server-confirmed aggregate source is currently mapped.',
    'Add H5_GAME_LOAD, H5_GAME_READY, H5_BET_READY and Origin aggregate mapping.'),
  STRUCT('origin_unmapped', 'core_funnel', 'origin_package_mapping_and_success_semantics', 'provisional',
    'Origin server events are available but package mapping and is_success semantics are not certified.',
    'Certify app_id/client_type mapping and event success enums before cross-end funnel comparison.'),
  STRUCT('ios_existing', 'stability', 'ios_crashlytics', 'data_gap',
    'No iOS Crashlytics table is currently visible in the enterprise project.',
    'Configure or locate the current iOS Crashlytics export before stability cards are enabled.'),
  STRUCT('all_native', 'data_quality', 'sessions_performance_collection_flag', 'quality_warning',
    'Android Sessions has performance_data_collection_enabled=false while Performance tables contain actual records.',
    'Use Performance table freshness/coverage as the authoritative source and investigate Sessions flag semantics.')
]);

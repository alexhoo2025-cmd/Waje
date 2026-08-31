CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.dim_endpoint` (
  endpoint STRING NOT NULL,
  platform STRING NOT NULL,
  app_package STRING NOT NULL,
  analytics_source STRING,
  performance_source STRING,
  crashlytics_source STRING,
  sessions_source STRING,
  source_status STRING NOT NULL,
  source_mapping_version STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL
)
OPTIONS(description = 'Approved endpoint-to-Firebase source mapping for aggregate-only device and performance analytics.');

MERGE `wajenigeria.waje_device_performance_mart.dim_endpoint` AS target
USING (
  SELECT endpoint, platform, app_package, analytics_source, performance_source, crashlytics_source, sessions_source, source_status, source_mapping_version, updated_at FROM UNNEST([
    STRUCT('android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package,
      'waje_ng_firebase_android.events_*' AS analytics_source,
      'waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID' AS performance_source,
      'waje_ng_firebase_android_crashlytics.com_hfhy_waje_special_ANDROID' AS crashlytics_source,
      'waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID' AS sessions_source,
      'provisional' AS source_status, 'v1' AS source_mapping_version, CURRENT_TIMESTAMP() AS updated_at),
    STRUCT('android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame',
      'waje_ng_firebase_android.events_*',
      'waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID',
      'waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_palmgame_ANDROID',
      'waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID',
      'provisional', 'v1', CURRENT_TIMESTAMP()),
    STRUCT('android_transsion_new', 'Android', 'com.hfhy.wajecasino.game',
      'waje_ng_firebase_android.events_*',
      'waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID',
      'waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_game_ANDROID',
      'waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID',
      'provisional', 'v1', CURRENT_TIMESTAMP()),
    STRUCT('ios_existing', 'iOS', 'com.wajegame.wajegame',
      'waje_ng_firebase_ios.events_*',
      'waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS',
      NULL, NULL,
      'provisional_source_mapping', 'v1', CURRENT_TIMESTAMP()),
    STRUCT('h5', 'H5', 'waje_ng_firebase_h5',
      'waje_ng_firebase_h5.events_*',
      NULL, NULL, NULL,
      'behavior_only_no_rum', 'v1', CURRENT_TIMESTAMP())
  ])
) AS source
ON target.endpoint = source.endpoint
WHEN MATCHED THEN UPDATE SET
  platform = source.platform,
  app_package = source.app_package,
  analytics_source = source.analytics_source,
  performance_source = source.performance_source,
  crashlytics_source = source.crashlytics_source,
  sessions_source = source.sessions_source,
  source_status = source.source_status,
  source_mapping_version = source.source_mapping_version,
  updated_at = source.updated_at
WHEN NOT MATCHED THEN INSERT ROW;

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.dim_event_taxonomy` (
  event_name STRING NOT NULL,
  event_category STRING NOT NULL,
  core_role STRING NOT NULL,
  include_in_engagement BOOL NOT NULL,
  include_in_client_behavior_funnel BOOL NOT NULL,
  taxonomy_version STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL
)
OPTIONS(description = 'Approved event-name taxonomy. Unknown events must remain unclassified and excluded from business funnels.');

MERGE `wajenigeria.waje_device_performance_mart.dim_event_taxonomy` AS target
USING (
  SELECT event_name, event_category, core_role, include_in_engagement, include_in_client_behavior_funnel, taxonomy_version, updated_at FROM UNNEST([
    STRUCT('session_start' AS event_name, 'lifecycle' AS event_category, 'session_start' AS core_role, TRUE AS include_in_engagement, TRUE AS include_in_client_behavior_funnel, 'v1' AS taxonomy_version, CURRENT_TIMESTAMP() AS updated_at),
    STRUCT('first_visit', 'lifecycle', 'first_visit', TRUE, FALSE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('first_open', 'lifecycle', 'first_open', TRUE, FALSE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('user_engagement', 'lifecycle', 'engagement', TRUE, FALSE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('page_view', 'page_experience', 'page_view', TRUE, TRUE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('screen_view', 'page_experience', 'screen_view', TRUE, TRUE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('register', 'business_behavior', 'register_behavior', FALSE, TRUE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('recharge', 'business_behavior', 'recharge_behavior', FALSE, TRUE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('withdraw', 'business_behavior', 'withdraw_behavior', FALSE, FALSE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('firstCharge', 'business_behavior', 'first_charge_behavior', FALSE, TRUE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('app_exception', 'stability_signal', 'client_exception_behavior', FALSE, FALSE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('notification_receive', 'notification', 'notification_receive', FALSE, FALSE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('notification_dismiss', 'notification', 'notification_dismiss', FALSE, FALSE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('notification_foreground', 'notification', 'notification_foreground', FALSE, FALSE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('notification_open', 'notification', 'notification_open', FALSE, FALSE, 'v1', CURRENT_TIMESTAMP())
  ])
) AS source
ON target.event_name = source.event_name
WHEN MATCHED THEN UPDATE SET
  event_category = source.event_category,
  core_role = source.core_role,
  include_in_engagement = source.include_in_engagement,
  include_in_client_behavior_funnel = source.include_in_client_behavior_funnel,
  taxonomy_version = source.taxonomy_version,
  updated_at = source.updated_at
WHEN NOT MATCHED THEN INSERT ROW;

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.dim_performance_trace` (
  event_type STRING NOT NULL,
  trace_category STRING NOT NULL,
  safe_for_dashboard BOOL NOT NULL,
  mapping_version STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL
)
OPTIONS(description = 'Safe performance trace categorization. Raw event_name is intentionally excluded because network request names can contain URL patterns.');

MERGE `wajenigeria.waje_device_performance_mart.dim_performance_trace` AS target
USING (
  SELECT event_type, trace_category, safe_for_dashboard, mapping_version, updated_at FROM UNNEST([
    STRUCT('DURATION_TRACE' AS event_type, 'duration_trace' AS trace_category, TRUE AS safe_for_dashboard, 'v1' AS mapping_version, CURRENT_TIMESTAMP() AS updated_at),
    STRUCT('SCREEN_TRACE', 'screen_trace', TRUE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('NETWORK_REQUEST', 'network_request', TRUE, 'v1', CURRENT_TIMESTAMP()),
    STRUCT('TRACE_METRIC', 'trace_metric', TRUE, 'v1', CURRENT_TIMESTAMP())
  ])
) AS source
ON target.event_type = source.event_type
WHEN MATCHED THEN UPDATE SET
  trace_category = source.trace_category,
  safe_for_dashboard = source.safe_for_dashboard,
  mapping_version = source.mapping_version,
  updated_at = source.updated_at
WHEN NOT MATCHED THEN INSERT ROW;

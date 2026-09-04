-- Metadata only. Candidate tables are not a certification of their business meaning.
SELECT
  table_name,
  field_path,
  data_type,
  description
FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE table_name IN (
  'history_event_client',
  'history_event_server',
  'realtime_event_client',
  'realtime_event_server',
  'realtime_event_details',
  'view_event_game',
  'view_metaevent_gamestart',
  'view_metaevent_gameend',
  'view_metaevent_betreward',
  'sys_game'
)
AND REGEXP_CONTAINS(
  LOWER(field_path),
  r'(target_day|server_time|local_time|time|event_type|game_type|game_id|user_id|play_id|room_id|session_id|bet|reward|score|robot|is_robot|user_type|package)'
)
ORDER BY table_name, field_path
LIMIT 3000;

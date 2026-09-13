-- Planned only; not executed while BigQuery MCP authorization is unavailable.
-- Confirm view lineage first. This does not establish native daily-table ETL by itself.
SELECT table_name, view_definition
FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.VIEWS`
WHERE table_name IN ('view_metaevent_active_events', 'view_user_version_daily')
LIMIT 20;

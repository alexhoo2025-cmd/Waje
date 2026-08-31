-- Waje App / H5 BigQuery schema inventory (read-only, aggregate/metadata only)
-- Target project: waje-analytics-readonly, dataset: analytics_504208609, location: US
-- Do not select raw events, user_id, user_pseudo_id, advertising_id, cookies, tokens,
-- complete URLs, transaction values, or other row-level identifiers.

-- 1. Dataset/table inventory
SELECT table_name, table_type, creation_time
FROM `waje-analytics-readonly.analytics_504208609.INFORMATION_SCHEMA.TABLES`
ORDER BY table_name DESC;

-- 2. Daily row counts and event-date boundaries
SELECT
  _TABLE_SUFFIX AS table_suffix,
  COUNT(*) AS row_count,
  COUNT(DISTINCT event_name) AS distinct_event_names,
  MIN(event_date) AS min_event_date,
  MAX(event_date) AS max_event_date
FROM `waje-analytics-readonly.analytics_504208609.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260822'
GROUP BY table_suffix
ORDER BY table_suffix;

-- 3. Complete nested schema paths; run once per table or for all listed tables.
SELECT table_name, field_path, data_type, description
FROM `waje-analytics-readonly.analytics_504208609.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE table_name IN ('events_20260820', 'events_20260821', 'events_20260822')
ORDER BY table_name, field_path;

-- 4. Schema consistency across the three daily tables
SELECT
  table_name,
  COUNT(*) AS field_path_count,
  COUNTIF(STRPOS(field_path, '.') = 0) AS top_level_count
FROM `waje-analytics-readonly.analytics_504208609.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE table_name IN ('events_20260820', 'events_20260821', 'events_20260822')
GROUP BY table_name
ORDER BY table_name;

-- 5. H5 Web platform/stream profile and App-field coverage
SELECT
  COALESCE(platform, '(not set)') AS platform,
  COALESCE(stream_id, '(not set)') AS stream_id,
  COUNT(*) AS event_count,
  COUNTIF(app_info.id IS NOT NULL) AS app_info_id_present,
  COUNTIF(app_info.firebase_app_id IS NOT NULL) AS firebase_app_id_present,
  COUNTIF(app_info.version IS NOT NULL) AS app_version_present
FROM `waje-analytics-readonly.analytics_504208609.events_20260822`
GROUP BY platform, stream_id
ORDER BY event_count DESC;

-- 6. Latest observed event-parameter keys (key names and occurrence counts only)
SELECT ep.key AS parameter_key, COUNT(*) AS occurrences
FROM `waje-analytics-readonly.analytics_504208609.events_20260822`,
  UNNEST(event_params) ep
GROUP BY parameter_key
ORDER BY occurrences DESC
LIMIT 100;

-- App-side note:
-- The target project currently exposes no Firebase Android App export dataset/table.
-- Do not replace the verified H5 table with guessed Firebase Performance table names.
-- After waje-nigeria read access is restored, inventory its actual dataset/table/schema
-- before adding App fields to this dictionary.

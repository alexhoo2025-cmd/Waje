-- Waje H5 GA4 BigQuery schema inventory (read-only, metadata and aggregate only)
-- Source: waje-analytics-readonly.analytics_504208609, location US.
-- Do not select raw event rows, user identifiers, transaction identifiers,
-- advertising identifiers, complete URLs, cookies, tokens or parameter values.

-- 1. H5 table inventory
SELECT table_name, table_type, creation_time
FROM `waje-analytics-readonly.analytics_504208609.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE 'events_%'
ORDER BY table_name;

-- 2. Daily volume and event-date coverage
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

-- 3. Curated H5 field paths. The source GA4 schema has 217 paths;
-- this H5 dictionary excludes nine non-Web semantic fields.
SELECT table_name, field_path, data_type, description
FROM `waje-analytics-readonly.analytics_504208609.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE table_name IN ('events_20260820', 'events_20260821', 'events_20260822')
  AND field_path NOT LIKE 'app_info%'
  AND field_path NOT IN (
    'device.advertising_id',
    'device.is_limited_ad_tracking',
    'device.vendor_id'
  )
ORDER BY table_name, field_path;

-- 4. Confirm H5 platform and stream only.
SELECT
  platform,
  stream_id,
  COUNT(*) AS event_count
FROM `waje-analytics-readonly.analytics_504208609.events_20260822`
GROUP BY platform, stream_id
ORDER BY event_count DESC;

-- 5. Latest observed event parameter keys; no parameter values returned.
SELECT ep.key AS parameter_key, COUNT(*) AS occurrences
FROM `waje-analytics-readonly.analytics_504208609.events_20260822`,
  UNNEST(event_params) ep
GROUP BY parameter_key
ORDER BY occurrences DESC
LIMIT 100;

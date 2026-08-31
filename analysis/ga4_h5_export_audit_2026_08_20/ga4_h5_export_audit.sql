-- GA4 H5 BigQuery export audit (aggregate-only).
-- Target: waje-analytics-readonly.analytics_504208609 (US Sandbox).
-- Run only after the GA4 link is submitted and events_YYYYMMDD tables appear.

-- 1) Export asset inventory and freshness.
SELECT
  table_name,
  table_type,
  creation_time
FROM `waje-analytics-readonly.analytics_504208609.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE 'events_%'
ORDER BY table_name DESC;

-- 2) Daily event continuity and volume for stable data only.
-- Excludes the most recent 3 property-timezone days because GA4 can update daily tables late.
SELECT
  event_date,
  COUNT(*) AS event_count,
  COUNT(DISTINCT event_name) AS distinct_event_names
FROM `waje-analytics-readonly.analytics_504208609.events_*`
WHERE _TABLE_SUFFIX BETWEEN 'YYYYMMDD' AND 'YYYYMMDD'
GROUP BY event_date
ORDER BY event_date;

-- 3) Event taxonomy coverage over the latest stable 28-day period.
SELECT
  event_name,
  COUNT(*) AS event_count
FROM `waje-analytics-readonly.analytics_504208609.events_*`
WHERE _TABLE_SUFFIX BETWEEN 'YYYYMMDD' AND 'YYYYMMDD'
GROUP BY event_name
ORDER BY event_count DESC;

-- 4) Host coverage over the latest stable 28-day period.
-- This returns aggregate traffic only; it does not expose user identifiers.
SELECT
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_location,
  COUNT(*) AS page_view_events
FROM `waje-analytics-readonly.analytics_504208609.events_*`
WHERE _TABLE_SUFFIX BETWEEN 'YYYYMMDD' AND 'YYYYMMDD'
  AND event_name = 'page_view'
GROUP BY page_location
HAVING page_view_events >= 10
ORDER BY page_view_events DESC;

-- Compare the daily result from query 2 with the GA4 Data API baseline for the
-- same Africa/Lagos dates. Flag a difference greater than 5% only after stream
-- selection, exclusions, and date boundaries are confirmed identical.

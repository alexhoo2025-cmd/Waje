-- Aggregate-only Phoenix cohort event inventory for payment-event contract validation.
-- It returns names and counts only, never event parameter values or users.
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS activity_date,
    event_name,
    user_pseudo_id,
    EXISTS (
      SELECT 1 FROM UNNEST(event_params) AS parameter
      WHERE parameter.key = 'page_location'
        AND REGEXP_CONTAINS(LOWER(COALESCE(parameter.value.string_value, '')), r'(^|[?&])p=h5phx([&#]|$)')
    ) AS h5phx_marker
  FROM `wajenigeria.analytics_517134955.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260828' AND '20260902'
    AND event_date BETWEEN '20260828' AND '20260902'
    AND user_pseudo_id IS NOT NULL AND user_pseudo_id != ''
), cohort AS (
  SELECT user_pseudo_id, MIN(activity_date) AS cohort_date
  FROM raw_events
  WHERE event_name = 'first_visit' AND h5phx_marker
  GROUP BY user_pseudo_id
)
SELECT
  raw_events.event_name,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(raw_events.user_pseudo_id) AS approx_cohort_subjects,
  MIN(raw_events.activity_date) AS first_observed_date,
  MAX(raw_events.activity_date) AS last_observed_date
FROM raw_events
JOIN cohort USING (user_pseudo_id)
WHERE raw_events.activity_date BETWEEN cohort.cohort_date AND DATE '2026-09-02'
GROUP BY raw_events.event_name
HAVING APPROX_COUNT_DISTINCT(raw_events.user_pseudo_id) >= 10
ORDER BY event_count DESC, raw_events.event_name
LIMIT 3000;

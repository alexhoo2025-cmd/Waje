-- Aggregate-only Phoenix p=h5phx Firebase client retention diagnosis.
-- A user qualifies on first_visit whose page URL contains p=h5phx.
-- No URLs or identifiers are returned.
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
), daily_activity AS (
  SELECT
    activity_date,
    user_pseudo_id,
    LOGICAL_OR(event_name = 'session_start') AS has_session_start,
    LOGICAL_OR(event_name = 'page_view') AS has_page_view,
    COUNT(*) AS event_count
  FROM raw_events
  GROUP BY activity_date, user_pseudo_id
)
SELECT
  cohort_date,
  COUNT(*) AS cohort_users,
  COUNTIF(EXISTS(SELECT 1 FROM daily_activity WHERE daily_activity.user_pseudo_id = cohort.user_pseudo_id AND daily_activity.activity_date = cohort.cohort_date AND daily_activity.has_session_start)) AS cohort_day_session_start_users,
  COUNTIF(EXISTS(SELECT 1 FROM daily_activity WHERE daily_activity.user_pseudo_id = cohort.user_pseudo_id AND daily_activity.activity_date = cohort.cohort_date AND daily_activity.has_page_view)) AS cohort_day_page_view_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), COUNTIF(EXISTS(SELECT 1 FROM daily_activity WHERE daily_activity.user_pseudo_id = cohort.user_pseudo_id AND daily_activity.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 1 DAY))), NULL) AS day_2_any_event_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), COUNTIF(EXISTS(SELECT 1 FROM daily_activity WHERE daily_activity.user_pseudo_id = cohort.user_pseudo_id AND daily_activity.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 1 DAY) AND daily_activity.has_session_start)), NULL) AS day_2_session_start_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), COUNTIF(EXISTS(SELECT 1 FROM daily_activity WHERE daily_activity.user_pseudo_id = cohort.user_pseudo_id AND daily_activity.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 1 DAY) AND daily_activity.has_page_view)), NULL) AS day_2_page_view_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), COUNTIF(EXISTS(SELECT 1 FROM daily_activity WHERE daily_activity.user_pseudo_id = cohort.user_pseudo_id AND daily_activity.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 3 DAY))), NULL) AS day_4_any_event_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), COUNTIF(EXISTS(SELECT 1 FROM daily_activity WHERE daily_activity.user_pseudo_id = cohort.user_pseudo_id AND daily_activity.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 3 DAY) AND daily_activity.has_session_start)), NULL) AS day_4_session_start_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), COUNTIF(EXISTS(SELECT 1 FROM daily_activity WHERE daily_activity.user_pseudo_id = cohort.user_pseudo_id AND daily_activity.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 3 DAY) AND daily_activity.has_page_view)), NULL) AS day_4_page_view_users,
  DATE '2026-09-02' AS data_cutoff_date
FROM cohort
WHERE cohort_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-02'
GROUP BY cohort_date
HAVING COUNT(*) >= 10
ORDER BY cohort_date;

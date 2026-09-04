-- Aggregate-only Phoenix cohort retention; no identifiers or URL values are returned.
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS activity_date,
    event_name,
    user_pseudo_id,
    EXISTS (
      SELECT 1
      FROM UNNEST(event_params) AS parameter
      WHERE parameter.key = 'page_location'
        AND REGEXP_CONTAINS(
          LOWER(COALESCE(parameter.value.string_value, '')),
          r'(^|[?&])p=h5phx([&#]|$)'
        )
    ) AS h5phx_marker
  FROM `wajenigeria.analytics_517134955.events_*`
  WHERE REGEXP_CONTAINS(_TABLE_SUFFIX, r'^\d{8}$')
    AND _TABLE_SUFFIX BETWEEN '20260828' AND '20260902'
    AND event_date BETWEEN '20260828' AND '20260902'
    AND user_pseudo_id IS NOT NULL
    AND user_pseudo_id != ''
),
cohort AS (
  SELECT user_pseudo_id, MIN(activity_date) AS cohort_date
  FROM raw_events
  WHERE event_name = 'first_visit' AND h5phx_marker
  GROUP BY user_pseudo_id
),
active_day AS (
  SELECT DISTINCT user_pseudo_id, activity_date
  FROM raw_events
  WHERE event_name = 'session_start'
),
daily AS (
  SELECT
    cohort.cohort_date,
    COUNT(DISTINCT cohort.user_pseudo_id) AS cohort_users,
    COUNT(DISTINCT IF(active_day.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 1 DAY), cohort.user_pseudo_id, NULL)) AS day_plus_1_users,
    COUNT(DISTINCT IF(active_day.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 3 DAY), cohort.user_pseudo_id, NULL)) AS day_plus_3_users,
    COUNT(DISTINCT IF(active_day.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 7 DAY), cohort.user_pseudo_id, NULL)) AS day_plus_7_users
  FROM cohort
  LEFT JOIN active_day USING (user_pseudo_id)
  GROUP BY cohort.cohort_date
)
SELECT
  cohort_date,
  cohort_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), day_plus_1_users, NULL) AS day_plus_1_retained_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), SAFE_DIVIDE(day_plus_1_users, cohort_users), NULL) AS day_plus_1_active_retention_rate,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), day_plus_3_users, NULL) AS day_plus_3_retained_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), SAFE_DIVIDE(day_plus_3_users, cohort_users), NULL) AS day_plus_3_active_retention_rate,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 7 DAY), day_plus_7_users, NULL) AS day_plus_7_retained_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 7 DAY), SAFE_DIVIDE(day_plus_7_users, cohort_users), NULL) AS day_plus_7_active_retention_rate,
  DATE '2026-09-02' AS data_cutoff_date
FROM daily
WHERE cohort_users >= 10
ORDER BY cohort_date

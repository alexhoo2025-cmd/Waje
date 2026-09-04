-- Aggregate-only diagnostic: tagged Phoenix link versus untagged Phoenix Browser control.
-- No user identifiers, URL values, or browser-version/device details are returned.
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS activity_date,
    event_name,
    user_pseudo_id,
    COALESCE(NULLIF(device.web_info.browser, ''), '(unknown)') AS browser,
    traffic_source.source AS first_source,
    traffic_source.medium AS first_medium,
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
first_visit AS (
  SELECT
    user_pseudo_id,
    activity_date AS cohort_date,
    CASE
      WHEN h5phx_marker THEN 'Phoenix 标记链接'
      WHEN browser = 'Phoenix Browser' THEN 'Phoenix Browser 未标记对照'
      WHEN LOWER(COALESCE(first_source, '')) = '(direct)'
       AND LOWER(COALESCE(first_medium, '')) = '(none)' THEN '其他浏览器直接访问'
      ELSE '其他浏览器有归因访问'
    END AS cohort_segment
  FROM raw_events
  WHERE event_name = 'first_visit'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY activity_date) = 1
),
active_day AS (
  SELECT DISTINCT user_pseudo_id, activity_date
  FROM raw_events
  WHERE event_name = 'session_start'
),
daily AS (
  SELECT
    first_visit.cohort_segment,
    first_visit.cohort_date,
    COUNT(DISTINCT first_visit.user_pseudo_id) AS cohort_users,
    COUNT(DISTINCT IF(active_day.activity_date = DATE_ADD(first_visit.cohort_date, INTERVAL 1 DAY), first_visit.user_pseudo_id, NULL)) AS day_plus_1_users,
    COUNT(DISTINCT IF(active_day.activity_date = DATE_ADD(first_visit.cohort_date, INTERVAL 3 DAY), first_visit.user_pseudo_id, NULL)) AS day_plus_3_users
  FROM first_visit
  LEFT JOIN active_day USING (user_pseudo_id)
  GROUP BY first_visit.cohort_segment, first_visit.cohort_date
)
SELECT
  cohort_segment,
  cohort_date,
  cohort_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), day_plus_1_users, NULL) AS day_plus_1_retained_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), SAFE_DIVIDE(day_plus_1_users, cohort_users), NULL) AS day_plus_1_active_retention_rate,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), day_plus_3_users, NULL) AS day_plus_3_retained_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), SAFE_DIVIDE(day_plus_3_users, cohort_users), NULL) AS day_plus_3_active_retention_rate,
  DATE '2026-09-02' AS data_cutoff_date
FROM daily
WHERE cohort_users >= 10
ORDER BY cohort_segment, cohort_date;

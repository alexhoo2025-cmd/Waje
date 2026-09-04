-- Aggregate-only first-day frontend interaction proxy for Phoenix and controls.
-- It does not return user IDs, URLs, page titles, parameter values, or sessions.
-- Page-view depth is a navigation proxy, not a page-load performance measure.
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS activity_date,
    event_name,
    user_pseudo_id,
    COALESCE(NULLIF(device.web_info.browser, ''), '(unknown)') AS browser,
    traffic_source.source AS first_source,
    traffic_source.medium AS first_medium,
    COALESCE((
      SELECT MAX(parameter.value.int_value)
      FROM UNNEST(event_params) AS parameter
      WHERE parameter.key = 'engagement_time_msec'
    ), 0) AS engagement_time_msec,
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
first_day_by_user AS (
  SELECT
    first_visit.cohort_segment,
    first_visit.user_pseudo_id,
    COUNTIF(raw_events.event_name = 'page_view') AS day0_page_view_events,
    COUNTIF(raw_events.event_name = 'scroll') AS day0_scroll_events,
    COUNTIF(raw_events.event_name = 'form_start') AS day0_form_start_events,
    COUNTIF(raw_events.event_name = 'user_engagement') AS day0_user_engagement_events,
    SUM(raw_events.engagement_time_msec) AS day0_engagement_time_msec
  FROM first_visit
  JOIN raw_events
    ON raw_events.user_pseudo_id = first_visit.user_pseudo_id
   AND raw_events.activity_date = first_visit.cohort_date
  GROUP BY first_visit.cohort_segment, first_visit.user_pseudo_id
)
SELECT
  cohort_segment,
  COUNT(*) AS first_visit_users,
  SUM(day0_page_view_events) AS page_view_events,
  SAFE_DIVIDE(SUM(day0_page_view_events), COUNT(*)) AS average_page_views_per_first_visit,
  COUNTIF(day0_page_view_events >= 2) AS multi_page_users,
  SAFE_DIVIDE(COUNTIF(day0_page_view_events >= 2), COUNT(*)) AS multi_page_user_rate,
  COUNTIF(day0_scroll_events > 0) AS scroll_users,
  COUNTIF(day0_form_start_events > 0) AS form_start_users,
  COUNTIF(day0_user_engagement_events > 0) AS user_engagement_users,
  COUNTIF(day0_engagement_time_msec > 0) AS positive_engagement_time_users,
  SAFE_DIVIDE(COUNTIF(day0_engagement_time_msec > 0), COUNT(*)) AS positive_engagement_time_rate
FROM first_day_by_user
GROUP BY cohort_segment
HAVING COUNT(*) >= 10
ORDER BY first_visit_users DESC;

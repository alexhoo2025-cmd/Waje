WITH profiles AS (
 SELECT DISTINCT user_id
 FROM `wajenigeria.origin_hfyl.user_events`
 WHERE target_day=DATE '2026-08-01' AND app_id=90006
 AND SAFE.PARSE_DATE('%Y-%m-%d',register_day)=DATE '2026-08-01'
 AND first_client_type=3
 AND COALESCE(download_channel,'') NOT IN ('PAWAJEH5PWA','PAWAJEH5PWAT','PAWAJEH5PWW')
 AND user_id IS NOT NULL AND user_id!=''
), paid AS (
 SELECT DISTINCT user_id
 FROM `wajenigeria.origin_hfyl.view_metaevent_order`
 WHERE target_day=DATE '2026-08-01' AND app_id=90006 AND is_success='pay_success'
 AND order_no IS NOT NULL AND order_no!=''
), daily AS (
 SELECT DISTINCT user_id
 FROM `wajenigeria.origin_hfyl.view_user_version_daily`
 WHERE target_day=DATE '2026-08-02' AND app_id=90006
), event_active AS (
 SELECT DISTINCT user_id
 FROM `wajenigeria.origin_hfyl.view_metaevent_active_events`
 WHERE target_day=DATE '2026-08-02' AND app_id=90006
 AND user_id IS NOT NULL AND user_id!=''
), flags AS (
 SELECT p.user_id,q.user_id IS NOT NULL AS is_paid,
 d.user_id IS NOT NULL AS daily_return,e.user_id IS NOT NULL AS event_return,
 DATE '2026-08-01' AS cohort_date
 FROM profiles p LEFT JOIN paid q ON p.user_id=q.user_id
 LEFT JOIN daily d ON p.user_id=d.user_id
 LEFT JOIN event_active e ON p.user_id=e.user_id
)
SELECT population,COUNT(*) AS users,COUNTIF(daily_return) AS daily_return_users,
 COUNTIF(event_return) AS event_return_users,
 COUNTIF(event_return AND NOT daily_return) AS event_only_return_users,
 COUNTIF(daily_return AND NOT event_return) AS daily_only_return_users
FROM flags
CROSS JOIN UNNEST(IF(is_paid,['全部新增用户','新增付费用户'],['全部新增用户'])) AS population
WHERE cohort_date=DATE '2026-08-01'
GROUP BY population
HAVING COUNT(*)>=10
LIMIT 10;

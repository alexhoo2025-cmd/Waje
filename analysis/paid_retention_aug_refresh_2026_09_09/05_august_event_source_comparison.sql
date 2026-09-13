-- Same base population, same app, same activity source for both cohorts.
WITH profile_rows AS (
 SELECT user_id,target_day AS profile_day,
 SAFE.PARSE_DATE('%Y-%m-%d',register_day) AS register_date,
 first_client_type,COALESCE(NULLIF(download_channel,''),'未记录') AS channel
 FROM `wajenigeria.origin_hfyl.user_events`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
 AND app_id=90006 AND user_id IS NOT NULL AND user_id!=''
), profiles AS (
 SELECT user_id,ARRAY_AGG(STRUCT(register_date,first_client_type,channel)
 ORDER BY profile_day DESC,register_date,first_client_type,channel LIMIT 1)[OFFSET(0)] AS p
 FROM profile_rows GROUP BY user_id
), pay_days AS (
 SELECT user_id,target_day AS payment_date
 FROM `wajenigeria.origin_hfyl.view_metaevent_order`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
 AND app_id=90006 AND is_success='pay_success'
 AND user_id IS NOT NULL AND user_id!='' AND order_no IS NOT NULL AND order_no!=''
 GROUP BY user_id,payment_date
), base AS (
 SELECT p.user_id,p.p.register_date AS cohort_date,
 CASE WHEN p.p.first_client_type=2 THEN 'Android'
 WHEN p.p.first_client_type=1 THEN 'iOS'
 WHEN p.p.first_client_type=3 AND p.p.channel IN ('PAWAJEH5PWA','PAWAJEH5PWAT','PAWAJEH5PWW') THEN 'PWA候选渠道'
 WHEN p.p.first_client_type=3 THEN 'H5（不含PWA候选渠道）'
 ELSE '平台未识别' END AS platform,
 q.user_id IS NOT NULL AS paid_on_registration
 FROM profiles p LEFT JOIN pay_days q ON p.user_id=q.user_id AND p.p.register_date=q.payment_date
 WHERE p.p.register_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
), activity AS (
 SELECT target_day AS activity_date,user_id
 FROM `wajenigeria.origin_hfyl.view_metaevent_active_events`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-09'
 AND app_id=90006 AND user_id IS NOT NULL AND user_id!=''
 GROUP BY activity_date,user_id
), calendar AS (
 SELECT activity_date,COUNT(*) AS accounts FROM activity GROUP BY activity_date
), segmented AS (
 SELECT b.user_id,b.cohort_date,population,segment AS platform,sample_mode
 FROM base b
 CROSS JOIN UNNEST(IF(b.paid_on_registration,['全部新增用户','新增付费用户'],['全部新增用户'])) AS population
 CROSS JOIN UNNEST(IF(b.platform IN ('Android','iOS'),[b.platform,'APP（Android+iOS）'],[b.platform])) AS segment
 CROSS JOIN UNNEST(['各日达标范围','固定8月1—27日']) AS sample_mode
 WHERE sample_mode='各日达标范围' OR cohort_date<=DATE '2026-08-27'
), flags AS (
 SELECT s.population,s.platform,s.sample_mode,s.cohort_date,d AS day_number,
 DATE_ADD(s.cohort_date,INTERVAL d-1 DAY)<=DATE '2026-09-09' AS within_window,
 c.activity_date IS NOT NULL AS date_available,
 a.user_id IS NOT NULL AS returned
 FROM segmented s CROSS JOIN UNNEST([2,3,4,5,6,7,8,9,10,11,12,13,14,30]) AS d
 LEFT JOIN calendar c ON c.activity_date=DATE_ADD(s.cohort_date,INTERVAL d-1 DAY)
 LEFT JOIN activity a ON a.user_id=s.user_id AND a.activity_date=DATE_ADD(s.cohort_date,INTERVAL d-1 DAY)
 WHERE s.sample_mode='各日达标范围' OR d<=14
)
SELECT population,platform,sample_mode,day_number,
 COUNT(*) AS cohort_users,
 COUNTIF(within_window) AS eligible_users,
 COUNTIF(within_window AND NOT date_available) AS eligible_users_missing_activity_date,
 IF(COUNTIF(within_window)>=10 AND COUNTIF(within_window AND NOT date_available)=0,
 COUNTIF(within_window AND returned),NULL) AS retained_users,
 IF(COUNTIF(within_window)>=10 AND COUNTIF(within_window AND NOT date_available)=0,
 SAFE_DIVIDE(COUNTIF(within_window AND returned),COUNTIF(within_window)),NULL) AS retention_rate,
 MIN(IF(within_window,cohort_date,NULL)) AS eligible_cohort_start,
 MAX(IF(within_window,cohort_date,NULL)) AS eligible_cohort_end,
 DATE '2026-09-09' AS data_cutoff
FROM flags
GROUP BY population,platform,sample_mode,day_number
HAVING COUNT(*)>=10
ORDER BY sample_mode,population,platform,day_number
LIMIT 3000;

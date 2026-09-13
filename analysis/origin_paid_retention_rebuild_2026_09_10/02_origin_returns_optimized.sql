WITH raw_profiles AS (
SELECT target_day AS cohort_date,app_id,xl_id,user_id,DATE(first_pay_date) AS first_pay_date,
 CASE
WHEN download_channel='WajeSpecial' AND first_media=80 THEN 'WajeSpecial-facebook'
WHEN download_channel='WajeSpecial' AND first_media=81 THEN 'WajeSpecial-googleadwords_int'
WHEN download_channel='WajeSpecial' AND first_media=84 THEN 'WajeSpecial-Google商店'
WHEN download_channel='PAWAJEIOS' AND first_media=58 THEN 'WAJEIOS-AppStore商店'
WHEN download_channel='PAWAJEBETH5' THEN 'WAJEBETH5'
WHEN download_channel='PAWAJEH5' AND first_media=80 THEN 'wajeH5-facebook'
WHEN download_channel='PAPAWAJEH5GA' AND first_media=81 THEN 'wajeH5ga-googlewords_int'
WHEN download_channel='PAWAJEH5PWW' AND first_media=80 THEN 'PWA'
ELSE NULL END AS sheet
FROM `wajenigeria.origin_hfyl.user_events`
WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND app_id=90006
), profiles AS (
SELECT cohort_date,sheet,xl_id,user_id,first_pay_date FROM raw_profiles
WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND sheet IS NOT NULL
)
, activity AS (
SELECT activity_date,xl_id FROM (
SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.view_event_server` WHERE target_day BETWEEN DATE '2026-08-02' AND DATE '2026-08-15' AND app_id=90006 AND event_type IN ('LOGIN','LOGOUT','REGISTER')
UNION ALL
SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.view_event_client` WHERE target_day BETWEEN DATE '2026-08-02' AND DATE '2026-08-15' AND app_id=90006 AND event_type IN ('LOGIN','LOGOUT','REGISTER','AL','AQ')
UNION ALL
SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.view_event_web` WHERE target_day BETWEEN DATE '2026-08-02' AND DATE '2026-08-15' AND app_id=90006 AND event_type IN ('AL','AQ','PD')
) GROUP BY activity_date,xl_id
), expanded AS (
SELECT p.cohort_date,p.sheet,p.xl_id,p.user_id,p.first_pay_date,day_number,
 DATE_ADD(p.cohort_date,INTERVAL day_number-1 DAY) AS observation_date,sample_mode
FROM profiles p CROSS JOIN UNNEST([2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]) AS day_number
CROSS JOIN UNNEST(['各日达标范围','固定8月1—26日']) AS sample_mode
WHERE (sample_mode='各日达标范围' OR (p.cohort_date<=DATE '2026-08-26' AND day_number<=15))
)
SELECT p.sheet,p.day_number,p.sample_mode,
MIN(p.cohort_date) AS cohort_start,MAX(p.cohort_date) AS cohort_end,
COUNT(DISTINCT CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id)) AS eligible_new,
COUNT(DISTINCT IF(a.xl_id IS NOT NULL,CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id),NULL)) AS returned_new,
COUNT(DISTINCT IF(p.cohort_date=p.first_pay_date,CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id),NULL)) AS eligible_new_paid,
COUNT(DISTINCT IF(p.cohort_date=p.first_pay_date AND a.xl_id IS NOT NULL,CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id),NULL)) AS returned_new_paid
FROM expanded p LEFT JOIN activity a ON p.xl_id=a.xl_id AND p.observation_date=a.activity_date
WHERE p.observation_date BETWEEN DATE '2026-08-02' AND DATE '2026-08-15'
GROUP BY p.sheet,p.day_number,p.sample_mode
HAVING eligible_new>=10
ORDER BY p.sheet,p.sample_mode,p.day_number LIMIT 3000;

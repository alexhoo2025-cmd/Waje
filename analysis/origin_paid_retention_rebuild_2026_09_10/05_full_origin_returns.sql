WITH profiles AS (
SELECT target_day AS initial_date,DATE(first_pay_date) AS first_pay_date,xl_id,user_id,
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
WHERE app_id=90006 AND target_day<=DATE '2026-09-09'
AND (target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
OR DATE(first_pay_date) BETWEEN DATE '2026-08-01' AND DATE '2026-08-31')
), cohorts AS (
SELECT initial_date AS cohort_date,xl_id,user_id,sheet,'全部新增' AS population
FROM profiles WHERE initial_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND sheet IS NOT NULL
UNION ALL
SELECT initial_date,xl_id,user_id,sheet,'新增付费'
FROM profiles WHERE initial_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND initial_date=first_pay_date AND sheet IS NOT NULL
UNION ALL
SELECT first_pay_date,xl_id,user_id,sheet,'首次付费'
FROM profiles WHERE first_pay_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND sheet IS NOT NULL
), activity AS (
SELECT activity_date,xl_id FROM (
SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.view_event_server` WHERE target_day BETWEEN DATE '2026-08-02' AND DATE '2026-09-09' AND app_id=90006 AND event_type IN ('LOGIN','LOGOUT','REGISTER') UNION ALL SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.view_event_client` WHERE target_day BETWEEN DATE '2026-08-02' AND DATE '2026-09-09' AND app_id=90006 AND event_type IN ('LOGIN','LOGOUT','REGISTER','AL','AQ') UNION ALL SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.view_event_web` WHERE target_day BETWEEN DATE '2026-08-02' AND DATE '2026-09-09' AND app_id=90006 AND event_type IN ('AL','AQ','PD')
) GROUP BY activity_date,xl_id
), expanded AS (
SELECT c.cohort_date,c.xl_id,c.user_id,c.sheet,c.population,day_number,sample_mode,
DATE_ADD(c.cohort_date,INTERVAL day_number-1 DAY) AS observation_date
FROM cohorts c CROSS JOIN UNNEST([2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]) AS day_number
CROSS JOIN UNNEST(['各日达标范围','固定8月1—26日']) AS sample_mode
WHERE sample_mode='各日达标范围' OR (c.cohort_date<=DATE '2026-08-26' AND day_number<=15)
)
SELECT p.sheet,p.population,p.day_number,p.sample_mode,
MIN(p.cohort_date) AS cohort_start,MAX(p.cohort_date) AS cohort_end,
COUNT(DISTINCT CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id)) AS eligible_xl_ids,
COUNT(DISTINCT CONCAT(CAST(p.cohort_date AS STRING),'|',p.user_id)) AS eligible_user_ids,
COUNT(DISTINCT IF(a.xl_id IS NOT NULL,CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id),NULL)) AS returned_xl_ids,
COUNT(DISTINCT IF(a.xl_id IS NOT NULL,CONCAT(CAST(p.cohort_date AS STRING),'|',p.user_id),NULL)) AS returned_user_ids
FROM expanded p LEFT JOIN activity a ON p.xl_id=a.xl_id AND p.observation_date=a.activity_date
WHERE p.observation_date BETWEEN DATE '2026-08-02' AND DATE '2026-09-09'
GROUP BY p.sheet,p.population,p.day_number,p.sample_mode
HAVING eligible_xl_ids>=10
ORDER BY p.sheet,p.population,p.sample_mode,p.day_number LIMIT 3000;

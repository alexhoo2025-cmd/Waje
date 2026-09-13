WITH mapping_raw AS (
SELECT user_id,xl_id,target_day,DATE(first_pay_date) AS first_pay_date,CASE WHEN download_channel='WajeSpecial' AND first_media=80 THEN 'WajeSpecial-facebook' WHEN download_channel='WajeSpecial' AND first_media=81 THEN 'WajeSpecial-googleadwords_int' WHEN download_channel='WajeSpecial' AND first_media=84 THEN 'WajeSpecial-Google商店' WHEN download_channel='PAWAJEIOS' AND first_media=58 THEN 'WAJEIOS-AppStore商店' WHEN download_channel='PAWAJEBETH5' THEN 'WAJEBETH5' WHEN download_channel='PAWAJEH5' AND first_media=80 THEN 'wajeH5-facebook' WHEN download_channel='PAPAWAJEH5GA' AND first_media=81 THEN 'wajeH5ga-googlewords_int' WHEN download_channel='PAWAJEH5PWW' AND first_media=80 THEN 'PWA' ELSE NULL END AS sheet
FROM `wajenigeria.origin_hfyl.user_events`
WHERE app_id=90006 AND target_day<=DATE '2026-09-09' AND download_channel IN ('PAPAWAJEH5GA','PAWAJEBETH5','PAWAJEH5','PAWAJEH5PWW','PAWAJEIOS','WajeSpecial')
), mapping AS (SELECT user_id,xl_id,target_day,first_pay_date,sheet FROM mapping_raw WHERE sheet IS NOT NULL),
registers AS (
SELECT target_day AS cohort_date,xl_id,user_id
FROM `wajenigeria.origin_hfyl.view_event_register`
WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND app_id=90006
), first_pay AS (
SELECT target_day AS cohort_date,user_id
FROM `wajenigeria.origin_hfyl.view_event_pay`
WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND app_id=90006
AND event_type='pay_success' AND is_first_buy IS TRUE
GROUP BY cohort_date,user_id
), facts AS (
SELECT r.cohort_date,m.sheet,'注册用户' AS metric,r.user_id
FROM registers r JOIN mapping m ON r.xl_id=m.xl_id
UNION ALL
SELECT p.cohort_date,m.sheet,'首充用户' AS metric,p.user_id
FROM first_pay p JOIN mapping m ON p.user_id=m.user_id
)
SELECT cohort_date,sheet,metric,COUNT(DISTINCT user_id) AS users
FROM facts WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
GROUP BY cohort_date,sheet,metric
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY cohort_date,sheet,metric LIMIT 3000;

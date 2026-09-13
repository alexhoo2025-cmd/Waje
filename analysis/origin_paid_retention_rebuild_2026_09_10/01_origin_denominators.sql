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
SELECT cohort_date,sheet,
COUNT(DISTINCT xl_id) AS new_xl_ids,
COUNT(DISTINCT IF(cohort_date=first_pay_date,xl_id,NULL)) AS new_paid_xl_ids,
COUNT(DISTINCT user_id) AS users,
COUNTIF(xl_id IS NULL OR xl_id='') AS empty_xl_rows,
COUNTIF(user_id IS NULL OR user_id='') AS empty_user_rows
FROM profiles GROUP BY cohort_date,sheet ORDER BY cohort_date,sheet LIMIT 3000;

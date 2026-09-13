WITH p AS (
SELECT target_day AS cohort_date,DATE(first_pay_date) AS first_pay_date,xl_id,user_id,CASE WHEN download_channel='WajeSpecial' AND first_media=80 THEN 'WajeSpecial-facebook' WHEN download_channel='WajeSpecial' AND first_media=81 THEN 'WajeSpecial-googleadwords_int' WHEN download_channel='WajeSpecial' AND first_media=84 THEN 'WajeSpecial-Google商店' WHEN download_channel='PAWAJEIOS' AND first_media=58 THEN 'WAJEIOS-AppStore商店' WHEN download_channel='PAWAJEBETH5' THEN 'WAJEBETH5' WHEN download_channel='PAWAJEH5' AND first_media=80 THEN 'wajeH5-facebook' WHEN download_channel='PAPAWAJEH5GA' AND first_media=81 THEN 'wajeH5ga-googlewords_int' WHEN download_channel='PAWAJEH5PWW' AND first_media=80 THEN 'PWA' ELSE NULL END AS sheet
FROM `wajenigeria.origin_hfyl.user_events`
WHERE app_id=90006 AND target_day<=DATE '2026-09-09'
AND (target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' OR DATE(first_pay_date) BETWEEN DATE '2026-08-01' AND DATE '2026-08-31')
), keys AS (
SELECT 'xl_id' AS key_type,xl_id AS key,COUNT(DISTINCT sheet) AS sheet_count,COUNT(DISTINCT cohort_date) AS date_count,COUNT(DISTINCT user_id) AS counterpart_count
FROM p WHERE sheet IS NOT NULL AND xl_id IS NOT NULL GROUP BY xl_id
UNION ALL
SELECT 'user_id',user_id,COUNT(DISTINCT sheet),COUNT(DISTINCT cohort_date),COUNT(DISTINCT xl_id)
FROM p WHERE sheet IS NOT NULL AND user_id IS NOT NULL AND user_id!='' GROUP BY user_id
)
SELECT key_type,COUNT(*) AS keys,COUNTIF(sheet_count>1) AS multiple_sheets,COUNTIF(date_count>1) AS multiple_dates,COUNTIF(counterpart_count>1) AS multiple_counterparts
FROM keys GROUP BY key_type HAVING COUNT(*)>=10 LIMIT 10;

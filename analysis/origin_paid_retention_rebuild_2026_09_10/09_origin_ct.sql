WITH media_map AS (
SELECT channel,ANY_VALUE(media_id) AS selected_media_id
FROM `wajenigeria.ares_hfyl.app_channel_media_package`
WHERE app_id=90006 GROUP BY channel HAVING COUNT(DISTINCT media_id)=1
), mapped AS (
SELECT t.target_day AS cohort_date,t.download_channel,CASE WHEN download_channel='WajeSpecial' AND m.selected_media_id=80 THEN 'WajeSpecial-facebook' WHEN download_channel='WajeSpecial' AND m.selected_media_id=81 THEN 'WajeSpecial-googleadwords_int' WHEN download_channel='WajeSpecial' AND m.selected_media_id=84 THEN 'WajeSpecial-Google商店' WHEN download_channel='PAWAJEIOS' AND m.selected_media_id=58 THEN 'WAJEIOS-AppStore商店' WHEN download_channel='PAWAJEBETH5' THEN 'WAJEBETH5' WHEN download_channel='PAWAJEH5' AND m.selected_media_id=80 THEN 'wajeH5-facebook' WHEN download_channel='PAPAWAJEH5GA' AND m.selected_media_id=81 THEN 'wajeH5ga-googlewords_int' WHEN download_channel='PAWAJEH5PWW' AND m.selected_media_id=80 THEN 'PWA' ELSE NULL END AS sheet,
t.ltv_1,t.audit_1,t.ltv_2,t.audit_2,t.ltv_3,t.audit_3,t.ltv_7,t.audit_7,t.ltv_14,t.audit_14,t.ltv_15,t.audit_15,t.ltv_30,t.audit_30
FROM `wajenigeria.track_hfyl.user_ltv` t LEFT JOIN media_map m ON t.first_channel=m.channel
WHERE t.target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND t.app_id=90006 AND t.data_type=1
)
SELECT cohort_date,sheet,COUNT(*) AS source_rows,
SUM(IFNULL(ltv_1,0)-IFNULL(audit_1,0)) AS ct_1, SUM(IFNULL(ltv_2,0)-IFNULL(audit_2,0)) AS ct_2, SUM(IFNULL(ltv_3,0)-IFNULL(audit_3,0)) AS ct_3, SUM(IFNULL(ltv_7,0)-IFNULL(audit_7,0)) AS ct_7, SUM(IFNULL(ltv_14,0)-IFNULL(audit_14,0)) AS ct_14, SUM(IFNULL(ltv_15,0)-IFNULL(audit_15,0)) AS ct_15, SUM(IFNULL(ltv_30,0)-IFNULL(audit_30,0)) AS ct_30
FROM mapped WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND sheet IS NOT NULL
GROUP BY cohort_date,sheet ORDER BY cohort_date,sheet LIMIT 3000;

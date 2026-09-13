WITH scoped AS (
SELECT target_day AS cohort_date,download_channel,first_channel,first_sub_channel,
ltv_14,audit_14,ltv_15,audit_15,ltv_30,audit_30
FROM `wajenigeria.track_hfyl.user_ltv`
WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
AND app_id=90006 AND data_type=1
AND download_channel IN ('WajeSpecial','PAWAJEIOS','PAWAJEBETH5','PAWAJEH5','PAPAWAJEH5GA','PAWAJEH5PWW')
)
SELECT download_channel,first_channel,first_sub_channel,COUNT(*) AS source_rows,
MIN(cohort_date) AS start_date,MAX(cohort_date) AS end_date
FROM scoped WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
GROUP BY download_channel,first_channel,first_sub_channel
ORDER BY download_channel,source_rows DESC LIMIT 3000;

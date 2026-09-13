WITH source AS (
 SELECT target_day AS stat_date,app_id,user_id,app_version
 FROM `wajenigeria.origin_hfyl.view_user_version_daily`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-09'
)
SELECT stat_date,app_id,COUNT(*) AS source_rows,
 COUNT(DISTINCT user_id) AS distinct_accounts,
 COUNTIF(user_id IS NULL OR user_id='') AS missing_user_rows,
 COUNTIF(app_version IS NULL OR app_version='') AS blank_version_rows
FROM source
WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-09'
GROUP BY stat_date,app_id
ORDER BY stat_date,app_id
LIMIT 3000;

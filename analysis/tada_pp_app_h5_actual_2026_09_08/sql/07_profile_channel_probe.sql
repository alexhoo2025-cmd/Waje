WITH profile_rows AS (
 SELECT target_day AS stat_date,user_id,register_day,register_time,first_channel,
        download_channel,first_package_name,first_client_type,is_test_uid
 FROM `wajenigeria.origin_hfyl.user_xlid`
 WHERE target_day BETWEEN DATE '2019-01-01' AND DATE '2026-09-07' AND app_id=90006
)
SELECT first_package_name,first_client_type,first_channel,download_channel,
       COUNT(1) AS profile_rows,COUNT(DISTINCT user_id) AS users,
       COUNTIF(register_time IS NULL OR register_time<=0) AS missing_registration_rows,
       COUNTIF(register_day IS NULL OR register_day='') AS missing_registration_day_rows,
       COUNTIF(first_channel IS DISTINCT FROM download_channel) AS channel_diff_rows,
       COUNTIF(is_test_uid=1) AS test_profile_rows
FROM profile_rows
WHERE stat_date BETWEEN DATE '2019-01-01' AND DATE '2026-09-07'
GROUP BY first_package_name,first_client_type,first_channel,download_channel
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY users DESC
LIMIT 1000;

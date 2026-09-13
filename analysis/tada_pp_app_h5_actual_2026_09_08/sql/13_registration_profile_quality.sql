-- Account-level checks remain inside BigQuery. Only whole-population counts leave it.
WITH candidates AS (
 SELECT target_day AS stat_date,user_id,register_time,register_day,
        download_channel,first_channel
 FROM `wajenigeria.origin_hfyl.user_xlid`
 WHERE target_day BETWEEN DATE '2019-01-01' AND DATE '2026-09-07'
   AND app_id=90006 AND user_id IS NOT NULL AND user_id!=''
), parsed AS (
 SELECT user_id,register_time,
        CASE WHEN register_time BETWEEN 1262304000000 AND 1788908399999
             THEN DATE(TIMESTAMP_MILLIS(register_time),'Africa/Lagos') END AS registration_date,
        SAFE_CAST(SUBSTR(register_day,1,10) AS DATE) AS stored_registration_date,
        COALESCE(NULLIF(download_channel,''),NULLIF(first_channel,'')) AS channel_name
 FROM candidates WHERE stat_date BETWEEN DATE '2019-01-01' AND DATE '2026-09-07'
), per_account AS (
 SELECT user_id,COUNT(1) AS profile_rows,
        COUNTIF(register_time>0 AND registration_date IS NULL) AS invalid_positive_registration_rows,
        COUNT(DISTINCT registration_date) AS registration_dates,
        MIN(registration_date) AS first_registration_date,
        COUNT(DISTINCT IF(registration_date IS NOT NULL,channel_name,NULL)) AS registered_channel_count,
        COUNTIF(registration_date IS NOT NULL AND stored_registration_date IS NOT NULL AND registration_date!=stored_registration_date) AS disagreement_rows,
        COUNTIF(registration_date IS NOT NULL AND stored_registration_date IS NOT NULL) AS comparable_date_rows,
        ARRAY_AGG(STRUCT(channel_name)
          ORDER BY IF(registration_date IS NOT NULL,0,1),register_time,COALESCE(channel_name,'') LIMIT 1)[OFFSET(0)] AS first_record
 FROM parsed GROUP BY user_id
)
SELECT COUNT(1) AS accounts,
       SUM(profile_rows) AS profile_rows,
       COUNTIF(profile_rows>1) AS accounts_with_multiple_profiles,
       COUNTIF(registration_dates=0) AS accounts_without_valid_registration,
       COUNTIF(registration_dates>1) AS accounts_with_registration_date_conflicts,
       COUNTIF(registered_channel_count>1) AS accounts_with_multiple_registered_channels,
       COUNTIF(first_record.channel_name IS NULL OR UPPER(first_record.channel_name) IN ('UNKNOWN','-9999','0')) AS accounts_with_unknown_first_channel,
       COUNTIF(disagreement_rows>0) AS accounts_with_stored_date_disagreement,
       SUM(comparable_date_rows) AS comparable_date_rows,
       SUM(disagreement_rows) AS stored_date_disagreement_rows,
       SUM(invalid_positive_registration_rows) AS invalid_positive_registration_rows,
       MIN(first_registration_date) AS earliest_registration_date,
       MAX(first_registration_date) AS latest_registration_date,
       COUNTIF(first_registration_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07') AS accounts_registered_in_requested_window
FROM per_account
HAVING COUNT(1)>=10
LIMIT 10;

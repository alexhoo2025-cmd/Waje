WITH raw_profiles AS (
 SELECT user_id,target_day AS cohort_date,
 SAFE.PARSE_DATE('%Y-%m-%d',register_day) AS register_date,first_client_type
 FROM `wajenigeria.origin_hfyl.user_events`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
 AND app_id=90006 AND user_id IS NOT NULL AND user_id!=''
), per_user AS (
 SELECT user_id,COUNT(*) AS profile_rows,
 COUNTIF(cohort_date=register_date) AS aligned_rows,
 COUNTIF(register_date IS NULL) AS missing_register_rows,
 COUNTIF(register_date<DATE '2026-08-01' OR register_date>DATE '2026-08-31') AS outside_august_rows,
 COUNT(DISTINCT register_date) AS register_variants,
 COUNT(DISTINCT first_client_type) AS platform_variants
 FROM raw_profiles
 WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
 GROUP BY user_id
)
SELECT COUNT(*) AS distinct_users,SUM(profile_rows) AS profile_rows,
 SUM(aligned_rows) AS date_aligned_rows,SUM(missing_register_rows) AS missing_register_rows,
 SUM(outside_august_rows) AS outside_august_rows,
 COUNTIF(register_variants>1) AS users_with_registration_conflict,
 COUNTIF(platform_variants>1) AS users_with_platform_conflict,
 COUNTIF(profile_rows>1) AS users_with_multiple_rows
FROM per_user
HAVING COUNT(*)>=10
LIMIT 1;

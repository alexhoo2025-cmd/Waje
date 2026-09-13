-- Paid cohorts, successful order-confirmed first-pay date, aggregate-only.
WITH profile_versions AS (
 SELECT user_id, target_day AS cohort_date,
   SAFE.PARSE_DATE('%Y-%m-%d',register_day) AS register_date,
   first_pay_date, first_client_type,
   COALESCE(NULLIF(first_package_name,''),'(blank)') AS package_name,
   COALESCE(NULLIF(download_channel,''),'(blank)') AS channel
 FROM `wajenigeria.origin_hfyl.user_events`
 WHERE target_day BETWEEN DATE '2020-01-01' AND DATE '2026-09-03'
   AND user_id IS NOT NULL AND user_id != ''
), profiles AS (
 SELECT user_id,
   ARRAY_AGG(STRUCT(register_date, first_pay_date, first_client_type, package_name, channel)
     ORDER BY cohort_date DESC, first_pay_date DESC LIMIT 1)[OFFSET(0)] AS p
 FROM profile_versions
 WHERE cohort_date BETWEEN DATE '2020-01-01' AND DATE '2026-09-03'
 GROUP BY user_id
)
SELECT FORMAT_DATE('%Y-%m', p.register_date) AS cohort_month,
 CASE WHEN p.first_client_type=2 THEN 'Android'
      WHEN p.first_client_type=1 THEN 'iOS'
      WHEN p.first_client_type=3 AND p.channel IN ('PAWAJEH5PWA','PAWAJEH5PWAT','PAWAJEH5PWW') THEN 'PWA候选渠道（待确认）'
      WHEN p.first_client_type=3 THEN 'H5（不含PWA候选渠道）'
      ELSE '平台未识别' END AS platform,
 COUNT(*) AS registered_users
FROM profiles
WHERE p.register_date BETWEEN DATE '2026-06-01' AND DATE '2026-08-31'
GROUP BY cohort_month,platform
HAVING COUNT(*)>=10
ORDER BY cohort_month,platform
LIMIT 100;

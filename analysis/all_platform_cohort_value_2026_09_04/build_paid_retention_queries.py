"""Generate bounded, aggregate-only payer cohort queries; daily records stay in BQ."""
from pathlib import Path
import calendar

ROOT = Path(__file__).resolve().parent
TEMPLATE = """-- Paid cohorts, successful order-confirmed first-pay date, aggregate-only.
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
), order_days AS (
 SELECT target_day AS payment_date, user_id, LOGICAL_OR(is_first_buy IS TRUE) AS has_first_payment
 FROM `wajenigeria.origin_hfyl.view_metaevent_order`
 WHERE target_day BETWEEN DATE '@START@' AND DATE '@END@'
   AND is_success='pay_success'
   AND user_id IS NOT NULL AND user_id != '' AND order_no IS NOT NULL AND order_no != ''
 GROUP BY payment_date,user_id
), candidates AS (
 SELECT p.user_id, '新增付费（注册当日付费）' AS payer_group, p.p.register_date AS cohort_date,
   p.p.first_client_type AS client_type,p.p.package_name AS package_name,p.p.channel AS channel
 FROM profiles p JOIN order_days o ON p.user_id=o.user_id AND p.p.register_date=o.payment_date
 WHERE p.p.register_date BETWEEN DATE '@START@' AND DATE '@END@'
 UNION ALL
 SELECT p.user_id, '首次付费（历史首充）' AS payer_group, p.p.first_pay_date AS cohort_date,
   p.p.first_client_type AS client_type,p.p.package_name AS package_name,p.p.channel AS channel
 FROM profiles p JOIN order_days o ON p.user_id=o.user_id AND p.p.first_pay_date=o.payment_date
 WHERE p.p.first_pay_date BETWEEN DATE '@START@' AND DATE '@END@' AND o.has_first_payment
), cohorts AS (
 SELECT user_id,payer_group,cohort_date,package_name,channel,
   CASE WHEN client_type=2 THEN 'Android'
        WHEN client_type=1 THEN 'iOS'
        WHEN client_type=3 AND channel IN ('PAWAJEH5PWA','PAWAJEH5PWAT','PAWAJEH5PWW') THEN 'PWA候选渠道（待确认）'
        WHEN client_type=3 THEN 'H5（不含PWA候选渠道）'
        ELSE '平台未识别' END AS platform
 FROM candidates
 WHERE cohort_date BETWEEN DATE '@START@' AND DATE '@END@'
), activity AS (
 SELECT target_day AS activity_date,user_id
 FROM `wajenigeria.origin_hfyl.view_user_version_daily`
 WHERE target_day BETWEEN DATE '@START@' AND DATE '2026-09-03'
 GROUP BY activity_date,user_id
), activity_dates AS (
 SELECT activity_date,COUNT(*) AS rows_seen FROM activity GROUP BY activity_date
), daily_flags AS (
 SELECT c.user_id,c.payer_group,c.cohort_date,c.platform,c.package_name,c.channel,d AS day_number,
   IF(cal.activity_date IS NOT NULL,1,0) AS eligible,
   IF(a.user_id IS NOT NULL,1,0) AS retained
 FROM cohorts c CROSS JOIN UNNEST([2,3,4,5,6,7,8,9,10,11,12,13,14,30,60,90]) AS d
 LEFT JOIN activity_dates cal ON cal.activity_date=DATE_ADD(c.cohort_date,INTERVAL d-1 DAY)
 LEFT JOIN activity a ON a.user_id=c.user_id AND a.activity_date=DATE_ADD(c.cohort_date,INTERVAL d-1 DAY)
), aggregated AS (
 SELECT payer_group,platform,
   IF(GROUPING(package_name)=1,'全部包',package_name) AS output_package_name,
   IF(GROUPING(channel)=1,'全部渠道',channel) AS output_channel,
   IF(GROUPING(channel)=1,'平台','包与渠道') AS breakdown,
   day_number,COUNT(*) AS cohort_users,SUM(eligible) AS eligible_users,
   SUM(IF(eligible=1,retained,0)) AS retained_users,
   MIN(IF(eligible=1,cohort_date,NULL)) AS eligible_cohort_start,
   MAX(IF(eligible=1,cohort_date,NULL)) AS eligible_cohort_end
 FROM daily_flags
 GROUP BY GROUPING SETS ((payer_group,platform,day_number),(payer_group,platform,package_name,channel,day_number))
)
SELECT '@MONTH@' AS cohort_month,payer_group,platform,output_package_name AS package_name,output_channel AS channel,breakdown,day_number,
 cohort_users,eligible_users,
 IF(eligible_users>=10,retained_users,NULL) AS retained_users,
 IF(eligible_users>=10,SAFE_DIVIDE(retained_users,eligible_users),NULL) AS retention_rate,
 eligible_cohort_start,eligible_cohort_end,DATE '2026-09-03' AS data_cutoff_date
FROM aggregated
WHERE cohort_users>=10
ORDER BY breakdown,payer_group,platform,channel,day_number
LIMIT 3000;
"""

for month in (6,7,8):
    m=f'2026-{month:02d}'
    sql=TEMPLATE.replace('@START@',m+'-01').replace('@END@',f'{m}-{calendar.monthrange(2026,month)[1]:02d}').replace('@MONTH@',m)
    (ROOT/'sql'/f'13_paid_retention_server_success_{m}.sql').write_text(sql,encoding='utf-8')

registration_sql = TEMPLATE.split(', order_days AS (')[0] + """
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
"""
(ROOT/'sql'/'14_paid_cohort_registration_denominators.sql').write_text(registration_sql,encoding='utf-8')

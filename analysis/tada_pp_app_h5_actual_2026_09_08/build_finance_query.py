from pathlib import Path
from build_full_queries import base

P=Path(__file__).resolve().parent
sql=base().split(', events AS (',1)[0]+""", events AS (
 SELECT target_day AS stat_date,user_id,event_type,is_success,is_accept,noun_type,asset_id,
        pay_amount,cash_num,change_count,order_no,serial_num,salt_key,server_time,is_test_uid
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND app_id=90006 AND event_type IN ('ORDER','WITHDRAW','AUDIT')
), dedup AS (
 SELECT stat_date,user_id,event_type,is_success,is_accept,noun_type,asset_id,pay_amount,cash_num,change_count
 FROM events WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
  AND (is_test_uid IS NULL OR is_test_uid!=1)
  AND (event_type!='ORDER' OR is_success='pay_success')
 QUALIFY ROW_NUMBER() OVER(PARTITION BY event_type,is_success,is_accept,COALESCE(NULLIF(order_no,''),NULLIF(serial_num,''),salt_key)
   ORDER BY SAFE_CAST(server_time AS INT64) DESC)=1
), labelled AS (
 SELECT e.stat_date,e.user_id,e.event_type,e.is_accept,e.noun_type,e.asset_id,e.pay_amount,e.cash_num,e.change_count,
 CASE WHEN p.channel_platform IN ('APP_Android','APP_iOS') THEN 'APP' ELSE COALESCE(p.channel_platform,'unmapped') END AS platform,
 CASE WHEN p.registration_date IS NULL THEN 'unknown_registration'
      WHEN DATE_DIFF(e.stat_date,p.registration_date,DAY)<0 THEN 'invalid_registration'
      WHEN DATE_DIFF(e.stat_date,p.registration_date,DAY)<30 THEN 'new_30d' ELSE 'old_over_30d' END AS age_group
 FROM dedup e LEFT JOIN mapped_profiles p ON p.user_id=e.user_id
)
SELECT IF(GROUPING(stat_date)=1,'period','daily') AS time_grain,COALESCE(stat_date,DATE '2026-08-01') AS date_key,
 IF(GROUPING(platform)=1,'all_platforms',platform) AS platform_group,
 IF(GROUPING(age_group)=1,'all_ages',age_group) AS age_segment,
 event_type,is_accept,noun_type,asset_id,
 COUNT(1) AS dedup_events,COUNT(DISTINCT user_id) AS accounts,
 SUM(pay_amount) AS paid_amount_native,SUM(cash_num) AS cash_num_native,SUM(change_count) AS change_count_native
FROM labelled
GROUP BY GROUPING SETS((platform,age_group,event_type,is_accept,noun_type,asset_id),(platform,event_type,is_accept,noun_type,asset_id),
 (stat_date,platform,event_type,is_accept,noun_type,asset_id),(event_type,is_accept,noun_type,asset_id))
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY event_type,time_grain,date_key,platform_group,age_segment,is_accept
LIMIT 1500;
"""
path=P/'sql/22_full_finance.sql'
if path.exists():raise RuntimeError('Preserve existing SQL')
path.write_text(sql)
print('Generated deduplicated payment and withdrawal-stage aggregates; AUDIT is not assumed to be bank payout success')

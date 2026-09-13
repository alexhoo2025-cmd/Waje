"""Origin-derived queries: bounded dates, aggregate-only, declared channel filters."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
CHANNELS=[('WajeSpecial-facebook','APP','WajeSpecial',80),('WajeSpecial-googleadwords_int','APP','WajeSpecial',81),('WajeSpecial-Google商店','APP','WajeSpecial',84),('WAJEIOS-AppStore商店','APP','PAWAJEIOS',58),('WAJEBETH5','H5','PAWAJEBETH5',None),('wajeH5-facebook','H5','PAWAJEH5',80),('wajeH5ga-googlewords_int','H5','PAPAWAJEH5GA',81),('PWA','PWA候选','PAWAJEH5PWW',80)]
(P/'channels.json').write_text(json.dumps([dict(zip(['sheet','group','download_channel','first_media'],r))for r in CHANNELS],ensure_ascii=False,indent=2))
case='CASE\n'+'\n'.join("WHEN download_channel='%s'%s THEN '%s'"%(code,'' if media is None else f' AND first_media={media}',sheet)for sheet,group,code,media in CHANNELS)+"\nELSE NULL END"
def save(name,sql,start='2026-08-01',end='2026-09-09'):
    (P/(name+'.sql')).write_text(sql)
    (P/(name+'.scope.json')).write_text(json.dumps({'start':start,'end':end,'purpose':'Origin algorithm reproduction; each query separately dry-run with shared audit budget'}))
base=f"""WITH raw_profiles AS (
SELECT target_day AS cohort_date,app_id,xl_id,user_id,DATE(first_pay_date) AS first_pay_date,
 {case} AS sheet
FROM `wajenigeria.origin_hfyl.user_events`
WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND app_id=90006
), profiles AS (
SELECT cohort_date,sheet,xl_id,user_id,first_pay_date FROM raw_profiles
WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND sheet IS NOT NULL
)
"""
save('01_origin_denominators',base+"""SELECT cohort_date,sheet,
COUNT(DISTINCT xl_id) AS new_xl_ids,
COUNT(DISTINCT IF(cohort_date=first_pay_date,xl_id,NULL)) AS new_paid_xl_ids,
COUNT(DISTINCT user_id) AS users,
COUNTIF(xl_id IS NULL OR xl_id='') AS empty_xl_rows,
COUNTIF(user_id IS NULL OR user_id='') AS empty_user_rows
FROM profiles GROUP BY cohort_date,sheet ORDER BY cohort_date,sheet LIMIT 3000;
""",end='2026-08-31')
for number,(start,end) in enumerate([('2026-08-02','2026-08-15'),('2026-08-16','2026-08-29'),('2026-08-30','2026-09-09')],2):
    sql=base+f""", activity AS (
SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.view_metaevent_active_events`
WHERE target_day BETWEEN DATE '{start}' AND DATE '{end}' AND app_id=90006
GROUP BY activity_date,xl_id
), expanded AS (
SELECT p.cohort_date,p.sheet,p.xl_id,p.user_id,p.first_pay_date,day_number,
 DATE_ADD(p.cohort_date,INTERVAL day_number-1 DAY) AS observation_date,sample_mode
FROM profiles p CROSS JOIN UNNEST([2,3,4,5,6,7,8,9,10,11,12,13,14,15,30]) AS day_number
CROSS JOIN UNNEST(['各日达标范围','固定8月1—26日']) AS sample_mode
WHERE (sample_mode='各日达标范围' OR (p.cohort_date<=DATE '2026-08-26' AND day_number<=15))
)
SELECT p.sheet,p.day_number,p.sample_mode,
MIN(p.cohort_date) AS cohort_start,MAX(p.cohort_date) AS cohort_end,
COUNT(DISTINCT CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id)) AS eligible_new,
COUNT(DISTINCT IF(a.xl_id IS NOT NULL,CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id),NULL)) AS returned_new,
COUNT(DISTINCT IF(p.cohort_date=p.first_pay_date,CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id),NULL)) AS eligible_new_paid,
COUNT(DISTINCT IF(p.cohort_date=p.first_pay_date AND a.xl_id IS NOT NULL,CONCAT(CAST(p.cohort_date AS STRING),'|',p.xl_id),NULL)) AS returned_new_paid
FROM expanded p LEFT JOIN activity a ON p.xl_id=a.xl_id AND p.observation_date=a.activity_date
WHERE p.observation_date BETWEEN DATE '{start}' AND DATE '{end}'
GROUP BY p.sheet,p.day_number,p.sample_mode
HAVING eligible_new>=10
ORDER BY p.sheet,p.sample_mode,p.day_number LIMIT 3000;
"""
    save(f'0{number}_origin_returns',sql)
print('Prepared denominators and three disjoint observation-date return segments')

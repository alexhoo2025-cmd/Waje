import json
from pathlib import Path
P=Path(__file__).resolve().parent;m=json.loads((P/'channels.json').read_text())
case='CASE '+' '.join("WHEN download_channel='%s'%s THEN '%s'"%(r['download_channel'],'' if r['first_media'] is None else f" AND m.selected_media_id={r['first_media']}",r['sheet'])for r in m)+' ELSE NULL END'
sql=f"""WITH media_map AS (
SELECT channel,ANY_VALUE(media_id) AS selected_media_id
FROM `wajenigeria.ares_hfyl.app_channel_media_package`
WHERE app_id=90006 GROUP BY channel HAVING COUNT(DISTINCT media_id)=1
), mapped AS (
SELECT t.target_day AS cohort_date,t.download_channel,{case} AS sheet,
t.ltv_1,t.audit_1,t.ltv_2,t.audit_2,t.ltv_3,t.audit_3,t.ltv_7,t.audit_7,t.ltv_14,t.audit_14,t.ltv_15,t.audit_15,t.ltv_30,t.audit_30
FROM `wajenigeria.track_hfyl.user_ltv` t LEFT JOIN media_map m ON t.first_channel=m.channel
WHERE t.target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND t.app_id=90006 AND t.data_type=1
)
SELECT cohort_date,sheet,COUNT(*) AS source_rows,
{', '.join(f'SUM(IFNULL(ltv_{d},0)-IFNULL(audit_{d},0)) AS ct_{d}'for d in [1,2,3,7,14,15,30])}
FROM mapped WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND sheet IS NOT NULL
GROUP BY cohort_date,sheet ORDER BY cohort_date,sheet LIMIT 3000;
"""
(P/'09_origin_ct.sql').write_text(sql);(P/'09_origin_ct.scope.json').write_text(json.dumps({'start':'2026-08-01','end':'2026-08-31','purpose':'Origin data_type=1 cumulative C-T; media mapping candidate must match channel-page reference before use'}))

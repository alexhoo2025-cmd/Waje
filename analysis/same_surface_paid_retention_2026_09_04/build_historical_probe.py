from pathlib import Path

ROOT=Path(__file__).resolve().parent
sql=(ROOT/'sql/04_same_surface_recent.sql').read_text()
sql=sql.replace("2026-09-01","2026-06-01")
sql=sql.replace('SELECT payer_group,cohort_date,origin_surface,anchor_client,day_number,\n COUNT(*)',
                "SELECT payer_group,FORMAT_DATE('%Y-%m',cohort_date) AS cohort_month,origin_surface,anchor_client,day_number,\n COUNT(*)")
sql=sql.replace('GROUP BY payer_group,cohort_date,origin_surface,anchor_client,day_number',
                'GROUP BY payer_group,cohort_month,origin_surface,anchor_client,day_number')
sql=sql.replace('ORDER BY payer_group,cohort_date,anchor_client,day_number','ORDER BY payer_group,cohort_month,anchor_client,day_number')
(ROOT/'sql/05_same_surface_full_history.sql').write_text(sql,encoding='utf-8')

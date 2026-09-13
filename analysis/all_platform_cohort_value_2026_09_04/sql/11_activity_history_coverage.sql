WITH activity AS (
 SELECT target_day AS cohort_date,user_id
 FROM `wajenigeria.origin_hfyl.view_user_version_daily`
 WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-09-03'
)
SELECT cohort_date, COUNT(DISTINCT user_id) AS active_users
FROM activity
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-03'
GROUP BY cohort_date
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY cohort_date
LIMIT 100;

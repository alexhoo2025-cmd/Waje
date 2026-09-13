WITH scoped AS (
 SELECT event_field,field_value,field_name,SAFE_CAST(SUBSTR(create_time,1,10) AS DATE) AS stat_date
 FROM `wajenigeria.track_hfyl.conf_event_field_enums`
 WHERE event_field IN ('is_accept','audit_type','withdraw_status','pay_status')
)
SELECT event_field,field_value,MAX(field_name) AS meaning,COUNT(1) AS definition_rows
FROM scoped WHERE stat_date<=DATE '2026-09-08' OR stat_date IS NULL
GROUP BY event_field,field_value ORDER BY event_field,field_value
LIMIT 100;

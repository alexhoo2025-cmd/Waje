WITH scoped AS (
 SELECT event_field,field_value,field_name,
        SAFE_CAST(SUBSTR(create_time,1,10) AS DATE) AS stat_date
 FROM `wajenigeria.track_hfyl.conf_event_field_enums`
 WHERE event_field IN ('client_type','mode_id','noun_type','asset_id','game_type','is_success','is_test_uid')
)
SELECT event_field,field_value,MAX(field_name) AS meaning,
       COUNT(1) AS definition_rows,COUNTIF(stat_date IS NULL) AS unparsed_creation_date_rows
FROM scoped WHERE stat_date<=DATE '2026-09-08' OR stat_date IS NULL
GROUP BY event_field,field_value
ORDER BY event_field,field_value
LIMIT 1000;

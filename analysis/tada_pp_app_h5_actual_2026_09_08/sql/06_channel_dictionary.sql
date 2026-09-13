WITH dictionary_rows AS (
 SELECT channel,channel_name,package_name,os,use_status,
        SAFE_CAST(SUBSTR(create_time,1,10) AS DATE) AS stat_date,
        SAFE_CAST(SUBSTR(update_time,1,10) AS DATE) AS mapping_update_date
 FROM `wajenigeria.ares_hfyl.app_channel_media_package`
 WHERE app_id=90006
)
SELECT channel,MAX(channel_name) AS channel_label,package_name,os,
       COUNT(1) AS definition_rows,COUNT(DISTINCT use_status) AS distinct_statuses,
       MIN(stat_date) AS earliest_mapping_date,MAX(mapping_update_date) AS latest_mapping_update
FROM dictionary_rows
WHERE stat_date<=DATE '2026-09-08' OR stat_date IS NULL
GROUP BY channel,package_name,os
ORDER BY channel,package_name,os
LIMIT 1000;

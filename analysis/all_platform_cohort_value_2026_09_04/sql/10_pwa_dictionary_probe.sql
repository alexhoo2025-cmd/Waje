WITH mapping AS (
 SELECT channel, channel_name, package_name, os, SAFE_CAST(create_time AS TIMESTAMP) AS created_at
 FROM `wajenigeria.ares_hfyl.app_channel_media_package`
)
SELECT channel, channel_name, package_name, os, COUNT(*) AS mapping_rows
FROM mapping
WHERE (created_at < TIMESTAMP '2026-09-05 00:00:00+00' OR created_at IS NULL)
 AND (REGEXP_CONTAINS(UPPER(COALESCE(channel,'')), r'PWA|PWW')
 OR REGEXP_CONTAINS(UPPER(COALESCE(channel_name,'')),r'PWA|PWW'))
GROUP BY channel,channel_name,package_name,os
LIMIT 100;

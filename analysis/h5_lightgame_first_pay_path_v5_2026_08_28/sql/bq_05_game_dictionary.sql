SELECT
  game_id,
  game_name,
  game_appkey,
  company_id,
  server_code
FROM `wajenigeria.origin_hfyl.sys_game`
WHERE game_id IN (9003, 9008, 9010, 9011, 9016)
ORDER BY game_id;


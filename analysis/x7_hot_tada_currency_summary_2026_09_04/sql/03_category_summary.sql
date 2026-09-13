-- Executed in isolated local SQLite; input is the 161 reviewed game-level
-- rows from the supplied workbook. The workbook Total row is excluded.
WITH grouped AS (
  SELECT game_type, COUNT(*) AS games,
         SUM(total_bet) AS total_bet, SUM(total_win) AS total_win,
         SUM(net_win) AS net_win, SUM(total_count) AS total_count
  FROM reviewed_game_summary
  GROUP BY game_type
)
SELECT game_type, games, total_bet, total_win, net_win, total_count,
       1.0 * total_win / NULLIF(total_bet, 0) AS weighted_rtp,
       1.0 * net_win / NULLIF(total_bet, 0) AS net_margin,
       1.0 * total_bet / NULLIF(SUM(total_bet) OVER (), 0) AS bet_share,
       1.0 * net_win / NULLIF(SUM(net_win) OVER (), 0) AS net_share
FROM grouped
ORDER BY total_bet DESC;

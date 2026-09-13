-- Executed locally in an isolated in-memory SQLite database.
-- Input: the seven game-level aggregate CSV rows joined through the reviewed
-- TaDa-provider/name catalog mapping; no user-level records are loaded.
-- These are cumulative snapshot amounts, not date-window transactions.
SELECT
  game_name, waje_game_id, third_party_game_id, sample_users,
  cumulative_rounds, sample_bet,
  1.0 * cumulative_rounds / NULLIF(sample_users, 0) AS rounds_per_user,
  1.0 * sample_bet / NULLIF(sample_users, 0) AS bet_per_user,
  last_update, status
FROM reviewed_participation_input
WHERE sample_users >= 10
ORDER BY sample_users DESC, waje_game_id;

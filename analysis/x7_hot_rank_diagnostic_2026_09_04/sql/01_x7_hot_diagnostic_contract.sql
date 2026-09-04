-- TEMPLATE ONLY. Do not execute until the authorised Waje aggregate views are
-- confirmed and the X7 HOT game_id is mapped.
-- Purpose: daily platform/package/entry/ranking/settlement aggregate needed to
-- distinguish recommendation exposure, user repeat play, and game economics.

WITH scoped AS (
  SELECT
    business_date,
    platform,
    package_name,
    app_version,
    web_version,
    release_id,
    entry_source,
    placement_id,
    display_position,
    recommendation_policy_version,
    game_id,
    canonical_game_name,
    impression_count,
    exposed_user_count,
    click_count,
    click_user_count,
    game_enter_user_count,
    favorite_user_count,
    repeat_user_count,
    valid_bet_amount,
    final_payout_amount,
    valid_round_count,
    high_payout_amount,
    data_cutoff_at,
    data_status
  FROM authorised_waje_x7_hot_daily_aggregate -- target view to be confirmed
  WHERE business_date >= DATE_SUB(DATE '2026-09-04', INTERVAL 90 DAY)
    AND business_date < DATE '2026-09-04'
    AND canonical_game_name = 'X7 HOT'
),
daily AS (
  SELECT
    business_date,
    platform,
    package_name,
    app_version,
    web_version,
    release_id,
    entry_source,
    placement_id,
    display_position,
    recommendation_policy_version,
    game_id,
    canonical_game_name,
    SUM(impression_count) AS impression_count,
    SUM(exposed_user_count) AS exposed_user_count,
    SUM(click_count) AS click_count,
    SUM(click_user_count) AS click_user_count,
    SUM(game_enter_user_count) AS game_enter_user_count,
    SUM(favorite_user_count) AS favorite_user_count,
    SUM(repeat_user_count) AS repeat_user_count,
    SUM(valid_bet_amount) AS valid_bet_amount,
    SUM(final_payout_amount) AS final_payout_amount,
    SUM(valid_round_count) AS valid_round_count,
    SUM(high_payout_amount) AS high_payout_amount,
    SAFE_DIVIDE(SUM(click_count), SUM(impression_count)) AS click_rate,
    SAFE_DIVIDE(SUM(game_enter_user_count), SUM(click_user_count)) AS enter_rate,
    SAFE_DIVIDE(SUM(repeat_user_count), SUM(exposed_user_count)) AS repeat_rate,
    SAFE_DIVIDE(SUM(final_payout_amount), SUM(valid_bet_amount)) AS actual_rtp,
    SUM(valid_bet_amount) - SUM(final_payout_amount) AS ggr,
    data_cutoff_at,
    data_status
  FROM scoped
  GROUP BY ALL
)
SELECT *
FROM daily
ORDER BY business_date, platform, package_name, display_position;
